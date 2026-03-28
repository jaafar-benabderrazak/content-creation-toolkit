# Project Research Summary

**Project:** content_creation — AI Generation Quality (v1.1 milestone)
**Domain:** AI-powered video generation pipeline — SDXL image generation, Suno music integration, prompt engineering, quality presets, image caching
**Researched:** 2026-03-28
**Confidence:** MEDIUM (architecture and caching patterns HIGH; Suno API MEDIUM due to no official public API)

## Executive Summary

This milestone (v1.1) upgrades an existing video generation pipeline by introducing three interconnected capabilities: config-driven SDXL prompt templates with profile-specific negative prompts, a Suno music API integration replacing Stable Audio, and a hash-based image cache that eliminates redundant generation on re-runs. The existing stack (PyTorch, diffusers, MoviePy, pydub, Remotion, Pydantic) remains unchanged; net new dependencies are `compel` (SDXL dual-encoder prompt weighting), `diskcache` (persistent SQLite-backed image cache), and `tenacity` (retry/polling for the Suno async API). Architecture research confirms that extracting AI generation into a `generators/` module — `generators/sdxl.py` and `generators/suno.py` — is the correct structural move to prevent the existing `study_with_me_generator.py` from becoming a 1000+ line monolith and to enable code reuse when the TikTok pipeline needs the same capabilities.

The recommended approach is strictly config-driven: all SDXL prompt templates, negative prompts, Suno genre tags, and quality preset parameters live in per-profile YAML files, not Python source. A `QualityProfile` dataclass becomes the single source of truth for all generation axes (SDXL steps/cfg/resolution, Suno model version and output format, video encoder CRF). The `SunoClient` abstraction layer is non-optional given that Suno has no official public API — every available wrapper reverse-engineers Suno's private web endpoints, which can break without notice. A stable-audio fallback path must coexist with Suno integration from day one.

The primary risk is Suno API fragility: all third-party Suno wrappers violate Suno's ToS and can fail silently on any frontend change. Secondary risks are image cache key staleness (if the cache key excludes any generation-determining parameter, stale images are served silently), and vocal bleed from Suno's `make_instrumental` flag (which is probabilistic, not deterministic, with a clean hit rate of ~70-80%). Both risks have clear mitigations: pin the Suno wrapper to an exact version, wrap all Suno calls behind a `generate_music() -> AudioSegment` interface with an explicit Stable Audio fallback, hash all generation parameters into the cache key (not just prompt text), and always generate 2-3 Suno tracks with a validation step before passing audio to video assembly.

---

## Key Findings

### Recommended Stack

The existing stack requires no changes. Three libraries are added. `compel>=2.0.2` provides SDXL-correct prompt weighting via `CompelForSDXL`, which handles SDXL's dual-encoder architecture and produces both `prompt_embeds` and `pooled_prompt_embeds` required by `StableDiffusionXLPipeline` — the base `Compel` class will not work for SDXL. `diskcache>=5.6.3` provides a SQLite-backed, process-restart-safe image cache keyed by SHA-256 of all generation parameters; it is simpler than Redis for local use and well-precedented in the SD community. `tenacity>=8.2.3` wraps the Suno async polling loop with exponential backoff and configurable timeout, eliminating the hung-pipeline failure mode. `requests>=2.31` (likely already present) handles all Suno REST calls.

**Core technologies:**
- `compel>=2.0.2`: SDXL prompt weighting — only library supporting `CompelForSDXL` with pooled embedding output; syntax `word++`/`word--` has minimal overhead
- `diskcache>=5.6.3`: Persistent image cache — SQLite-backed, survives process restarts, hash-keyed entries, 10GB size limit configurable
- `tenacity>=8.2.3`: Suno polling retry — exponential backoff with cap at 30s; mandatory for a generation path that takes 30s–3min
- Suno third-party wrapper (`sunoapi.org` or `kie.ai`): REST music generation — standard Bearer auth, version-pinned; `sunoapi.org` most documented; `kie.ai` supports Suno V5/V4.5

**Critical version requirement:** `compel>=2.0.2` requires `diffusers>=0.26.3` (existing codebase uses 0.26.3 — compatible). Use `CompelForSDXL`, not `Compel`.

### Expected Features

**Must have (table stakes for v1.1):**
- Per-profile SDXL prompt templates in YAML — hardcoded prompts produce identical images across runs; this is the day-one expectation
- Configurable negative prompts per profile — SDXL without profile-specific negatives produces watermarks, bland aesthetics, or style contamination
- Quality preset as unified gate — `QualityProfile` setting must control all generation axes simultaneously (SDXL steps, resolution, Suno model, video CRF); partial control causes quality drift between pipeline stages
- Hash-based image cache — re-generating 24 scenes at 45s each on every run (18 min) is not viable for iterative content creation
- Suno integration with `make_instrumental=True` and profile-matched genre tags from YAML — not hardcoded in Python
- Stable Audio fallback path — mandatory given Suno's ToS and API fragility

**Should have (differentiators for v1.1):**
- Multi-track generation (2-3 candidates) with validation gate before video assembly — mitigates vocal bleed risk
- Parallel Suno task submission before SDXL batch — hides 60-180s Suno latency behind SDXL's 18-min batch; net user impact: zero added wait time
- JSON sidecar files alongside cached images — human-inspectable cache, enables targeted invalidation by profile

**Defer (v1.2+):**
- Duration-aware segment chaining for videos >8 min (`extend_audio` endpoint) — trigger: first long-form video exceeds Suno v5's 8-min cap
- Multi-track UI selection in Gradio — trigger: cache fills with single-track generations that don't survive quality checks

**Defer (v2+):**
- FLUX model support — different prompt format (natural language vs keyword stacks); requires new template schema
- EasyNegative embedding support — requires embedding file management; low ROI vs explicit YAML token list for v1.1

### Architecture Approach

The recommended architecture extracts AI generation into a new `generators/` package (`generators/sdxl.py`, `generators/suno.py`) that the existing `study_with_me_generator.py` delegates to. `PipelineConfig` gains two sub-models (`SDXLSettings`, `SunoSettings`) that each generator receives as typed arguments — generators must not import `PipelineConfig` directly to keep the boundary clean. The `shared/remotion_renderer.py` and `shared/pipeline_runner.py` layers require no changes. Suno task submission happens immediately after config load (before SDXL starts) so that Suno's 60-180s polling wait is absorbed into SDXL's generation time via `concurrent.futures.ThreadPoolExecutor`. The `generate_enhanced_music()` contract (`-> AudioSegment`) is preserved as the interface; Suno implementation sits behind it with Stable Audio as fallback.

**Major components:**
1. `config/pipeline_config.py` + profile YAMLs — central schema extension; `SDXLSettings` and `SunoSettings` sub-models added; all prompt templates, negative prompts, genre tags, and quality parameters live here
2. `generators/sdxl.py` (`SDXLGenerator`) — SDXL prompt assembly from profile templates; batched image generation with hash-based cache lookup/store; refactored from existing inline code in `study_with_me_generator.py`
3. `generators/suno.py` (`SunoClient`) — REST POST/poll/download client; exponential backoff polling; `make_instrumental` enforcement; AudioSegment conversion before return; Stable Audio fallback on failure
4. `study_with_me_generator.py` (refactored) — orchestrator; delegates to generators; adds `suno_generation` and `image_cache` keys to `progress.json` for resumability

**Suggested build order:** Config extension → `generators/sdxl.py` extraction (verifiable: images identical to pre-refactor) → `generators/suno.py` (test standalone against real API key before wiring) → wire Suno into study generator with threading → update profile YAMLs.

### Critical Pitfalls

1. **Suno ToS/API fragility** — Wrap ALL Suno calls in `SunoClient`; pin wrapper to exact version (`==` not `>=`); implement Stable Audio fallback before considering Suno integration done; mock the HTTP layer in all tests (never hit live API in CI).

2. **Cache key missing generation parameters** — Cache key must SHA-256 hash the full parameter dict: `prompt + negative_prompt + quality_preset + profile + seed + model_version`. Hashing only the prompt text silently serves stale images after any other parameter changes. Write a JSON sidecar with every cached image.

3. **Vocal bleed from `make_instrumental=True`** — The flag is probabilistic (~70-80% clean). Always generate 2-3 tracks; run a validation step (librosa pitch detection or listening pass) before passing audio to video assembly. Maintain a bank of 3-5 pre-validated fallback tracks per profile.

4. **Async polling without timeout bounds** — Implement a hard 5-minute timeout with exponential backoff (5s → 10s → 20s → cap at 60s). On timeout, fall back to cached track and continue pipeline. A `while status != "complete"` loop with no max-attempts hangs the entire pipeline on any Suno server-side failure.

5. **SD1.5 negative prompts in SDXL** — SDXL handles anatomy better natively; porting SD1.5 mega-negative-prompts degrades SDXL output quality. SDXL negatives must be short (under 30 tokens), style-focused (`"cartoon, anime, watermark, logo, text"`), and tuned per profile. Never share a single negative prompt across all profiles.

---

## Implications for Roadmap

Based on combined research findings and the dependency graph established in FEATURES.md, the following phase structure is recommended.

### Phase 1: Config Foundation and Prompt Templates
**Rationale:** All other features depend on a stable config schema and resolved prompt template structure. `SDXLSettings`/`SunoSettings` sub-models must exist before generators can read from config. YAML prompt templates must be stable before the cache key can be designed (the hash must be computed from the fully-resolved prompt string, not the template key). Zero runtime risk — config extension has no impact until generators use it.
**Delivers:** Extended `PipelineConfig` with `SDXLSettings` and `SunoSettings`; updated `lofi_study.yaml`, `cinematic.yaml`, `tech_tutorial.yaml` with per-profile SDXL prompts, negative prompts, Suno genre tags, and quality preset parameters
**Addresses:** Prompt template library (P1), negative prompt config (P1), profile-matched genre tags (P1), quality preset as unified gate (P1)
**Avoids:** Pitfall 5 (SD1.5 negatives in SDXL), Pitfall 7 (profile-genre mapping hardcoded in Python)

### Phase 2: SDXL Generator Extraction and Image Caching
**Rationale:** Extracting existing SDXL code into `generators/sdxl.py` is verifiable (images must be identical to pre-refactor) and creates the module boundary needed before any new generation logic is added. Image caching is implemented here because its cache key design depends on the prompt template structure from Phase 1 being finalized. Caching must be implemented before Suno integration (Phase 3) to avoid redundant generation during Suno debugging.
**Delivers:** `generators/sdxl.py` with `SDXLGenerator.build_prompt()` template method and `generate_batch()` with hash-based cache; `.cache/images/` directory with JSON sidecar files; `study_with_me_generator.py` delegating to `SDXLGenerator`
**Uses:** `compel>=2.0.2` (prompt weighting), `diskcache>=5.6.3` (image cache), `hashlib` (SHA-256 cache keys)
**Avoids:** Pitfall 4 (incomplete cache key), Pitfall 5 (SDXL negative prompt design validated against sample images per profile)

### Phase 3: Suno Integration with Fallback and Validation
**Rationale:** Suno is the highest-risk component (unofficial API, ToS exposure, vocal bleed). It is implemented last so the SDXL and caching foundation is stable before introducing the external dependency. The `generate_music() -> AudioSegment` interface contract already exists from Stable Audio — Suno sits behind it without changing callers. Stable Audio fallback and track validation must be implemented and tested before this phase is considered complete.
**Delivers:** `generators/suno.py` (`SunoClient`) with submit/poll/download/convert pipeline; `tenacity`-backed polling with 5-minute hard timeout; 2-3 track generation with vocal validation gate; Stable Audio fallback on failure; `SunoClient` wired into `study_with_me_generator.py` with Suno task submitted in background thread before SDXL loop; `progress.json` extended with `suno_generation` key for resumability
**Uses:** `tenacity>=8.2.3` (polling retry), `requests>=2.31` (REST client), `concurrent.futures.ThreadPoolExecutor` (parallel Suno/SDXL)
**Avoids:** Pitfall 1 (Suno fragility — abstraction layer, exact version pin, fallback), Pitfall 2 (vocal bleed — multi-track + validation), Pitfall 3 (hung poll loop — timeout + backoff), Pitfall 6 (AudioSegment contract preserved)

### Phase Ordering Rationale

- Config must precede generators because generators are parameterized by config sub-models; out-of-order implementation causes scattered hardcoded values that must be refactored
- SDXL extraction precedes Suno integration because the `generators/` package structure must be established before a second generator is added; also, SDXL is deterministic and verifiable, making it a safer first extraction
- Suno is last because it is the highest-risk component; implementing it on top of a stable foundation allows the fallback path to be tested against real Stable Audio output before Suno replaces it
- The parallel Suno/SDXL thread pattern (submit Suno task before SDXL batch) is only possible after both generators are independently stable; this optimization is implemented in Phase 3's wiring step

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Suno Integration):** Suno API provider selection (sunoapi.org vs kie.ai) requires validation of current pricing, `make_instrumental` support, `duration` parameter field names, and exact response schema before implementation. Field names differ between providers. Check `suno.ai/developers` for a first-party API release before committing to a third-party wrapper.
- **Phase 3 (vocal validation):** librosa-based pitch detection for vocal bleed is a heuristic; confidence LOW. Phase planning should investigate lightweight vocal detection options (librosa, a pre-trained VAD model) before committing to an implementation approach.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Config Foundation):** Pydantic sub-model extension and YAML profile structure follow established patterns from the existing codebase; no research needed.
- **Phase 2 (SDXL + Caching):** `compel` and `diskcache` patterns are HIGH confidence from official documentation; extraction refactor follows standard module boundary patterns; no research needed beyond verifying `compel` version compatibility at milestone start.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | `compel`, `diskcache`, `tenacity` additions are HIGH confidence from official sources; Suno provider selection (sunoapi.org vs kie.ai) is MEDIUM — third-party wrappers only |
| Features | MEDIUM | Codebase patterns (table stakes features) HIGH; Suno v5 capabilities (duration, model versions) LOW — based on third-party summaries without official docs |
| Architecture | HIGH | Existing codebase verified directly; generator extraction pattern well-established; Suno REST pattern corroborated across multiple third-party providers |
| Pitfalls | MEDIUM-HIGH | SDXL and caching pitfalls HIGH from verified sources; Suno vocal bleed MEDIUM (community source); ToS risk HIGH from official Suno ToS |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Suno provider field names:** The exact JSON field names for `make_instrumental`, `duration`, `task_id`, `status`, and `audio_url` differ between sunoapi.org and kie.ai. Verify against live documentation before implementing `SunoClient`. If a first-party Suno API has launched at `suno.ai/developers`, prefer it and the third-party pattern is moot.
- **compel version at milestone start:** Confirm `compel` PyPI version is still `>=2.0.2` and compatible with the project's current `diffusers` install before pinning in requirements.txt.
- **diskcache PIL Image serialization:** Test that `diskcache` correctly pickles SDXL 1024x1024 PIL Image objects (expected to work; not yet validated against project's specific output format).
- **Image caching in Python SDXL pipelines:** No authoritative source found for hash-based scene caching outside of ComfyUI's native node pattern. The approach is derived from general content-addressable storage patterns. Flag for validation during Phase 2 implementation.
- **Vocal detection approach for Suno output:** The multi-track + listening-pass strategy is well-motivated; the programmatic heuristic (librosa pitch detection) has LOW confidence as a reliable vocal bleed detector. Validate or substitute during Phase 3 planning.

---

## Sources

### Primary (HIGH confidence)
- `damian0815/compel` GitHub — `CompelForSDXL` usage, SDXL dual-encoder support
- Hugging Face diffusers docs — official compel integration with `StableDiffusionXLPipeline`
- `grantjenks/python-diskcache` GitHub + PyPI — diskcache 5.6.3, SQLite-backed, size limits
- Suno Terms of Service (`suno.com/terms-of-service`) — ToS restrictions on API access and commercial use
- Existing codebase (`study_with_me_generator.py`, `config/pipeline_config.py`, `shared/remotion_renderer.py`) — verified 2026-03-28
- `.planning/codebase/CONCERNS.md` — existing codebase bugs and tech debt

### Secondary (MEDIUM confidence)
- `sunoapi.org` documentation — Suno API quickstart, Bearer auth, polling pattern
- `aimlapi.com` — Suno API Reality blog post; provider landscape; ToS analysis
- `kie.ai` docs — `make_instrumental`, Suno V5/V4.5 support, `duration` parameter
- Layer.ai — SDXL-specific negative prompt guidance
- Neurocanvas — SDXL best practices, prompt structure
- Segmind — SDXL prompt guide (natural language over tags)
- Cache invalidation strategy patterns — Cachee.ai blog

### Tertiary (LOW confidence)
- `gcui-art/suno-api` GitHub — `make_instrumental`, `duration` parameter reference; unofficial tool, fragility risk documented
- Third-party Suno feature summaries (aitoolsdevpro.com, aimlapi.com review) — Suno v5 capabilities; not from official Suno docs
- Suno vocal bleed / instrumental reliability — aimusicservice.com community source
- Prompt template patterns — LTX Studio, Upsampler guides; pattern discovery only, not authoritative

---
*Research completed: 2026-03-28*
*Ready for roadmap: yes*

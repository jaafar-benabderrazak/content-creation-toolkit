# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** One command produces a publish-ready video — from prompt to YouTube upload — with human approval gates via Discord/Slack before anything goes public.
**Current focus:** Milestone v1.4 — Instagram Style Reference System (Phase 24)

## Current Position

Phase: 24 of 24 (v1.4 — Instagram style reference system, @radstream aesthetic, img2img with reference images)
Plan: 2 of 3 completed in current phase
Status: In Progress
Last activity: 2026-03-29 — 24-02 complete: StyleRefSettings schema added to PipelineConfig; cinematic.yaml wired to radstream

Progress: [███████░░░] 70% (v1.4 milestone — 2/3 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 4 (v1.2 milestone; 13+ across all milestones)
- Average duration: 4 min
- Total execution time: 0.27 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08-remotion-compilation | 4 | 16 min | 4 min |
| 09-config-extension | 3 | ~9 min | 3 min |
| 10-sdxl-caching | 2 | ~6 min | 3 min |
| 11-suno-integration | 2 | ~8 min | 4 min |
| 14-vercel-dashboard | 4 | ~25 min | 6 min |

**Recent Trend:**
- Last 5 plans: 08-01 (5 min), 08-02 (3 min), 08-03 (4 min), 08-04 (2 min), 14-04 (est. 6 min)
- Trend: Stable
| Phase 16 P03 | 1 | 1 tasks | 1 files |
| Phase 16-smart-defaults P02 | 8 | 2 tasks | 4 files |
| Phase 17 P03 | 1 | 1 tasks | 1 files |
| Phase 17 P04 | 2 | 1 tasks | 1 files |
| Phase 18-ai-prompt-generation P01 | 1 | 1 tasks | 1 files |
| Phase 19 P02 | 1 | 2 tasks | 1 files |
| Phase 19 P01 | ~5 min | 2 tasks | 3 files |
| Phase 19 P03 | 5 | 3 tasks | 1 files |
| Phase 21 P01 | 2min | 2 tasks | 2 files |
| Phase 21 P03 | 1 | 1 tasks | 1 files |
| Phase 24 P02 | 3 | 1 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting v1.2 work:

- [v1.2 Roadmap]: DFLT phases before BRND — env var pre-fill is consumed by branding fetch (API key sourcing) and must be stable first
- [v1.2 Roadmap]: BRND before AGEN — AGEN-02 (profile-aware prompts) reads profile style; branding assets (avatar, name) must be available before tag pipeline runs end-to-end (AGEN-05)
- [v1.2 Roadmap]: BRND-03 (intro/outro generation) assigned to Phase 17, not a separate phase — it depends on BRND-01 (channel data fetch) and logically completes the branding surface; separating it would leave Phase 17 without a verifiable output
- [v1.2 Roadmap]: Phase numbered 16/17/18 (not 15) — Phase 15 stub removed; continuous numbering from 14 preserved
- [Phase 14]: YouTube quota reads from YOUTUBE_QUOTA_USED env var — pipeline must update env var after each upload
- [Phase 14]: In-memory status log accepted for serverless warm-instance persistence — cold starts reset the log
- [Phase 16-01]: ENV_VAR_MAP excludes OPENAI_API_KEY and REPLICATE_API_TOKEN — no corresponding PipelineConfig fields; add entries only when schema fields exist
- [Phase 16-01]: suno.api_key provenance requires raw YAML pre-read — model validator injects env value before load_with_env_defaults loop can inspect it
- [Phase 16-01]: load_with_env_defaults is the preferred runtime load path; from_yaml remains for tests and tools that don't need env pre-fill
- [Phase 16]: KNOWN_ENV_VARS list-of-dicts preserves insertion order for stdout; None sections silently skip injection; exit code 0 always
- [Phase 16-smart-defaults]: ENV_VAR_MAP inlined in route.ts as TS mirror of Python constant; provenance kept as separate React state; EnvBadge defined inline in ProfileEditor
- [Phase 17-01]: BrandingSettings.refresh_branding is a runtime flag — not added to ENV_VAR_MAP; explicit refresh=True is primary cache invalidation path; TTL (7 days) is safety net only
- [Phase 17-01]: avatar_local_path stored as absolute str in BrandingData; downstream consumers (watermark, thumbnail, intro/outro) read from single cache source under .cache/branding/
- [Phase 17-02]: Lazy import of fetch_channel_branding inside try/except in run_post_process — branding.py never imported at module level; failure is a warning not a crash
- [Phase 17-02]: Avatar composite size fixed at 80px at bottom-right with 16px margin in thumbnail_gen — spec-defined values; no new config fields added
- [Phase 17]: Avatar branching uses two explicit FFmpeg command builds rather than dynamic filter_complex — clearer, easier to debug
- [Phase 17]: generate_branding_clips skips existing files — callers control cache invalidation, consistent with 17-01 cache strategy
- [Phase 17]: All branding imports lazy inside the branding_enabled if-gate — zero overhead when disabled
- [Phase 17]: YAML clip paths explicitly set take precedence over generated branding clips — user config wins
- [Phase 18-01]: No module-level side effects — PromptGenerator instantiation is the API key check point, not import time
- [Phase 18-01]: All OpenAI exceptions wrapped as PromptGenerationError — callers only handle one exception type
- [Phase 18-02]: _run_prompt_generation uses lazy imports (yaml, generators.prompt_generator) — zero overhead when --tags is not used
- [Phase 18-02]: YAML write-back uses yaml.safe_load → mutate → yaml.dump(sort_keys=False) — preserves field ordering in profile YAML
- [Phase 18-02]: cinematic.yaml positive_prompt was already present; Task 2 was a verification pass with no file change
- [Phase 19-01]: jobs.json written on first instantiation if absent — Plan 03 can assume file always present
- [Phase 19-01]: Past-due pending jobs on restart fire immediately via daemon thread — no queue drain delay
- [Phase 19-01]: Atomic save via .json.tmp + Path.replace prevents corrupt JSON on crash
- [Phase 19-01]: _run_job guards on status=='pending' before executing — prevents double-execution on restart
- [Phase 19]: Atomic save via .tmp + Path.replace prevents corrupt JSON on crash
- [Phase 19]: status validation raises ValueError inline in update_status — fast fail at mutation point
- [Phase 19]: Module-level get_roadmap() lazy singleton — zero overhead on import, safe for multi-call UI code
- [Phase 19]: stream_pipeline uses subprocess.Popen generator with 500-line rolling buffer — non-blocking stdout streaming in Gradio
- [Phase 19]: Execute/Schedule/Roadmap tab helper functions defined at module level above build_ui() — importable and testable independently
- [Phase 21]: _validate alias at module level: static method exposed for direct import compatibility
- [Phase 21]: thumbnail_text placed after youtube_tags in PublishSettings — no ENV_VAR_MAP entry (generated content, not credential)
- [Phase 21]: youtube_tags count validation: range 15-20 enforced in _validate() matching _USER_PROMPT spec
- [Phase 24-02]: StyleRefSettings placed after BrandingSettings in pipeline_config.py — style conditioning logically follows branding in the model hierarchy
- [Phase 24-02]: session_file left as Optional[str] = None, commented out in YAML — sensitive path, not a hardcoded value
- [Phase 24-02]: style_strength default 0.6 — safe midpoint matching IP-Adapter scale / Seedream image_input weight semantics
- [Phase 24-02]: backend pattern constraint ^(replicate|local_ipadapter)$ — explicit allowlist prevents silent misconfiguration

### Roadmap Evolution

- Phase 19 added: Local Gradio UI — pipeline execution, scheduling, video content roadmap/queue
- Phase 24 added: Instagram style reference system — @radstream aesthetic, img2img with reference images

### Pending Todos

- Phase 11 pre-planning: validate Suno provider field names (sunoapi.org vs kie.ai) for make_instrumental, duration, task_id, status, audio_url before implementing SunoClient
- Phase 11 pre-planning: investigate lightweight vocal detection options (librosa pitch detection vs pre-trained VAD model)
- Phase 10 pre-planning: confirm compel>=2.0.2 PyPI version compatibility with current diffusers install

### Blockers/Concerns

- [Pre-Phase 5]: YouTube quota increase SLA is variable — file quota increase request with Google if >6 uploads/day required
- [Pre-Phase 7]: AnimateDiff Gradio version pin not yet inspected — run `grep -i gradio AnimateDiff/requirements.txt` before Phase 7 planning
- [Pre-Phase 11]: Suno has no official public API — third-party wrappers can break silently; check suno.ai/developers before committing
- ~~[Phase 17 BRND-03]: Intro/outro generation complexity~~ — RESOLVED in 17-03 (FFmpeg lavfi, avatar overlay conditional)

## Session Continuity

Last session: 2026-03-29
Stopped at: Completed 24-02-PLAN.md — StyleRefSettings schema added to PipelineConfig; cinematic.yaml wired to radstream
Resume file: None

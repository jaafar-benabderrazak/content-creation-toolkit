# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** One command produces a publish-ready video — from prompt to YouTube upload — with human approval gates via Discord/Slack before anything goes public.
**Current focus:** Phase 14 — Vercel Dashboard UI (plan 1/4 complete)

## Current Position

Phase: 14 — Vercel Dashboard UI for Pipeline Config, Token/Credit Monitoring, and Top-Up Controls
Plan: 01 complete (1/4 plans done in phase)
Status: 14-01 done — Next.js 16 dashboard scaffold with sidebar nav, shadcn/ui components, Vercel config
Last activity: 2026-03-28 — 14-01 complete: dashboard/ directory with Next.js 16.2.1, layout.tsx sidebar, vercel.json, .env.example

Progress: [████░░░░░░] 40% (v1.1 milestone)

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 4 min
- Total execution time: 0.27 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 08-the-compilation-via-remotion-should-be-top-notch | 4 | 16 min | 4 min |
| Phase 09-config-extension-and-prompt-templates P02 | 2 | 2 tasks | 3 files |
| Phase 09-config-extension-and-prompt-templates P01 | 2 | 2 tasks | 1 files |
| Phase 09-config-extension-and-prompt-templates P03 | 1 | 2 tasks | 2 files |
| Phase 10-sdxl-generator-extraction-and-image-caching P01 | 1 | 2 tasks | 2 files |
| Phase 11-suno-music-integration P01 | 3 | 2 tasks | 3 files |
| Phase 11-suno-music-integration P02 | 5 | 1 tasks | 1 files |
| Phase 14 P01 | 18 | 2 tasks | 17 files |

### Recent Trend

- Last 5 plans: 08-01 (5 min), 08-02 (3 min), 08-03 (~4 min), 08-04 (2 min)
- Trend: —

Updated after each plan completion.

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Gradio UI placed last (Phase 7) — it is a frontend for what already exists; building it first produces a stub with nothing behind it
- [Roadmap]: CONF-02 (Gradio UI) assigned to Phase 7, not Phase 1 — Phase 1 is schema/YAML/profiles only
- [Research]: Gradio must run in isolated venv from AnimateDiff (AnimateDiff pins Gradio 3.36.1); audit AnimateDiff/requirements.txt before writing any Phase 7 code
- [Research]: YouTube OAuth app must be moved to Production status before unattended uploads — Testing mode limits refresh tokens to 7 days
- [Research]: Use separate GCP project for development to avoid exhausting production quota during testing
- [Phase 08]: ProfileConfig uses explicit interface with union types instead of typeof lofiStudyProfile to prevent TS narrowing rejecting slide and wipe profiles
- [Phase 08]: useWindowedAudioData at 4.0.441 takes options object {src,frame,fps,windowInSeconds} not raw string; AudioVisualizer updated accordingly
- [Phase 08-the-compilation-via-remotion-should-be-top-notch]: Cast component props to any in Root.tsx — Remotion LooseComponentType does not accept typed FC props
- [Phase 08-the-compilation-via-remotion-should-be-top-notch]: Cast getPresentation return to any in StudyVideo.tsx — union of TransitionPresentation types not assignable to single typed slot
- [Phase 08-the-compilation-via-remotion-should-be-top-notch]: _resolve_quality uses lofi-study defaults as fallback for unknown profiles
- [Phase 08-the-compilation-via-remotion-should-be-top-notch]: WAV conversion caches result on disk; on ffmpeg failure returns original path for graceful degradation
- [v1.1 Roadmap]: Phase 9 (config + prompts) must precede Phase 10 (SDXL extraction) — cache key SHA-256 hashes fully-resolved prompt strings; template schema must be stable before cache key is designed
- [v1.1 Roadmap]: Phase 10 (SDXL extraction) must precede Phase 11 (Suno) — generators/ package structure established before second generator is added; SDXL is deterministic and verifiable, making it the safer first extraction
- [v1.1 Roadmap]: Suno assigned to Phase 11 (last) — highest-risk component (unofficial API, ToS exposure, vocal bleed); fallback path tested against real Stable Audio output before Suno replaces it
- [v1.1 Research]: Use CompelForSDXL (not Compel) — base Compel class does not produce pooled_prompt_embeds required by StableDiffusionXLPipeline
- [v1.1 Research]: SDXL negative prompts must be short (under 30 tokens), style-focused, per-profile — SD1.5 mega-lists degrade SDXL output quality
- [v1.1 Research]: Cache key must SHA-256 hash the full parameter dict (prompt + negative_prompt + quality_preset + profile + seed + model_version) — hashing only prompt text silently serves stale images after any other parameter change
- [v1.1 Research]: Pin Suno third-party wrapper to exact version (== not >=); implement Stable Audio fallback before considering Suno integration done
- [v1.1 Research]: Suno make_instrumental flag is probabilistic (~70-80% clean) — always generate 2-3 tracks and validate before passing to video assembly
- [v1.1 Research]: Hard 300s polling timeout on Suno with exponential backoff (5s → 10s → 20s → cap 60s); on timeout fall back to Stable Audio
- [Phase 09-config-extension-and-prompt-templates]: SDXL negative prompts capped at 7 terms per profile — SD1.5 mega-lists degrade SDXL output quality
- [Phase 09-config-extension-and-prompt-templates]: tech_tutorial scene_templates omit {weather}/{time_of_day} variables — consistent with enable_weather: false in profile
- [Phase 09-config-extension-and-prompt-templates]: make_instrumental: true mandatory on all profiles — vocal bleed unacceptable for study/ambient/tutorial content
- [Phase 09-config-extension-and-prompt-templates]: quality_preset validator lives on PipelineConfig — only PipelineConfig has access to both video.quality_preset and sdxl/suno sub-models simultaneously
- [Phase 09-config-extension-and-prompt-templates]: SDXLSettings.negative_prompt and SunoSettings.genre have no defaults — ValidationError on omission enforces PRMT-02 at schema load time
- [Phase 09-config-extension-and-prompt-templates]: str.format_map(_StrictFormatMap) chosen over .format(**kwargs) — enables targeted ValueError with variable name instead of generic KeyError
- [Phase 09-config-extension-and-prompt-templates]: build_compel_prompt tested via sys.modules patch not real GPU — GPU/model dependency excluded from test suite by design
- [Phase 10-sdxl-generator-extraction-and-image-caching]: SDXLGenerator uses lazy torch/diffusers imports in _generate_one — GPU-free module import and unit testing without model weights
- [Phase 10-sdxl-generator-extraction-and-image-caching]: Cache key uses full 64-char SHA-256 digest of sort_keys JSON — any single param change produces different key (SDXL-02)
- [Phase 10-sdxl-generator-extraction-and-image-caching]: create_fallback_image retained in study_with_me_generator.py — has second call site in outer exception handler outside the removed function
- [Phase 10-sdxl-generator-extraction-and-image-caching]: getattr(pipeline_config, 'sdxl', None) or SDXLSettings(...) pattern handles VideoConfig (no sdxl field) without AttributeError at call site
- [Phase 11-suno-music-integration]: Manual timing loop in _poll_until_complete over tenacity decorator — allows elapsed time logging per interval
- [Phase 11-suno-music-integration]: generate_music catches broad Exception covering TimeoutError, HTTPError, RuntimeError — no failure escapes public interface
- [Phase 11-suno-music-integration]: ThreadPoolExecutor(max_workers=1) used in orchestrator — synchronous main() has no event loop; concurrent.futures is the correct async primitive here
- [Phase 11-suno-music-integration]: _suno_executor.shutdown(wait=False) called after audio block — future already resolved at that point; avoids blocking video assembly
- [Phase 14]: Next.js 16.2.1 used instead of 15.x — CVE-2025-66478 patched; autoprefixer required explicitly by Turbopack build
- [Phase 14]: shadcn/ui components written manually — CLI prompts are interactive TTY-only; non-interactive execution requires direct file authoring

### Roadmap Evolution

- Phase 8 added: Remotion compilation quality — top-notch video rendering with advanced effects
- Phases 9-11 added: v1.1 AI Generation Quality milestone (config extension, SDXL caching, Suno integration)
- Phase 12 added: Discord approval loops for images/video + auto YouTube publish
- Phase 13 added: YouTube credential setup + video thumbnail generation
- Phase 14 added: Vercel dashboard UI — pipeline config, token/credit monitoring, top-up controls

### Pending Todos

- Phase 11 pre-planning: validate Suno provider field names (sunoapi.org vs kie.ai) for make_instrumental, duration, task_id, status, audio_url before implementing SunoClient
- Phase 11 pre-planning: investigate lightweight vocal detection options (librosa pitch detection vs pre-trained VAD model) — current approach is LOW confidence heuristic
- Phase 10 pre-planning: confirm compel>=2.0.2 PyPI version compatibility with project's current diffusers install before pinning in requirements.txt
- Phase 10 pre-planning: validate diskcache PIL Image serialization for SDXL 1024x1024 output format

### Blockers/Concerns

- [Pre-Phase 5]: YouTube quota increase SLA is variable — if >6 uploads/day is required, file quota increase request with Google before committing to a release timeline
- [Pre-Phase 7]: AnimateDiff Gradio version pin not yet inspected — determines isolation strategy; run `grep -i gradio AnimateDiff/requirements.txt` before Phase 7 planning
- [Pre-Phase 11]: Suno has no official public API — all third-party wrappers violate Suno's ToS and can break silently on any frontend change; check suno.ai/developers for a first-party API before committing to a third-party wrapper

## Session Continuity

Last session: 2026-03-28T21:45:03Z
Stopped at: Completed 14-01-PLAN.md — Next.js 16 dashboard scaffold with sidebar nav, shadcn/ui, Vercel config; dashboard/ directory created
Resume file: None

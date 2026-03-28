# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** One command produces a publish-ready video — from prompt to YouTube upload — with human approval gates via Discord/Slack before anything goes public.
**Current focus:** Milestone v1.2 — Smart Automation (Phase 16)

## Current Position

Phase: 16 of 18 (v1.2 — Smart Defaults)
Plan: — of — in current phase
Status: Ready to plan
Last activity: 2026-03-28 — v1.2 roadmap created (Phases 16-18: smart defaults, channel branding, AI prompt gen)

Progress: [░░░░░░░░░░] 0% (v1.2 milestone)

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

### Pending Todos

- Phase 11 pre-planning: validate Suno provider field names (sunoapi.org vs kie.ai) for make_instrumental, duration, task_id, status, audio_url before implementing SunoClient
- Phase 11 pre-planning: investigate lightweight vocal detection options (librosa pitch detection vs pre-trained VAD model)
- Phase 10 pre-planning: confirm compel>=2.0.2 PyPI version compatibility with current diffusers install

### Blockers/Concerns

- [Pre-Phase 5]: YouTube quota increase SLA is variable — file quota increase request with Google if >6 uploads/day required
- [Pre-Phase 7]: AnimateDiff Gradio version pin not yet inspected — run `grep -i gradio AnimateDiff/requirements.txt` before Phase 7 planning
- [Pre-Phase 11]: Suno has no official public API — third-party wrappers can break silently; check suno.ai/developers before committing
- [Phase 17 BRND-03]: Intro/outro generation complexity — Remotion or FFmpeg compositing from channel assets; validate asset format (avatar PNG dimensions, description length) before implementation

## Session Continuity

Last session: 2026-03-28
Stopped at: v1.2 roadmap written — Phases 16 (Smart Defaults), 17 (Channel Branding), 18 (AI Prompt Generation) created with full success criteria and 100% requirement coverage
Resume file: None

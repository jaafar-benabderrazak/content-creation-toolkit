# Content Creation Toolkit

## What This Is

A unified Python content generation platform that automates video creation (long-form study videos, short-form TikTok tutorials), with AI-powered image/audio/script generation, automated post-production editing, YouTube publishing, and team notification workflows via Discord/Slack. Designed for a single creator running pipelines locally on a GPU-capable machine.

## Core Value

One command produces a publish-ready video — from prompt to YouTube upload — with human approval gates via Discord/Slack before anything goes public.

## Requirements

### Validated

- ✓ Study video generation with AI images and ambient music — existing
- ✓ TikTok tutorial pipeline with script generation and voiceover — existing
- ✓ Stable Diffusion XL image generation with fallbacks — existing
- ✓ Stable Audio music generation with crossfading — existing
- ✓ OpenAI script generation with template fallback — existing
- ✓ ElevenLabs TTS with OpenAI TTS fallback — existing
- ✓ Progress tracking and resumable generation — existing
- ✓ TikTok direct posting via Content API — existing
- ✓ Configurable video quality presets (1080p/720p/480p) — existing
- ✓ Visual effects (parallax, dynamic lighting, time progression) — existing

### Active (v2.0 — Cloud Deploy)

- [ ] Clerk authentication on the Next.js dashboard (single user)
- [ ] Supabase database for video roadmap, execution history, generated prompts, user settings
- [ ] Cloud pipeline execution via Modal/Replicate (no local GPU needed)
- [ ] GitHub CI/CD for automated deployments
- [ ] Migrate local JSON files (video_roadmap.json, execution_log.json) to Supabase tables
- [ ] Dashboard reads/writes all data from Supabase (not local filesystem)
- [ ] Pipeline trigger sends jobs to cloud workers instead of local subprocess

### Shipped (v1.2 — Smart Automation)

- ✓ Smart defaults + env var fallback — Phase 16
- ✓ YouTube channel branding + auto watermark/intro/outro — Phase 17
- ✓ AI prompt generation (tags → Claude → 8 sections) — Phase 18
- ✓ Local Gradio UI with scheduling + content roadmap — Phase 19
- ✓ Unified Next.js dashboard — Phase 23
- ✓ Instagram style reference system — Phase 24

### Shipped (v1.1 — AI Generation Quality)

- ✓ SDXLSettings/SunoSettings sub-models + quality presets — Phase 9
- ✓ Profile YAML prompt templates with negative prompts — Phase 9
- ✓ PromptTemplate with variable substitution + compel weighting — Phase 9
- ✓ SDXL generator extraction + hash-based image caching — Phase 10
- ✓ Suno music integration via kie.ai with fallback — Phase 11
- ✓ Discord approval loops for images/video — Phase 12
- ✓ YouTube credential setup + auto-publish — Phase 13
- ✓ Vercel dashboard UI — Phase 14

### Shipped (v1.0)

- ✓ Pydantic config schema + YAML profiles + validation — Phase 1
- ✓ Post-processing pipeline (watermark, subtitles, intro/outro) — Phase 2
- ✓ Thumbnail generation (best frame + text overlay) — Phase 3
- ✓ Discord/Slack notifications + approval gate — Phase 4
- ✓ YouTube publisher (OAuth, resumable upload, quota guard) — Phase 5
- ✓ Pipeline integration (shared runner wired into both pipelines) — Phase 6
- ✓ Config UI (Gradio Blocks) — Phase 7
- ✓ Top-notch Remotion video compilation — Phase 8

### Out of Scope

- YouTube scheduling and optimal time posting — v2, keep v1 simple with immediate upload
- Full channel management (playlists, end screens, analytics) — v2
- Web-hosted UI — v1 is local (Gradio or CLI-based)
- Scene-level AI intelligence (auto-trim, pacing) — complex, defer to v2
- Cloud deployment — stays local for now
- Mobile app — not relevant

## Context

- Brownfield codebase: two working pipelines (study_with_me_generator.py, faceless TikTok pipeline) plus AnimateDiff integration
- Known tech debt: bare exceptions, deprecated PIL calls, hardcoded font paths, no tests (see .planning/codebase/CONCERNS.md)
- GPU requirement: NVIDIA with 6GB+ VRAM for SDXL, runs on Windows 11 primarily
- Current integrations: OpenAI, ElevenLabs, TikTok API, Hugging Face Hub
- New integrations needed: YouTube Data API v3, Discord webhooks, Slack webhooks, Suno API
- Prompts currently hardcoded in Python source — major pain point driving the config UI requirement
- Stable Audio replaced by Suno API for music generation in v1.1

## Constraints

- **Runtime**: Local GPU machine, Python 3.10+, no cloud infra
- **UI**: Gradio for config UI (already a dependency via AnimateDiff)
- **APIs**: YouTube Data API v3 requires OAuth 2.0 setup and quota management
- **Notifications**: Webhook-based (no bot framework needed for v1)
- **Backwards compat**: Existing CLI interfaces must keep working alongside new UI

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Gradio for config UI | Already a dependency, runs locally, good for forms/previews | -- Pending |
| Webhook-based notifications (not bots) | Simpler setup, no persistent process needed, sufficient for alerts + approval | -- Pending |
| YouTube Data API v3 (not scraping) | Official API, reliable, supports thumbnails and metadata | -- Pending |
| Shared publish/notify layer | Both pipelines need the same post-production steps, DRY | -- Pending |
| Best-frame thumbnail extraction | Leverages existing video frames, adds text overlay, avoids extra SD generation | -- Pending |

---
*Last updated: 2026-03-28 after initialization*

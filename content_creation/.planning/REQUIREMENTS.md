# Requirements: Content Creation Toolkit v1.1

**Defined:** 2026-03-28
**Core Value:** One command produces a publish-ready video — from prompt to YouTube upload — with human approval gates via Discord/Slack before anything goes public.

## v1.1 Requirements — AI Generation Quality

### Prompt Engineering

- [x] **PRMT-01**: Each profile (lofi-study, tech-tutorial, cinematic) has a YAML-defined prompt template with style-specific positive and negative prompts
- [x] **PRMT-02**: Negative prompts are short (5-8 terms) and SDXL-optimized — no SD1.5 mega-lists
- [x] **PRMT-03**: Quality presets (high/medium/fast) append quality-specific suffixes to prompts (e.g., "masterpiece, best quality" for high)
- [x] **PRMT-04**: Prompt templates support per-scene variation (weather, time-of-day) via template variables
- [x] **PRMT-05**: compel-based prompt weighting for emphasis control (e.g., "(warm lighting)1.3")

### SDXL Generator

- [x] **SDXL-01**: SDXL generation extracted into generators/sdxl.py — importable by both pipelines
- [x] **SDXL-02**: Hash-based image caching (prompt + all params → cache key) skips regeneration of unchanged scenes
- [x] **SDXL-03**: Cache hit/miss progress indicator distinguishes cached vs. fresh images during generation
- [x] **SDXL-04**: Quality presets map to concrete SDXL params (steps: high=35, medium=25, fast=15; guidance_scale: high=8.0, medium=7.5, fast=7.0)

### Suno Music

- [x] **SUNO-01**: SunoClient abstraction class with generate_music() → audio file path interface
- [x] **SUNO-02**: Profile-matched genre selection (lofi-study→"lofi chill", cinematic→"orchestral cinematic", tech-tutorial→"upbeat electronic")
- [x] **SUNO-03**: Duration-aware generation matching video length (with stitching for videos > max Suno duration)
- [x] **SUNO-04**: Instrumental-only enforcement via make_instrumental flag
- [x] **SUNO-05**: Suno returns 2 tracks per prompt — pipeline uses all generated tracks (stitch for longer videos, or present both in approval gate for selection)
- [x] **SUNO-06**: Stable Audio fallback when Suno is unavailable or fails
- [x] **SUNO-07**: Async Suno submission before SDXL batch to hide latency
- [x] **SUNO-08**: Hard timeout on Suno polling (default 300s) to prevent pipeline hang

### Config Extension

- [x] **CFGX-01**: SDXLSettings sub-model added to PipelineConfig (negative_prompt, steps, guidance_scale, enable_refiner)
- [x] **CFGX-02**: SunoSettings sub-model added to PipelineConfig (genre, make_instrumental, track_count, api_key via env var)
- [x] **CFGX-03**: Quality presets unified across image + music generation (single quality_preset drives both)

## v1.2 Requirements — Dashboard

### Vercel Dashboard UI

- [x] **DASH-01**: A Next.js 15 dashboard project exists at dashboard/ with shadcn/ui, Tailwind, and vercel.json — `vercel deploy` from dashboard/ succeeds
- [ ] **DASH-02**: User can select a named profile (lofi_study, tech_tutorial, cinematic) in the browser, edit any field, click Save, and the YAML file on disk is updated — no terminal required
- [x] **DASH-03**: Dashboard shows current credit balances for Suno (kie.ai), Replicate, and OpenAI, fetched live from each provider's API on page load
- [x] **DASH-04**: Each credit card has a Top Up button that opens the provider's billing page in a new tab; missing API keys show "Not configured" badge instead of an error
- [x] **DASH-05**: User can select a profile and click Trigger Generation from the dashboard; the pipeline starts on the local machine and status updates appear in the log within 3 seconds

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| ControlNet/LoRA support | Complex, requires model-specific setup per style — defer to v2 |
| Suno official API | Does not exist yet — built for third-party wrappers with abstraction |
| Vocal detection/filtering | Low confidence approach, manual selection via approval gate sufficient for v1.1 |
| SDXL refiner model | Adds 30%+ generation time for marginal quality gain — defer |
| Beat-sync transitions | Requires beat timestamp computation — deferred to v2 per v1.0 decision |

## Traceability

| Requirement | Phase | Status |
| ----------- | ----- | ------ |
| PRMT-01 | Phase 9 | Complete |
| PRMT-02 | Phase 9 | Complete |
| PRMT-03 | Phase 9 | Complete |
| PRMT-04 | Phase 9 | Complete |
| PRMT-05 | Phase 9 | Complete |
| SDXL-01 | Phase 10 | Complete |
| SDXL-02 | Phase 10 | Complete |
| SDXL-03 | Phase 10 | Complete |
| SDXL-04 | Phase 10 | Complete |
| SUNO-01 | Phase 11 | Complete |
| SUNO-02 | Phase 11 | Complete |
| SUNO-03 | Phase 11 | Complete |
| SUNO-04 | Phase 11 | Complete |
| SUNO-05 | Phase 11 | Complete |
| SUNO-06 | Phase 11 | Complete |
| SUNO-07 | Phase 11 | Complete |
| SUNO-08 | Phase 11 | Complete |
| CFGX-01 | Phase 9 | Complete |
| CFGX-02 | Phase 9 | Complete |
| CFGX-03 | Phase 9 | Complete |
| DASH-01 | Phase 14 | Not started |
| DASH-02 | Phase 14 | Not started |
| DASH-03 | Phase 14 | Not started |
| DASH-04 | Phase 14 | Not started |
| DASH-05 | Phase 14 | Not started |

**Coverage:**

- v1.1 requirements: 20 total
- v1.2 requirements: 5 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-28 — Phase 14 dashboard requirements added (DASH-01 through DASH-05)*

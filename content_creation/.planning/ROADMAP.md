# Roadmap: Content Creation Toolkit

## Overview

This milestone adds a shared publish/notify/post-processing layer to an existing two-pipeline video generation toolkit. Starting from a validated config schema, the build proceeds through post-processing, thumbnail generation, webhook notifications, YouTube publishing, pipeline hook injection, and finally a Gradio config UI — each phase independently testable, each unblocking the next. The result is one command that produces a publish-ready video with a human approval gate before anything reaches YouTube.

v1.1 (AI Generation Quality) extends the foundation with profile-driven SDXL prompt templates, hash-based image caching, and Suno music integration replacing Stable Audio. Config schema extension comes first; Suno integration last (highest risk).

v1.2 (Smart Automation) closes the manual-input loop: smart defaults pre-fill all env-sourced credentials, channel branding is fetched from YouTube and applied automatically, and AI prompt generation lets the user supply only tags — OpenAI writes every SDXL and Suno prompt. One command with tags produces a branded, publish-ready video.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Config Foundation** - Pydantic schema, YAML profiles, and validation layer that all other components depend on
- [ ] **Phase 2: Post-Processing Pipeline** - Shared FFmpeg module for watermark, subtitle burn-in, and intro/outro append
- [ ] **Phase 3: Thumbnail Generation** - OpenCV best-frame extraction with Pillow text overlay producing YouTube-compliant output
- [ ] **Phase 4: Notifications and Approval Gate** - Discord/Slack webhook notifications and file-based human approval gate
- [ ] **Phase 5: YouTube Publisher** - OAuth token persistence, resumable upload, quota guard, and thumbnail attach
- [ ] **Phase 6: Pipeline Integration** - Hook injection at both pipeline tails wiring all shared services end-to-end
- [ ] **Phase 7: Config UI** - Gradio Blocks interface exposing config load/save and subprocess-based pipeline launch
- [x] **Phase 8: Remotion Compilation Quality** - Spring-physics motion, profile-driven effect bundles, and YouTube-optimized render flags
- [x] **Phase 9: Config Extension and Prompt Templates** - SDXLSettings/SunoSettings sub-models and per-profile YAML prompt templates that all v1.1 generators depend on (completed 2026-03-28)
- [x] **Phase 10: SDXL Generator Extraction and Image Caching** - generators/sdxl.py module with hash-based cache eliminating redundant scene regeneration (completed 2026-03-28)
- [x] **Phase 11: Suno Music Integration** - SunoClient with async submission, multi-track generation, vocal validation, and Stable Audio fallback (completed 2026-03-28)
- [ ] **Phase 12: Discord Approval Loops** - Discord approval gate for images and video before YouTube publish
- [ ] **Phase 13: YouTube Credential Setup and Thumbnail Publishing** - OAuth setup and thumbnail attach for YouTube publishing
- [ ] **Phase 14: Vercel Dashboard UI** - Browser-based pipeline config, credit monitoring, and pipeline trigger
- [x] **Phase 16: Smart Defaults** - Config loader pre-fills all env-sourced credentials and shows source provenance in the dashboard (completed 2026-03-28)
- [x] **Phase 17: Channel Branding** - YouTube channel data fetch, branding propagation to watermark/thumbnail, cached locally, and auto-generated intro/outro clips (completed 2026-03-28)
- [ ] **Phase 18: AI Prompt Generation** - Tag-to-prompt via OpenAI with profile-aware scene variation, saved to YAML, enabling end-to-end tag-only pipeline runs

## Phase Details

### Phase 1: Config Foundation
**Goal**: Users can define pipeline behavior in YAML files with named profiles, and the system validates configs at load time before any generation runs

**Depends on**: Nothing (first phase)

**Requirements**: CONF-01, CONF-03, CONF-04, CONF-05

**Success Criteria** (what must be TRUE):

1. User can write a YAML config file with scene prompts, styles, and moods and run either pipeline without touching Python source
2. User can select a named profile (lofi-study, tech-tutorial, cinematic) and have the correct prompts, effects, and post-production settings applied automatically
3. Loading a config with a missing required field or invalid value produces a clear error message that identifies the bad field — generation does not start
4. Both the study video pipeline and TikTok pipeline accept the same config file format with no format conversion
5. Credentials and config files are gitignored on first setup; no secrets are committed to the repo

**Plans**: 4 plans

- [ ] 01-01-PLAN.md — PipelineConfig Pydantic model with VideoSettings, PostSettings, PublishSettings, NotifySettings sub-models and YAML round-trip
- [ ] 01-02-PLAN.md — Three named profile YAML files (lofi_study, tech_tutorial, cinematic) under config/profiles/ and .gitignore for secrets
- [ ] 01-03-PLAN.md — --config CLI argument wired into both pipelines with read-only load and pre-generation validation
- [ ] 01-04-PLAN.md — pytest suite covering missing fields, wrong types, invalid enum values, and YAML round-trip (TDD)

### Phase 2: Post-Processing Pipeline
**Goal**: Every finished video automatically has watermark, subtitles, and intro/outro applied before any downstream step touches it

**Depends on**: Phase 1

**Requirements**: POST-01, POST-02, POST-03, POST-04, POST-05

**Success Criteria** (what must be TRUE):

1. A finished video from either pipeline exits post-processing with a visible watermark overlay in the configured position
2. A finished video exits post-processing with subtitle text burned in from the generated SRT file
3. A finished video exits post-processing with the configured intro clip prepended and outro clip appended
4. Any of the three post-processing steps can be individually disabled per profile via config flag — disabling one does not break the others
5. The post-processing module is a single importable shared module that both pipelines use; no duplicated FFmpeg logic exists

**Plans**: TBD

- [ ] 02-01: Implement shared/post_process.py with FFmpeg subprocess calls for watermark overlay
- [ ] 02-02: Add subtitle burn-in step with explicit Windows font path handling
- [ ] 02-03: Add intro/outro concat step using FFmpeg concat demuxer
- [ ] 02-04: Add per-step enable/disable flags driven by PipelineConfig profile settings
- [ ] 02-05: Integration tests against sample output from each pipeline (short-form and long-form clips)

### Phase 3: Thumbnail Generation
**Goal**: Every finished video automatically produces a YouTube-compliant thumbnail with title text composited over the sharpest extracted frame

**Depends on**: Phase 2

**Requirements**: THMB-01, THMB-02, THMB-03

**Success Criteria** (what must be TRUE):

1. The thumbnail module selects the sharpest frame from the processed video without decoding the entire file
2. The output thumbnail has title text and channel branding composited over the selected frame
3. The output thumbnail is exactly 1280x720, saved as JPEG or PNG, and is under 2 MB

**Plans**: TBD

- [ ] 03-01: Implement shared/thumbnail_gen.py with OpenCV Laplacian sharpness scoring and FFmpeg seek-based frame extraction
- [ ] 03-02: Add Pillow text overlay with configurable font, size, position, and channel branding
- [ ] 03-03: Add output validation (dimensions, format, file size) with explicit error on constraint violation

### Phase 4: Notifications and Approval Gate
**Goal**: Users receive webhook notifications with video preview when generation completes and can approve or defer publishing from Discord or Slack before the pipeline touches YouTube

**Depends on**: Phase 3

**Requirements**: NOTF-01, NOTF-02, NOTF-03, NOTF-04, NOTF-05, APPR-01, APPR-02, APPR-03, APPR-04

**Success Criteria** (what must be TRUE):

1. A Discord webhook notification arrives when generation completes, including a thumbnail preview image and metadata summary (title, duration, profile used)
2. A Slack webhook notification arrives for the same events via the same shared notifier module — no duplicated send logic
3. An error alert reaches both Discord and Slack when generation or upload fails, identifying the failure stage
4. After generation, the pipeline pauses and waits for an approval signal before proceeding to publish; it does not upload automatically
5. A user can approve via CLI flag or by placing a flag file, and the pipeline resumes to publish; an unapproved video is retained locally and can be published later
6. Webhook URLs are configured through environment variables or the config file — no URLs appear in source code

**Plans**: TBD

- [ ] 04-01: Implement shared/notifier.py with Discord embed send using discord-webhook 1.4.1
- [ ] 04-02: Add Slack Block Kit notification using slack-sdk 3.41.0 with files_upload_v2 for thumbnail
- [ ] 04-03: Implement file-based approval gate with configurable timeout and clear CLI override flag
- [ ] 04-04: Add error alert path covering generation failure and upload failure stages
- [ ] 04-05: Add NOTF_DISCORD_WEBHOOK_URL and NOTF_SLACK_WEBHOOK_URL env var loading with fallback to config file

### Phase 5: YouTube Publisher
**Goal**: Users can publish a processed, approved video to YouTube with persistent OAuth credentials that do not require re-authentication on each run

**Depends on**: Phase 4

**Requirements**: YT-01, YT-02, YT-03, YT-04, YT-05

**Success Criteria** (what must be TRUE):

1. A processed, approved video uploads to YouTube with the configured title, description, tags, and category without manual browser intervention after initial OAuth setup
2. The generated thumbnail is attached to the published video via thumbnails.set
3. OAuth credentials are stored to disk after initial consent and automatically refreshed on subsequent runs without prompting the user
4. A failed upload retries with exponential backoff; a 404 session-expired response restarts the upload session rather than retrying the expired session
5. The publisher estimates remaining daily quota before uploading and refuses to start the upload if fewer than 1,600 units remain, printing the estimated usage to stdout

**Plans**: TBD

- [ ] 05-01: Implement shared/publisher.py with OAuth InstalledAppFlow, token persistence to credentials/, and silent refresh
- [ ] 05-02: Add standalone python shared/publisher.py --setup CLI for one-time consent flow (never triggered from Gradio)
- [ ] 05-03: Implement videos.insert resumable upload with exponential backoff distinguishing 404 (restart) from 5xx (retry)
- [ ] 05-04: Add thumbnails.set call with Short detection guard
- [ ] 05-05: Add pre-upload quota guard reading from YouTube Data API quotas endpoint and refusing upload below 1,600 unit threshold

### Phase 6: Pipeline Integration
**Goal**: Both existing pipelines run the full post-processing, notification, approval gate, and YouTube publish chain when config flags are enabled, while continuing to function identically without config flags

**Depends on**: Phase 5

**Requirements**: INTG-01, INTG-02, INTG-03

**Success Criteria** (what must be TRUE):

1. Running either pipeline with --config pointing to a config file with publish enabled triggers the full chain: post-process → thumbnail → notify → approval gate → YouTube upload
2. Running either pipeline without --config or with all publish flags disabled produces the same output as before this milestone — no behavior change, no import errors
3. New post-processing and publish features are activated only when explicitly enabled in the config file; no feature runs unless opted in

**Plans**: TBD

- [ ] 06-01: Add shared service hook at tail of study_with_me_generator.py main() calling run_post_process, notify_and_gate, publish_to_youtube in order
- [ ] 06-02: Add identical hook at tail of faceless TikTok pipeline main()
- [ ] 06-03: End-to-end dry-run test through full chain with a sample video (upload disabled, approval auto-approved) to validate all wiring

### Phase 7: Config UI
**Goal**: Users can load, edit, and launch either pipeline from a Gradio web interface on localhost without editing YAML files or using the CLI

**Depends on**: Phase 6

**Requirements**: CONF-02

**Success Criteria** (what must be TRUE):

1. User can open localhost:7860 in a browser, load a named profile, edit prompt and publish fields, save the config, and launch either pipeline — all without touching the terminal after startup
2. Pipeline stdout progress appears in the Gradio UI as the pipeline runs; the UI does not hang or freeze during generation
3. The Gradio app launches without conflicting with AnimateDiff's Gradio dependency; both can be used in the same environment or clear isolation steps are documented
4. The last-used config is auto-saved to configs/last_run.yaml on each submit so a crash does not lose the configuration

**Plans**: TBD

- [ ] 07-01: Audit AnimateDiff/requirements.txt Gradio pin and determine isolation strategy (separate venv or patch)
- [ ] 07-02: Implement gradio_app.py with Blocks UI: VideoSettings tab, PublishSettings tab, NotifySettings tab, profile dropdown, load/save YAML
- [ ] 07-03: Add subprocess-based pipeline launcher with stdout tailing routed to Gradio Textbox output component
- [ ] 07-04: Add auto-save to configs/last_run.yaml on each submit and upload result (YouTube URL or error) display

### Phase 8: Remotion Compilation Quality
**Goal**: Both Remotion compositions produce professional-quality video output — spring-physics motion, profile-driven effect bundles (transitions, grain, vignette, typography), audio visualization, and YouTube-optimized render flags — all driven by a profile prop passed from Python

**Depends on**: Phase 7

**Requirements**: REND-01, REND-02, REND-03, REND-04, REND-05

**Success Criteria** (what must be TRUE):

1. Both compositions accept a profile prop that selects distinct effect sets (transitions, spring config, grain intensity, vignette strength, font family, CSS color filter)
2. StudyVideo inter-scene cuts use TransitionSeries with profile-matched presentation (fade/wipe/slide) — no manual opacity crossfade
3. All element motion (parallax, zoom, title entrance, bullet reveals, timer pop-in) uses spring() — no bare linear interpolate for entrances
4. FilmGrain renders animated SVG noise (seed={frame}) at profile-specified intensity; renders nothing when grainIntensity is 0
5. Root.tsx computes StudyVideo duration via calculateMetadata() from the sceneDurations prop — no hardcoded 30*60*120
6. Python renderer passes profile prop, quality-tier CRF/preset, --color-space bt709, and --audio-codec aac to every render

**Plans**: 4 plans

- [x] 08-01-PLAN.md — npm package installation, profile system (3 profiles + index), fonts/index.ts, FilmGrain, Vignette, TextReveal, AudioVisualizer shared components
- [x] 08-02-PLAN.md — StudyVideo refactor (TransitionSeries, spring motion, profile-aware overlays) + Root.tsx calculateMetadata
- [x] 08-03-PLAN.md — TechTutorial refactor (spring title, TextReveal bullets, profile-aware overlays)
- [x] 08-04-PLAN.md — remotion_renderer.py extended with profile prop, quality flags, sceneDurations, WAV conversion helper

### Phase 9: Config Extension and Prompt Templates
**Goal**: PipelineConfig holds all SDXL and Suno generation parameters as typed sub-models, and every profile YAML contains the prompt templates, negative prompts, and genre tags that generators read at runtime — no generation parameters hardcoded in Python source

**Depends on**: Phase 8

**Requirements**: CFGX-01, CFGX-02, CFGX-03, PRMT-01, PRMT-02, PRMT-03, PRMT-04, PRMT-05

**Success Criteria** (what must be TRUE):

1. User can change image generation style for a profile by editing a YAML file (positive prompt, negative prompt, quality suffix) without modifying any Python source file
2. Each profile YAML contains a distinct short negative prompt (5-8 terms, SDXL-optimized) — loading a profile with a missing negative_prompt field raises a Pydantic validation error before generation starts
3. Setting quality_preset: high in the config causes both SDXL (steps=35, guidance_scale=8.0) and Suno (higher model tier) to apply quality-appropriate parameters simultaneously from a single field
4. A scene template with a {weather} or {time_of_day} variable in the YAML resolves to the correct string when rendered — unresolved variables raise a clear error, not a generation attempt with literal braces in the prompt
5. A prompt assembled through compel weighting (e.g., "(warm lighting)1.3") produces valid prompt_embeds and pooled_prompt_embeds without a runtime error from CompelForSDXL

**Plans**: 3 plans

- [ ] 09-01-PLAN.md — SDXLSettings and SunoSettings sub-models added to pipeline_config.py; quality_preset validator drives steps/guidance_scale/model_version simultaneously
- [ ] 09-02-PLAN.md — All three profile YAMLs extended with sdxl (positive_prompt, negative_prompt, scene_templates) and suno (genre, prompt_tags) blocks
- [ ] 09-03-PLAN.md — PromptTemplate.render() with variable substitution and ValueError on unresolved vars; build_compel_prompt() helper; pytest TDD suite

### Phase 10: SDXL Generator Extraction and Image Caching
**Goal**: SDXL generation runs from an importable generators/sdxl.py module with a hash-based cache that skips scenes whose prompt and parameters have not changed since the last run — re-running an unchanged pipeline produces zero new GPU compute

**Depends on**: Phase 9

**Requirements**: SDXL-01, SDXL-02, SDXL-03, SDXL-04

**Success Criteria** (what must be TRUE):

1. Both the study video pipeline and TikTok pipeline import SDXLGenerator from generators/sdxl.py — no SDXL inference code remains inline in either pipeline file
2. Running the pipeline twice with identical prompt, negative prompt, quality preset, profile, seed, and model version produces zero API/GPU calls on the second run; the progress indicator shows cache hits for every scene
3. Changing any single generation parameter (e.g., quality_preset from medium to high) invalidates only that scene's cache entry — other scenes still show cache hits on the next run
4. The .cache/images/ directory contains a JSON sidecar alongside each cached image recording the full parameter dict used to generate it — a human can read the sidecar and know exactly what produced that image

**Plans**: 2 plans

- [ ] 10-01-PLAN.md — generators/ package and SDXLGenerator with hash-based cache, sidecar write, and hit/miss logging
- [ ] 10-02-PLAN.md — Refactor study_with_me_generator.py to delegate to SDXLGenerator; remove inline SDXL code

### Phase 11: Suno Music Integration
**Goal**: The pipeline generates music via Suno matched to the active profile's genre and the video's exact duration, with Stable Audio as an automatic fallback, and Suno task submission runs in a background thread so it does not add wall-clock time to the pipeline

**Depends on**: Phase 10

**Requirements**: SUNO-01, SUNO-02, SUNO-03, SUNO-04, SUNO-05, SUNO-06, SUNO-07, SUNO-08

**Success Criteria** (what must be TRUE):

1. A study video run with Suno enabled produces music that matches the profile's genre tag (lofi chill / orchestral cinematic / upbeat electronic) and is instrumental — no audible vocal content passes through to the assembled video
2. A video longer than Suno's single-generation maximum receives stitched audio covering its full duration — there is no silence gap or abrupt cut at the stitch point
3. When Suno is unavailable (API timeout, HTTP error, or credentials missing), the pipeline falls back to Stable Audio and completes without manual intervention — a warning is printed identifying the fallback trigger
4. Suno task submission begins before the SDXL image batch starts; by the time the last image is generated, Suno audio is already downloaded and ready — the user does not wait for Suno after images complete
5. If Suno polling exceeds 300 seconds, the pipeline stops polling, activates the Stable Audio fallback, and continues — the pipeline never hangs indefinitely on a Suno server-side delay

**Plans**: 2 plans

- [ ] 11-01-PLAN.md — generators/suno.py with SunoClient: REST submit, exponential-backoff polling (hard 300s timeout), multi-track download, duration stitching, and Stable Audio fallback
- [ ] 11-02-PLAN.md — ThreadPoolExecutor wiring in study_with_me_generator.py: Suno submission before SDXL batch, future.result() after images complete, suno_generation progress key

### Phase 12: Discord Approval Loops
**Goal:** [To be planned]
**Depends on:** Phase 11
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd:plan-phase 12 to break down)

### Phase 13: YouTube Credential Setup and Thumbnail Publishing
**Goal:** [To be planned]
**Depends on:** Phase 12
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd:plan-phase 13 to break down)

### Phase 14: Vercel Dashboard UI
**Goal:** A browser-based dashboard deployed on Vercel provides pipeline config editing, live credit balance monitoring across all API providers, top-up links, pipeline trigger via webhook, and a live generation status log — the user never needs to edit YAML files or SSH into the local machine to manage the pipeline

**Depends on:** Phase 13 (can also run independently — no Python pipeline dependency)
**Plans:** 4/4 plans executed

Plans:

- [x] 14-01-PLAN.md — Next.js 15 project scaffold with shadcn/ui, Tailwind, vercel.json, and .env.example
- [x] 14-02-PLAN.md — Config editor: GET/PUT YAML profile API routes + ProfileEditor UI component
- [x] 14-03-PLAN.md — Credit monitor: API routes for Suno/Replicate/OpenAI/YouTube + CreditCard UI components
- [x] 14-04-PLAN.md — Pipeline trigger + status log: POST status receiver, trigger forwarder, GenerationLog polling component

### Phase 16: Smart Defaults
**Goal**: The config loader silently pre-fills every credential and webhook URL from environment variables, the dashboard visually separates env-sourced values from YAML-defined ones, and a first-run helper generates a starter profile so a new machine is ready to run a pipeline after one setup command

**Depends on**: Phase 14

**Requirements**: DFLT-01, DFLT-02, DFLT-03

**Success Criteria** (what must be TRUE):

1. Running a pipeline on a machine where DISCORD_WEBHOOK_URL, OPENAI_API_KEY, YOUTUBE_CLIENT_ID (and all other recognised env vars) are set produces a fully-populated config without the user touching any YAML file
2. The Vercel dashboard config editor shows a distinct visual badge (e.g., "ENV" label) beside every field whose value was sourced from an environment variable rather than the YAML profile, so the user knows which values to override in the profile if they want YAML-pinned values
3. Running the first-run setup command on a fresh checkout scans all known env vars, writes a starter YAML profile with every discoverable value pre-filled, and prints a list of any env vars that were not found so the user knows exactly what is missing
4. A field present in the YAML profile always takes precedence over the environment variable — env vars are the fallback, not the override

**Plans**: 3 plans

Plans:

- [ ] 16-01-PLAN.md — PipelineConfig.load_with_env_defaults() classmethod with ENV_VAR_MAP and provenance tracking
- [ ] 16-02-PLAN.md — Dashboard GET route returns provenance map; ProfileEditor renders ENV badge next to env-sourced fields
- [ ] 16-03-PLAN.md — setup.py CLI scans env vars, writes starter YAML profile, prints found/missing summary

### Phase 17: Channel Branding
**Goal**: The pipeline fetches YouTube channel name, avatar, and description once via the existing OAuth credentials, caches the result locally, and automatically applies channel branding as the watermark text, thumbnail corner logo, and auto-generated intro/outro clips — no manual video files or branding config required

**Depends on**: Phase 16

**Requirements**: BRND-01, BRND-02, BRND-03, BRND-04, BRND-05

**Success Criteria** (what must be TRUE):

1. Running the pipeline with channel branding enabled produces a watermark that reads the YouTube channel name without any watermark_text field set in the config — the channel name is fetched automatically and applied
2. The thumbnail produced by the pipeline has the channel avatar image composited as a corner logo overlay without the user providing a local logo file
3. The intro and outro clips attached to the assembled video display the channel avatar, channel name, and a one-line tagline derived from the channel description — generated programmatically from fetched assets with no manually supplied video files
4. Re-running the pipeline a second time (without calling explicit refresh) does not make any YouTube API call — branding assets are read from the local cache
5. Running the pipeline with --refresh-branding (or equivalent flag) discards the local cache, re-fetches channel assets from the YouTube Data API, and updates the cache before generation proceeds

**Plans**: 4 plans

Plans:

- [ ] 17-01-PLAN.md — shared/branding.py with channel fetch, avatar download, local cache (7-day TTL + explicit refresh); BrandingSettings sub-model in pipeline_config.py
- [ ] 17-02-PLAN.md — Watermark branding fallback in post_process.py; avatar corner logo overlay in thumbnail_gen.py
- [ ] 17-03-PLAN.md — shared/branding_clips.py: FFmpeg-based intro/outro generation from channel avatar + name + tagline
- [ ] 17-04-PLAN.md — pipeline_runner.py wiring: branding fetch before post-process, avatar_path forwarded to thumbnail, generated clips injected into concat step

### Phase 18: AI Prompt Generation
**Goal**: The user supplies only a comma-separated tag string and a profile name; OpenAI generates a full SDXL positive prompt, negative prompt, and Suno music prompt matched to the profile's style, produces 8 scene-level variations, saves them to the profile YAML for inspection, and the pipeline runs end-to-end without any manual prompt editing

**Depends on**: Phase 17

**Requirements**: AGEN-01, AGEN-02, AGEN-03, AGEN-04, AGEN-05

**Success Criteria** (what must be TRUE):

1. Running the pipeline with --tags "lofi, rain, cozy, study" produces a video without the user writing any SDXL or Suno prompt — OpenAI fills every prompt field before generation starts
2. Prompts generated from a cinematic profile tag set read cinematically (lens flare, bokeh, film grain phrasing) while prompts generated from the same tags against a lofi profile read warmly and softly — profile style propagates into OpenAI output
3. A single tag invocation produces 8 distinct scene prompt variants covering different moments, lighting conditions, or compositional angles — the assembled video has no repeated frames caused by identical prompts
4. After tag-based generation, the profile YAML on disk contains the generated prompts under the sdxl.scene_templates key — the user can open the YAML, read every prompt, and edit them before re-running without tags
5. Running the pipeline with --tags and no other prompt configuration produces a finished, assembled video — no intermediate manual step is required between tag input and video output

**Plans**: 2 plans

Plans:

- [ ] 18-01-PLAN.md — generators/prompt_generator.py: PromptGenerator class with OpenAI-backed generate() returning structured prompt payload (positive, negative, 8 scene variants, music)
- [ ] 18-02-PLAN.md — --tags CLI flag wired into study_with_me_generator.py with YAML write-back and graceful fallback to existing profile prompts

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 16 → 17 → 18

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Config Foundation | 0/4 | Not started | - |
| 2. Post-Processing Pipeline | 0/5 | Not started | - |
| 3. Thumbnail Generation | 0/3 | Not started | - |
| 4. Notifications and Approval Gate | 0/5 | Not started | - |
| 5. YouTube Publisher | 0/5 | Not started | - |
| 6. Pipeline Integration | 0/3 | Not started | - |
| 7. Config UI | 0/4 | Not started | - |
| 8. Remotion Compilation Quality | 4/4 | Complete | 2026-03-28 |
| 9. Config Extension and Prompt Templates | 3/3 | Complete | 2026-03-28 |
| 10. SDXL Generator Extraction and Image Caching | 2/2 | Complete | 2026-03-28 |
| 11. Suno Music Integration | 2/2 | Complete | 2026-03-28 |
| 12. Discord Approval Loops | 0/? | Not started | - |
| 13. YouTube Credential Setup and Thumbnail Publishing | 0/? | Not started | - |
| 14. Vercel Dashboard UI | 4/4 | In Progress | - |
| 16. Smart Defaults | 3/3 | Complete   | 2026-03-28 |
| 17. Channel Branding | 4/4 | Complete   | 2026-03-28 |
| 18. AI Prompt Generation | 1/2 | In Progress|  |

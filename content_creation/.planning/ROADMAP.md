# Roadmap: Content Creation Toolkit

## Overview

This milestone adds a shared publish/notify/post-processing layer to an existing two-pipeline video generation toolkit. Starting from a validated config schema, the build proceeds through post-processing, thumbnail generation, webhook notifications, YouTube publishing, pipeline hook injection, and finally a Gradio config UI — each phase independently testable, each unblocking the next. The result is one command that produces a publish-ready video with a human approval gate before anything reaches YouTube.

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

- [ ] 08-01-PLAN.md — npm package installation, profile system (3 profiles + index), fonts/index.ts, FilmGrain, Vignette, TextReveal, AudioVisualizer shared components
- [ ] 08-02-PLAN.md — StudyVideo refactor (TransitionSeries, spring motion, profile-aware overlays) + Root.tsx calculateMetadata
- [ ] 08-03-PLAN.md — TechTutorial refactor (spring title, TextReveal bullets, profile-aware overlays)
- [ ] 08-04-PLAN.md — remotion_renderer.py extended with profile prop, quality flags, sceneDurations, WAV conversion helper

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Config Foundation | 0/4 | Not started | - |
| 2. Post-Processing Pipeline | 0/5 | Not started | - |
| 3. Thumbnail Generation | 0/3 | Not started | - |
| 4. Notifications and Approval Gate | 0/5 | Not started | - |
| 5. YouTube Publisher | 0/5 | Not started | - |
| 6. Pipeline Integration | 0/3 | Not started | - |
| 7. Config UI | 0/4 | Not started | - |
| 8. Remotion Compilation Quality | 2/4 | In Progress|  |

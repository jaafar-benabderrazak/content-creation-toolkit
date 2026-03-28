# Project Research Summary

**Project:** Content Creation Pipeline — Publishing & Post-Processing Milestone
**Domain:** Local Python video generation pipeline — config UI, post-processing, YouTube publishing, webhook notifications
**Researched:** 2026-03-28
**Confidence:** HIGH (stack and architecture verified against official sources and direct codebase inspection; pitfalls HIGH for YouTube/Gradio, MEDIUM for webhook approval patterns)

## Executive Summary

This milestone adds a shared publish/notify/post-processing layer to an existing two-pipeline video generation toolkit (study-with-me generator + faceless TikTok pipeline). Both pipelines currently produce MP4 files with no automated delivery path. The expert pattern for this type of local, single-operator automation is a thin shared services layer injected at the tail of each pipeline's `main()` function, leaving all existing generation logic untouched. The shared layer covers post-processing (watermark, subtitle burn-in, intro/outro via FFmpeg), thumbnail generation (OpenCV sharpness scoring + Pillow text overlay), YouTube upload via the official Data API v3, and Discord/Slack webhook notifications with a file-based human approval gate.

The recommended approach is to build config infrastructure first (Pydantic model + YAML profiles), then shared services in dependency order (post-process → thumbnail → notifier → publisher), and expose everything through a Gradio 5.x config UI last. Gradio must run in a separate venv from AnimateDiff, which pins Gradio 3.36.1. The Gradio UI launches pipelines as subprocesses rather than calling them in-process, which is required to avoid GPU memory conflicts and CUDA thread-safety issues on Windows. The entire config layer uses Pydantic for schema validation — silent bad configs are a documented failure mode if YAML is loaded without validation.

The two critical risks are YouTube API quota exhaustion (1,600 units per upload against a 10,000-unit daily limit, shared across all API keys in the same Google Cloud project) and OAuth refresh token expiry when the Google Cloud app is left in "Testing" mode (7-day limit). Both require addressing before any unattended upload logic is written. A third systemic risk is the existing codebase pattern of bare `except` clauses, which silently swallows quota errors, upload failures, and webhook rate-limit responses — all new code in the shared layer must use explicit exception handling.

## Key Findings

### Recommended Stack

The existing stack (MoviePy 1.0.x, OpenCV 4.x, Pillow 12.1.1, FFmpeg system, pydub) must not be upgraded during this milestone. MoviePy 2.x breaks the `moviepy.editor` import path and renames all `.set_*` methods to `.with_*` — both existing pipelines use the v1 API extensively. Post-processing should route long-form video operations through FFmpeg subprocesses rather than MoviePy to avoid OOM on 120-minute files.

Five new libraries are needed: `google-api-python-client==2.193.0` + `google-auth-oauthlib==1.3.0` + `google-auth-httplib2==0.3.0` (YouTube upload), `slack-sdk==3.41.0` (Slack webhooks), and `discord-webhook==1.4.1` (Discord webhooks). Gradio 5.x (>=5.0,<6.0) is required for the config UI in an isolated venv. Gradio 6.x has breaking changes to `gr.ChatInterface` and `gr.Dataframe`; do not use for this milestone.

**Core technologies:**
- `google-api-python-client` 2.193.0: YouTube Data API v3 upload client — only supported method for programmatic upload; handles resumable protocol automatically
- `google-auth-oauthlib` 1.3.0: OAuth 2.0 installed-app flow — required; service accounts do not work for user channel uploads
- `slack-sdk` 3.41.0: Slack webhook client — provides error handling and Block Kit formatting over raw `requests.post()`
- `discord-webhook` 1.4.1: Discord webhook with embed support — avoids full bot framework for a notification-only use case
- Gradio 5.x (isolated venv): Config UI — already a project dependency; 5.x avoids AnimateDiff conflict and Gradio 6.x breaking changes
- MoviePy 1.0.x (existing, stay): Video composition — upgrading to 2.x requires rewriting both existing pipelines
- FFmpeg subprocess: Subtitle burn-in and long-form post-processing — avoids MoviePy 1.x ImageMagick dependency for TextClip

### Expected Features

**Must have (table stakes) — v1 this milestone:**
- YAML config schema + Pydantic validation — all other features depend on this; must come first
- YouTube upload with resumable protocol + OAuth token persistence — core delivery mechanism; token refresh must work silently after initial setup
- Custom thumbnail upload via `thumbnails.set` — discovery signal; auto-generated thumbnails are visibly inferior
- Post-processing: watermark overlay + subtitle burn-in + intro/outro append — baseline for public-ready output
- Best-frame thumbnail extraction with text overlay — uses existing frames via OpenCV sharpness scoring; no extra SD generation
- Discord webhook notifications (generation complete + error alerts)
- Slack webhook notifications (same events, shared module)
- Human approval gate: webhook preview notification + file-based gate before publish — prevents accidental publish without bot infrastructure
- Shared `notifier.py` + `publisher.py` modules imported by both pipelines — no divergent implementations
- Gradio 5.x config UI exposing prompt, style, publish, and notify fields

**Should have (v1.x after validation):**
- Template/edit profiles (lofi-study, tech-tutorial, cinematic YAML bundles)
- Color grade presets per profile (FFmpeg curves/LUT filter)
- Extended pipeline resumability through post-prod and upload stages

**Defer (v2+):**
- Interactive Discord/Slack approval bot with reaction/button handling — requires persistent process and public endpoint; overkill for single-operator local tool
- YouTube scheduling / optimal post timing — adds API scope complexity without v1 value
- Full channel management (playlists, end screens, analytics) — scope creep
- Multi-account YouTube publishing — single creator, single credential file in v1

### Architecture Approach

The architecture uses a four-layer model: Config Layer (Pydantic `PipelineConfig` + YAML profiles) → existing Pipeline Scripts (unchanged, hook added at `main()` tail) → Shared Services Layer (`shared/post_process.py`, `shared/publisher.py`, `shared/notifier.py`, `shared/thumbnail_gen.py`) → Config UI (`gradio_app.py` launching pipelines as subprocesses). Dependencies are strictly one-directional: shared/ imports nothing from pipeline scripts; Gradio communicates with pipelines only via subprocess and filesystem (YAML configs, output paths). OAuth credentials live in a gitignored `credentials/` directory.

**Major components:**
1. `config/pipeline_config.py` — Pydantic `PipelineConfig` with nested `VideoSettings`, `PublishSettings`, `NotifySettings`; YAML round-trip via `from_yaml()` / `to_yaml()`
2. `config/profiles/` — Named YAML preset files (lofi_study, tech_tutorial, cinematic); loaded by profile name
3. `shared/post_process.py` — FFmpeg subprocess for color grade, watermark overlay, intro/outro concat, subtitle burn-in
4. `shared/thumbnail_gen.py` — OpenCV frame extraction with Laplacian sharpness scoring; Pillow text overlay; 1280×720 JPEG output
5. `shared/notifier.py` — Discord + Slack webhook send; file-based approval gate with 1-hour timeout
6. `shared/publisher.py` — YouTube OAuth token load/refresh; `videos.insert` resumable upload; `thumbnails.set`; separate `--setup` CLI for one-time OAuth consent
7. `gradio_app.py` — Gradio Blocks UI; loads/saves `PipelineConfig` to YAML; launches pipelines via `subprocess.Popen`; tails subprocess stdout for progress

### Critical Pitfalls

1. **OAuth refresh token expiry in Testing mode** — Google limits refresh tokens to 7 days for "External" apps in "Testing" status. Address immediately after OAuth integration: move app to "Production" status or use a Google Workspace internal app. Add a startup token validity check before every upload attempt.

2. **YouTube quota exhaustion from test uploads** — `videos.insert` costs 1,600 of the 10,000 daily units, shared across all API keys in the same GCP project. Use a separate GCP project for development. Add a pre-upload quota guard that refuses to upload when estimated remaining units < 1,600.

3. **Gradio CUDA hang with `queue=True` on Windows** — PyTorch CUDA operations inside Gradio thread-pool callbacks hang indefinitely (confirmed GitHub issues #12492, #6609). Never call GPU inference directly from Gradio event handlers. Launch pipelines as subprocesses; Gradio only monitors progress.

4. **Resumable upload session expiry** — YouTube session URIs expire if upload bytes are not sent promptly after session initiation. Initiate the upload session only after post-processing, thumbnail generation, and approval are all complete — immediately before sending bytes. Distinguish `404` (expired session, restart) from `5xx` (retryable).

5. **Config YAML loaded without schema validation** — Silent bad configs (typo in field name uses `None` silently) run the pipeline to completion with wrong parameters. Pydantic validation must raise immediately on load for missing or unknown fields. Schema-first design: define `PipelineConfig` before writing any config-loading code.

6. **Bare `except` swallowing API failures** — Existing codebase has this pattern. All new code in shared/ must use explicit exception types (`HttpError`, `TransportError`, `RefreshError`). Silent swallow of quota errors, 429 rate limits, or webhook failures is not acceptable in a notification/publish layer.

## Implications for Roadmap

Based on combined research findings, the component dependency graph from ARCHITECTURE.md dictates a clear build order. The suggested 7-phase structure below respects hard dependencies (config before everything, publisher last among shared services) while grouping related concerns.

### Phase 1: Config Foundation
**Rationale:** Every other component depends on `PipelineConfig` and YAML profiles. Building UI or shared services before this results in ad-hoc config structures that require rewriting. Schema-first is also the primary defense against the silent bad-config pitfall.
**Delivers:** `config/pipeline_config.py` (Pydantic model), `config/profiles/` (3 starter YAML files), `.env` extension for webhook URLs and credential paths, `.gitignore` updates for `credentials/` and `configs/`
**Addresses:** YAML config schema + loading (P1 feature), template profiles foundation
**Avoids:** Config YAML missing field validation pitfall; credentials committed to git

### Phase 2: Post-Processing Pipeline
**Rationale:** Post-processing is a prerequisite for YouTube upload (publisher operates on final artifact) and for thumbnail generation (runs after video is assembled). It has no external auth dependencies — testable fully offline.
**Delivers:** `shared/post_process.py` — watermark overlay, subtitle burn-in (FFmpeg), intro/outro append; tested against both pipeline output formats
**Uses:** FFmpeg subprocess, MoviePy 1.0.x (existing), Pillow (existing)
**Implements:** Post-processing shared service layer
**Avoids:** MoviePy v1/v2 API mismatch pitfall (pin and audit version first); OOM on long-form video (use FFmpeg subprocess, not MoviePy for >10-min content)

### Phase 3: Thumbnail Generation
**Rationale:** Thumbnail must exist before `thumbnails.set` is called in the publisher. OpenCV + Pillow — no external auth. Builds on post-processing phase (thumbnail generated from the processed video, not the raw render).
**Delivers:** `shared/thumbnail_gen.py` — OpenCV best-frame extraction via sharpness scoring, Pillow text overlay, 1280×720 JPEG output; Short vs. long-form detection to gate `thumbnails.set` eligibility
**Uses:** OpenCV 4.x (existing), Pillow 12.1.1 (existing)
**Avoids:** Thumbnail upload failing on Shorts pitfall; frame extraction performance trap (FFmpeg `-ss` seek, not full decode)

### Phase 4: Notifications + Approval Gate
**Rationale:** Notifier can be built and tested without OAuth (webhook URLs are just HTTP POST). The approval gate behavior must be established before the publisher is wired up — publisher fires only after gate is passed. Discord and Slack are built together into one shared module to prevent divergent implementations.
**Delivers:** `shared/notifier.py` — Discord embed + Slack Block Kit notifications; file-based approval gate with 1-hour timeout; preview image attached to notification; explicit file-size guard (25 MB threshold) for Discord attachments
**Uses:** `discord-webhook==1.4.1`, `slack-sdk==3.41.0`
**Avoids:** Approval gate blocking main thread indefinitely pitfall; Discord 25 MB attachment limit silent failure; webhook URLs in source code (use `.env`)

### Phase 5: YouTube Publisher
**Rationale:** Publisher is the most complex external integration (OAuth, resumable upload, quota management, thumbnail attach). All prerequisites (processed video, thumbnail, approval) must exist before wiring this up. Separating `--setup` CLI for OAuth from the publish function prevents the anti-pattern of triggering OAuth inside Gradio.
**Delivers:** `shared/publisher.py` — OAuth token persistence and silent refresh; `videos.insert` resumable upload with exponential backoff; `thumbnails.set` with explicit Short detection; quota guard (refuse upload if < 1,600 units estimated); separate `python shared/publisher.py --setup` for one-time consent flow
**Uses:** `google-api-python-client==2.193.0`, `google-auth-oauthlib==1.3.0`, `google-auth-httplib2==0.3.0`
**Avoids:** OAuth Testing mode 7-day expiry pitfall; quota exhaustion pitfall; resumable session expiry pitfall; credentials committed to git

### Phase 6: Pipeline Integration
**Rationale:** Hook injection into existing pipeline scripts is the lowest-risk step — three to four lines at each `main()` tail. Deferred until all shared services are tested independently. Existing CLI behavior remains unchanged; new behavior is additive.
**Delivers:** Hook at tail of `study_with_me_generator.py main()` and `faceless_tiktok_pipeline main()` calling `run_post_process` → `notify_and_gate` → `publish_to_youtube`; config argument added to each pipeline's CLI (`--config path/to/config.yaml`); end-to-end test of the full chain
**Avoids:** Modifying pipeline internals anti-pattern; single monolithic god-config anti-pattern

### Phase 7: Config UI (Gradio)
**Rationale:** Gradio UI is last because it exposes what already exists. Building it before shared services produces a UI with no real behavior to wire. The Gradio venv isolation and subprocess-launch pattern must be resolved before writing any UI code — the environment audit comes first.
**Delivers:** `gradio_app.py` — Gradio Blocks with tabs for VideoSettings, PublishSettings, NotifySettings; load/save YAML config (profile dropdown + custom save); subprocess-based pipeline launch with stdout tailing for progress; auto-save to `configs/last_run.yaml` on each submit; upload result (YouTube URL or error) routed back to Gradio output component
**Uses:** Gradio 5.x (isolated venv, `>=5.0,<6.0`)
**Avoids:** Gradio CUDA hang pitfall (subprocess launch, never direct GPU call in handler); Gradio version conflict with AnimateDiff (audit `AnimateDiff/requirements.txt` before writing any code); Gradio ephemeral state pitfall (auto-save to disk)

### Phase Ordering Rationale

- Config (Phase 1) before everything — all shared modules import `PipelineConfig`; no config = no contract
- Post-process (Phase 2) before thumbnail (Phase 3) — thumbnail operates on processed video; dependency is explicit in FEATURES.md
- Notifications (Phase 4) before publisher (Phase 5) — approval gate result is the input that gates the publish call
- Publisher (Phase 5) before integration (Phase 6) — hook injection only makes sense when all shared functions exist and are tested
- Gradio (Phase 7) last — it is a frontend for the entire system; building it first produces a UI stub with nothing behind it
- Each phase through Phase 5 is independently testable without Gradio, which isolates the Gradio venv conflict to a single phase

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (YouTube Publisher):** YouTube's quota increase request process and timeline for production apps is not well-documented. If >6 uploads/day is a requirement, verify quota increase SLA before committing to a release timeline.
- **Phase 7 (Config UI):** Gradio venv isolation strategy (Option A: separate venv + JSON handoff vs. Option C: patch AnimateDiff) requires an environment audit of the actual `AnimateDiff/requirements.txt` Gradio pin before the approach can be confirmed. This is a pre-condition for Phase 7.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Config Foundation):** Pydantic YAML config is a well-established pattern; implementation is straightforward.
- **Phase 2 (Post-Processing):** FFmpeg subprocess calls for watermark, subtitle, and concat are fully documented; MoviePy 1.x behavior is known.
- **Phase 3 (Thumbnail Generation):** OpenCV Laplacian sharpness scoring + Pillow overlay is a standard pipeline; no novel integration.
- **Phase 4 (Notifications):** Discord and Slack webhook patterns are thoroughly documented; file-based gate requires no research.
- **Phase 6 (Pipeline Integration):** Three lines of code at each `main()` tail; no research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All library versions verified against PyPI; MoviePy 1.x vs 2.x breaking changes confirmed against official migration guide; Gradio 6.x breaking changes confirmed against official migration guide |
| Features | HIGH | YouTube API v3 features verified against official docs; Discord/Slack patterns verified against official docs; approval gate pattern is LOW confidence (no reference implementation found, but the file-based approach is simple enough that confidence gap is acceptable) |
| Architecture | HIGH | Direct codebase inspection; all patterns verified against official sources; build order derivable from explicit dependency graph in ARCHITECTURE.md |
| Pitfalls | MEDIUM-HIGH | YouTube API and Gradio pitfalls are HIGH (confirmed GitHub issues, official docs, and community reports); webhook approval-gate and post-processing pitfalls are MEDIUM (corroborated but fewer primary sources) |

**Overall confidence:** HIGH

### Gaps to Address

- **AnimateDiff Gradio version pin:** Exact version pinned in `AnimateDiff/requirements.txt` was not inspected. Run `grep -i gradio AnimateDiff/requirements.txt` before Phase 7. This determines whether Option A (separate venv) or Option C (patch) is the correct isolation strategy.
- **YouTube quota increase timeline:** If the production use case requires >6 uploads/day, a quota increase request must be filed with Google and the review timeline is variable. Validate requirement against the 6/day limit before Phase 5.
- **Windows font path for subtitle burn-in:** CONCERNS.md notes an existing font-path issue on Windows. FFmpeg subtitle filter on Windows requires explicit font path in the `subtitles` filter argument (`force_style='FontName=...'`). Needs validation on the target machine in Phase 2.
- **Slack `files.upload` deprecation:** Slack deprecated `files.upload` in March 2025. If video preview file sharing via Slack is needed in Phase 4, use `files_upload_v2` via `slack-sdk`. Text-only + thumbnail image notifications are unaffected.

## Sources

### Primary (HIGH confidence)
- YouTube Data API v3 official docs (upload, resumable, thumbnails.set, quota, errors, OAuth) — developers.google.com/youtube/v3
- google-auth-oauthlib `InstalledAppFlow` docs — googleapis.dev
- Gradio 5 announcement — huggingface.co/blog/gradio-5
- Gradio 6 Migration Guide — gradio.app/main/guides/gradio-6-migration-guide
- Gradio GitHub issues #12492, #6609, #6971 (CUDA hang, queue freeze, GPU memory) — confirmed by maintainers
- Slack SDK Webhook Client docs — slack.dev/python-slack-sdk/webhook
- Slack files_upload deprecation — docs.slack.dev
- MoviePy 2.x migration guide — zulko.github.io/moviepy/getting_started/updating_to_v2
- discord-webhook PyPI — pypi.org/project/discord-webhook
- Discord webhook rate limits — discord.com/developers/docs/topics/rate-limits
- Codebase direct inspection: `study_with_me_generator.py`, `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`, `.planning/codebase/CONCERNS.md`
- PyPI version verification for all recommended packages — confirmed 2026-03-28

### Secondary (MEDIUM confidence)
- OAuth2 refresh token expiration in YouTube API — Google Developer Forums + Napkyn blog (corroborates official 7-day Testing mode policy)
- YouTube upload guide 2026 — Postproxy blog (corroborates official resumable upload protocol)
- Python YouTube upload with OAuth 2.0 reauthentication — Medium 2025 (corroborates token persistence pattern)
- Discord webhook file size limits — birdie0 guide (corroborates Discord official behavior)
- Pydantic YAML config — pydantic-yaml PyPI (official package, well-supported)

### Tertiary (LOW confidence)
- YouTube API quota exhausted community thread — support.google.com (community-verified behavior, not official doc)
- n8n Slack approval workflow — pattern reference only, not a direct implementation source
- Pipeline design pattern — startdataengineering.com (WebSearch only; pattern is standard)

---
*Research completed: 2026-03-28*
*Ready for roadmap: yes*

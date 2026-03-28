# Requirements: Content Creation Toolkit

**Defined:** 2026-03-28
**Core Value:** One command produces a publish-ready video — from prompt to YouTube upload — with human approval gates via Discord/Slack before anything goes public.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Configuration

- [ ] **CONF-01**: User can define scene prompts, styles, and moods in a YAML config file without editing Python source
- [ ] **CONF-02**: User can load, edit, and save pipeline configs through a Gradio web UI on localhost
- [ ] **CONF-03**: User can select a named profile (lofi-study, tech-tutorial, cinematic) that bundles prompts, effects, and post-production settings
- [ ] **CONF-04**: Config schema is validated at load time with clear error messages for invalid fields
- [ ] **CONF-05**: Both pipelines (study video, TikTok) load config from the same schema and file format

### Post-Production

- [ ] **POST-01**: Pipeline automatically applies watermark overlay to finished video
- [ ] **POST-02**: Pipeline automatically burns subtitles into the video from generated SRT
- [ ] **POST-03**: Pipeline automatically prepends intro and appends outro clips to the video
- [ ] **POST-04**: Post-production steps are configurable per profile (enable/disable each step)
- [ ] **POST-05**: Post-production runs on the output of both existing pipelines via a shared module

### Thumbnails

- [ ] **THMB-01**: Pipeline extracts the sharpest frame from generated video as thumbnail candidate
- [ ] **THMB-02**: Pipeline composites title text and channel branding onto the thumbnail image
- [ ] **THMB-03**: Thumbnail output meets YouTube requirements (1280x720, JPEG/PNG, <2MB)

### YouTube Publishing

- [ ] **YT-01**: Pipeline uploads finished video to YouTube with title, description, tags, and category
- [ ] **YT-02**: Pipeline uploads generated thumbnail to the published video
- [ ] **YT-03**: OAuth 2.0 refresh token is persisted to disk so re-authentication is not required each run
- [ ] **YT-04**: Upload uses resumable protocol with exponential backoff on failure
- [ ] **YT-05**: Pipeline respects YouTube quota limits and warns when approaching daily cap

### Notifications

- [ ] **NOTF-01**: Pipeline sends Discord webhook notification when video generation completes
- [ ] **NOTF-02**: Pipeline sends Slack webhook notification when video generation completes
- [ ] **NOTF-03**: Pipeline sends error alert to Discord/Slack when generation or upload fails
- [ ] **NOTF-04**: Notification includes video thumbnail preview and metadata summary
- [ ] **NOTF-05**: User configures webhook URLs via environment variables or config file

### Approval Gate

- [ ] **APPR-01**: After generation, pipeline sends preview notification and pauses before publishing
- [ ] **APPR-02**: User confirms publish via CLI command or flag file
- [ ] **APPR-03**: Pipeline proceeds to YouTube upload only after approval is confirmed
- [ ] **APPR-04**: Unapproved videos are retained locally and can be published later

### Integration

- [ ] **INTG-01**: Shared notify/publish module is importable by both study and TikTok pipelines
- [ ] **INTG-02**: Existing CLI interfaces for both pipelines continue to work without the new features
- [ ] **INTG-03**: New features are activated via config flags (opt-in, not forced)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Profiles

- **PROF-01**: Color grade presets applied per profile via FFmpeg LUT filters
- **PROF-02**: Per-profile pacing and transition timing configuration

### Advanced Publishing

- **ADVP-01**: YouTube scheduling with optimal post time selection
- **ADVP-02**: Playlist management and auto-categorization
- **ADVP-03**: Interactive Discord/Slack bot with approval buttons (requires persistent process)

### Pipeline Resilience

- **RESL-01**: Resumable pipeline state through post-production and upload stages
- **RESL-02**: Concurrent generation queue with resource management

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web-hosted UI | Breaks local-GPU constraint; adds cloud infra, auth, HTTPS |
| YouTube scheduling | Separate quota, timezone logic, analytics scope expansion |
| Full channel management (playlists, end screens, analytics) | Scope creep; each adds quota cost and test surface |
| Interactive approval bot (Discord/Slack) | Requires persistent process + public endpoint; impossible locally without ngrok |
| Auto-scene detection / smart trimming | Heavy AI models, nondeterministic, deferred per user decision |
| Multi-account YouTube publishing | Not needed for single creator workflow |
| TikTok thumbnail/cover automation | TikTok Content API cover image surface is unstable |
| Cloud deployment | Stays local for this milestone |
| Real-time progress streaming to UI | Gradio progress bar is sufficient; WebSockets adds complexity |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONF-01 | Phase 1 | Pending |
| CONF-02 | Phase 7 | Pending |
| CONF-03 | Phase 1 | Pending |
| CONF-04 | Phase 1 | Pending |
| CONF-05 | Phase 1 | Pending |
| POST-01 | Phase 2 | Pending |
| POST-02 | Phase 2 | Pending |
| POST-03 | Phase 2 | Pending |
| POST-04 | Phase 2 | Pending |
| POST-05 | Phase 2 | Pending |
| THMB-01 | Phase 3 | Pending |
| THMB-02 | Phase 3 | Pending |
| THMB-03 | Phase 3 | Pending |
| YT-01 | Phase 5 | Pending |
| YT-02 | Phase 5 | Pending |
| YT-03 | Phase 5 | Pending |
| YT-04 | Phase 5 | Pending |
| YT-05 | Phase 5 | Pending |
| NOTF-01 | Phase 4 | Pending |
| NOTF-02 | Phase 4 | Pending |
| NOTF-03 | Phase 4 | Pending |
| NOTF-04 | Phase 4 | Pending |
| NOTF-05 | Phase 4 | Pending |
| APPR-01 | Phase 4 | Pending |
| APPR-02 | Phase 4 | Pending |
| APPR-03 | Phase 4 | Pending |
| APPR-04 | Phase 4 | Pending |
| INTG-01 | Phase 6 | Pending |
| INTG-02 | Phase 6 | Pending |
| INTG-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-28 after roadmap creation*

# Requirements: Content Creation Toolkit v1.2

**Defined:** 2026-03-28
**Core Value:** One command with tags produces a publish-ready video — zero manual prompt writing, channel-branded, auto-published.

## v1.2 Requirements — Smart Automation

### Smart Defaults

- [x] **DFLT-01**: Config loader pre-fills Discord webhook URL, API keys, and channel info from environment variables when not set in YAML
- [x] **DFLT-02**: Dashboard config editor shows which values are env-sourced vs. YAML-defined (visual distinction)
- [x] **DFLT-03**: First-run setup detects all available env vars and generates a starter profile with populated defaults

### Channel Branding

- [x] **BRND-01**: Pipeline fetches YouTube channel name, avatar image, and description via YouTube Data API using existing OAuth credentials
- [x] **BRND-02**: Watermark text defaults to channel name when not explicitly set in config
- [x] **BRND-03**: Intro/outro clips auto-generated from channel avatar + name + description tagline (no manual video files needed)
- [x] **BRND-04**: Thumbnail branding uses channel avatar as corner logo overlay
- [x] **BRND-05**: Channel branding cached locally — re-fetched only on explicit refresh or config change

### AI Prompt Generation

- [x] **AGEN-01**: User provides only tags (e.g., "lofi, rain, cozy, study") and OpenAI generates full SDXL positive prompt, negative prompt, and Suno music prompt
- [x] **AGEN-02**: Generated prompts respect the active profile's style (cinematic tags produce cinematic prompt style)
- [x] **AGEN-03**: Tag-to-prompt generation produces scene variation prompts (8 variants from tags, not 1 repeated prompt)
- [x] **AGEN-04**: Generated prompts are saved to the profile YAML so they're visible and editable before generation
- [x] **AGEN-05**: Pipeline can run end-to-end with just tags + profile name — no manual prompt editing required

### Local Gradio UI

- [x] **GRAD-01**: User can launch the Study Video pipeline from the Gradio UI Execute tab; pipeline stdout streams line-by-line without freezing the browser tab
- [x] **GRAD-02**: Execute tab accepts an optional tags field forwarded as --tags to the pipeline subprocess
- [x] **GRAD-03**: User can queue a pipeline run for a future datetime; the scheduler fires the subprocess at the scheduled time
- [x] **GRAD-04**: Schedule tab shows all queued jobs with status (pending/running/done/failed) and supports job cancellation
- [x] **GRAD-05**: User can add a planned video entry (title, tags, profile, notes) to the content roadmap from the Gradio UI
- [x] **GRAD-06**: Content Roadmap tab lists entries with status badges and supports status transitions (planned → producing → published)
- [x] **GRAD-07**: Roadmap entries can be reordered (move up/down) and deleted from the UI

## Out of Scope

| Feature | Reason |
|---------|--------|
| Auto-detect channel "vibe" from video history | Requires analyzing existing videos — complex, defer to v2 |
| Multi-channel support | Single channel workflow for now |
| Prompt marketplace/sharing | Over-engineering for single creator |
| Auto-scheduling YouTube uploads | Deferred per v1.0 decision |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DFLT-01 | Phase 16 | Complete |
| DFLT-02 | Phase 16 | Complete |
| DFLT-03 | Phase 16 | Complete |
| BRND-01 | Phase 17 | Complete |
| BRND-02 | Phase 17 | Complete |
| BRND-03 | Phase 17 | Complete |
| BRND-04 | Phase 17 | Complete |
| BRND-05 | Phase 17 | Complete |
| AGEN-01 | Phase 18 | Complete |
| AGEN-02 | Phase 18 | Complete |
| AGEN-03 | Phase 18 | Complete |
| AGEN-04 | Phase 18 | Complete |
| AGEN-05 | Phase 18 | Complete |
| GRAD-01 | Phase 19 | Planned |
| GRAD-02 | Phase 19 | Planned |
| GRAD-03 | Phase 19 | Planned |
| GRAD-04 | Phase 19 | Planned |
| GRAD-05 | Phase 19 | Planned |
| GRAD-06 | Phase 19 | Planned |
| GRAD-07 | Phase 19 | Planned |

**Coverage:**
- v1.2 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-03-28*

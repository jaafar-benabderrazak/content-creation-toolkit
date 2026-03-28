# Requirements: Content Creation Toolkit v1.2

**Defined:** 2026-03-28
**Core Value:** One command with tags produces a publish-ready video — zero manual prompt writing, channel-branded, auto-published.

## v1.2 Requirements — Smart Automation

### Smart Defaults

- [ ] **DFLT-01**: Config loader pre-fills Discord webhook URL, API keys, and channel info from environment variables when not set in YAML
- [ ] **DFLT-02**: Dashboard config editor shows which values are env-sourced vs. YAML-defined (visual distinction)
- [ ] **DFLT-03**: First-run setup detects all available env vars and generates a starter profile with populated defaults

### Channel Branding

- [ ] **BRND-01**: Pipeline fetches YouTube channel name, avatar image, and description via YouTube Data API using existing OAuth credentials
- [ ] **BRND-02**: Watermark text defaults to channel name when not explicitly set in config
- [ ] **BRND-03**: Intro/outro clips auto-generated from channel avatar + name + description tagline (no manual video files needed)
- [ ] **BRND-04**: Thumbnail branding uses channel avatar as corner logo overlay
- [ ] **BRND-05**: Channel branding cached locally — re-fetched only on explicit refresh or config change

### AI Prompt Generation

- [ ] **AGEN-01**: User provides only tags (e.g., "lofi, rain, cozy, study") and OpenAI generates full SDXL positive prompt, negative prompt, and Suno music prompt
- [ ] **AGEN-02**: Generated prompts respect the active profile's style (cinematic tags produce cinematic prompt style)
- [ ] **AGEN-03**: Tag-to-prompt generation produces scene variation prompts (8 variants from tags, not 1 repeated prompt)
- [ ] **AGEN-04**: Generated prompts are saved to the profile YAML so they're visible and editable before generation
- [ ] **AGEN-05**: Pipeline can run end-to-end with just tags + profile name — no manual prompt editing required

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
| DFLT-01 | — | Pending |
| DFLT-02 | — | Pending |
| DFLT-03 | — | Pending |
| BRND-01 | — | Pending |
| BRND-02 | — | Pending |
| BRND-03 | — | Pending |
| BRND-04 | — | Pending |
| BRND-05 | — | Pending |
| AGEN-01 | — | Pending |
| AGEN-02 | — | Pending |
| AGEN-03 | — | Pending |
| AGEN-04 | — | Pending |
| AGEN-05 | — | Pending |

**Coverage:**
- v1.2 requirements: 13 total
- Mapped to phases: 0
- Unmapped: 13

---
*Requirements defined: 2026-03-28*

# Feature Research

**Domain:** Video content creation automation pipeline (local, single-creator, Python)
**Researched:** 2026-03-28
**Confidence:** MEDIUM — primary sources are YouTube Data API v3 official docs, Discord/Slack official docs, and multiple corroborated WebSearch findings. Approval-gate-over-webhook pattern is confirmed as feasible but implementation specifics are LOW confidence (no direct reference implementation found).

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features this toolkit must have for the new milestone to feel complete. Missing any of these makes the system feel half-built.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| YouTube upload (title, description, tags, category) | Any publishing pipeline without actual publishing is a preview tool | MEDIUM | `videos.insert` costs 1,600 quota units. 10,000 units/day default = ~6 uploads/day. Resumable upload required for all files >5 MB |
| Custom thumbnail upload to YouTube | YouTube itself surfaces thumbnails as a primary discovery signal; auto-generated thumbnails are visibly worse | LOW | `thumbnails.set` costs ~50 units. Requires 1280×720 px, JPEG/PNG, max 2 MB. Cannot be set on Shorts |
| OAuth 2.0 token persistence (refresh token storage) | Re-authenticating every run breaks automation entirely | MEDIUM | Must use `access_type=offline`, store refresh token to disk/file, handle `RefreshError` and re-auth flow. Scope: `youtube.upload` not full `youtube` |
| Resumable upload with retry/exponential backoff | Large video files fail on flaky connections without recovery; non-resumable = restart from zero | MEDIUM | Use `MediaFileUpload(chunksize=-1, resumable=True)` + `next_chunk()` loop with exponential backoff on `TransportError` |
| Discord webhook notification on completion | Creator needs to know generation is done without polling the terminal | LOW | Webhooks are send-only HTTP POST. Rate limit: 30 messages/minute. No bot, no OAuth. Just a URL |
| Slack webhook notification on completion | Same as Discord — creator may use Slack instead | LOW | Incoming webhooks via Block Kit or simple JSON payload. Same pattern as Discord |
| Error alert notifications (Discord/Slack) | Silent failures leave the creator unaware for hours | LOW | Same channel/webhook, different message format. Include pipeline stage and error summary |
| Prompt/config externalized to YAML or JSON | Prompts hardcoded in Python source = requires code edit per video; unworkable for regular use | MEDIUM | Load at runtime; support both file path and UI-provided override. Gradio can read/write YAML via standard Python |
| Gradio config UI exposing prompt and style fields | CLI-only config with YAML is still developer-facing; Gradio makes it accessible for non-code changes | MEDIUM | Gradio already a dep via AnimateDiff. Use `gr.Textbox`, `gr.Dropdown`, `gr.File` for config load/save |
| Post-production: watermark overlay | Branded output is baseline for any public content | LOW | FFmpeg overlay filter or MoviePy `CompositeVideoClip`. Trivial to add once pipeline exists |
| Post-production: subtitle burn-in | Subtitles are required for accessibility and engagement on short-form; YouTube auto-captions are unreliable | MEDIUM | FFmpeg `subtitles` filter or MoviePy + pysrt. Requires generated .srt from TTS script |
| Post-production: intro/outro append | Channel identity; every professional channel has it | LOW | FFmpeg concat or MoviePy concatenation. Intro/outro are static video files |

---

### Differentiators (Competitive Advantage)

Features beyond baseline that match the project's core value ("one command to publish-ready").

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Human approval gate via Discord/Slack before publish | Prevents publishing mistakes without requiring manual terminal intervention; aligns with async creator workflow | HIGH | Discord webhooks are send-only. True interactive approval (Approve/Reject buttons) requires either: (a) a Discord bot with slash commands/interactions, or (b) polling a Slack webhook response URL. For v1, a simpler pattern works: send preview + prompt manual command or flag file to confirm. See dependency notes |
| Template/edit profiles (lofi-study, tech-tutorial, cinematic) | Eliminates per-video reconfiguration; profile bundles color grade preset, font, watermark, pacing | MEDIUM | Implement as named YAML config bundles. One profile = one YAML file under `profiles/`. Loaded by both pipelines |
| Best-frame thumbnail extraction + text overlay | Avoids extra SD generation cost; uses existing video frames; deterministic | MEDIUM | OpenCV or MoviePy for frame scoring (sharpness, brightness variance). PIL/Pillow for text overlay. Output: 1280×720 JPEG |
| Color grade preset per profile | Consistent visual identity across videos; differentiates from raw AI output | MEDIUM | FFmpeg `curves` or `eq` filter for simple LUT-style grading. Full LUT (.cube) via `lut3d` filter. Apply per profile |
| Shared notification/publish layer (both pipelines use same module) | Prevents divergence where study pipeline and TikTok pipeline behave differently in production | LOW | Extract `publisher.py` and `notifier.py` as shared modules imported by both pipeline entry points |
| Resumable pipeline state (generation can restart mid-stage) | Already exists for generation; extending to post-production and publish stages prevents full reruns | MEDIUM | Existing progress tracking mechanism; extend checkpoint markers to cover post-prod and upload stages |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full Discord/Slack bot for approval (interactive buttons in v1) | Feels like the right UX for approval workflows | Requires persistent process, OAuth bot registration, gateway connection, hosting. Doubles the operational surface for a local tool. Discord's interaction endpoint must be publicly reachable — impossible in local-only context without ngrok | v1: send preview notification + require creator to run `publish --approve <job_id>` CLI command or place a flag file. v2: consider bot if remote access is needed |
| YouTube scheduling / optimal post time | Creators want to maximize reach | Requires YouTube scheduling API (separate quota), timezone logic, analytics read access. Out of scope per PROJECT.md | Immediate upload is the v1 contract; scheduling deferred to v2 |
| Web-hosted UI | More accessible than local Gradio | Adds cloud infra, auth, secrets management, HTTPS, port exposure. Breaks local-GPU constraint | Local Gradio on `localhost:7860` is the contract for v1 |
| Full channel management (playlists, end screens, cards, analytics) | Single API, why not use all of it? | Each feature adds quota cost, OAuth scope expansion, and test surface. YouTube audit requirements get stricter with broader scopes | Add only what drives value: `videos.insert` + `thumbnails.set` is the minimum |
| Real-time progress streaming to UI | Looks impressive | Requires WebSockets or SSE in Gradio, significantly increases complexity for incremental benefit | Gradio's existing progress bar component (`gr.Progress`) is sufficient; polling works for local use |
| Auto-scene detection and smart trimming | AI-driven editing sounds like a differentiator | Requires video understanding models (heavy), is highly subjective, and produces unpredictable cuts. Already deferred in PROJECT.md | Manual scene config in YAML profiles is deterministic and faster |
| Multi-channel / multi-account YouTube publishing | Power creator workflow | OAuth token management multiplies in complexity; quota per project means juggling GCP projects | One account, one project, one credential file in v1 |
| TikTok thumbnail support via automation | TikTok has cover image support | TikTok Content API cover image is set differently and the API surface changes frequently. Out of scope for this milestone | TikTok pipeline already posts directly; add cover support only if TikTok API stabilizes |

---

## Feature Dependencies

```
[YAML/JSON Config Files]
    └──required by──> [Gradio Config UI]  (UI reads/writes YAML; can't expose what doesn't exist)
    └──required by──> [Template/Edit Profiles]  (profiles ARE YAML files)

[Template/Edit Profiles]
    └──required by──> [Color Grade Preset Per Profile]
    └──required by──> [Post-Production Pipeline]  (profile drives which post-prod steps run)

[Post-Production Pipeline]
    └──required by──> [Best-Frame Thumbnail Extraction]  (runs after video is assembled)
    └──required by──> [Subtitle Burn-In]  (needs assembled video)
    └──required by──> [Watermark Overlay]  (needs assembled video)
    └──required by──> [Intro/Outro Append]  (needs assembled video)

[Post-Production Pipeline]
    └──required by──> [YouTube Upload]  (upload the finished artifact)
    └──required by──> [Thumbnail Upload to YouTube]  (thumbnail must exist before thumbnails.set call)

[YouTube Upload]
    └──required by──> [OAuth 2.0 Token Persistence]  (upload fails without valid token)
    └──required by──> [Resumable Upload + Retry]  (upload needs this to be reliable)
    └──required by──> [Thumbnail Upload to YouTube]  (needs videoId from upload response)

[Discord/Slack Notifications]
    └──required by──> [Human Approval Gate v1]  (approval gate sends preview via notification)

[Human Approval Gate v1]
    └──required by──> [YouTube Upload]  (publish only fires after approval confirmed)

[Shared Notify/Publish Layer]
    └──enhances──> [Discord/Slack Notifications]  (one implementation, both pipelines)
    └──enhances──> [YouTube Upload]  (one implementation, both pipelines)
```

### Dependency Notes

- **YAML Config required before Gradio UI:** The UI is a frontend for config files. Building the UI first without a schema results in a UI that doesn't persist anything. Define config schema first.
- **Post-production required before YouTube upload:** Upload operates on the final video artifact. Post-prod must output a single file before upload fires.
- **Thumbnail required before thumbnails.set:** `thumbnails.set` requires a `videoId` (from the upload response) and a local image file. Thumbnail generation must complete before the upload call returns and before thumbnails.set is called.
- **OAuth token persistence blocks all YouTube features:** Without stored refresh token, the entire YouTube surface requires re-auth on every run. This is the first YouTube feature to implement.
- **Approval gate in v1 does not require a bot:** Send preview URL/file via webhook, then gate publish on CLI flag or file presence. No interactive button infrastructure needed.

---

## MVP Definition

### Launch With (v1) — This Milestone

- [ ] **YAML config schema + file-based loading** — all other config-dependent features require this foundation
- [ ] **Gradio UI with form fields for prompt/style/pipeline config** — replaces hardcoded Python; minimum: text fields, dropdowns, load/save config buttons
- [ ] **Post-production pipeline: watermark + subtitle burn-in + intro/outro** — baseline for public-ready output; apply to both study and TikTok pipelines
- [ ] **Best-frame thumbnail extraction with text overlay** — leverages existing frames; avoids additional SD generation
- [ ] **YouTube upload with OAuth persistence + resumable + thumbnail set** — core publishing feature; must handle token refresh silently
- [ ] **Discord webhook notification (generation complete + error alerts)** — minimum viable monitoring
- [ ] **Slack webhook notification (same events)** — parity with Discord; shared module
- [ ] **Human approval gate: preview notification + CLI confirm before publish** — prevents accidental publish without requiring bot infrastructure
- [ ] **Shared notify/publish module** — both pipelines must import the same code; no divergent implementations

### Add After Validation (v1.x)

- [ ] **Template/edit profiles (lofi-study, tech-tutorial, cinematic YAML bundles)** — add after basic post-production is working and profiles can be tested against real outputs
- [ ] **Color grade presets per profile** — add once profile system is in place; low effort when framework exists
- [ ] **Resumable pipeline state through post-prod and upload stages** — add when failed runs become common enough to justify; existing generation resumption already works

### Future Consideration (v2+)

- [ ] **Interactive approval bot (Discord/Slack)** — defer until remote operation or team use requires it; local CLI gate is sufficient for single creator
- [ ] **YouTube scheduling / optimal post timing** — defer per PROJECT.md; adds API scope and complexity without v1 value
- [ ] **Full channel management (playlists, end screens, analytics)** — defer; scope creep for a generation toolkit
- [ ] **Auto-scene detection / smart trimming** — defer per PROJECT.md; AI video understanding is heavy and nondeterministic
- [ ] **Multi-account YouTube publishing** — defer; not needed for single creator

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| YAML config schema + loading | HIGH | LOW | P1 |
| Gradio config UI | HIGH | MEDIUM | P1 |
| OAuth 2.0 token persistence | HIGH | MEDIUM | P1 — blocks all YouTube features |
| YouTube upload (resumable) | HIGH | MEDIUM | P1 |
| Thumbnail extraction + overlay | HIGH | MEDIUM | P1 |
| Thumbnail upload to YouTube | HIGH | LOW | P1 — depends on upload |
| Post-production: watermark | MEDIUM | LOW | P1 |
| Post-production: subtitle burn-in | HIGH | MEDIUM | P1 |
| Post-production: intro/outro | MEDIUM | LOW | P1 |
| Discord webhook notifications | MEDIUM | LOW | P1 |
| Slack webhook notifications | MEDIUM | LOW | P1 |
| Human approval gate (CLI pattern) | HIGH | LOW | P1 |
| Shared notify/publish module | MEDIUM | LOW | P1 — prevents divergence |
| Template/edit profiles | MEDIUM | MEDIUM | P2 |
| Color grade presets | MEDIUM | MEDIUM | P2 |
| Resumable pipeline state (extended) | MEDIUM | MEDIUM | P2 |
| Interactive approval bot | LOW | HIGH | P3 |
| YouTube scheduling | LOW | HIGH | P3 |
| Multi-account publishing | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for this milestone
- P2: Add after P1 validated
- P3: Future consideration

---

## Competitor Feature Analysis

| Feature | Typical SaaS tools (Opus Clip, Zebracat) | Open-source AI-Content-Studio | Our Approach |
|---------|------------------------------------------|-------------------------------|--------------|
| Config UI | Web-based, hosted | None (hardcoded) | Local Gradio — no cloud infra |
| Publishing | Automated, immediate | Automated, CLI | Gated: approval before publish |
| Thumbnail | AI-generated (cloud) | None | Best-frame extraction, local |
| Notifications | Email, in-app | None | Discord + Slack webhooks |
| Approval gate | None (auto-publish) | None | CLI gate after preview notification |
| Post-production | Automatic transitions, captions | FFmpeg basic | Profiles-driven: per-pipeline presets |
| Platform support | YouTube + TikTok + Instagram | YouTube only | YouTube + TikTok (existing) |
| Infra requirement | Cloud, subscription | Local | Local GPU, no subscription |

---

## Sources

- [YouTube Data API v3 — Upload a Video (official)](https://developers.google.com/youtube/v3/guides/uploading_a_video) — HIGH confidence
- [YouTube Data API v3 — Resumable Uploads (official)](https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol) — HIGH confidence
- [YouTube Data API v3 — Thumbnails: set (official)](https://developers.google.com/youtube/v3/docs/thumbnails/set) — HIGH confidence
- [YouTube Data API v3 — Quota and compliance (official)](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits) — HIGH confidence
- [Discord Webhooks — Official documentation](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) — HIGH confidence
- [Discord Webhook Resource — Developer docs](https://discord.com/developers/docs/resources/webhook) — HIGH confidence
- [Slack — Approval workflow development guide (official)](https://api.slack.com/best-practices/blueprints/approval-workflows) — HIGH confidence
- [YouTube upload API guide — 2026 (Postproxy)](https://postproxy.dev/blog/youtube-upload-api-guide/) — MEDIUM confidence (corroborates official docs)
- [Python YouTube upload with OAuth 2.0 reauthentication (Medium, 2025)](https://python.plainenglish.io/uploading-videos-to-youtube-using-python-and-oauth-2-0-a-step-by-step-guide-with-reauthentication-fea2602e6f3d) — MEDIUM confidence
- [MoviePy documentation](https://zulko.github.io/moviepy/) — HIGH confidence (official)
- [FFmpeg subtitle burn-in guide](https://www.ffmpeg.media/articles/subtitles-burn-in-soft-subs-format-conversion) — MEDIUM confidence
- [n8n — Interactive Slack approval + webhooks](https://n8n.io/workflows/5049-interactive-slack-approval-and-data-submission-system-with-webhooks/) — LOW confidence (pattern reference only)
- [YouTube automation 2026 — Thinkpeak](https://thinkpeak.ai/youtube-automations-2026-guide/) — LOW confidence (trend reference)

---

*Feature research for: Video content creation automation pipeline*
*Researched: 2026-03-28*

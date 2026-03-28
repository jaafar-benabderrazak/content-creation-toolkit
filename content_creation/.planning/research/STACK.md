# Stack Research

**Domain:** Python video generation pipeline — publishing, post-processing, config UI, notifications
**Researched:** 2026-03-28
**Confidence:** HIGH (all versions verified against PyPI; library choices verified against official docs and multiple sources)

---

## Context: What is Already in Place

Do not re-introduce or version-pin these. They are constraints, not choices.

| Technology | Version (existing) | Role |
|---|---|---|
| MoviePy | 1.0.x | Video composition — existing codebase uses v1 API (`moviepy.editor`, `.set_*` methods) |
| OpenCV (cv2) | 4.x | Frame processing, codec handling |
| Pillow | latest (12.1.1 on PyPI) | Image post-processing, text overlays |
| Gradio | 3.36.1 (AnimateDiff pin) | Existing AnimateDiff UI dep — version conflict risk with new UI |
| FFmpeg | system | External codec dependency |
| pydub | 0.25.x+ | Audio manipulation |

---

## Recommended Stack for New Capabilities

### 1. Configuration UI

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| Gradio | **5.x** (pin `>=5.0,<6.0`) | Configuration UI for prompt/scene/style inputs | Gradio 6.10.0 is current stable but has its own breaking changes from 5.x. Use 5.x because AnimateDiff pins 3.36.1 — you will run the new UI in a separate venv or process. Gradio 5 is the last major version with stable component APIs before the 6.x ChatInterface/Dataframe restructure. Gradio is already a project dependency so no conceptual overhead. |

**Rationale for 5.x over 6.x:** Gradio 6 (6.10.0, released March 24 2026) introduced breaking changes to `gr.ChatInterface` message format, `gr.Dataframe` parameter syntax, and `AppError` exception hierarchy. For a config form UI (not a chatbot), 5.x provides all needed primitives (`gr.Blocks`, `gr.Textbox`, `gr.Slider`, `gr.File`, `gr.Button`, `gr.Tab`) without requiring migration risk. Upgrade to 6 in a later milestone when AnimateDiff dependency conflict is resolved.

**Alternative:** Streamlit 1.43+ — nearly identical developer experience for forms. Use Streamlit if the team already uses it or if Gradio environment isolation proves too painful. Streamlit has cleaner session state management but worse file upload UX for video previews.

**Do NOT use:** Flask/FastAPI with a custom HTML frontend — massively over-engineers a local tool that needs a config form, not a web app.

---

### 2. Post-Processing Pipeline (color grade, transitions, watermark, subtitles)

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| MoviePy | **1.0.x (existing — do not upgrade)** | Clip composition, concatenation, overlays | The existing codebase uses MoviePy 1.x API (`moviepy.editor`, `.set_position()`, `.set_opacity()`, `.set_audio()`). MoviePy 2.0 (latest: 2.2.1) has critical breaking changes: removed `moviepy.editor` namespace, renamed all `.set_*` to `.with_*`, dropped ImageMagick, refactored effects to classes. Upgrading would require rewriting both existing pipelines. Stay on 1.0.x for this milestone. |
| Pillow | **12.1.1** | Watermark compositing, text overlay rendering on thumbnail frames | Already in use. `Image.alpha_composite()` for watermark, `ImageDraw.text()` with `ImageFont.truetype()` for text. No additional dep needed. |
| FFmpeg | system (existing) | Subtitle burn-in via `ffmpeg -vf subtitles=...` subprocess call | MoviePy delegates to FFmpeg. For subtitle burn-in, call FFmpeg directly via `subprocess` rather than going through MoviePy's subtitle tooling (which requires ImageMagick in 1.x). |

**Color grading in MoviePy 1.x:** Use `clip.fl_image()` with a numpy-based LUT function. No additional library needed — numpy is already installed. For more complex grades (curves, hue rotation), add `colour-science` (PyPI: `colour-science`, version `0.4.x+`), but this is optional.

**Subtitle burn-in options:**

| Approach | Library | When to Use |
|---|---|---|
| Hard-coded SRT burn via FFmpeg subprocess | None (just `subprocess`) | Simplest, production quality, no new dep |
| Soft subtitle overlay via MoviePy TextClip | ImageMagick required (MoviePy 1.x) | Only if ImageMagick is already installed |
| Python subtitles library | `pysrt` 1.1.2 | When you need to parse SRT files into timed clips |

**Recommendation:** FFmpeg subprocess for subtitle burn-in (hard subtitles). Add `pysrt` only if SRT file parsing is needed.

---

### 3. YouTube Data API v3 Integration

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| `google-api-python-client` | **2.193.0** | YouTube API v3 client (`videos.insert`, `thumbnails.set`) | Official Google client library. The only supported method for programmatic YouTube uploads. Handles resumable upload protocol automatically via `MediaFileUpload`. |
| `google-auth-oauthlib` | **1.3.0** | OAuth 2.0 flow for installed applications | Required for `InstalledAppFlow.from_client_secrets_file()` + `flow.run_local_server()`. Handles token refresh via `credentials.refresh(Request())`. |
| `google-auth-httplib2` | **0.3.0** | HTTP transport for google-auth credentials | Required by `google-api-python-client`. Do not replace with `requests` — the client library requires this transport. |

**Upload specifics (verified against official docs):**
- Use `MediaFileUpload(path, chunksize=-1, resumable=True)` — chunked resumable protocol required for all videos >5 MB
- `videos.insert` costs **1,600 quota units** per upload; default quota is 10,000 units/day = ~6 uploads/day before hitting quota
- Thumbnail upload: `thumbnails.set(videoId=id)` with JPEG/PNG, max 2 MB, recommended 1280×720 16:9
- OAuth scope: `https://www.googleapis.com/auth/youtube.upload` (narrowest scope that allows upload + thumbnail)
- Store token as JSON file (`token.json`) and reload on subsequent runs — avoids re-authorizing every pipeline run

**Token persistence pattern:**
```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_credentials(token_path, secrets_path):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
    return creds
```

**Do NOT use:** `pytube`, `yt-dlp`, or any scraping library for uploads — these are download tools, not upload APIs, and violate ToS.

---

### 4. Discord Webhook Notifications

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| `discord-webhook` | **1.4.1** | Structured Discord webhook messages with embeds, file attachments | Thin wrapper over `requests` that handles embed formatting, file uploads (for video previews), and rate-limit responses. For a notification-only v1 (no bot framework), this is the right scope. |
| `requests` | existing | Fallback HTTP client if `discord-webhook` is inadequate | Already in the project. Pure `requests.post()` to the webhook URL works fine for text-only notifications. |

**Approval gate pattern:** Discord webhooks are one-way (send only). For an approval gate, the recommended v1 approach is:
1. Send preview notification with embed + video link via webhook
2. Write a `pending_approval` flag file to disk
3. Poll a shared approval endpoint OR use a separate lightweight mechanism

**Two viable approval gate implementations:**

| Approach | Mechanism | Complexity | Recommendation |
|---|---|---|---|
| File-based gate | Write `approval_pending.json`, operator deletes or renames to `approved` | Trivial | Use for v1 — matches the "single creator, local machine" constraint |
| Discord bot reaction polling | `discord.py` bot monitors a channel for thumbs-up reaction | Moderate | Overkill for v1; requires persistent process and bot token |
| Slack webhook + manual confirmation | Send to Slack, operator replies in thread, pipeline polls Slack API | Moderate | Works if team uses Slack; requires Slack app, not just webhook |

**Verdict:** For v1, use file-based approval gate. Discord/Slack webhooks notify; a simple `input()` prompt or file poll gates the publish step. Do not build a bot for v1.

**Do NOT use:** `discord.py` (full bot framework) for v1 — requires a persistent bot process, privileged intents, and Discord bot application registration. Webhook-only is explicitly stated as the design decision.

---

### 5. Slack Webhook Notifications

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| `slack-sdk` | **3.41.0** | Slack webhook client via `WebhookClient` | Official Slack SDK. `WebhookClient(url).send(text=..., blocks=[...])` handles Block Kit formatting, retries, and response validation. Preferred over raw `requests.post()` because it validates response status codes and raises on failure. |

**Alternative:** Raw `requests.post(webhook_url, json={"text": message})` — works but provides no error handling. Use `slack-sdk` for production reliability; use raw requests only for throwaway scripts.

**Block Kit for approval notifications:**
```python
from slack_sdk.webhook import WebhookClient

webhook = WebhookClient(os.environ["SLACK_WEBHOOK_URL"])
webhook.send(
    text="Video ready for review",
    blocks=[
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*\nReview and approve before YouTube upload."}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "value": "approve"},
        ]}
    ]
)
```
Note: button interactivity requires a Slack app with request URL configured — not available with incoming webhooks alone. For v1, send notification text only; approval is handled out-of-band (file flag or CLI prompt).

---

### 6. AI Thumbnail Generation

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| OpenCV (`cv2`) | existing | Frame extraction from video at multiple intervals | `cv2.VideoCapture` + `cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)` for targeted frame extraction. Extract at 25%, 50%, 75% of video length and score by sharpness (Laplacian variance). |
| Pillow | existing (12.1.1) | Text overlay, border, branding on selected frame | `ImageDraw`, `ImageFont.truetype()`. Already used in the TikTok pipeline for caption rendering. |

**No new dependencies needed for thumbnail generation.** The approach is:
1. Extract N candidate frames with OpenCV
2. Score by sharpness: `cv2.Laplacian(gray, cv2.CV_64F).var()` — higher = sharper
3. Select best frame, convert to PIL Image
4. Composite text overlay, logo watermark via Pillow
5. Resize to 1280×720 JPEG for YouTube thumbnails.set

**Optional AI enhancement:** `transformers` (already installed) can run CLIP zero-shot scoring to pick the "most visually interesting" frame against a text prompt. Only add this if pure sharpness scoring produces poor results — it adds inference overhead.

**Do NOT use:** Dedicated thumbnail SaaS APIs (Canva API, Adobe Express) — adds external dependency, cost, and network round-trip for a local pipeline.

---

## Supporting Library Summary

| Library | Version | New? | Purpose |
|---|---|---|---|
| `google-api-python-client` | 2.193.0 | Yes | YouTube API v3 client |
| `google-auth-oauthlib` | 1.3.0 | Yes | OAuth 2.0 installed app flow |
| `google-auth-httplib2` | 0.3.0 | Yes | HTTP transport for google-auth |
| `slack-sdk` | 3.41.0 | Yes | Slack webhook client |
| `discord-webhook` | 1.4.1 | Yes | Discord webhook with embeds |
| `gradio` | 5.x (>=5.0,<6.0) | Yes (new version) | Config UI — separate from AnimateDiff's 3.36.1 |
| `pysrt` | 1.1.2 | Yes (optional) | SRT subtitle file parsing |
| `python-dotenv` | 1.2.2 | Yes | `.env` file loading for new API keys |
| `pyyaml` | 6.0.3 | Existing | YAML config file parsing for UI-saved configs |
| `Pillow` | 12.1.1 | Existing | Thumbnail compositing |
| `opencv-python` | 4.13.0.92 | Existing | Frame extraction |
| `requests` | existing | Existing | HTTP fallback |

---

## Installation

```bash
# YouTube publishing
pip install google-api-python-client==2.193.0 google-auth-oauthlib==1.3.0 google-auth-httplib2==0.3.0

# Notifications
pip install slack-sdk==3.41.0 discord-webhook==1.4.1

# Config UI (in a separate venv or after resolving AnimateDiff conflict)
pip install "gradio>=5.0,<6.0"

# Env management (new)
pip install python-dotenv==1.2.2

# Optional: subtitle parsing
pip install pysrt==1.1.2
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|---|---|---|
| `google-api-python-client` | `pytube` | pytube is a download library, not an upload client. Has no `videos.insert` implementation. |
| `google-api-python-client` | Direct HTTP with `requests` | Resumable upload protocol requires complex chunking, retry logic, and session management. The official client handles all of this. |
| `slack-sdk` | Raw `requests.post()` | Works but provides zero error handling. For a notification system, knowing when delivery failed matters. |
| `discord-webhook` | `discord.py` | Full bot framework — requires persistent process, bot registration, privileged intents. Webhook-only is the stated design constraint. |
| `discord-webhook` | Raw `requests.post()` | Fine for text. `discord-webhook` adds embed formatting and file attachment support needed for video preview thumbnails at no real cost. |
| Gradio 5.x | Gradio 6.x | Gradio 6 has breaking changes to core components. AnimateDiff pins 3.36.1. Use 5.x to minimize migration scope for this milestone. |
| Gradio 5.x | Streamlit 1.43+ | Either works. Choose Gradio because it's already a project dependency. |
| MoviePy 1.x (stay) | MoviePy 2.x (upgrade) | 2.x has breaking changes to `moviepy.editor` import path and all `.set_*` methods. Both existing pipelines would require rewrite. Defer upgrade to a dedicated migration milestone. |
| FFmpeg subprocess (subtitles) | MoviePy TextClip | TextClip in MoviePy 1.x requires ImageMagick — an extra system dep. FFmpeg produces better subtitle rendering and is already present. |
| OpenCV + Pillow (thumbnails) | Dedicated AI thumbnail service | Adds external dependency and cost. OpenCV sharpness scoring is sufficient for best-frame selection. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|---|---|---|
| MoviePy 2.x for new post-processing | Breaks existing `moviepy.editor` imports in both pipelines. API incompatible with `.set_*` pattern used throughout. | Stay on MoviePy 1.0.x; plan a dedicated upgrade milestone |
| Gradio 6.x for this milestone | Breaking changes in `gr.ChatInterface`, `gr.Dataframe`. AnimateDiff dependency conflict unresolved. | Gradio 5.x in isolated venv |
| `discord.py` bot | Requires persistent process, bot token, privileged intents — massively over-engineers a webhook notification system | `discord-webhook` library |
| YouTube upload via scraping/automation (`yt-dlp`, `selenium`) | Violates YouTube ToS, fragile against UI changes, no metadata/thumbnail control | `google-api-python-client` with Data API v3 |
| Service account auth for YouTube | YouTube Data API does not support service accounts for user channel uploads. Only OAuth 2.0 installed flow works. | `InstalledAppFlow` from `google-auth-oauthlib` |
| `imageio-ffmpeg` for subtitle burn-in | Adds another FFmpeg wrapper when `subprocess` + system FFmpeg is already present | `subprocess.run(["ffmpeg", "-vf", "subtitles=..."])` |

---

## Version Compatibility Notes

| Package | Compatible With | Notes |
|---|---|---|
| `google-api-python-client==2.193.0` | `google-auth-oauthlib==1.3.0`, `google-auth-httplib2==0.3.0` | All three must be installed together; they share the `google-auth` dependency chain |
| `gradio>=5.0,<6.0` | Python 3.10+ | Gradio 5 dropped Python 3.8 support. Python 3.10+ (existing constraint) is fine. |
| `discord-webhook==1.4.1` | `requests` (any recent) | `discord-webhook` uses `requests` internally; no conflict with existing usage |
| MoviePy 1.0.x | `opencv-python` 4.x, `Pillow` 12.x | No conflict. MoviePy 2.x would conflict with existing `.editor` imports. |
| `slack-sdk==3.41.0` | Python 3.6+ | No conflicts with existing stack |

---

## Stack Patterns for This Milestone

**Gradio isolation pattern** (critical — AnimateDiff pins Gradio 3.36.1):
- Option A: Separate Python venv for the config UI process; communicate with pipelines via JSON config files written to disk
- Option B: Launch Gradio UI as a subprocess from the main pipeline with a dedicated venv
- Option C: Resolve AnimateDiff dep by patching it to accept Gradio 5.x (check AnimateDiff's actual Gradio usage first)

**Recommended:** Option A (separate venv, JSON hand-off). Matches existing pattern of file-based data flow (generated images, audio, video all go through filesystem). Config UI writes a `pipeline_config.json`; pipeline reads it on start.

**OAuth token management:**
- Store `token.json` in a `.secrets/` directory at project root
- Add `.secrets/` to `.gitignore`
- Never pass token path as a hardcoded string — use an env var `YOUTUBE_TOKEN_PATH`

**Notification architecture:**
- Build a single `notifications.py` module with `NotificationService` class
- Methods: `send_generation_complete()`, `send_approval_request()`, `send_error()`, `send_upload_complete()`
- Both Discord and Slack send the same payload — use a strategy pattern or simple conditional dispatch
- Both pipelines (study video, TikTok) import from this module — shared layer as specified in PROJECT.md

---

## Sources

- PyPI version verification: `curl https://pypi.org/pypi/{package}/json` — versions confirmed 2026-03-28 (HIGH confidence)
- [YouTube Data API v3 — Upload a Video](https://developers.google.com/youtube/v3/guides/uploading_a_video) — resumable upload, OAuth scopes, quota (HIGH confidence)
- [YouTube Data API v3 — Videos: insert](https://developers.google.com/youtube/v3/docs/videos/insert) — 1,600 units cost confirmed (HIGH confidence)
- [google-auth-oauthlib InstalledAppFlow](https://googleapis.dev/python/google-auth-oauthlib/latest/reference/google_auth_oauthlib.flow.html) — token refresh pattern (HIGH confidence)
- [Gradio 5 announcement — Hugging Face blog](https://huggingface.co/blog/gradio-5) — Gradio 5 major features (HIGH confidence)
- [Gradio 6 Migration Guide](https://www.gradio.app/main/guides/gradio-6-migration-guide) — breaking changes in 6.x confirmed (HIGH confidence)
- [Slack SDK Webhook Client](https://slack.dev/python-slack-sdk/webhook/index.html) — WebhookClient usage (HIGH confidence)
- [MoviePy 2.x migration guide](https://zulko.github.io/moviepy/getting_started/updating_to_v2.html) — breaking changes in 2.0 confirmed (HIGH confidence)
- [discord-webhook PyPI](https://pypi.org/project/discord-webhook/) — version 1.4.1 confirmed (HIGH confidence)
- WebSearch: YouTube quota system, MoviePy 2.0 changes, Gradio 5/6 migration — MEDIUM confidence (corroborated by official docs)

---

*Stack research for: content creation pipeline — publishing milestone*
*Researched: 2026-03-28*

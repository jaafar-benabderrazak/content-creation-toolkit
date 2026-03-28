# Pitfalls Research

**Domain:** Content creation automation — YouTube publishing, webhook notifications, config UI, post-processing, thumbnail generation added to existing Python video generation toolkit
**Researched:** 2026-03-28
**Confidence:** MEDIUM-HIGH (YouTube API and Gradio pitfalls HIGH; webhook approval-gate and post-processing pitfalls MEDIUM)

---

## Critical Pitfalls

### Pitfall 1: OAuth2 Refresh Token Silently Expiring in "Testing" Mode

**What goes wrong:**
YouTube Data API OAuth2 apps left in "Testing" status on the Google Cloud Console issue refresh tokens that expire after 7 days. Uploads work during development, then start failing in production with `google.auth.exceptions.RefreshError: Token has been expired or revoked`. The app must re-run the OAuth consent flow interactively every week, which breaks any unattended pipeline.

**Why it happens:**
Google's OAuth policy for "External" apps in "Testing" status deliberately limits refresh token lifetime to 7 days. Developers test locally, get tokens, move on — and don't notice expiry until the pipeline runs unattended days later. Moving the app to "Production" status requires a Google verification review for sensitive scopes, which developers defer.

**How to avoid:**
- Immediately after OAuth integration works: submit the Google Cloud project for "Production" verification, or switch the OAuth consent screen to "Internal" if using a Google Workspace account (internal apps get long-lived tokens without review)
- Store the `token.json` / credential file path in config, not hardcoded
- Add a startup check that proactively refreshes the token before each upload attempt and logs clearly when refresh fails
- Never gate an unattended pipeline on a token obtained in Testing mode

**Warning signs:**
- Upload works in initial dev session but fails the following week with no code changes
- `RefreshError` or `invalid_grant` in logs
- Having to re-run OAuth flow more than once during development

**Phase to address:** YouTube publishing phase (before any unattended upload logic is written)

---

### Pitfall 2: YouTube Quota Exhaustion Blocking the Entire Project Quota Pool

**What goes wrong:**
Every `videos.insert` call costs 1,600 quota units out of a default 10,000 units/day. That is a hard limit of ~6 uploads per day. Quota resets at midnight Pacific Time, not per-user. All API keys in the same Google Cloud project share this pool — creating additional API keys does not multiply quota. A batch test run or a pipeline bug that retries failed uploads can exhaust the day's quota in minutes, blocking all API calls (including reads) for 24 hours.

**Why it happens:**
Developers underestimate the per-upload cost and run tests against the real quota. The 1,600-unit cost for `videos.insert` is not prominently documented in most tutorials.

**How to avoid:**
- Run all upload tests against a dedicated test Google Cloud project separate from the production project
- Implement a quota tracker: before each upload attempt, check whether units remain (calculate locally by tracking calls with timestamps)
- Add a guard in the upload function: refuse to upload if estimated remaining quota < 1,600 units
- Request a quota increase via the Google Cloud Console before going to production if the pipeline needs >6 uploads/day

**Warning signs:**
- `quotaExceeded` or `dailyLimitExceeded` 403 errors from any API call (including metadata reads) after a batch test run
- Upload function silently swallowed in a broad `except Exception` (already a pattern in this codebase — see CONCERNS.md)

**Phase to address:** YouTube publishing phase (before writing any retry or test-upload logic)

---

### Pitfall 3: Gradio CUDA/GPU Operations Hanging When `queue=True`

**What goes wrong:**
Gradio's default event handler queue (`queue=True`) runs callbacks in a thread pool. PyTorch CUDA operations invoked inside those threads hang indefinitely at certain kernel calls on Windows. This means any Gradio "Generate" button that triggers SDXL or audio model inference will freeze the UI permanently with no error output. The pipeline already runs on Windows 11 with NVIDIA GPU.

**Why it happens:**
PyTorch's CUDA context is not thread-safe in all configurations. Gradio's thread pool executor creates workers that don't own a CUDA context, causing blocking synchronization. This is a known open issue in Gradio (gradio-app/gradio#12492, gradio-app/gradio#6609) as of late 2025.

**How to avoid:**
- Do not run heavy GPU inference (SDXL, Stable Audio, model loading) directly inside Gradio event handler callbacks
- Instead, have the Gradio button handler enqueue a job to a separate subprocess or background thread that already owns a CUDA context, then use Gradio's progress/state polling to update the UI
- If direct invocation is required, use `queue=False` on the specific event (accepts reduced concurrency)
- Test GPU path explicitly through the Gradio UI before considering the config UI phase complete

**Warning signs:**
- "Generate" button spins indefinitely with no log output
- Gradio process shows GPU memory allocated but no forward-pass logs
- Works fine running the generator script directly from CLI but hangs inside Gradio

**Phase to address:** Config UI phase (design the UI-to-pipeline bridge before wiring up GPU calls)

---

### Pitfall 4: Resumable Upload Session URI Expiring Mid-Pipeline

**What goes wrong:**
YouTube's resumable upload protocol issues a session URI that has a finite lifetime. If the upload is paused for too long (e.g., waiting for an approval gate, or a slow GPU generation step running before the upload was initiated), the session URI expires and subsequent `PUT` requests return `404 Not Found`. The upload must restart from scratch, consuming another 1,600 quota units.

**Why it happens:**
The pipeline design initiates the OAuth flow or upload session early in the pipeline, then other steps (post-processing, thumbnail generation, approval) run before the actual upload bytes are sent. Session URIs are not permanent.

**How to avoid:**
- Initiate the resumable upload session only after all pre-upload steps (post-processing, thumbnail, approval) are complete — immediately before sending bytes
- Implement exponential backoff (1s → 2s → 4s → up to 64s) for 5xx errors, but do not retry 404 (expired session) — restart the full session instead
- Use `MediaFileUpload` with `chunksize` explicitly set; handle `HttpError` and distinguish 404 (expired) from 5xx (retryable)

**Warning signs:**
- Upload function receives `404` from `next_chunk()` despite the video file existing
- Upload process succeeds on small test files but fails on large (>1 GB) production videos
- Long delays between pipeline steps before upload begins

**Phase to address:** YouTube publishing phase (upload function design)

---

### Pitfall 5: Discord/Slack Approval Gate Implemented as Synchronous Polling

**What goes wrong:**
The approval gate (send preview, wait for thumbs-up before publishing) gets implemented as a loop that polls a webhook response URL or checks for a Discord reaction. This blocks the Python main thread for potentially minutes to hours. On a single-process local machine, this freezes the entire pipeline and prevents any other operation. If the process is killed, the approval state is lost.

**Why it happens:**
Outgoing webhooks (Discord/Slack) are fire-and-forget. Getting a "human approved" signal back requires either: (a) a listener server, (b) polling a Discord/Slack API endpoint, or (c) a file/flag checked by a separate process. Developers default to option (b) as a blocking loop.

**How to avoid:**
- For v1 (local, single-creator): implement approval as a CLI prompt (`input("Approve? [y/n]")`) after the webhook notification is sent — simpler, no polling, no server
- If webhook-driven approval is required: write a flag file to disk when the notification fires; use a separate watcher process or a simple `while` loop with `time.sleep(5)` and a hard timeout (e.g., 30 minutes), not a tight spin
- Document the approval timeout behavior explicitly — what happens if nobody responds?

**Warning signs:**
- Approval function blocks the process with no timeout
- No way to cancel/skip approval once started
- Process must be killed with Ctrl+C to abandon an upload

**Phase to address:** Notifications/approval phase

---

## Moderate Pitfalls

### Pitfall 6: YouTube Thumbnail Upload Failing on Shorts or Unverified Channels

**What goes wrong:**
`thumbnails.set` returns a `403 forbidden` with reason `"The caller does not have permission"` in two cases: (1) the video is identified as a YouTube Short (vertical format, <60s), or (2) the channel is not phone/ID verified. Custom thumbnails are disabled for Shorts regardless of API permissions.

**How to avoid:**
- Detect Short vs. long-form before calling `thumbnails.set`: check aspect ratio and duration of output video
- Verify the YouTube channel has custom thumbnail permissions enabled (channel settings → verify phone number)
- Wrap `thumbnails.set` in explicit error handling that distinguishes permission errors from network errors; log clearly which case occurred

**Phase to address:** Thumbnail generation phase

---

### Pitfall 7: MoviePy v1 vs v2 API Break in Post-Processing

**What goes wrong:**
MoviePy 2.0 renamed core methods (`subclip()` → `subclipped()`, `resize()` → `resized()`, `set_position()` → `with_position()`). The existing codebase uses moviepy and may be pinned to v1 or unpinned. Adding new post-processing code using v2 API against an environment running v1 causes `AttributeError` at runtime with no clear version context in the traceback. The existing codebase's dependency situation (deprecated moviepy noted in CONCERNS.md) compounds this.

**How to avoid:**
- Pin `moviepy` to a specific major version in requirements.txt before writing post-processing code
- Run `import moviepy; print(moviepy.__version__)` in the target environment before writing any post-processing code and pick the API version accordingly
- Do not mix v1 and v2 API calls in the same file

**Phase to address:** Post-processing phase (first action: pin and audit moviepy version)

---

### Pitfall 8: Discord Webhook File Attachment Size Limit Causing Silent Failures

**What goes wrong:**
Discord webhooks accept file attachments up to 25 MB (standard servers) or 500 MB (Nitro boosted servers). Preview videos for approval sent as attachments will fail silently if the file exceeds the limit — the webhook returns `400 Request Entity Too Large` which, if swallowed by a broad `except`, looks like a successful notification. The creator sees no Discord message and assumes the pipeline is stuck.

**How to avoid:**
- For preview notifications: send a low-res proxy (720p or lower) or a GIF preview, not the full production video
- Check file size before attempting webhook attachment; if over 20 MB (safe threshold), send only a thumbnail image + metadata text instead
- Never use bare `except` on webhook calls (this codebase already has this pattern — fixing it in CONCERNS.md should apply to all new code too)

**Phase to address:** Notifications phase

---

### Pitfall 9: Gradio Version Conflict with Existing AnimateDiff Dependency

**What goes wrong:**
AnimateDiff's requirements pin an old version of `gradio` (likely 3.x or early 4.x). Installing Gradio 5.x or 6.x for the new config UI breaks AnimateDiff's web UI if it has its own Gradio components. The version conflict either forces the new UI to use old Gradio (losing features), or breaks AnimateDiff.

**Why it happens:**
Gradio releases major versions with breaking changes every 6-12 months (4.0, 5.0, 6.0 all in the record). AnimateDiff's `requirements.txt` may not be maintained to track these.

**How to avoid:**
- Before designing the config UI: check the exact Gradio version AnimateDiff pins: `cat AnimateDiff/requirements.txt | grep gradio`
- If there is a conflict: isolate AnimateDiff in its own virtual environment or accept a specific Gradio version for both
- Design the config UI to work on whatever Gradio version the environment already has — do not assume Gradio 5+ features

**Phase to address:** Config UI phase (environment audit before any UI code)

---

### Pitfall 10: Config YAML/JSON Not Validated Against Schema — Silent Bad Configs

**What goes wrong:**
YAML/JSON-backed prompt configs loaded from disk are passed directly into pipeline functions. A typo in a field name (e.g., `duraion` instead of `duration`) silently uses a default or None value. The pipeline runs to completion but produces a video with wrong parameters. The creator only discovers the error after watching the output.

**How it happens:**
Python dict access with `.get()` returns `None` for missing keys silently. No schema validation is applied at load time.

**How to avoid:**
- Define a Pydantic model or dataclass for every config schema; validate loaded YAML/JSON against it at load time and raise immediately on unknown/missing fields
- All config load functions must fail loudly (not silently use defaults) when required fields are absent

**Phase to address:** Config UI phase (schema-first design — define schemas before building the UI)

---

## Technical Debt Patterns

Shortcuts relevant to the new milestone capabilities.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Storing OAuth token.json in project root | Easy to find | Accidentally committed to git; credential leak | Never — use a config dir outside the repo |
| Single YouTube API project for dev + prod | No project management overhead | One test run can exhaust prod quota for 24 hours | Never once production uploads start |
| Bare `except` on API calls (already in codebase) | Faster to write | Swallows quota errors, upload failures, webhook 429s silently | Never |
| Gradio `gr.Interface` instead of `gr.Blocks` for config UI | Faster initial setup | Cannot add conditional UI, multi-step workflows, or progress bars | Only for trivial single-function UIs |
| Sending full-res video as Discord preview | No extra ffmpeg pass | Exceeds 25 MB limit on any video >2 min; webhook silently fails | Never |
| Hard-coding webhook URLs in source | Fast wiring during dev | URLs in version control; rotation requires code changes | Never — use env vars |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| YouTube Data API v3 | Treating quota as "per key" — creating multiple API keys to multiply quota | Quota is per Google Cloud project, not per key. Use separate projects for dev/prod. |
| YouTube Data API v3 | Calling `thumbnails.set` before the video finishes processing on YouTube's side | Video processing is async; poll `videos.list` for `processingStatus == "succeeded"` before setting thumbnail |
| YouTube OAuth2 | Storing token in memory only; losing it on process restart | Persist `token.json` to disk (or a configured path) and reload at startup |
| Discord webhooks | Not handling `429 Retry-After` header | Read `Retry-After` from response header; sleep for that duration before retrying. Failed requests still consume rate limit. |
| Discord webhooks | Sending a new message for each pipeline event with no context | Use message edits/updates to the same message to avoid channel spam during a single pipeline run |
| Slack webhooks | Assuming Incoming Webhook URL is stable long-term | Slack deactivates webhooks when the installing user leaves a workspace; document the URL source and owner |
| Gradio | Expecting `gr.State` to persist across browser refresh | Gradio session state is ephemeral; config state must be explicitly saved to disk to survive UI restarts |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Running thumbnail frame extraction on full-res video in Python | Takes 2-3 minutes for a 60-min video | Use ffmpeg's `-ss` seek flag (input-side) + `thumbnail` filter; do not decode entire video in Python | Any video >10 min |
| Uploading thumbnail as a separate API call in a naive retry loop | Double-counts quota if first call returned ambiguous error | Check `videos.list` thumbnail field after upload to verify before retrying `thumbnails.set` | First upload with network hiccup |
| Loading post-processing clips into memory with MoviePy for 120-min videos | OOM (existing concern in CONCERNS.md — frame buffering) | Use ffmpeg subprocess calls for long-form post-processing; reserve MoviePy for clips <10 min | Any video >30 min on 16 GB RAM system |
| Triggering SDXL model reload on each "preview" click in Gradio config UI | 60-90 second delay per click | Load model once at Gradio app startup into `gr.State` or module-level variable; share across requests | First user of config UI |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| YouTube OAuth `client_secret.json` in project root without `.gitignore` entry | Credential exposure in version control | Add `client_secret*.json` and `token.json` to `.gitignore` immediately; store outside project root |
| Discord/Slack webhook URLs in source code or config files tracked by git | Anyone with repo access can post to the channel | Store webhook URLs in `.env`; `.env` already in use in this project — extend it |
| No HMAC validation on incoming Slack interaction payloads (if implementing interactive approval) | Any HTTP client can fake an approval | Validate Slack's `X-Slack-Signature` header using the signing secret for any endpoint that accepts approval signals |
| Logging full API responses that may contain OAuth tokens | Token leakage in log files | Sanitize log output; never log `Authorization` headers or `access_token` fields |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Config UI submits generation and provides no progress feedback for 2-4 hour runs | Creator thinks the UI is frozen; kills process mid-generation | Use Gradio's `gr.Progress` or streaming generator to emit timestamped status updates every ~30 seconds |
| Approval notification contains no preview of what is being approved | Creator must find the file manually to review | Include a frame grab (image) or the thumbnail in the Discord/Slack message alongside the title/description |
| Config UI resets all fields on every page load (ephemeral Gradio state) | Creator must re-enter all settings for each run | Auto-save config to a `last_run.yaml` file; reload it on startup |
| YouTube upload success/failure reported only in terminal, not in Gradio UI | Creator using the UI never sees upload status | Route upload result (video URL or error) back to a Gradio output component after pipeline completes |

---

## "Looks Done But Isn't" Checklist

- [ ] **YouTube OAuth setup:** Token persisted to disk and reloaded on restart — verify by restarting the process and uploading without re-authorizing
- [ ] **YouTube upload:** Video actually appears on the channel as "public" (not stuck at "processing" or defaulting to "private") — verify in YouTube Studio
- [ ] **Thumbnail:** Custom thumbnail visible on the video in YouTube Studio — `thumbnails.set` returns 200 but YouTube can still reject the image silently
- [ ] **Discord notification:** Message appears in the correct channel with the preview image attached — test with a >25 MB and a <25 MB file to validate the size guard
- [ ] **Slack notification:** Webhook URL still active — Slack deactivates stale webhooks; test the URL before relying on it
- [ ] **Config UI:** Loaded YAML config round-trips correctly (save → reload → same values) — validation schema catches missing required fields
- [ ] **Post-processing:** Subtitle burn-in renders correctly on Windows (font path issue from CONCERNS.md); test on target machine not just developer terminal
- [ ] **Approval gate:** Pipeline does not hang forever if nobody approves — there is a timeout and a fallback behavior
- [ ] **Gradio GPU path:** "Generate" button works end-to-end through UI, not just via CLI script

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| OAuth refresh token expired (Testing mode) | LOW | Re-run OAuth consent flow to get new token; then immediately move app to Production status |
| YouTube quota exhausted | MEDIUM | Wait until midnight PT for reset; switch to separate dev Google Cloud project immediately to prevent recurrence |
| Resumable upload session expired | LOW | Re-initiate upload session (costs 1,600 quota units again); add session-freshness check before upload |
| Discord message failed silently due to file size | LOW | Add file-size check; regenerate notification with thumbnail image only |
| MoviePy v1/v2 API mismatch | MEDIUM | Pin version, audit all moviepy calls in new post-processing code against pinned version's docs |
| Gradio UI frozen (CUDA/queue issue) | MEDIUM | Restart Gradio process; refactor GPU calls out of event handler into subprocess |
| Config YAML produced wrong video (schema not validated) | HIGH | Add Pydantic validation to config loader; re-run pipeline with corrected config |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| OAuth2 refresh token expiry (Testing mode) | YouTube publishing | Run unattended upload 8+ days after OAuth setup — token must still work |
| YouTube quota exhaustion | YouTube publishing | Separate dev/prod projects confirmed; quota guard function present |
| Gradio CUDA hang with queue=True | Config UI | Click Generate through Gradio UI, GPU runs without hang; progress appears |
| Resumable upload session expiry | YouTube publishing | Simulate a delayed upload (sleep before sending bytes); confirm session-freshness check fires |
| Approval gate blocking main thread | Notifications/approval | Approval gate has a documented timeout; pipeline continues (or aborts cleanly) after timeout |
| Thumbnail upload failing on Shorts | Thumbnail generation | Short vs. long-form detection present; `thumbnails.set` not called for Shorts |
| MoviePy v1/v2 API break | Post-processing | `moviepy` version pinned in requirements.txt; no deprecated v1 method calls in new code |
| Discord 25 MB attachment limit | Notifications/approval | File-size guard present; notification test with >25 MB file sends thumbnail-only fallback |
| Gradio version conflict with AnimateDiff | Config UI | `AnimateDiff/requirements.txt` Gradio version audited before writing any UI code |
| Config YAML missing field validation | Config UI | Pydantic schema defined; loading a config with a missing required field raises immediately |
| OAuth credentials committed to git | YouTube publishing | `client_secret*.json` and `token.json` in `.gitignore`; `git log --all -- token.json` returns nothing |
| Subtitle/font path failure on Windows | Post-processing | Text overlay renders with correct font on Windows target machine, not fallback default font |

---

## Sources

- [YouTube Data API v3 — Resumable Uploads](https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol) — HIGH confidence (official docs)
- [YouTube Data API v3 — Videos: insert](https://developers.google.com/youtube/v3/docs/videos/insert) — HIGH confidence (official docs)
- [YouTube Data API v3 — Errors reference](https://developers.google.com/youtube/v3/docs/errors) — HIGH confidence (official docs)
- [YouTube Data API v3 — OAuth 2.0 authentication](https://developers.google.com/youtube/v3/guides/authentication) — HIGH confidence (official docs)
- [OAuth2 refresh token expiration and YouTube API — Google Developer Forums](https://discuss.google.dev/t/oauth2-refresh-token-expiration-and-youtube-api-v3/160874) — MEDIUM confidence (Google forum, multiple corroborating sources)
- [Napkyn — Why Your YouTube API Refresh Token Keeps Expiring](https://www.napkyn.com/blog/youtube-api-refresh-token-expiring-fix) — MEDIUM confidence (verified against official behavior)
- [Discord webhook rate limits — official Discord docs](https://discord.com/developers/docs/topics/rate-limits) — HIGH confidence (official docs)
- [Discord rate limits — webhooks guide](https://birdie0.github.io/discord-webhooks-guide/other/rate_limits.html) — MEDIUM confidence
- [Gradio — State in Blocks](https://www.gradio.app/guides/state-in-blocks) — HIGH confidence (official docs)
- [Gradio — Running Background Tasks](https://www.gradio.app/guides/running-background-tasks) — HIGH confidence (official docs)
- [Gradio — CUDA hang issue #12492](https://github.com/gradio-app/gradio/issues/12492) — HIGH confidence (maintainer-confirmed GitHub issue)
- [Gradio — UI freeze with generators issue #6609](https://github.com/gradio-app/gradio/issues/6609) — HIGH confidence (GitHub issue)
- [Gradio — GPU memory not released issue #6971](https://github.com/gradio-app/gradio/issues/6971) — HIGH confidence (GitHub issue)
- [Gradio 6 Migration Guide](https://www.gradio.app/main/guides/gradio-6-migration-guide) — HIGH confidence (official docs)
- [google-api-python-client — Media Upload](https://googleapis.github.io/google-api-python-client/docs/media.html) — HIGH confidence (official docs)
- [MoviePy — PyPI](https://pypi.org/project/moviepy/) — HIGH confidence (official)
- [YouTube API quota exceeded — community thread](https://support.google.com/youtube/thread/378827800/can-no-longer-upload-videos-with-youtube-data-api-v3-despite-having-massive-quota) — MEDIUM confidence (community-verified behavior)
- Codebase analysis: `.planning/codebase/CONCERNS.md` — HIGH confidence (direct codebase audit)

---
*Pitfalls research for: content creation automation (YouTube publishing, webhook notifications, config UI, post-processing, thumbnail generation)*
*Researched: 2026-03-28*

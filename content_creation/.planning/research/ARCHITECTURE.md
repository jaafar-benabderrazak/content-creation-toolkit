# Architecture Research

**Domain:** Python video generation pipeline — shared publish/notify/config layer
**Researched:** 2026-03-28
**Confidence:** HIGH (codebase directly inspected, patterns verified against official sources)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Config UI Layer (Gradio)                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Config UI (gradio_app.py) — loads/saves YAML configs        │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
└───────────────────────────┼─────────────────────────────────────────┘
                            │ writes/reads YAML
┌───────────────────────────▼─────────────────────────────────────────┐
│                        Config Layer (config/)                        │
│  ┌─────────────────────┐  ┌────────────────────┐                    │
│  │  PipelineConfig     │  │  ProfileRegistry   │                    │
│  │  (Pydantic model)   │  │  (lofi/tutorial/   │                    │
│  │  YAML ↔ dataclass   │  │   cinematic YAML)  │                    │
│  └──────────┬──────────┘  └────────────────────┘                    │
└─────────────┼───────────────────────────────────────────────────────┘
              │ typed config objects
┌─────────────▼───────────────────────────────────────────────────────┐
│                   Pipeline Layer (existing scripts)                  │
│  ┌───────────────────────────┐  ┌───────────────────────────────┐   │
│  │  study_with_me_generator  │  │  faceless_tiktok_pipeline     │   │
│  │  (unchanged CLI entry)    │  │  (unchanged CLI entry)        │   │
│  └──────────────┬────────────┘  └────────────────┬──────────────┘   │
└─────────────────┼────────────────────────────────┼──────────────────┘
                  │ both call                       │ both call
┌─────────────────▼────────────────────────────────▼──────────────────┐
│                   Shared Services Layer (shared/)                    │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  post_process   │  │  publisher       │  │  notifier        │   │
│  │  (color grade,  │  │  (YouTube API,   │  │  (Discord/Slack  │   │
│  │   watermark,    │  │   thumbnail      │  │   webhooks,      │   │
│  │   intro/outro,  │  │   attach,        │  │   approval gate) │   │
│  │   subtitle burn)│  │   metadata set)  │  │                  │   │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  thumbnail_gen (frame extraction + text overlay + styling)   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `gradio_app.py` | Config UI — expose pipeline params as form fields, load/save YAML | Gradio Blocks with state persistence |
| `config/PipelineConfig` | Typed config model, YAML serialization, validation | Pydantic BaseModel + pydantic-yaml |
| `config/profiles/` | Named preset YAML files (lofi-study, tech-tutorial, cinematic) | Static YAML files, loaded by profile name |
| `shared/post_process.py` | Post-render transforms applied before publish | FFmpeg subprocess + MoviePy |
| `shared/publisher.py` | YouTube upload, OAuth token management, thumbnail attach | google-api-python-client |
| `shared/notifier.py` | Discord/Slack webhook send, approval gate wait | requests + polling loop |
| `shared/thumbnail_gen.py` | Best-frame extraction + text overlay + style | OpenCV or PIL frame read + PIL draw |
| Existing pipeline scripts | Video generation (unchanged) — consume config, return output path | As-is, minimally modified |

## Recommended Project Structure

```
content_creation/
├── study_with_me_generator.py       # unchanged — add shared/ call at end of main()
├── faceless_tech_ai_tik_tok_...py   # unchanged — add shared/ call at end of build_one()
│
├── gradio_app.py                    # NEW — config UI entry point
│
├── config/                          # NEW — typed config layer
│   ├── __init__.py
│   ├── pipeline_config.py           # PipelineConfig Pydantic model
│   └── profiles/                    # Named preset YAML files
│       ├── lofi_study.yaml
│       ├── tech_tutorial.yaml
│       └── cinematic.yaml
│
├── shared/                          # NEW — shared services
│   ├── __init__.py
│   ├── post_process.py              # Color grade, watermark, intro/outro, subtitle burn
│   ├── publisher.py                 # YouTube upload + OAuth token management
│   ├── notifier.py                  # Discord/Slack webhooks + approval gate
│   └── thumbnail_gen.py             # Frame extraction + text overlay
│
├── credentials/                     # NEW — gitignored, OAuth tokens + secrets
│   ├── .gitkeep
│   ├── client_secrets.json          # YouTube OAuth client credentials (user-provided)
│   └── youtube_token.pickle         # Cached OAuth token (auto-generated)
│
├── configs/                         # NEW — user-saved YAML run configs (gitignored)
│   └── .gitkeep
│
├── AnimateDiff/                     # unchanged
└── .planning/
```

### Structure Rationale

- **`shared/`**: Single import target for both pipelines. No circular deps — shared/ imports nothing from the pipeline scripts.
- **`config/`**: Decouples config representation from UI and from pipeline internals. Pydantic gives validation; YAML gives human-editable files.
- **`credentials/`**: Isolates secrets from code. Gitignored. `client_secrets.json` is the only file the user manually places here.
- **`configs/`**: Run-specific YAML files saved by the Gradio UI. User can version-control or share these independently.
- **`gradio_app.py` at root**: Consistent with existing pattern — all entry points are at root level (study_with_me_generator.py, etc.).

## Architectural Patterns

### Pattern 1: Post-Pipeline Hook (Thin Injection at main() Tail)

**What:** The existing `main()` functions in each pipeline script return the rendered MP4 path. Add a single call to `shared.run_post_pipeline(output_path, config)` at the tail of each `main()`, after the existing render succeeds. The shared layer takes over from that point.

**When to use:** Adding cross-cutting behavior (publish, notify) to existing scripts without refactoring their internals.

**Trade-offs:** Minimal invasiveness — existing CLI behavior unchanged. No dependency inversion needed. Slight duplication: both `main()` functions get the same tail block, but it's two lines, not a framework.

**Example:**
```python
# At the tail of study_with_me_generator.py main() — after existing render
if args.out.exists():
    from shared.post_process import run_post_process
    from shared.notifier import notify_and_gate
    from shared.publisher import publish_to_youtube

    processed_path = run_post_process(args.out, pipeline_config)
    approved = notify_and_gate(processed_path, pipeline_config)
    if approved and pipeline_config.publish.youtube_enabled:
        publish_to_youtube(processed_path, pipeline_config)
```

### Pattern 2: Pydantic Config as the Single Config Contract

**What:** Define `PipelineConfig` as a Pydantic BaseModel with nested sub-configs (`VideoSettings`, `PublishSettings`, `NotifySettings`). Both the Gradio UI and the CLI read/write this same model. YAML is the serialization format.

**When to use:** When config is shared across UI, CLI, and multiple scripts. Pydantic gives free validation, type coercion, and `.model_dump()` / `.model_validate()` for round-tripping with YAML.

**Trade-offs:** Adds pydantic as a hard dependency (already present via Gradio/diffusers transitively). Migration from existing dataclasses is a copy operation — the existing `VideoConfig`, `AudioConfig`, `EffectsConfig` dataclasses map 1:1 to Pydantic nested models.

**Example:**
```python
# config/pipeline_config.py
from pydantic import BaseModel, Field
from typing import Optional

class VideoSettings(BaseModel):
    duration_minutes: int = 120
    quality_preset: str = "high"
    resolution: str = "1080p"
    style_prompt: str = "cinematic, professional photography, warm lighting"

class PublishSettings(BaseModel):
    youtube_enabled: bool = False
    youtube_title: str = ""
    youtube_description: str = ""
    youtube_tags: list[str] = Field(default_factory=list)

class NotifySettings(BaseModel):
    discord_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    require_approval: bool = True

class PipelineConfig(BaseModel):
    profile: str = "default"
    video: VideoSettings = Field(default_factory=VideoSettings)
    publish: PublishSettings = Field(default_factory=PublishSettings)
    notify: NotifySettings = Field(default_factory=NotifySettings)

    @classmethod
    def from_yaml(cls, path) -> "PipelineConfig":
        import yaml
        return cls.model_validate(yaml.safe_load(open(path)))

    def to_yaml(self, path):
        import yaml
        open(path, "w").write(yaml.dump(self.model_dump(), default_flow_style=False))
```

### Pattern 3: Synchronous Approval Gate via Polling

**What:** `notifier.notify_and_gate()` sends a preview notification (Discord/Slack embed with video filename, thumbnail, duration) then polls a file-based or environment flag for approval. For v1, the simplest gate is: send notification with instructions ("reply `approve` in this channel or create `{work_dir}/approved` file"), then poll for the file's existence with a timeout.

**When to use:** When you need human-in-the-loop before publish but don't want to run a persistent bot process.

**Trade-offs:** File-based polling is simple and requires zero infrastructure beyond webhooks. The downside is manual — user must create a file or type a command to approve. This is acceptable for v1 where the operator is the same person running the script.

**Example:**
```python
# shared/notifier.py
import time, requests
from pathlib import Path

def notify_and_gate(video_path: Path, config) -> bool:
    _send_discord(video_path, config.notify.discord_webhook_url)
    _send_slack(video_path, config.notify.slack_webhook_url)

    if not config.notify.require_approval:
        return True

    gate_file = video_path.parent / f"{video_path.stem}.approved"
    print(f"[Notify] Waiting for approval. Create '{gate_file}' to proceed, or Ctrl+C to abort.")
    timeout = 3600  # 1 hour
    for _ in range(timeout):
        if gate_file.exists():
            gate_file.unlink()
            return True
        time.sleep(1)
    print("[Notify] Approval timeout — skipping publish.")
    return False
```

## Data Flow

### Full Pipeline Run (with shared layer)

```
User → CLI args or Gradio UI
    ↓
PipelineConfig loaded from YAML profile or UI fields
    ↓
Existing pipeline main() executes (unchanged internals)
    → generates MP4 at output_path
    ↓
shared/post_process.py
    → applies color grade, watermark, intro/outro (FFmpeg)
    → burns subtitles if SRT exists alongside video
    → writes processed MP4 (replaces or suffixes original)
    ↓
shared/thumbnail_gen.py
    → extracts best frame via OpenCV (highest sharpness score)
    → draws title text overlay with PIL
    → writes thumbnail PNG
    ↓
shared/notifier.py — notify_and_gate()
    → sends Discord embed (video name, duration, thumbnail)
    → sends Slack message
    → polls for gate_file OR skips gate if require_approval=False
    ↓ (if approved or no gate)
shared/publisher.py — publish_to_youtube()
    → loads OAuth token from credentials/youtube_token.pickle
    → if token missing/expired: opens browser for consent flow, saves new token
    → calls videos.insert (resumable upload, chunks)
    → calls thumbnails.set with thumbnail PNG
    → prints YouTube URL
    ↓
Done
```

### Config Round-Trip (Gradio UI)

```
User opens Gradio (python gradio_app.py)
    ↓
Gradio loads config/profiles/lofi_study.yaml → PipelineConfig
    ↓
UI fields populate from model fields
    ↓
User edits fields → clicks Save
    ↓
PipelineConfig.to_yaml(configs/my_run.yaml)
    ↓
User clicks "Run Study Video"
    ↓
Gradio calls: subprocess.run(["python", "study_with_me_generator.py",
    "--config", "configs/my_run.yaml", "--out", output_path])
    ↓
Pipeline reads config, generates video, calls shared layer
```

### Key Data Flows

1. **Config flows down only:** `PipelineConfig` is constructed once (from YAML or UI), passed into shared functions, never mutated. Pipeline scripts receive it as read-only input.
2. **Output path flows up:** Existing scripts produce `output_path` (Path). Shared layer receives this path. No shared mutable state.
3. **Credentials are external:** OAuth token stored in `credentials/youtube_token.pickle`. Shared publisher loads it. Gradio UI never touches credentials directly.
4. **Approval gate is side-channel:** File-based gate (`{stem}.approved`) allows out-of-process human approval without piping stdin or running a bot.

## Integration Points

### External Services

| Service | Integration Pattern | Auth | Quota / Limits | Notes |
|---------|---------------------|------|----------------|-------|
| YouTube Data API v3 | `google-api-python-client` + resumable upload | OAuth 2.0 installed-app flow, token cached in `.pickle` | 1,600 units per `videos.insert`; 10,000 units/day default; ~6 uploads/day | Requires OAuth consent screen setup in Google Cloud Console; no service account support |
| Discord webhook | HTTP POST to webhook URL (no bot needed) | Webhook URL in config (secret) | Rate limit: 30 requests/minute per webhook | POST JSON payload with embeds; thumbnail as URL or file attachment |
| Slack webhook | HTTP POST to incoming webhook URL | Webhook URL in config (secret) | Standard Slack rate limits | `files_upload_v2` for file sharing (legacy `files.upload` deprecated March 2025) |

### Internal Boundaries

| Boundary | Communication | Constraint |
|----------|---------------|------------|
| Pipeline scripts ↔ shared/ | Direct Python import + function call | shared/ must not import from pipeline scripts (one-way dependency only) |
| Gradio UI ↔ Pipeline scripts | subprocess.run() — Gradio launches pipeline as child process | Decoupled: Gradio does not call pipeline functions directly; avoids GPU memory conflicts |
| shared/post_process ↔ FFmpeg | subprocess + ffmpeg-python or direct subprocess call | FFmpeg must be on PATH; Windows path handling required |
| config/ ↔ both pipelines | Import PipelineConfig, call `.from_yaml()` | Config module has no pipeline-specific code |
| credentials/ ↔ publisher | File read at runtime | `.gitignore` credentials/; never hardcode paths |

## Anti-Patterns

### Anti-Pattern 1: Modifying Existing Pipeline Internals

**What people do:** Refactor `build_enhanced_video()` or `build_one()` to accept publish/notify parameters, threading shared concerns into generation logic.

**Why it's wrong:** Breaks existing CLI contracts, creates merge conflicts with future pipeline changes, couples generation to publishing (they should be independent — generation should work fine without network access).

**Do this instead:** Hook at `main()` tail only. Generation functions stay pure (input → output file). Shared layer is called only after successful render.

### Anti-Pattern 2: Single Monolithic Config Dataclass Replacing All Existing Configs

**What people do:** Create one god-config that absorbs `VideoConfig`, `AudioConfig`, `EffectsConfig`, `Style`, `BotCfg`, `RenderCfg` — forcing a full rewrite of both pipelines.

**Why it's wrong:** The existing dataclasses are working and tested (implicitly). Replacing them requires touching every function signature in both 600+ line scripts. High rewrite risk for zero user-visible benefit.

**Do this instead:** Keep existing dataclasses unchanged inside their scripts. `PipelineConfig` is a new, additive config for the shared layer only. It holds `VideoSettings` as a subset (prompt, quality preset, style) and `PublishSettings` / `NotifySettings`. Gradio populates both: existing CLI args from `VideoSettings` fields, shared layer behavior from `PublishSettings` / `NotifySettings`.

### Anti-Pattern 3: Running YouTube OAuth in the Gradio Process

**What people do:** Trigger the OAuth browser consent flow inside the Gradio tab's event handler, expecting it to open a browser and block until authenticated.

**Why it's wrong:** Gradio runs as a local web server. Browser redirects from OAuth flow conflict with the Gradio browser tab. Blocking Gradio's event loop for an interactive OAuth flow causes UI hangs.

**Do this instead:** OAuth setup is a one-time CLI operation: `python shared/publisher.py --setup`. This opens the browser, completes consent, saves `youtube_token.pickle`. Subsequent Gradio-triggered runs load the cached token silently.

### Anti-Pattern 4: Polling Discord for Approval via Bot

**What people do:** Implement a Discord bot that reads messages in a channel to detect "approve" replies, requiring a persistent bot process and bot token.

**Why it's wrong:** v1 doesn't need a persistent process. Bot requires additional OAuth, server permissions, and uptime. Overkill for a single-operator local tool.

**Do this instead:** Webhook for outbound notification (no bot needed). File-based gate for approval. Operator creates a marker file or runs `touch output.approved` from terminal. The generation script is already blocking — polling a file is trivial.

### Anti-Pattern 5: Gradio Directly Invoking GPU Pipeline Functions

**What people do:** Import `study_with_me_generator.main()` and call it from a Gradio button click handler in-process.

**Why it's wrong:** The GPU pipeline loads SDXL into VRAM at startup. If Gradio is already holding GPU memory (AnimateDiff), the second load OOMs. In-process calls also block Gradio's event loop for hours.

**Do this instead:** Gradio launches pipeline as a subprocess (`subprocess.Popen`). Shows a progress log by tailing the subprocess's stdout. GPU memory is isolated per process.

## Scaling Considerations

This is a single-operator local tool. Scaling in the traditional sense is not a concern. What matters is:

| Concern | Current State | With Shared Layer |
|---------|---------------|-------------------|
| Multiple pipeline types | Each script is fully standalone | Both call same shared functions — behavior is consistent |
| Config sprawl | Prompts hardcoded in Python source | YAML profiles in config/profiles/, editble without touching code |
| YouTube quota exhaustion | Not applicable (no YT upload exists) | 1,600 units per upload; at 6 videos/day limit triggers; monitor with quota dashboard |
| OAuth token expiry | Not applicable | Pickle-cached refresh token handles silently; only re-consent if revoked |
| Webhook rate limits | Not applicable | One notification per video render; well within Discord/Slack limits |
| Long approval waits | Not applicable | 1-hour gate timeout is sufficient; configurable |

## Build Order Implications

Dependencies between components determine phase ordering:

```
1. config/ (PipelineConfig, profiles)
       ↓ required by all shared/ modules and Gradio UI
2. shared/post_process.py
       ↓ no external auth; testable independently
3. shared/thumbnail_gen.py
       ↓ no external auth; feeds publisher
4. shared/notifier.py
       ↓ no auth (webhook URLs in config); testable with curl
5. shared/publisher.py
       ↓ requires OAuth setup — most complex external auth
6. gradio_app.py
       ↓ requires all shared/ and config/ to exist
7. Pipeline script integration (hook injection at main() tail)
       final step — lowest risk, just adds 3-4 lines to each script
```

Post-processing and thumbnail should be built before publisher because the publisher calls both (attaches thumbnail, uploads processed file). Notifier can be built in parallel with post-process. Gradio UI is last because it just exposes what's already built.

## Sources

- Codebase direct inspection: `study_with_me_generator.py`, `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` (2026-03-28)
- YouTube Data API v3 upload docs: [developers.google.com/youtube/v3/guides/uploading_a_video](https://developers.google.com/youtube/v3/guides/uploading_a_video) — MEDIUM confidence (official source, WebSearch verified)
- YouTube quota reference: [developers.google.com/youtube/v3/docs/videos/insert](https://developers.google.com/youtube/v3/docs/videos/insert) — HIGH confidence (official docs)
- Discord webhook Python: [github.com/lovvskillz/python-discord-webhook](https://github.com/lovvskillz/python-discord-webhook) — MEDIUM confidence (multiple sources agree)
- Slack file upload v2: [docs.slack.dev/tools/python-slack-sdk/tutorial/uploading-files/](https://docs.slack.dev/tools/python-slack-sdk/tutorial/uploading-files/) — HIGH confidence (official Slack SDK docs; files.upload deprecated March 2025 confirmed)
- Pydantic YAML config: [pydantic-yaml PyPI](https://pypi.org/project/pydantic-yaml/) — MEDIUM confidence (official package, well-supported)
- Pipeline pattern: [startdataengineering.com — Data Pipeline Design Patterns](https://www.startdataengineering.com/post/code-patterns/) — LOW confidence (WebSearch only, but pattern is standard)
- Gradio subprocess isolation: Training data + Gradio docs pattern — MEDIUM confidence

---
*Architecture research for: content_creation unified publish/notify/config layer*
*Researched: 2026-03-28*

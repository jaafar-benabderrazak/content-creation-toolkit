# Architecture Research

**Domain:** AI-powered video generation pipeline — v1.1 AI Generation Quality milestone
**Researched:** 2026-03-28
**Confidence:** HIGH (existing codebase verified; Suno API: MEDIUM — third-party wrapper, no official API)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Config Layer (Pydantic YAML)                     │
│  PipelineConfig → VideoSettings (style_prompt, music_prompt, mood)   │
│  profiles/lofi_study.yaml  cinematic.yaml  tech_tutorial.yaml        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                     AI Generation Layer (NEW v1.1)                   │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐ │
│  │   generators/sdxl.py         │  │   generators/suno.py         │ │
│  │   SDXLGenerator              │  │   SunoClient                 │ │
│  │   - build_prompt(scene,prof) │  │   - generate(prompt,genre,   │ │
│  │   - generate_batch(scenes)   │  │     duration_s, instrumental)│ │
│  │   - cache_lookup/store       │  │   - poll_until_ready(task_id)│ │
│  └──────────────┬───────────────┘  │   - download(url) → Path    │ │
│                 │                  └───────────────┬──────────────┘ │
└─────────────────┼──────────────────────────────────┼───────────────┘
                  │                                  │
┌─────────────────▼──────────────────────────────────▼───────────────┐
│                  Existing Pipeline (study_with_me_generator.py)      │
│  generate_images_enhanced_sd()  →  [image paths]                    │
│  generate_enhanced_music()      →  [audio path]   ← replaced        │
│  build_enhanced_video()         →  Remotion renderer                │
└─────────────────────────────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                  Shared Post-process/Publish Layer                   │
│  pipeline_runner.py → post_process → thumbnail → notify → publish   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `config/pipeline_config.py` | PipelineConfig + VideoSettings schema; YAML load/dump | All generators via profile fields |
| `generators/sdxl.py` (new) | SDXL prompt assembly from templates + scene data; batched image generation with caching | `study_with_me_generator.py` |
| `generators/suno.py` (new) | Suno API HTTP client; async polling; instrumental enforcement; WAV download | `study_with_me_generator.py` |
| `study_with_me_generator.py` | Main orchestrator; calls generators; hands paths to Remotion | `generators/`, `shared/remotion_renderer.py` |
| `shared/remotion_renderer.py` | Subprocess call to `npx remotion render`; props serialization | Output only |
| `shared/pipeline_runner.py` | Post-process → thumbnail → notify → publish chain | `shared/*`, YouTube API |

## Recommended Project Structure

```
content_creation/
├── config/
│   ├── pipeline_config.py       # PipelineConfig — add SDXLSettings, SunoSettings
│   └── profiles/
│       ├── lofi_study.yaml      # add: sdxl.*, suno.*
│       ├── cinematic.yaml
│       └── tech_tutorial.yaml
├── generators/                  # NEW — extracted AI generation modules
│   ├── __init__.py
│   ├── sdxl.py                  # SDXLGenerator with prompt templates
│   └── suno.py                  # SunoClient with polling + download
├── shared/
│   ├── remotion_renderer.py     # existing — no changes needed
│   ├── pipeline_runner.py       # existing — no changes needed
│   └── ...
└── study_with_me_generator.py   # refactored: delegates to generators/
```

### Structure Rationale

- **generators/**: Separates API clients from pipeline orchestration. Both pipelines (study, TikTok) can import from here without duplication. Easy to mock in future tests.
- **config/pipeline_config.py**: Central config extension point. New `SDXLSettings` and `SunoSettings` sub-models are added here rather than scattered in generator scripts.

## Architectural Patterns

### Pattern 1: Config-Driven Prompt Templates

**What:** Profile YAML files carry prompt template strings that SDXLGenerator interpolates with scene-specific variables at generation time. No hardcoded prompts in Python source.

**When to use:** Required for all SDXL calls. Enables per-profile aesthetic control (lofi warmth vs. cinematic cool) without code changes.

**Trade-offs:** YAML editing is the user-facing prompt interface; reduces flexibility for one-off experiments, but that is intentional.

**Example:**
```python
# config/pipeline_config.py additions
class SDXLSettings(BaseModel):
    base_style_suffix: str = "high resolution, professional photography, 8K"
    negative_prompt: str = "blurry, watermark, text, logo, deformed, low quality"
    steps_high: int = 35
    steps_medium: int = 25
    steps_fast: int = 15
    guidance_scale: float = 7.5
    enable_refiner: bool = False   # SDXL refiner pass (quality vs. speed)

class SunoSettings(BaseModel):
    genre: str = "lofi"            # lofi | cinematic | electronic | ambient
    make_instrumental: bool = True
    model_version: str = "chirp-v3"
    track_count: int = 2           # generate N tracks, use longest/best

# VideoSettings gets new fields:
# sdxl: SDXLSettings = Field(default_factory=SDXLSettings)
# suno: SunoSettings = Field(default_factory=SunoSettings)
```

```python
# generators/sdxl.py — prompt assembly
class SDXLGenerator:
    def build_prompt(self, scene: dict, profile_style: str, sdxl_cfg: SDXLSettings) -> str:
        base = scene["prompt"]
        style_var = random.choice(STYLE_VARIATIONS)
        weather = random.choice(WEATHER_EFFECTS) if scene["environment"] == "indoor" else ""
        suffix = sdxl_cfg.base_style_suffix
        return f"{base}, {profile_style}, {style_var}, {weather}, {suffix}".strip(", ")
```

### Pattern 2: Async-Poll Client for Suno

**What:** `SunoClient.generate()` submits a task and returns a `task_id`. A separate `poll_until_ready()` method retries with exponential backoff until `audio_url` is populated. `download()` fetches the WAV and caches it locally.

**When to use:** Required. Suno generation takes 30s–3 min. Blocking HTTP is not viable at scale; polling avoids thread starvation.

**Trade-offs:** Adds wall-clock latency (minimum ~60s for full-length track). Parallelizing image generation and music polling hides most of this latency.

**Example:**
```python
# generators/suno.py
import time, requests, logging
from pathlib import Path

logger = logging.getLogger(__name__)

GENERATE_URL = "https://api.sunoapi.org/api/v1/generate"
QUERY_URL    = "https://api.sunoapi.org/api/v1/query"

class SunoClient:
    def __init__(self, api_key: str):
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def generate(self, prompt: str, duration_seconds: int,
                 genre: str, make_instrumental: bool = True,
                 model_version: str = "chirp-v3") -> str:
        """Submit generation task. Returns task_id."""
        payload = {
            "prompt": f"{genre}, {prompt}",
            "make_instrumental": make_instrumental,
            "mv": model_version,
            "duration": duration_seconds,
            "wait_audio": False,
        }
        r = requests.post(GENERATE_URL, json=payload, headers=self.headers, timeout=30)
        r.raise_for_status()
        return r.json()["task_id"]

    def poll_until_ready(self, task_id: str,
                         timeout: int = 300, interval: int = 10) -> list[dict]:
        """Poll until complete. Returns list of track dicts with audio_url."""
        deadline = time.time() + timeout
        backoff = interval
        while time.time() < deadline:
            time.sleep(backoff)
            r = requests.get(f"{QUERY_URL}?task_id={task_id}",
                             headers=self.headers, timeout=15)
            data = r.json()
            if data.get("status") == "complete":
                return data["data"]
            if data.get("status") == "error":
                raise RuntimeError(f"Suno generation failed: {data}")
            backoff = min(backoff * 1.5, 30)
        raise TimeoutError(f"Suno task {task_id} not ready in {timeout}s")

    def download(self, audio_url: str, dest: Path) -> Path:
        """Download audio to dest path. Returns path."""
        r = requests.get(audio_url, timeout=120, stream=True)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        return dest
```

### Pattern 3: Image Generation Cache (Hash-Based Skip)

**What:** Before calling SDXL, compute a cache key from `(scene_prompt + profile_style + sdxl_cfg_hash)`. If a matching image exists in the work directory, skip generation. Only regenerate when prompts or config change.

**When to use:** Required for iteration speed. SDXL at high quality = ~45s/image on a 4090. 24 scenes = 18 min. Caching reduces re-runs to seconds when only downstream config changes.

**Trade-offs:** Cache invalidation is coarse (full re-gen if any prompt changes). Acceptable for v1.1.

**Example:**
```python
# generators/sdxl.py
import hashlib, json

def _cache_key(scene: dict, style: str, cfg: SDXLSettings) -> str:
    payload = {"scene": scene["prompt"], "style": style,
               "neg": cfg.negative_prompt, "steps": cfg.steps_high}
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]

def generate_batch(self, scenes, profile_style, sdxl_cfg, out_dir, force=False):
    paths = []
    for i, scene in enumerate(scenes):
        key = _cache_key(scene, profile_style, sdxl_cfg)
        cached = out_dir / f"scene_{i:03d}_{key}.png"
        if cached.exists() and not force:
            logger.info(f"[SDXL] Cache hit: scene {i}")
            paths.append(cached)
            continue
        img = self._generate_one(scene, profile_style, sdxl_cfg)
        img.save(cached)
        paths.append(cached)
    return paths
```

## Data Flow

### v1.1 Generation Flow (study_with_me_generator.py)

```
CLI --config profiles/lofi_study.yaml
    │
    ▼
PipelineConfig.from_yaml()
    │
    ├─► SDXLGenerator.generate_batch(scenes, config.video.style_prompt, config.video.sdxl)
    │       ├─ cache_lookup → hit → reuse
    │       └─ miss → pipe(full_prompt, negative_prompt, steps) → save PNG → progress.json
    │
    ├─► SunoClient.generate(config.video.music_prompt, duration_s, config.video.suno.genre)
    │       └─ returns task_id  ← happens in parallel with image generation if threaded
    │
    ├─► SunoClient.poll_until_ready(task_id) → [track_dicts]
    │       └─ select track (longest / first)
    │
    ├─► SunoClient.download(audio_url) → audio.mp3
    │       └─ _ensure_wav(audio.mp3) → audio.wav  (remotion_renderer handles this)
    │
    └─► remotion_renderer.render_study_video(images, audio_path, output_path, ...)
            └─ npx remotion render StudyVideo → output.mp4
```

### Config Extension Data Flow

```
VideoSettings (existing)
    + SDXLSettings (new)       ← consumed by generators/sdxl.py
    + SunoSettings (new)       ← consumed by generators/suno.py

Profile YAML:
  video:
    style_prompt: "..."         ← passed to SDXLGenerator.build_prompt()
    music_prompt: "..."         ← passed to SunoClient.generate()
    sdxl:
      negative_prompt: "..."
      steps_high: 35
      enable_refiner: false
    suno:
      genre: lofi
      make_instrumental: true
      track_count: 2
```

### Parallelism Opportunity

Image generation (CPU-GPU bound) and Suno polling (network-bound, 60–180s wait) are independent. Submit the Suno task immediately after config load, then run SDXL batch. By the time SDXL finishes, Suno is likely ready. This hides Suno's latency behind SDXL's.

```
t=0    Submit Suno task (returns task_id in ~1s)
t=0    Start SDXL batch (24 images × ~45s = ~18 min)
t=90s  Suno ready (poll succeeds, download audio)
t=18m  SDXL done → render immediately, audio already waiting
```

Implementation: use `concurrent.futures.ThreadPoolExecutor` to run Suno polling in a background thread while SDXL runs in main thread.

## Anti-Patterns

### Anti-Pattern 1: Inlining API Clients in the Generator Script

**What people do:** Add `import requests; requests.post("https://api.suno...")` directly inside `study_with_me_generator.py`, alongside the existing SDXL code.

**Why it's wrong:** The generator is already 700+ lines. Inlining Suno logic creates a 1000+ line monolith. The TikTok pipeline also needs music — duplication becomes inevitable. API keys, retry logic, and download paths scatter across scripts.

**Do this instead:** `generators/suno.py` as a standalone client. The pipeline script imports and calls it. The TikTok pipeline can import the same client when needed.

### Anti-Pattern 2: Blocking on Suno Poll in Main Thread

**What people do:** Submit task, `time.sleep(120)`, fetch result.

**Why it's wrong:** Fixed sleep of 120s wastes 60–90s on every run when Suno finishes early. Fixed sleep of 60s causes failures when Suno takes longer (network congestion, server load).

**Do this instead:** Exponential backoff polling with a configurable timeout (default 300s). Start the task before SDXL so the wait is mostly hidden.

### Anti-Pattern 3: Storing Suno API Key in YAML Profiles

**What people do:** Add `suno_api_key: sk-abc123` to `lofi_study.yaml` alongside other config.

**Why it's wrong:** Profile YAMLs are likely committed to git. API key exposure.

**Do this instead:** Read from environment variable (`SUNO_API_KEY`). `SunoSettings` in config holds non-secret parameters only. `SunoClient.__init__` reads `os.environ["SUNO_API_KEY"]` or raises a clear error.

### Anti-Pattern 4: Profile-Independent Negative Prompts

**What people do:** Hardcode a single negative prompt string in `generate_images_enhanced_sd()` that applies to all profiles.

**Why it's wrong:** The lofi profile needs to suppress corporate/clinical aesthetics; the cinematic profile needs to suppress cartoon/anime styles. Same negative prompt degrades quality for at least one profile.

**Do this instead:** `SDXLSettings.negative_prompt` in each profile YAML. The lofi YAML has its own negative prompt, the cinematic YAML has its own.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Suno API (third-party wrapper) | REST POST to generate, GET to poll, HTTP download | No official Suno API. Use `sunoapi.org` or `kie.ai` wrappers. `make_instrumental: true` enforces no vocals. Key in `SUNO_API_KEY` env var. Generation returns 2 tracks; use first complete one. |
| SDXL (local diffusers) | Already integrated in `study_with_me_generator.py` | Refactor into `generators/sdxl.py`. No new dependencies. Hash-based cache added around the existing `pipe()` call. |
| Remotion | Already integrated in `shared/remotion_renderer.py` | No changes needed for v1.1. Audio path passed as-is; `_ensure_wav()` already handles MP3→WAV conversion. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `config/` → `generators/` | `SDXLSettings`, `SunoSettings` passed as typed dataclass args | Generators must not import `PipelineConfig` directly — receive only their settings sub-model |
| `generators/` → `study_with_me_generator.py` | Returns `list[Path]` (images), `Path` (audio) | Generator output contracts must not change — Remotion renderer depends on these |
| `generators/suno.py` → filesystem | Downloads to `{work_dir}/audio/suno_track_{n}.mp3` | Consistent with existing `{work_dir}/audio/` convention in progress.json |
| `study_with_me_generator.py` → `progress.json` | Extend existing schema with `suno_generation` and `image_cache` keys | Preserves resumability — if Suno download complete, skip on re-run |

## Suggested Build Order

1. **Extend `PipelineConfig`** — add `SDXLSettings` and `SunoSettings` sub-models; update all three profile YAMLs. This is prerequisite for everything else and has zero runtime impact until generators use it.

2. **`generators/sdxl.py`** — extract existing SDXL code from `study_with_me_generator.py` into `SDXLGenerator`; add `build_prompt()` template method; add hash-based cache. Replace the inline SDXL block in the study generator with `SDXLGenerator` calls. Verifiable: images should be identical to pre-refactor.

3. **`generators/suno.py`** — implement `SunoClient` with submit/poll/download. Test with a standalone script against a real Suno wrapper API key before wiring into the pipeline. Verify `make_instrumental: true` works and output is WAV-compatible.

4. **Wire Suno into `study_with_me_generator.py`** — replace `generate_enhanced_music()` (Stable Audio) with `SunoClient` call. Thread the Suno submit before SDXL loop for latency hiding. Add `suno_generation` key to `progress.json`.

5. **Update profile YAMLs** — add `sdxl` and `suno` sections per profile with tuned values (lofi: warm/analog genre; cinematic: orchestral/epic genre; tech-tutorial: electronic/minimal genre).

## Sources

- Existing codebase: `study_with_me_generator.py`, `shared/remotion_renderer.py`, `shared/pipeline_runner.py`, `config/pipeline_config.py` — verified 2026-03-28
- Suno API wrapper pattern: https://docs.sunoapi.org/suno-api/generate-music (MEDIUM confidence — third-party, not official Suno)
- `make_instrumental` parameter: https://docs.kie.ai/suno-api/generate-music (MEDIUM confidence — corroborated across multiple third-party wrappers)
- SDXL negative prompt best practices: https://neurocanvas.net/blog/sdxl-best-practices-guide/ (MEDIUM confidence — community knowledge, consistent with Layer.ai docs)
- SDXL prompt style (natural language over tags): https://blog.segmind.com/prompt-guide-for-stable-diffusion-xl-crafting-textual-descriptions-for-image-generation/ (MEDIUM confidence)

---
*Architecture research for: Content Creation Toolkit v1.1 — AI Generation Quality milestone*
*Researched: 2026-03-28*

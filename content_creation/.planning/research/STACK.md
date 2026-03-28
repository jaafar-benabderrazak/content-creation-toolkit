# Stack Research

**Domain:** AI content generation — music integration and image quality enhancement
**Researched:** 2026-03-28
**Confidence:** MEDIUM (Suno API official status uncertain; SDXL/caching findings HIGH)

## Context: What Changes in This Milestone

This is a stack delta document. The existing stack (PyTorch, diffusers, MoviePy, pydub, Remotion, Pydantic, OpenAI, ElevenLabs) is validated and unchanged. This documents only NET NEW additions or version changes needed for:

1. Suno API music generation (replacing Stable Audio)
2. SDXL prompt engineering via compel
3. Smart image batching and caching via diskcache
4. Quality preset system affecting generation params

---

## Recommended Stack — New Additions

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `requests` | stdlib or `>=2.31` | HTTP client for Suno API REST calls | Already likely present; handles Bearer auth, POST/GET, JSON; no SDK needed for a simple polling loop |
| `compel` | `>=2.0.2` | SDXL prompt weighting and blending | Only library that exposes `CompelForSDXL` with pooled embedding support; integrates directly with `diffusers` pipeline; syntax `word++` / `word--` is minimal overhead |
| `diskcache` | `>=5.6.3` | Persistent disk-backed cache for generated images | Pure-Python, SQLite-backed, faster than Redis for local use; AUTOMATIC1111 webui uses it for the same purpose; hash-keyed entries survive process restarts |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `hashlib` | stdlib | Generate deterministic SHA-256 cache keys from prompt + params | Every image generation call; `sha256(prompt + seed + steps + size).hexdigest()` as cache key |
| `python-dotenv` | `>=1.0.0` | Load `SUNO_API_KEY` and other new env vars from `.env` | Already a best practice; ensures `SUNO_API_KEY` is never hardcoded |
| `tenacity` | `>=8.2.3` | Retry decorator for Suno API polling and flaky network calls | Suno generation is async/polling; wrap status-check loop with exponential backoff |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `pytest` | Unit tests for prompt template rendering and cache hit/miss logic | Add tests for `PromptTemplate.render()` and `ImageCache.get()/set()` during this milestone |

---

## Installation

```bash
# New dependencies for this milestone
pip install compel>=2.0.2 diskcache>=5.6.3 tenacity>=8.2.3

# Already present but verify version
pip install requests>=2.31

# Optional: load .env in local dev
pip install python-dotenv>=1.0.0
```

---

## Suno API Integration Details

### Official API Status — IMPORTANT

**Suno.ai does not ship a public official API as of March 2026.** Multiple third-party providers (`sunoapi.org`, `kie.ai`, `aimlapi.com`) offer REST wrappers around Suno's web platform. The landscape:

| Provider | Type | API Base URL | Notes |
|----------|------|-------------|-------|
| sunoapi.org | Third-party wrapper | `https://api.sunoapi.org` | Most documented, used by AUTOMATIC1111 community |
| kie.ai | Third-party aggregator | `https://api.kie.ai` | Supports Suno V5, V4.5; straightforward auth |
| aimlapi.com | Third-party aggregator | `https://api.aimlapi.com` | Multi-model platform, includes Suno |
| gcui-art/suno-api (GitHub) | Self-hosted reverse-proxy | Self-hosted | Requires cookie-based session pool; operational risk |

**Recommendation:** Use `sunoapi.org` or `kie.ai` — standard Bearer token auth, documented REST endpoints, lower operational risk than self-hosting a cookie-pool proxy. Validate pricing before committing.

**Confidence:** MEDIUM — No official Suno docs available; based on multiple third-party sources that agree on the API surface.

### Authentication Pattern

```python
import os
import requests

SUNO_API_KEY = os.environ["SUNO_API_KEY"]
SUNO_BASE_URL = "https://api.sunoapi.org"  # or kie.ai equivalent

headers = {
    "Authorization": f"Bearer {SUNO_API_KEY}",
    "Content-Type": "application/json",
}
```

### Generation Request Pattern (Async Polling)

Music generation is asynchronous. The pattern across all third-party providers is identical:

1. POST `/api/v1/generate` (or `/api/custom_generate`) → returns `task_id`
2. Poll GET `/api/v1/task/{task_id}` every 2–5 seconds until `status == "completed"`
3. Extract `audio_url` from completed response and download

```python
# Minimal example — actual field names vary by provider, verify against docs
payload = {
    "prompt": "lo-fi hip hop, ambient, calm, study music",
    "make_instrumental": True,    # enforces no vocals
    "duration": 120,              # seconds — match video length
    "mv": "chirp-v5",             # model version
}

response = requests.post(f"{SUNO_BASE_URL}/api/v1/generate", headers=headers, json=payload)
task_id = response.json()["task_id"]

# Polling loop (use tenacity for production retry)
import time
while True:
    status_resp = requests.get(f"{SUNO_BASE_URL}/api/v1/task/{task_id}", headers=headers)
    data = status_resp.json()
    if data["status"] == "completed":
        audio_url = data["audio_url"]
        break
    time.sleep(3)
```

**Critical parameters:**
- `make_instrumental: True` — mandatory; prevents vocal generation
- `duration` — in seconds; pass exact video length to avoid mismatch
- `prompt` includes style tags: `"lofi, ambient, no vocals, study, calm"`

### Genre/Profile Mapping

Map existing video profiles to Suno prompt genre tags:

| Profile | Recommended Suno Prompt Style Tags |
|---------|-----------------------------------|
| study_lofi | `"lofi hip hop, ambient, calm, 80bpm, piano, vinyl"` |
| cinematic | `"cinematic orchestral, epic, atmospheric, no vocals"` |
| electronic | `"electronic, synthwave, upbeat, energetic, no vocals"` |
| nature_ambient | `"ambient, nature sounds, peaceful, meditation, no vocals"` |

---

## SDXL Prompt Engineering Details

### compel — Prompt Weighting for SDXL

`CompelForSDXL` is the correct class (not the base `Compel`). It handles SDXL's dual-encoder architecture (two CLIP text encoders) and produces both `prompt_embeds` and `pooled_prompt_embeds` required by `StableDiffusionXLPipeline`.

```python
from compel import Compel, ReturnedEmbeddingsType
from diffusers import StableDiffusionXLPipeline

pipeline = StableDiffusionXLPipeline.from_pretrained(...)

compel = Compel(
    tokenizer=[pipeline.tokenizer, pipeline.tokenizer_2],
    text_encoder=[pipeline.text_encoder, pipeline.text_encoder_2],
    returned_embeddings_type=ReturnedEmbeddingsType.PENULTIMATE_HIDDEN_STATES_NON_NORMALIZED,
    requires_pooled=[False, True],
)

# Weight syntax: word++ raises weight, word-- lowers weight
prompt = "cozy lofi study room, warm lighting++, bookshelf, plants, golden hour, photorealistic++"
negative = "blurry, watermark, text, signature, low quality"

conditioning, pooled = compel(prompt)
negative_conditioning, negative_pooled = compel(negative)
```

Pass to pipeline:
```python
image = pipeline(
    prompt_embeds=conditioning,
    pooled_prompt_embeds=pooled,
    negative_prompt_embeds=negative_conditioning,
    negative_pooled_prompt_embeds=negative_pooled,
    num_inference_steps=35,
    guidance_scale=8.0,
).images[0]
```

### SDXL Negative Prompt Strategy

SDXL requires shorter, focused negative prompts (not SD 1.5 mega-lists). Standard effective negative prompt for this project:

```python
NEGATIVE_PROMPTS = {
    "default": "blurry, watermark, text overlay, signature, low quality, artifacts, distorted",
    "study_scene": "blurry, text, watermark, people, faces, distorted, cartoon, anime",
    "nature": "blurry, watermark, text, people, urban, city, distorted",
    "tech_tutorial": "blurry, watermark, text, signature, low quality, artifacts",
}
```

**Key finding:** Avoid pasting SD 1.5 negative lists into SDXL — counterproductive. SDXL handles anatomy/hands natively; negatives should target style deviations only. (MEDIUM confidence — multiple sources agree, verified against Layer.ai and Segmind docs.)

### Profile-Specific Prompt Templates

Store prompt templates in Pydantic config (already validated in v1.0), not hardcoded in Python source. Structure:

```python
class ScenePromptTemplate(BaseModel):
    base_prompt: str        # "{subject}, {style}, {lighting}, {quality_suffix}"
    negative_prompt: str    # profile-specific negative
    quality_suffixes: dict  # {"low": "...", "medium": "...", "high": "masterpiece, 8k, photorealistic"}
```

---

## Image Caching Details

### diskcache — Disk-Backed Persistent Cache

Cache key = SHA-256 of all generation-determining inputs: prompt + negative_prompt + seed + steps + guidance_scale + width + height.

```python
import diskcache
import hashlib
import json

cache = diskcache.Cache("./cache/images", size_limit=10 * 1024**3)  # 10 GB limit

def make_cache_key(prompt: str, negative: str, seed: int, steps: int,
                    guidance: float, width: int, height: int) -> str:
    params = json.dumps({
        "prompt": prompt, "negative": negative, "seed": seed,
        "steps": steps, "guidance": guidance, "width": width, "height": height
    }, sort_keys=True)
    return hashlib.sha256(params.encode()).hexdigest()

def get_or_generate_image(pipeline, params: dict) -> Image:
    key = make_cache_key(**params)
    if key in cache:
        return cache[key]  # PIL Image stored via pickle
    image = pipeline(**params).images[0]
    cache[key] = image
    return image
```

**Invalidation strategy:** Cache entries survive process restarts (SQLite-backed). Clear manually or set `size_limit`. Never auto-expire on content changes — the hash key handles invalidation implicitly (changed prompt = different hash = cache miss).

---

## Quality Presets — Generation Parameter Mapping

| Preset | SDXL Steps | Guidance Scale | Resolution | Suno Model | Music Duration |
|--------|-----------|----------------|------------|------------|----------------|
| `low` | 15 | 7.0 | 768x768 | `chirp-v4` | exact |
| `medium` | 25 | 7.5 | 1024x1024 | `chirp-v4.5` | exact |
| `high` | 35 | 8.0 | 1024x1024 | `chirp-v5` | exact |

These extend the existing quality preset system in `INTEGRATIONS.md` (lines 133–135 show steps 35/25/15 and guidance 8.0/7.5/7.0 are already partially implemented).

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `sunoapi.org` / `kie.ai` (third-party Suno wrapper) | `gcui-art/suno-api` (self-hosted) | Only if you need cost control and are willing to maintain a cookie-pool server; fragile, breaks when Suno updates auth |
| `compel` for prompt weighting | `diffusers` native `StableDiffusionXLPipeline(prompt=...)` | If you never need weighted prompts; baseline quality is acceptable without weighting |
| `diskcache` for image cache | `joblib.Memory` | joblib is better for numpy-heavy data science workflows; diskcache is better for PIL Images and has simpler size limits |
| Third-party Suno API | `stable-audio-tools` (existing) | If Suno pricing is prohibitive or API reliability is insufficient; Stable Audio is already integrated and free |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `gcui-art/suno-api` self-hosted | Requires cookie pool maintenance; breaks on Suno session invalidation; operational burden for a single-creator tool | Hosted third-party provider (sunoapi.org or kie.ai) |
| SD 1.5 negative prompt mega-lists with SDXL | Counterproductive — SDXL handles anatomy natively; long negative lists degrade generation quality | Short, style-focused negative prompts (5–8 terms max) |
| `Malith-Rukshan/Suno-API` (PyPI `SunoAI`) | Cookie-session based; no official support; high breakage risk | REST-based third-party provider |
| Hardcoded prompt strings in Python source | Already identified as pain point in PROJECT.md; blocks profile-based customization | Pydantic `ScenePromptTemplate` in YAML config |

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `compel>=2.0.2` | `diffusers>=0.26.3` | `CompelForSDXL` requires diffusers `StableDiffusionXLPipeline`; existing codebase uses 0.26.3 — compatible |
| `diskcache>=5.6.3` | Python 3.10+, any PyTorch version | No conflicts; pure-Python |
| `tenacity>=8.2.3` | Any Python 3.10+ | No conflicts |
| `compel` | `transformers>=4.25.1` | Uses CLIP tokenizers from transformers; existing version is compatible |

---

## Open Questions / Validation Required

1. **Suno API provider selection:** `sunoapi.org` vs `kie.ai` — verify current pricing tiers and `make_instrumental` + `duration` parameter support before committing. Field names may differ slightly between providers.
2. **Suno API official release:** Suno has indicated a first-party API is in development. Check `suno.ai/developers` before milestone start — if released, prefer it over third-party wrappers.
3. **diskcache PIL Image serialization:** Confirm PIL Image objects pickle correctly with diskcache (expected: yes, but test with SDXL 1024x1024 output size).
4. **compel version pinning:** `compel` PyPI last confirmed active version needs verification against the project's current `diffusers` version at milestone start.

---

## Sources

- [sunoapi.org documentation](https://docs.sunoapi.org/suno-api/quickstart) — Suno API quickstart, Bearer auth pattern (MEDIUM confidence — third-party)
- [aimlapi.com Suno API Reality article](https://aimlapi.com/blog/the-suno-api-reality) — Official API status, provider landscape (MEDIUM confidence)
- [gcui-art/suno-api GitHub](https://github.com/gcui-art/suno-api) — `make_instrumental`, `duration` parameter reference (MEDIUM confidence — unofficial)
- [damian0815/compel GitHub](https://github.com/damian0815/compel) — `CompelForSDXL` usage, SDXL dual-encoder support (HIGH confidence — official library)
- [Hugging Face diffusers — Prompt Weighting](https://huggingface.co/docs/diffusers/using-diffusers/weighted_prompts) — Official diffusers docs on compel integration (HIGH confidence)
- [Layer.ai — SDXL Negative Prompts](https://help.layer.ai/en/articles/8120630-how-to-write-negative-prompts-relevant-for-sdxl-only) — SDXL-specific negative prompt strategy (MEDIUM confidence)
- [grantjenks/python-diskcache GitHub](https://github.com/grantjenks/python-diskcache) — diskcache 5.6.3, SQLite-backed, size limits (HIGH confidence — official)
- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui/actions/runs/8313482089/workflow) — Precedent for diskcache in SD context (MEDIUM confidence)
- [diskcache PyPI](https://pypi.org/project/diskcache/) — Current version 5.6.3 (HIGH confidence)

---
*Stack research for: content_creation v1.1 — AI Generation Quality milestone*
*Researched: 2026-03-28*

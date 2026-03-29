# Phase 24: Instagram Style Reference System — Research

**Researched:** 2026-03-29
**Domain:** Instagram scraping, visual style extraction, IP-Adapter style transfer, Replicate API integration
**Confidence:** MEDIUM (scraping reliability LOW; style transfer patterns HIGH; integration patterns MEDIUM)

## Summary

Phase 24 adds a style reference subsystem that scrapes a target Instagram account (@radstream), extracts color/mood descriptors from those images, stores a persistent "style profile" on disk, and injects that profile into future generation calls via either (a) IP-Adapter style conditioning in local diffusers or (b) reference image inputs to the Seedream 5 Replicate model. The phase must integrate cleanly with the existing `ImageGenerator` in `generators/image_gen.py` — specifically adding a `style_reference_path` parameter that is passed to whatever generation backend is active.

The two hardest sub-problems are: (1) reliably getting images out of Instagram in 2026 and (2) making style conditioning actually produce consistent visual output across 8+ scene variants. For (1), instaloader requires a logged-in session cookie — anonymous public-profile access now consistently triggers redirects to the login page. For (2), the InstantStyle approach (IP-Adapter with per-layer scale targeting only `up_blocks.0.attentions.1`) separates style from content and is the current best-practice for consistent aesthetics without content bleed.

The @radstream account could not be independently verified through web search — it returned no specific results. Treat the account handle as an implementation input the user confirms at runtime; the scraper must work against any public profile, not hardcode @radstream assumptions. The lofi/aesthetic niche it likely inhabits has well-understood visual properties: warm desaturated palettes, shallow depth of field, film grain texture, moody low-key lighting — these map directly to existing cinematic.yaml prompt vocabulary.

**Primary recommendation:** Use instaloader with browser cookie import for scraping; use InstantStyle layer-targeted IP-Adapter (via local diffusers or the `h94/IP-Adapter` HuggingFace weights) for style transfer; store extracted style profile as JSON with cached PIL-serialized embeddings; expose `style_ref` parameter on `ImageGenerator.generate_scenes()`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| instaloader | 4.15+ | Download Instagram posts/images to disk | Sole maintained Python-native Instagram download library; Bellingcat toolkit standard |
| colorthief | 0.2.1 | Extract dominant color palette from images | Pure Python + Pillow, no sklearn dependency; palette returned as RGB list |
| scikit-learn | 1.x | KMeans clustering for advanced palette extraction | Used when colorthief palette granularity is insufficient; already likely in project env |
| diffusers | 0.37+ | Load IP-Adapter weights, run InstantStyle style conditioning | Official HuggingFace library; `load_ip_adapter()` and `set_ip_adapter_scale()` are the stable API |
| transformers | 4.x | CLIPVisionModelWithProjection for IP-Adapter Plus | Required for ViT-H image encoder used by ip-adapter-plus_sdxl_vit-h weights |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow (PIL) | 10.x | Image loading, resizing, format conversion | Always — already project dependency |
| requests | 2.x | Download image URLs returned from instaloader | Already project dependency |
| numpy | 1.x | Pixel array manipulation for color extraction | Already project dependency |
| torch | 2.x | Required backend for diffusers IP-Adapter | Only when running local IP-Adapter; not needed for Replicate path |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| instaloader | playwright browser automation | Playwright is more robust against Instagram blocking but adds heavyweight browser dependency; instaloader + session cookie is sufficient for a small reference scrape (20-50 images) |
| instaloader | Instagram Basic Display API | Official API requires app approval, user OAuth — impractical for automated scraping of a third-party account |
| IP-Adapter local | Seedream 5 Replicate `image_input` style reference | Replicate path requires no GPU locally, but $0.05+/call for every generation; IP-Adapter local is free after model download |
| colorthief | sklearn KMeans on raw pixels | sklearn gives more control (n_colors, init strategy) but colorthief is faster and already handles quantization internally |

**Installation:**
```bash
pip install instaloader colorthief
# diffusers/transformers already installed or via:
pip install diffusers transformers accelerate
```

## Architecture Patterns

### Recommended Project Structure
```
generators/
├── image_gen.py          # existing — add style_reference parameter
├── style_reference.py    # NEW: scraper + extractor + profile manager
└── ...

.cache/
├── images/               # existing scene image cache
└── style_reference/
    ├── @radstream/        # one dir per Instagram handle
    │   ├── posts/         # downloaded .jpg files
    │   ├── profile.json   # extracted style profile
    │   └── embeddings.ipadpt  # serialized IP-Adapter image embeddings (optional)
    └── ...
```

### Pattern 1: Style Profile JSON Schema
**What:** A serializable dict capturing color palette, mood descriptors, and reference image paths, stored alongside scraped images. Consumed by prompt augmentation and IP-Adapter conditioning.
**When to use:** Whenever a generation call specifies a `style_ref` profile name.

```python
# Source: derived from colorthief docs + project cache pattern (image_gen.py sidecar convention)
import json
from pathlib import Path

STYLE_PROFILE_SCHEMA = {
    "handle": "@radstream",
    "scraped_at": "2026-03-29T12:00:00Z",
    "post_count": 24,
    "dominant_colors": [
        [42, 38, 55],   # RGB tuples — warm dark purple
        [180, 145, 110],  # warm sand
        [90, 110, 140],   # muted blue-gray
    ],
    "color_temperature": "warm",   # warm | cool | neutral
    "brightness_level": "low",     # low | medium | high
    "contrast_level": "medium",    # low | medium | high
    "mood_descriptors": [
        "moody", "cinematic", "warm", "atmospheric", "lofi"
    ],
    "reference_images": [
        ".cache/style_reference/@radstream/posts/post_001.jpg",
        ".cache/style_reference/@radstream/posts/post_002.jpg",
        # ... up to 10 images
    ],
    "prompt_prefix": "warm muted tones, cinematic grain, atmospheric low-key lighting, film photography",
}
```

### Pattern 2: Instagram Scraping via instaloader with Session Cookie
**What:** Download the most-recent N posts from a public profile using a browser-imported session cookie.
**When to use:** At style profile creation time (one-off or on explicit refresh).

```python
# Source: instaloader official docs + GitHub issue #2427 workaround
import instaloader
from pathlib import Path

def scrape_profile_images(
    handle: str,
    post_limit: int = 30,
    cache_dir: Path = Path(".cache/style_reference"),
    cookie_file: str = None,  # path to Firefox/Chrome cookie file
) -> list[Path]:
    L = instaloader.Instaloader(
        download_pictures=True,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )

    # Load browser session (required in 2026 for public profiles)
    if cookie_file:
        # instaloader v4.14+ supports --load-cookies
        L.load_session_from_file(username=None, sessionfile=cookie_file)
    else:
        # Attempt anonymous — may fail with LoginRequiredException
        pass

    target_dir = cache_dir / handle.lstrip("@")
    target_dir.mkdir(parents=True, exist_ok=True)
    posts_dir = target_dir / "posts"
    posts_dir.mkdir(exist_ok=True)

    images = []
    try:
        profile = instaloader.Profile.from_username(L.context, handle.lstrip("@"))
        for i, post in enumerate(profile.get_posts()):
            if i >= post_limit:
                break
            if post.is_video:
                continue
            L.download_post(post, target=str(posts_dir))
            # instaloader saves as YYYY-MM-DD_HH-MM-SS_UTC.jpg
    except instaloader.LoginRequiredException:
        raise RuntimeError(
            f"Instagram requires login to access @{handle}. "
            "Run: instaloader --login=<username> to generate a session file, "
            "or use --load-cookies=<browser_cookies_path>."
        )

    return list(posts_dir.glob("*.jpg"))
```

### Pattern 3: Style Feature Extraction
**What:** From a set of downloaded images, extract dominant colors and infer mood descriptors using colorthief + brightness/contrast heuristics.
**When to use:** After scraping, before storing profile.json.

```python
# Source: colorthief docs (https://github.com/fengsp/color-thief-py) + OpenCV heuristics
from colorthief import ColorThief
import numpy as np
from PIL import Image

def extract_style_features(image_paths: list[Path]) -> dict:
    """Extract color palette and mood descriptors from a set of images."""
    all_colors = []
    brightness_scores = []
    contrast_scores = []

    for path in image_paths[:20]:  # cap at 20 for speed
        ct = ColorThief(str(path))
        palette = ct.get_palette(color_count=5, quality=1)
        all_colors.extend(palette)

        # Brightness + contrast from PIL
        img = Image.open(path).convert("L")
        arr = np.array(img)
        brightness_scores.append(arr.mean())
        contrast_scores.append(arr.std())

    # Aggregate dominant colors via KMeans
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=5, n_init=10, random_state=42)
    km.fit(all_colors)
    dominant = [list(map(int, c)) for c in km.cluster_centers_]

    avg_brightness = np.mean(brightness_scores)
    avg_contrast = np.mean(contrast_scores)

    return {
        "dominant_colors": dominant,
        "color_temperature": _classify_temperature(dominant),
        "brightness_level": "low" if avg_brightness < 85 else "high" if avg_brightness > 170 else "medium",
        "contrast_level": "low" if avg_contrast < 35 else "high" if avg_contrast > 70 else "medium",
    }

def _classify_temperature(colors: list) -> str:
    """Classify overall color temperature from RGB centroids."""
    avg_r = np.mean([c[0] for c in colors])
    avg_b = np.mean([c[2] for c in colors])
    if avg_r - avg_b > 15:
        return "warm"
    elif avg_b - avg_r > 15:
        return "cool"
    return "neutral"
```

### Pattern 4: InstantStyle Layer-Targeted IP-Adapter (LOCAL path)
**What:** Style-only IP-Adapter conditioning using diffusers `set_ip_adapter_scale` with a dict targeting only the style injection layer.
**When to use:** When running local GPU inference (not Replicate). Requires diffusers + torch.

```python
# Source: HuggingFace diffusers IP-Adapter docs
# https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter
import torch
from diffusers import AutoPipelineForText2Image
from diffusers.utils import load_image

pipeline = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
).to("cuda")

pipeline.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="sdxl_models",
    weight_name="ip-adapter_sdxl.bin",
)

# InstantStyle: target ONLY the style layer (up_blocks.0.attentions.1)
# This injects style without distorting composition
scale = {
    "up": {"block_0": [0.0, 1.0, 0.0]},
}
pipeline.set_ip_adapter_scale(scale)

# Use multiple reference images as a list for richer style signal
style_images = [load_image(str(p)) for p in reference_image_paths[:10]]

result = pipeline(
    prompt="cozy study room, warm light, atmospheric",
    ip_adapter_image=style_images,
    negative_prompt="text, watermark, low quality",
    guidance_scale=5.0,
).images[0]
```

### Pattern 5: Precompute and Cache Image Embeddings
**What:** Precompute IP-Adapter image embeddings once from reference images and save to disk, avoiding re-encoding on every generation call.
**When to use:** Always — multiple generations sharing the same style profile should not re-encode the reference images each time.

```python
# Source: HuggingFace diffusers IP-Adapter docs — prepare_ip_adapter_image_embeds
import torch

image_embeds = pipeline.prepare_ip_adapter_image_embeds(
    ip_adapter_image=style_images,
    ip_adapter_image_embeds=None,
    device="cuda",
    num_images_per_prompt=1,
    do_classifier_free_guidance=True,
)
# Save to .cache/style_reference/@handle/embeddings.ipadpt
torch.save(image_embeds, str(embeddings_path))

# Load on subsequent calls
image_embeds = torch.load(str(embeddings_path))
pipeline(
    prompt=prompt,
    ip_adapter_image_embeds=image_embeds,
    ...
)
```

### Pattern 6: Replicate Path — Seedream 5 with `image_input`
**What:** Pass reference images to Seedream 5 via Replicate API using the `image_input` parameter. No local GPU required.
**When to use:** When `REPLICATE_API_TOKEN` is set and no local GPU is available.

```python
# Source: Replicate Seedream 5 docs (replicate.com/bytedance/seedream-5-lite)
# Seedream 5 accepts up to 14 reference images via image_input array
import replicate, requests, base64, io
from PIL import Image

def _style_ref_to_data_uris(image_paths: list[Path], max_refs: int = 6) -> list[str]:
    uris = []
    for p in image_paths[:max_refs]:
        b64 = base64.b64encode(p.read_bytes()).decode()
        uris.append(f"data:image/jpeg;base64,{b64}")
    return uris

output = replicate.run(
    "bytedance/seedream-5-lite",
    input={
        "prompt": f"style reference: {style_profile['prompt_prefix']}, {user_prompt}",
        "image_input": _style_ref_to_data_uris(reference_images),
        "aspect_ratio": "16:9",
        "output_format": "png",
    },
)
```

### Anti-Patterns to Avoid

- **Anonymous instaloader scraping without session:** Instagram now redirects public profile requests to the login page without a session cookie. Anonymous downloads will raise `LoginRequiredException`. Always provide a session or cookie file.
- **Hardcoding @radstream in code:** The scraper should accept any handle. @radstream is a user-supplied configuration value, not a code constant.
- **Using IP-Adapter at full scale (1.0) without InstantStyle targeting:** Full-scale IP-Adapter copies content AND style from the reference image. Use the `"up": {"block_0": [0.0, 1.0, 0.0]}` scale dict to inject style only.
- **Re-encoding reference images on every generation call:** Precompute embeddings once with `prepare_ip_adapter_image_embeds` and cache the `.ipadpt` file. Re-encoding 10 reference images per generation is expensive.
- **Scraping on every pipeline run:** Scraping should be a one-time setup step (like branding fetch). Cache the profile.json and reference images; re-scrape only on explicit `--refresh-style-ref` flag.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Instagram image download | Custom requests session with cookies | instaloader | instaloader handles rate limiting, session management, filename conventions, LoginRequiredException |
| Color palette extraction | Custom per-pixel RGB histogram | colorthief + KMeans | Median-cut quantization + clustering handles gamma, perceptual color grouping correctly |
| Style conditioning in diffusers | Manual cross-attention manipulation | IP-Adapter `load_ip_adapter()` + `set_ip_adapter_scale()` | diffusers handles weight loading, encoder routing, CFG guidance doubling |
| IP-Adapter model download | Manually download .bin files | `load_ip_adapter("h94/IP-Adapter", ...)` | diffusers auto-downloads from HuggingFace Hub with caching |

**Key insight:** Instagram's anti-bot defenses and IP-Adapter's cross-attention injection are both complex enough that custom solutions break silently. Use the maintained libraries.

## Common Pitfalls

### Pitfall 1: instaloader LoginRequiredException on Public Profiles
**What goes wrong:** `instaloader.LoginRequiredException` raised even for public profiles in 2026. Anonymous scraping returns HTTP 301 redirect to login page.
**Why it happens:** Instagram tightened anonymous API access post-2023. Without a session cookie, all profile requests redirect to login.
**How to avoid:** Use `instaloader --login=<username>` to generate a session file, then load it via `L.load_session_from_file()`, or use `--load-cookies` with browser cookie export. Document this as a one-time user setup step.
**Warning signs:** `LoginRequiredException`, `ProfileNotExistsException`, or HTTP 301 in instaloader output.

### Pitfall 2: IP-Adapter Injecting Content Instead of Style
**What goes wrong:** Generated images look like the reference photos, not just stylistically influenced — composition, subjects, and scene elements are copied from reference images.
**Why it happens:** Using full-scale IP-Adapter (`scale=0.8` uniform) injects both layout information (from `down_blocks.2`) and style (from `up_blocks.0`). The layout injection is what causes content bleed.
**How to avoid:** Use the InstantStyle per-layer scale dict targeting only `up_blocks.0`: `{"up": {"block_0": [0.0, 1.0, 0.0]}}`. This disables layout injection while preserving style transfer.
**Warning signs:** Generated scenes showing the same furniture, people, or room layouts as reference Instagram photos.

### Pitfall 3: Stale Cached Embeddings After Reference Image Updates
**What goes wrong:** User updates reference images by re-scraping, but old `.ipadpt` embedding file is reused, producing outdated style conditioning.
**Why it happens:** Embedding cache is keyed by path, not by image content hash.
**How to avoid:** Key the `.ipadpt` cache file by a hash of the sorted reference image paths + their file mtimes. Regenerate embeddings when the hash changes.
**Warning signs:** Style profile visual output doesn't match newly scraped reference images.

### Pitfall 4: Replicate Rate and Cost Accumulation from Reference Images
**What goes wrong:** Passing 10 reference images to every Seedream call multiplies token costs; large base64 payloads slow requests.
**Why it happens:** Each data URI adds payload size; Seedream pricing scales with output quality, not input count, but large payloads increase latency.
**How to avoid:** Cap reference images at 4-6 for Replicate path. Resize reference images to 512px before encoding for data URIs.
**Warning signs:** Replicate response times >30s; unexpectedly high credit consumption.

### Pitfall 5: @radstream Account Doesn't Exist or Is Private
**What goes wrong:** `ProfileNotExistsException` or `PrivateProfileNotFollowedException` if @radstream is private or the handle is wrong.
**Why it happens:** Handle assumed to be public. Research did not verify the account exists.
**How to avoid:** Wrap `Profile.from_username()` in explicit exception handling. Provide a clear user message with setup instructions when scraping fails. Allow user to manually place images in `.cache/style_reference/<handle>/posts/` as a fallback.
**Warning signs:** `ProfileNotExistsException` at scrape time.

### Pitfall 6: `enable_model_cpu_offload()` Called Before `load_ip_adapter()`
**What goes wrong:** `CLIPVisionModel` image encoder gets offloaded to CPU before loading, causing a runtime error when IP-Adapter tries to use it.
**Why it happens:** diffusers docs explicitly warn: "enable_model_cpu_offload() should be enabled AFTER the IP-Adapter is loaded."
**How to avoid:** Always call `pipeline.load_ip_adapter(...)` → `pipeline.set_ip_adapter_scale(...)` → `pipeline.enable_model_cpu_offload()` in that order.

## Code Examples

### Verified: Minimal instaloader Profile Scrape
```python
# Source: https://instaloader.github.io/as-module.html
import instaloader

L = instaloader.Instaloader(download_videos=False, save_metadata=False)
# Login required in 2026 for public profile access:
L.load_session_from_file(username="your_username")  # after: instaloader --login=<user>

profile = instaloader.Profile.from_username(L.context, "radstream")
for i, post in enumerate(profile.get_posts()):
    if i >= 30:
        break
    L.download_post(post, target=".cache/style_reference/radstream/posts")
```

### Verified: InstantStyle Scale Dict for Style-Only IP-Adapter
```python
# Source: https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter
# "Style and layout control" section — InstantStyle approach
scale = {
    "up": {"block_0": [0.0, 1.0, 0.0]},  # up_blocks.0.attentions.1 = style layer
}
pipeline.set_ip_adapter_scale(scale)
```

### Verified: Multiple Style Images as ip_adapter_image List
```python
# Source: https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter
# "Multiple IP-Adapters" section
style_images = [load_image(str(p)) for p in reference_image_paths[:10]]
pipeline(
    prompt="a cozy study room with warm lighting",
    ip_adapter_image=[style_images, face_image],  # list of lists for multiple adapters
    negative_prompt="monochrome, lowres, bad anatomy",
).images[0]
```

### Verified: Precompute and Persist Embeddings
```python
# Source: https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter
# "Image embeddings" section
import torch

image_embeds = pipeline.prepare_ip_adapter_image_embeds(
    ip_adapter_image=style_images,
    ip_adapter_image_embeds=None,
    device="cuda",
    num_images_per_prompt=1,
    do_classifier_free_guidance=True,
)
torch.save(image_embeds, "embeddings.ipadpt")
# Later: image_embeds = torch.load("embeddings.ipadpt")
```

### Verified: colorthief Palette Extraction
```python
# Source: https://github.com/fengsp/color-thief-py
from colorthief import ColorThief

ct = ColorThief("reference.jpg")
dominant = ct.get_color(quality=1)       # (R, G, B)
palette = ct.get_palette(color_count=8)  # list of (R, G, B)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| IP-Adapter uniform scale (0.8) | InstantStyle per-layer scale dict | Apr 2024 | Separates style from content; no composition bleed |
| Anonymous instaloader scrape | Session cookie required | 2023-2024 | Scraping now requires authenticated session for all public profiles |
| Single reference image | List of reference images (up to 10) | IP-Adapter Plus 2024 | Richer style signal from multiple images reduces over-fitting to single reference |
| bytedance/seedream-3 on Replicate | bytedance/seedream-5-lite (14 ref images) | Late 2025 | Seedream 5 accepts up to 14 reference images natively via `image_input` |
| Download full model weights for IP-Adapter | `load_ip_adapter()` from HuggingFace Hub | diffusers 0.20+ | Auto-download with caching; no manual weight management |

**Deprecated/outdated:**
- `bytedance/seedream-3` Replicate endpoint: Seedream 5 and 5-lite are the current generation. Use `bytedance/seedream-5-lite` for cost-efficiency.
- IP-Adapter uniform float scale for style transfer: Per-layer dict is the correct approach for style-only conditioning.

## Open Questions

1. **Does @radstream exist as a public Instagram account?**
   - What we know: Web search returned no results confirming this handle exists or describing their visual aesthetic.
   - What's unclear: Whether the account is public, private, or exists at all.
   - Recommendation: Make the handle a configurable parameter (`style_ref_handle` in profile YAML or CLI). Scrape fails gracefully with clear error + manual fallback (user drops images into `.cache/style_reference/<handle>/posts/`).

2. **Does the project have a GPU available for local IP-Adapter inference?**
   - What we know: `generators/image_gen.py` falls back to CPU-only local SD 1.5 as last resort. Primary path is Replicate. IP-Adapter diffusers inference requires CUDA for reasonable performance.
   - What's unclear: Whether a local GPU is available or intended to be used.
   - Recommendation: Default to the Replicate path (Seedream 5 `image_input`) which requires no GPU. Make local IP-Adapter an opt-in path controlled by a `style_ref_backend: replicate | local_ipadapter` config flag.

3. **How should style references bind to roadmap videos?**
   - What we know: Phase 19 added a `VideoRoadmap` with entries having title/tags/profile/notes fields.
   - What's unclear: Whether binding means "this roadmap entry uses @radstream style" as a roadmap field or as a profile YAML field.
   - Recommendation: Add `style_ref_handle` to the profile YAML (e.g., `cinematic.yaml` gets `style_ref: "@radstream"`). The roadmap entry selects a profile, the profile declares its style reference. No schema change to `VideoRoadmap` needed.

4. **Instagram ToS: risk level for this use case?**
   - What we know: Instagram TOS prohibits automated data collection. However, a 2024 court ruling (Meta v. Bright Data) established that scraping public data while logged out may not constitute a contract violation. Using reference images privately for local style conditioning (not re-publishing) is lower risk than public redistribution.
   - What's unclear: Whether authenticated instaloader scraping of a public account for private local use has been challenged.
   - Recommendation: Keep scraped images in `.cache/` (gitignored). Do not re-publish or distribute the reference images. Document that this is for personal local use only. Do not add scraped images to repo.

## Sources

### Primary (HIGH confidence)
- `https://huggingface.co/docs/diffusers/using-diffusers/ip_adapter` — IP-Adapter load, set_ip_adapter_scale, InstantStyle layer dict, image embeddings precomputation, multiple images
- `https://instaloader.github.io/as-module.html` — Profile.from_username, get_posts, download_post, Instaloader constructor params
- `https://github.com/fengsp/color-thief-py` — get_color, get_palette API
- `https://replicate.com/bytedance/seedream-5-lite` — image_input parameter, sequential_image_generation, aspect_ratio, size params

### Secondary (MEDIUM confidence)
- `https://github.com/instaloader/instaloader/issues/2427` — LoginRequiredException for public profiles confirmed; cookie workaround documented
- `https://instaloader.github.io/troubleshooting.html` — rate limiting behavior, authenticated vs anonymous limits
- InstantStyle GitHub `instantX-research/InstantStyle` — up_blocks.0.attentions.1 is style layer, down_blocks.2 is layout layer
- `https://sociavault.com/blog/instagram-scraping-legal-2025` — ToS analysis, Meta v. Bright Data ruling

### Tertiary (LOW confidence)
- @radstream account existence and aesthetic: not independently verified via web search. Treat as user-confirmed input.
- Seedream 5 reference image pricing: exact cost-per-run not retrieved; estimate based on Seedream 3 pricing (~$0.03-0.05/run).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — instaloader, colorthief, diffusers IP-Adapter all verified against official docs
- Architecture/integration: MEDIUM — patterns derived from verified library APIs; integration with existing ImageGenerator is straightforward but untested
- Pitfalls: HIGH — LoginRequiredException and IP-Adapter content-bleed are well-documented in official sources and GitHub issues
- @radstream aesthetics: LOW — account not found in web search; aesthetic properties extrapolated from lofi/cinematic niche

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (instaloader behavior changes frequently; re-verify login requirements before planning if delayed >2 weeks)

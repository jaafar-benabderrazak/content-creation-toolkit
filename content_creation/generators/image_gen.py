"""Image generator — API-based generation with single-image variant system.

Default: generates ONE base image via API, creates scene variants via
PIL transforms (crop, zoom, brightness, color shift). Multiple distinct
images only when explicitly requested.

Supports: OpenAI DALL-E 3, with local SDXL fallback.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import random
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

CACHE_DIR_NAME = ".cache/images"


def _cache_key(params: dict) -> str:
    serialised = json.dumps(params, sort_keys=True).encode()
    return hashlib.sha256(serialised).hexdigest()


# ---------------------------------------------------------------------------
# Variant generation from a single base image
# ---------------------------------------------------------------------------

VARIANT_TRANSFORMS = [
    # (name, transform_fn)
    ("original", lambda img: img),
    ("zoom_center", lambda img: _zoom_crop(img, 1.15, 0.5, 0.5)),
    ("zoom_left", lambda img: _zoom_crop(img, 1.2, 0.25, 0.45)),
    ("zoom_right", lambda img: _zoom_crop(img, 1.2, 0.75, 0.45)),
    ("zoom_top", lambda img: _zoom_crop(img, 1.15, 0.5, 0.3)),
    ("warm_shift", lambda img: _color_shift(img, warmth=1.15, brightness=1.05)),
    ("cool_shift", lambda img: _color_shift(img, warmth=0.9, brightness=0.95)),
    ("bright", lambda img: _color_shift(img, warmth=1.0, brightness=1.12, contrast=1.05)),
    ("moody", lambda img: _color_shift(img, warmth=1.05, brightness=0.88, contrast=1.1)),
    ("soft_focus", lambda img: img.filter(ImageFilter.GaussianBlur(radius=1.5))),
]


def _zoom_crop(img: Image.Image, scale: float, cx: float, cy: float) -> Image.Image:
    """Crop a zoomed region from the image centered at (cx, cy) proportional coords."""
    w, h = img.size
    new_w, new_h = int(w / scale), int(h / scale)
    left = int((w - new_w) * cx)
    top = int((h - new_h) * cy)
    cropped = img.crop((left, top, left + new_w, top + new_h))
    return cropped.resize((w, h), Image.LANCZOS)


def _color_shift(
    img: Image.Image,
    warmth: float = 1.0,
    brightness: float = 1.0,
    contrast: float = 1.0,
) -> Image.Image:
    """Apply color temperature, brightness, and contrast adjustments."""
    result = img
    if brightness != 1.0:
        result = ImageEnhance.Brightness(result).enhance(brightness)
    if contrast != 1.0:
        result = ImageEnhance.Contrast(result).enhance(contrast)
    if warmth != 1.0:
        result = ImageEnhance.Color(result).enhance(warmth)
    return result


def generate_variants(base_image: Image.Image, count: int) -> List[Image.Image]:
    """Generate `count` variants from a single base image."""
    variants = []
    transforms = VARIANT_TRANSFORMS[:count] if count <= len(VARIANT_TRANSFORMS) else (
        VARIANT_TRANSFORMS * (count // len(VARIANT_TRANSFORMS) + 1)
    )[:count]

    for name, fn in transforms:
        variant = fn(base_image.copy())
        variants.append(variant)
        logger.info(f"[ImageGen] Variant: {name}")

    return variants


# ---------------------------------------------------------------------------
# Style reference helpers
# ---------------------------------------------------------------------------

def _style_ref_to_data_uris(image_paths: list, max_refs: int = 6) -> list:
    """Encode reference images as base64 data URIs for Replicate image_input."""
    import base64
    import io as _io

    from PIL import Image as _PIL_Image

    uris = []
    for p in image_paths[:max_refs]:
        p = Path(p)
        if not p.exists():
            continue
        # Resize to 512px max side to reduce payload size (per research pitfall 4)
        img = _PIL_Image.open(p).convert("RGB")
        w, h = img.size
        if max(w, h) > 512:
            scale = 512 / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), _PIL_Image.LANCZOS)
        buf = _io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        uris.append(f"data:image/jpeg;base64,{b64}")
    return uris


# ---------------------------------------------------------------------------
# Local IP-Adapter generation (CUDA required)
# ---------------------------------------------------------------------------

def _generate_ipadapter(
    prompt: str,
    style_ref_paths: list,
    style_strength: float = 0.6,
) -> Image.Image:
    """Generate via local SDXL + InstantStyle IP-Adapter. Requires CUDA."""
    import torch
    from diffusers import AutoPipelineForText2Image
    from diffusers.utils import load_image

    if not torch.cuda.is_available():
        raise RuntimeError(
            "IP-Adapter local backend requires CUDA. "
            "Set style_ref_backend='replicate' to use Replicate instead."
        )

    pipeline = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
    ).to("cuda")

    pipeline.load_ip_adapter(
        "h94/IP-Adapter",
        subfolder="sdxl_models",
        weight_name="ip-adapter_sdxl.bin",
    )

    # InstantStyle: style-only layer targeting (no content/composition bleed)
    scale = {"up": {"block_0": [0.0, style_strength, 0.0]}}
    pipeline.set_ip_adapter_scale(scale)
    # IMPORTANT: enable_model_cpu_offload AFTER load_ip_adapter (per diffusers docs)
    pipeline.enable_model_cpu_offload()

    style_images = [load_image(str(p)) for p in style_ref_paths[:10] if Path(p).exists()]

    result = pipeline(
        prompt=prompt,
        ip_adapter_image=style_images,
        negative_prompt="text, watermark, low quality, blurry",
        guidance_scale=5.0,
        num_inference_steps=30,
        width=1792,
        height=1024,
    ).images[0]
    del pipeline
    torch.cuda.empty_cache()
    return result


# ---------------------------------------------------------------------------
# API-based image generation
# ---------------------------------------------------------------------------

def generate_image_api(
    prompt: str,
    size: str = "1792x1024",
    quality: str = "hd",
    model: str = "dall-e-3",
    api_key: Optional[str] = None,
    style_ref_paths: Optional[list] = None,
    style_ref_backend: str = "replicate",
) -> Image.Image:
    """Generate a single image via best available API.

    Priority: IP-Adapter local (if style_ref_backend=local_ipadapter + CUDA)
              → Seedream 5 (Replicate) → DALL-E 3 (OpenAI) → Local SD 1.5.
    Returns a PIL Image.
    """
    # IP-Adapter local path (CUDA only)
    if style_ref_paths and style_ref_backend == "local_ipadapter":
        try:
            return _generate_ipadapter(prompt, style_ref_paths)
        except RuntimeError as e:
            logger.warning(f"[ImageGen] IP-Adapter failed ({e}), falling back to Replicate...")

    # Try Seedream 5 via Replicate first
    replicate_token = os.environ.get("REPLICATE_API_TOKEN")
    if replicate_token:
        try:
            return _generate_seedream(prompt, replicate_token, style_ref_paths=style_ref_paths)
        except Exception as e:
            logger.warning(f"[ImageGen] Seedream failed ({e}), trying DALL-E 3...")

    # Try DALL-E 3 (no style ref support)
    openai_key = api_key or os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            return _generate_dalle(prompt, openai_key, size, quality, model)
        except Exception as e:
            logger.warning(f"[ImageGen] DALL-E 3 failed ({e}), falling back to local SD")

    # Last resort: local SD 1.5
    return _generate_local(prompt)


def _generate_seedream(
    prompt: str,
    token: str,
    style_ref_paths: Optional[list] = None,
) -> Image.Image:
    """Generate image via ByteDance Seedream 5 on Replicate."""
    import replicate as rep
    import requests as req

    os.environ["REPLICATE_API_TOKEN"] = token
    logger.info(f"[ImageGen] Seedream 5 (Replicate): {prompt[:70]}...")

    inp = {
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "output_format": "png",
        "num_outputs": 1,
    }

    if style_ref_paths:
        uris = _style_ref_to_data_uris(style_ref_paths, max_refs=6)
        if uris:
            inp["image_input"] = uris
            logger.info(f"[ImageGen] Seedream 5: {len(uris)} style reference images injected")

    output = rep.run(
        "bytedance/seedream-5-lite",
        input=inp,
    )

    # output is a list of FileOutput URLs
    url = output[0] if isinstance(output, list) else output
    image_data = req.get(str(url)).content
    img = Image.open(io.BytesIO(image_data)).convert("RGB")
    logger.info(f"[ImageGen] Seedream done: {img.size}")
    return img


def _generate_dalle(
    prompt: str, key: str, size: str, quality: str, model: str,
) -> Image.Image:
    """Generate image via OpenAI DALL-E 3."""
    import requests as req
    from openai import OpenAI

    client = OpenAI(api_key=key)
    logger.info(f"[ImageGen] DALL-E 3: {prompt[:70]}...")
    response = client.images.generate(
        model=model, prompt=prompt, size=size, quality=quality, n=1,
    )
    image_data = req.get(response.data[0].url).content
    return Image.open(io.BytesIO(image_data)).convert("RGB")


def _generate_local(prompt: str) -> Image.Image:
    """Generate image via local Stable Diffusion 1.5 on CPU (last resort)."""
    import torch
    from diffusers import StableDiffusionPipeline

    logger.info(f"[ImageGen] Local SD 1.5 (CPU): {prompt[:60]}...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=torch.float32, safety_checker=None,
    )
    pipe.to("cpu")
    pipe.enable_attention_slicing()
    img = pipe(
        prompt, num_inference_steps=25, width=768, height=512,
        guidance_scale=8.0, generator=torch.manual_seed(42),
    ).images[0]
    del pipe
    return img


# ---------------------------------------------------------------------------
# Main generator class
# ---------------------------------------------------------------------------

class ImageGenerator:
    """Generates scene images for video pipelines.

    Default behavior: ONE base image → N variants via transforms.
    Set `multi_image=True` for distinct images per scene.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else Path(CACHE_DIR_NAME)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_scenes(
        self,
        prompt: str,
        negative_prompt: str = "",
        scene_count: int = 8,
        profile: str = "default",
        quality: str = "hd",
        size: str = "1792x1024",
        target_resolution: Tuple[int, int] = (1920, 1080),
        multi_image: bool = False,
        api_key: Optional[str] = None,
        seed: int = 42,
        style_ref_handle: Optional[str] = None,
        style_ref_backend: str = "replicate",
    ) -> List[Path]:
        """Generate scene images and return their file paths.

        Parameters
        ----------
        prompt : str
            The image generation prompt.
        negative_prompt : str
            Negative prompt (used for cache key, not sent to DALL-E).
        scene_count : int
            Number of scene images to produce.
        profile : str
            Profile name for cache key.
        quality : str
            "hd" or "standard" for DALL-E 3.
        size : str
            DALL-E size string (e.g., "1792x1024").
        target_resolution : tuple
            Final output resolution (width, height).
        multi_image : bool
            If True, generate a distinct image per scene.
            If False (default), generate ONE image and create variants.
        api_key : str, optional
            OpenAI API key override.
        seed : int
            Seed for reproducibility (cache key component).
        style_ref_handle : str, optional
            Instagram handle whose cached style profile provides reference
            images for Seedream 5 image_input / IP-Adapter conditioning.
            Requires a populated .cache/style_reference/<handle>/profile.json.
        style_ref_backend : str
            "replicate" (default) uses Seedream 5 image_input on Replicate.
            "local_ipadapter" uses InstantStyle IP-Adapter locally (CUDA required).

        Returns
        -------
        list[Path]
            Paths to generated scene images.
        """
        out_dir = self.cache_dir / "scenes"
        out_dir.mkdir(parents=True, exist_ok=True)

        if multi_image:
            return self._generate_multi(
                prompt, negative_prompt, scene_count, profile,
                quality, size, target_resolution, out_dir, api_key, seed,
                style_ref_handle, style_ref_backend,
            )
        else:
            return self._generate_single_with_variants(
                prompt, negative_prompt, scene_count, profile,
                quality, size, target_resolution, out_dir, api_key, seed,
                style_ref_handle, style_ref_backend,
            )

    def _resolve_style_ref_paths(self, style_ref_handle: str) -> Optional[list]:
        """Resolve reference image paths from a cached StyleReferenceManager profile."""
        try:
            from generators.style_reference import StyleReferenceManager
            mgr = StyleReferenceManager()
            paths = [str(p) for p in mgr.get_reference_image_paths(style_ref_handle)]
            if not paths:
                logger.warning(
                    f"[ImageGen] No reference images found for @{style_ref_handle} "
                    "— generating without style ref"
                )
                return None
            return paths
        except Exception as e:
            logger.warning(f"[ImageGen] StyleRef load failed ({e}) — continuing without style ref")
            return None

    def _generate_single_with_variants(
        self,
        prompt: str,
        negative_prompt: str,
        scene_count: int,
        profile: str,
        quality: str,
        size: str,
        target_resolution: Tuple[int, int],
        out_dir: Path,
        api_key: Optional[str],
        seed: int,
        style_ref_handle: Optional[str] = None,
        style_ref_backend: str = "replicate",
    ) -> List[Path]:
        """Generate ONE base image, then create variants."""
        params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "profile": profile,
            "quality": quality,
            "size": size,
            "seed": seed,
            "mode": "single",
            "style_ref_handle": style_ref_handle or "",
        }
        key = _cache_key(params)

        # Check cache for base image
        base_path = out_dir / f"base_{key[:16]}.png"
        sidecar = base_path.with_suffix(".json")

        if base_path.exists() and sidecar.exists():
            logger.info(f"[ImageGen] Cache hit: base image ({key[:8]})")
            base = Image.open(base_path)
        else:
            logger.info(f"[ImageGen] Generating base image via API...")

            # Resolve style reference paths if handle provided
            style_ref_paths = None
            if style_ref_handle:
                style_ref_paths = self._resolve_style_ref_paths(style_ref_handle)

            base = generate_image_api(
                prompt,
                size=size,
                quality=quality,
                api_key=api_key,
                style_ref_paths=style_ref_paths,
                style_ref_backend=style_ref_backend,
            )
            base = base.resize(target_resolution, Image.LANCZOS)
            base.save(str(base_path), "PNG")
            sidecar.write_text(json.dumps(params, indent=2), encoding="utf-8")
            logger.info(f"[ImageGen] Base image saved: {base_path.name}")

        # Generate variants
        variants = generate_variants(base, scene_count)
        paths = []
        for i, variant in enumerate(variants):
            variant = variant.resize(target_resolution, Image.LANCZOS)
            p = out_dir / f"scene_{i:03d}_{key[:12]}.jpg"
            variant.save(str(p), "JPEG", quality=95)
            paths.append(p)

        logger.info(f"[ImageGen] {scene_count} variants from 1 base image")
        return paths

    def _generate_multi(
        self,
        prompt: str,
        negative_prompt: str,
        scene_count: int,
        profile: str,
        quality: str,
        size: str,
        target_resolution: Tuple[int, int],
        out_dir: Path,
        api_key: Optional[str],
        seed: int,
        style_ref_handle: Optional[str] = None,
        style_ref_backend: str = "replicate",
    ) -> List[Path]:
        """Generate a distinct image for each scene."""
        # Resolve style ref paths once for the whole batch
        style_ref_paths = None
        if style_ref_handle:
            style_ref_paths = self._resolve_style_ref_paths(style_ref_handle)

        paths = []
        for i in range(scene_count):
            scene_prompt = f"{prompt}, scene {i+1}, variation {i+1}"
            params = {
                "prompt": scene_prompt,
                "negative_prompt": negative_prompt,
                "profile": profile,
                "quality": quality,
                "size": size,
                "seed": seed + i,
                "mode": "multi",
                "scene_index": i,
                "style_ref_handle": style_ref_handle or "",
            }
            key = _cache_key(params)
            img_path = out_dir / f"scene_{i:03d}_{key[:12]}.jpg"
            sidecar = img_path.with_suffix(".json")

            if img_path.exists() and sidecar.exists():
                logger.info(f"[ImageGen] Cache hit: scene {i} ({key[:8]})")
            else:
                logger.info(f"[ImageGen] Generating scene {i+1}/{scene_count}...")
                img = generate_image_api(
                    scene_prompt,
                    size=size,
                    quality=quality,
                    api_key=api_key,
                    style_ref_paths=style_ref_paths,
                    style_ref_backend=style_ref_backend,
                )
                img = img.resize(target_resolution, Image.LANCZOS)
                img.save(str(img_path), "JPEG", quality=95)
                sidecar.write_text(json.dumps(params, indent=2), encoding="utf-8")

            paths.append(img_path)

        logger.info(f"[ImageGen] {scene_count} distinct images generated")
        return paths

"""SDXLGenerator — prompt assembly, hash-based image caching, batched generation."""
from __future__ import annotations

import hashlib
import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.prompt_template import PromptTemplate, build_compel_prompt
from config.pipeline_config import SDXLSettings

# ---------------------------------------------------------------------------
# Module-level constants (verbatim from study_with_me_generator.py)
# ---------------------------------------------------------------------------

STYLE_VARIATIONS: List[str] = [
    "cinematic film grain, 35mm lens, natural color grading, soft contrast",
    "shot on Fujifilm X-T4, Film Simulation Classic Chrome, natural bokeh",
    "Sony A7R V, 50mm f/1.4, shallow depth of field, creamy bokeh",
    "Canon R5, cinematic color science, warm highlights, rich shadows",
    "Leica M11, street photography aesthetic, natural light, authentic mood",
    "Phase One medium format, incredible detail, smooth gradients",
]

WEATHER_EFFECTS: List[str] = [
    "gentle rain on windows with bokeh droplets",
    "soft snow falling outside, cozy indoor warmth contrast",
    "golden hour sunbeams streaming through windows",
    "dramatic storm clouds visible through windows, moody lighting",
    "clear blue sky with fluffy white clouds",
    "overcast sky with soft diffused lighting",
]

MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
CACHE_DIR_NAME = ".cache/images"


# ---------------------------------------------------------------------------
# Module-level private helper
# ---------------------------------------------------------------------------

def _cache_key(params: dict) -> str:
    """Return 64-char SHA-256 hex digest of a JSON-serialised parameter dict.

    Uses sort_keys=True so insertion order does not affect the key.
    """
    serialised = json.dumps(params, sort_keys=True).encode()
    return hashlib.sha256(serialised).hexdigest()


# ---------------------------------------------------------------------------
# SDXLGenerator
# ---------------------------------------------------------------------------

class SDXLGenerator:
    """Handles prompt assembly from profile templates, hash-based image caching,
    and batched generation with cache hit/miss progress indicators.

    GPU/model imports are deferred to _generate_one so this class is importable
    and unit-testable without a CUDA device or model weights present.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else Path(CACHE_DIR_NAME)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        scene: dict,
        sdxl_cfg: SDXLSettings,
        extra_context: dict | None = None,
    ) -> Tuple[str, str]:
        """Assemble (positive_prompt, negative_prompt) for a single scene dict.

        Parameters
        ----------
        scene:
            Scene dict; must contain a ``"prompt"`` key (may be a plain string
            or a format-string with ``{variable}`` placeholders).
        sdxl_cfg:
            SDXLSettings instance — provides quality_suffix and negative_prompt.
        extra_context:
            Optional extra variables merged into the render context.

        Returns
        -------
        tuple[str, str]
            (positive_prompt, negative_prompt)
        """
        context: dict = {**scene, **(extra_context or {})}
        resolved = PromptTemplate.render(
            scene["prompt"], context, quality_suffix=sdxl_cfg.quality_suffix
        )

        # Append a random style variation
        style = random.choice(STYLE_VARIATIONS)
        resolved = f"{resolved}, {style}"

        # Append a weather effect for indoor scenes at medium/high quality
        if scene.get("environment") == "indoor" and sdxl_cfg.steps >= 25:
            weather = random.choice(WEATHER_EFFECTS)
            resolved = f"{resolved}, {weather}"

        negative = sdxl_cfg.negative_prompt
        return resolved, negative

    # ------------------------------------------------------------------
    # Parameter dict
    # ------------------------------------------------------------------

    def _params_dict(
        self,
        positive: str,
        negative: str,
        sdxl_cfg: SDXLSettings,
        profile: str,
        seed: int,
    ) -> dict:
        """Build the canonical parameter dict used for cache key computation
        and JSON sidecar serialisation."""
        return {
            "prompt": positive,
            "negative_prompt": negative,
            "steps": sdxl_cfg.steps,
            "guidance_scale": sdxl_cfg.guidance_scale,
            "width": sdxl_cfg.width,
            "height": sdxl_cfg.height,
            "profile": profile,
            "seed": seed,
            "model_id": MODEL_ID,
        }

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _sidecar_path(self, image_path: Path) -> Path:
        """Return the JSON sidecar path for a given PNG path."""
        return image_path.with_suffix(".json")

    def _write_sidecar(self, image_path: Path, params: dict) -> None:
        """Write params as pretty-printed JSON alongside the image."""
        self._sidecar_path(image_path).write_text(
            json.dumps(params, indent=2), encoding="utf-8"
        )

    def _cache_lookup(self, key: str) -> Optional[Path]:
        """Return the cached PNG path if it and its sidecar JSON both exist."""
        matches = list(self.cache_dir.glob(f"*_{key}.png"))
        if matches:
            candidate = matches[0]
            if self._sidecar_path(candidate).exists():
                return candidate
        return None

    # ------------------------------------------------------------------
    # Batch generation entry point
    # ------------------------------------------------------------------

    def generate_batch(
        self,
        scenes: List[dict],
        sdxl_cfg: SDXLSettings,
        profile: str,
        out_dir: Path,
        seed_offset: int = 42,
        force: bool = False,
    ) -> List[Path]:
        """Generate images for a list of scene dicts, using disk cache for hits.

        Parameters
        ----------
        scenes:
            List of scene dicts; each must have a ``"prompt"`` key.
        sdxl_cfg:
            SDXLSettings instance (already configured with quality preset values).
        profile:
            Profile name string (e.g. ``"lofi_study"``); included in cache key.
        out_dir:
            Directory where generated PNGs are written.
        seed_offset:
            Base seed; scene seed = seed_offset + scene_index.
        force:
            When True, bypass cache and always regenerate.

        Returns
        -------
        list[Path]
            Ordered list of paths (cached or newly generated) for each scene.
        """
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results: List[Path] = []

        for i, scene in enumerate(scenes):
            positive, negative = self.build_prompt(scene, sdxl_cfg)
            seed = seed_offset + i
            params = self._params_dict(positive, negative, sdxl_cfg, profile, seed)
            key = _cache_key(params)

            if not force:
                cached = self._cache_lookup(key)
                if cached is not None:
                    self.logger.info(
                        "[SDXL] Cache hit: scene %d (key=%s)", i, key[:8]
                    )
                    results.append(cached)
                    continue

            self.logger.info("[SDXL] Generating scene %d ...", i)
            image = self._generate_one(positive, negative, sdxl_cfg, seed)
            image_path = out_dir / f"scene_{i:03d}_{key[:12]}.png"
            image.save(str(image_path), quality=95)
            self._write_sidecar(image_path, params)
            results.append(image_path)

        return results

    # ------------------------------------------------------------------
    # Single image generation (lazy GPU imports)
    # ------------------------------------------------------------------

    def _generate_one(
        self,
        positive: str,
        negative: str,
        sdxl_cfg: SDXLSettings,
        seed: int,
    ) -> Any:
        """Load the SDXL pipeline, generate one image, unload pipeline.

        All GPU/model imports are deferred inside this method so the module
        is importable without CUDA or model weights present.
        """
        import torch  # noqa: PLC0415
        from diffusers import (  # noqa: PLC0415
            StableDiffusionXLPipeline,
            DPMSolverMultistepScheduler,
        )

        if torch.cuda.is_available():
            device = "cuda"
            dtype = torch.float16
            variant: Optional[str] = "fp16"
        else:
            device = "cpu"
            dtype = torch.float32
            variant = None

        pipe = StableDiffusionXLPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
            use_safetensors=True,
            variant=variant,
        )
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config
        )
        pipe = pipe.to(device)

        if device == "cuda":
            pipe.enable_model_cpu_offload()
            pipe.enable_vae_slicing()
            pipe.enable_attention_slicing(1)

        # Attempt compel weighting; fall back to plain strings on ImportError
        try:
            cond, pooled, neg_cond, neg_pooled = build_compel_prompt(
                positive, negative, pipe
            )
            image = pipe(
                prompt_embeds=cond,
                pooled_prompt_embeds=pooled,
                negative_prompt_embeds=neg_cond,
                negative_pooled_prompt_embeds=neg_pooled,
                num_inference_steps=sdxl_cfg.steps,
                guidance_scale=sdxl_cfg.guidance_scale,
                width=sdxl_cfg.width,
                height=sdxl_cfg.height,
                generator=torch.manual_seed(seed),
            ).images[0]
        except ImportError:
            image = pipe(
                prompt=positive,
                negative_prompt=negative,
                num_inference_steps=sdxl_cfg.steps,
                guidance_scale=sdxl_cfg.guidance_scale,
                width=sdxl_cfg.width,
                height=sdxl_cfg.height,
                generator=torch.manual_seed(seed),
            ).images[0]

        del pipe
        if device == "cuda":
            torch.cuda.empty_cache()

        return image

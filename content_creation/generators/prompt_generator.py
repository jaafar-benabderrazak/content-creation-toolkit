"""
generators/prompt_generator.py
--------------------------------
OpenAI-backed prompt engineering module.

Converts user tags and a profile style string into a full prompt payload:
  - positive_prompt: SDXL positive prompt (50-80 words)
  - negative_prompt: SDXL negative prompt (5-10 terms)
  - scene_templates: list of exactly 8 distinct scene variation prompts (40-60 words each)
  - music_prompt: Suno-compatible music prompt (20-30 words)

Usage
-----
    from generators.prompt_generator import PromptGenerator, PromptGenerationError

    pg = PromptGenerator()  # reads OPENAI_API_KEY from environment
    result = pg.generate(
        tags="lofi, rain, cozy, study",
        profile_style="cinematic wide shot, dramatic lighting, film photography",
    )
    # result["positive_prompt"], result["negative_prompt"],
    # result["scene_templates"], result["music_prompt"]
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config.pipeline_config import PipelineConfig

import openai


class PromptGenerationError(Exception):
    """Raised when prompt generation fails.

    Causes:
      - OPENAI_API_KEY is not set in the environment or provided explicitly
      - The OpenAI API call raises any exception
      - The returned JSON is missing required keys
      - scene_templates does not contain exactly 8 distinct strings
    """


_REQUIRED_KEYS = {"positive_prompt", "negative_prompt", "scene_templates", "music_prompt"}
_SCENE_TEMPLATE_COUNT = 8


class PromptGenerator:
    """Generate SDXL and Suno prompts via OpenAI.

    Parameters
    ----------
    api_key:
        OpenAI API key.  Falls back to ``OPENAI_API_KEY`` environment variable.
        Raises :class:`PromptGenerationError` if no key is available.
    model:
        OpenAI chat model to use.  Defaults to ``"gpt-4o-mini"``.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise PromptGenerationError("OPENAI_API_KEY not set")
        self.model = model
        self._client = openai.OpenAI(api_key=resolved_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, tags: str, profile_style: str) -> dict:
        """Generate a full prompt payload from user tags and a profile style.

        Parameters
        ----------
        tags:
            Comma-separated keywords describing the desired aesthetic.
            Example: ``"lofi, rain, cozy, study"``
        profile_style:
            Visual style string sourced from the profile's
            ``video.style_prompt`` field (see :meth:`_build_profile_style`).
            Example: ``"cinematic wide shot, dramatic lighting, film photography"``

        Returns
        -------
        dict with keys:
            - ``positive_prompt`` (str): SDXL positive prompt, 50-80 words
            - ``negative_prompt`` (str): SDXL negative prompt, 5-10 terms
            - ``scene_templates`` (list[str]): exactly 8 distinct scene variation
              prompts, each 40-60 words
            - ``music_prompt`` (str): Suno-compatible music prompt, 20-30 words

        Raises
        ------
        PromptGenerationError
            On API failure, malformed JSON, missing keys, or incorrect
            ``scene_templates`` count.
        """
        system_message = {
            "role": "system",
            "content": (
                f"You are a professional AI image prompt engineer. "
                f"Generate prompts for a {profile_style} visual aesthetic. "
                f"Return only valid JSON, no markdown."
            ),
        }
        user_message = {
            "role": "user",
            "content": (
                f"Tags: {tags}\n\n"
                "Generate:\n"
                f"- positive_prompt: one SDXL positive prompt (50-80 words) that captures the tags in the {profile_style} aesthetic\n"
                "- negative_prompt: SDXL negative prompt (5-10 terms) optimized for this style\n"
                f"- scene_templates: list of exactly {_SCENE_TEMPLATE_COUNT} distinct scene variation prompts, "
                "each 40-60 words, covering different moments/lighting/compositions derived from the tags\n"
                "- music_prompt: Suno-compatible music prompt (20-30 words) matching the mood of the tags\n\n"
                "Return JSON only."
            ),
        }

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[system_message, user_message],
                temperature=0.8,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            data: dict = json.loads(content)
        except Exception as e:
            raise PromptGenerationError(str(e)) from e

        # Validate required keys
        missing = _REQUIRED_KEYS - data.keys()
        if missing:
            raise PromptGenerationError(
                f"OpenAI response missing required keys: {sorted(missing)}"
            )

        # Validate scene_templates is a list of exactly 8 strings
        scene_templates = data["scene_templates"]
        if not isinstance(scene_templates, list):
            raise PromptGenerationError(
                f"scene_templates must be a list, got {type(scene_templates).__name__}"
            )
        actual_count = len(scene_templates)
        if actual_count != _SCENE_TEMPLATE_COUNT:
            raise PromptGenerationError(
                f"scene_templates must contain exactly {_SCENE_TEMPLATE_COUNT} items, "
                f"got {actual_count}"
            )

        return data

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_profile_style(config: "PipelineConfig") -> str:
        """Extract the visual style string from a PipelineConfig.

        Convenience helper so callers don't need to know which field to read.

        Parameters
        ----------
        config:
            Loaded :class:`~config.pipeline_config.PipelineConfig` instance.

        Returns
        -------
        str
            The ``video.style_prompt`` value from the config.
        """
        return config.video.style_prompt

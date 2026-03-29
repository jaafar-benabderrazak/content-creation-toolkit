"""
generators/prompt_generator.py
--------------------------------
Claude-backed prompt engineering module.

Converts user tags and a profile style string into a full prompt payload:
  - positive_prompt: SDXL positive prompt (50-80 words)
  - negative_prompt: SDXL negative prompt (5-10 terms)
  - scene_templates: list of exactly 8 distinct scene variation prompts (40-60 words each)
  - music_prompt: Suno-compatible music prompt (20-30 words)
  - thumbnail_text: short punchy text overlay for the thumbnail (3-7 words, ALL CAPS)
  - youtube_title: SEO-optimized YouTube title (60 chars max)
  - youtube_description: 150-200 word YouTube description
  - youtube_tags: JSON array of exactly 15-20 SEO tags

Falls back to OpenAI if ANTHROPIC_API_KEY is not set.

Usage
-----
    from generators.prompt_generator import PromptGenerator, PromptGenerationError

    pg = PromptGenerator()  # reads ANTHROPIC_API_KEY (or OPENAI_API_KEY) from environment
    result = pg.generate(
        tags="lofi, rain, cozy, study",
        profile_style="cinematic wide shot, dramatic lighting, film photography",
    )
"""

from __future__ import annotations

import json
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config.pipeline_config import PipelineConfig


class PromptGenerationError(Exception):
    """Raised when prompt generation fails."""


_REQUIRED_KEYS = {
    "positive_prompt",
    "negative_prompt",
    "scene_templates",
    "music_prompt",
    "thumbnail_text",
    "youtube_title",
    "youtube_description",
    "youtube_tags",
}
_SCENE_TEMPLATE_COUNT = 8

_SYSTEM_PROMPT = (
    "You are a professional AI image prompt engineer. "
    "Generate prompts for a {profile_style} visual aesthetic. "
    "Return only valid JSON, no markdown fences, no explanation."
)

_USER_PROMPT = (
    "Tags: {tags}\n\n"
    "Generate a JSON object with these exact keys:\n"
    "- positive_prompt: one SDXL positive prompt (50-80 words) that captures the tags in the {profile_style} aesthetic\n"
    "- negative_prompt: SDXL negative prompt (5-10 terms, comma-separated) optimized for this style\n"
    "- scene_templates: list of exactly 8 distinct scene variation prompts, "
    "each 40-60 words, covering different moments/lighting/compositions derived from the tags\n"
    "- music_prompt: Suno-compatible music prompt (20-30 words) matching the mood of the tags\n"
    "- thumbnail_text: short punchy text overlay for the thumbnail (3-7 words, ALL CAPS, "
    "derived from the positive prompt atmosphere — e.g. \"MIDNIGHT STUDY VIBES\" or \"GOLDEN HOUR FOCUS\")\n"
    "- youtube_title: SEO-optimized YouTube title (60 chars max) including mood/atmosphere keywords "
    "derived from the tags and positive_prompt style\n"
    "- youtube_description: 150-200 word YouTube description with relevant keywords derived from scene themes; "
    "include 2-3 paragraph breaks; end with a call to subscribe\n"
    "- youtube_tags: JSON array of exactly 15-20 SEO tags derived from the tags input and generated content; "
    "mix broad (lofi study, study with me) and specific (rainy day studying, cozy study session)\n\n"
    "Return JSON only. No markdown."
)


class PromptGenerator:
    """Generate SDXL and Suno prompts via Claude (Anthropic) or OpenAI fallback.

    Priority: ANTHROPIC_API_KEY → OPENAI_API_KEY
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._anthropic_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._openai_key = os.environ.get("OPENAI_API_KEY")
        self._model = model

        if not self._anthropic_key and not self._openai_key:
            raise PromptGenerationError(
                "Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY is set"
            )

    def generate(self, tags: str, profile_style: str) -> dict:
        """Generate a full prompt payload from user tags and profile style."""
        if self._anthropic_key:
            return self._generate_claude(tags, profile_style)
        return self._generate_openai(tags, profile_style)

    def _generate_claude(self, tags: str, profile_style: str) -> dict:
        """Generate prompts via Anthropic Claude API."""
        import anthropic

        client = anthropic.Anthropic(api_key=self._anthropic_key)
        model = self._model or "claude-sonnet-4-20250514"

        try:
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                system=_SYSTEM_PROMPT.format(profile_style=profile_style),
                messages=[{
                    "role": "user",
                    "content": _USER_PROMPT.format(tags=tags, profile_style=profile_style),
                }],
            )
            content = response.content[0].text
            data = self._parse_json(content)
        except PromptGenerationError:
            raise
        except Exception as e:
            raise PromptGenerationError(f"Claude API error: {e}") from e

        self._validate(data)
        return data

    def _generate_openai(self, tags: str, profile_style: str) -> dict:
        """Generate prompts via OpenAI (fallback)."""
        import openai

        client = openai.OpenAI(api_key=self._openai_key)
        model = self._model or "gpt-4o-mini"

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT.format(profile_style=profile_style)},
                    {"role": "user", "content": _USER_PROMPT.format(tags=tags, profile_style=profile_style)},
                ],
                temperature=0.8,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            data = json.loads(content)
        except Exception as e:
            raise PromptGenerationError(f"OpenAI API error: {e}") from e

        self._validate(data)
        return data

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Extract JSON from Claude response (may have markdown fences)."""
        # Strip markdown code fences if present
        cleaned = re.sub(r"```json\s*", "", text)
        cleaned = re.sub(r"```\s*$", "", cleaned)
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise PromptGenerationError(f"Invalid JSON in response: {e}") from e

    @staticmethod
    def _validate(data: dict) -> None:
        """Validate response has all required keys and correct structure."""
        missing = _REQUIRED_KEYS - data.keys()
        if missing:
            raise PromptGenerationError(f"Missing keys: {sorted(missing)}")

        templates = data["scene_templates"]
        if not isinstance(templates, list):
            raise PromptGenerationError(
                f"scene_templates must be a list, got {type(templates).__name__}"
            )
        if len(templates) != _SCENE_TEMPLATE_COUNT:
            raise PromptGenerationError(
                f"scene_templates must have {_SCENE_TEMPLATE_COUNT} items, got {len(templates)}"
            )

        ytags = data.get("youtube_tags", [])
        if not isinstance(ytags, list):
            raise PromptGenerationError(
                f"youtube_tags must be a list, got {type(ytags).__name__}"
            )
        if not (15 <= len(ytags) <= 20):
            raise PromptGenerationError(
                f"youtube_tags must have 15-20 items, got {len(ytags)}"
            )

    @staticmethod
    def _build_profile_style(config: "PipelineConfig") -> str:
        return config.video.style_prompt


# Module-level alias so callers can import _validate directly
_validate = PromptGenerator._validate

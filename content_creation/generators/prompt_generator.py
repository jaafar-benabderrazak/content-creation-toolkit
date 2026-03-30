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
    "thumbnail_prompt",
    "youtube_title",
    "youtube_description",
    "youtube_tags",
}
_SCENE_TEMPLATE_COUNT = 8

_SYSTEM_PROMPT = (
    "You are a world-class AI content director who creates viral YouTube video concepts. "
    "You combine deep expertise in Stable Diffusion XL prompt engineering, YouTube SEO, "
    "music mood design, and thumbnail psychology. "
    "Your prompts produce photorealistic, cinematic, emotionally resonant imagery. "
    "Style: {profile_style}. "
    "Return only valid JSON — no markdown fences, no explanation, no commentary."
)

_USER_PROMPT = (
    "Theme tags: {tags}\n"
    "Visual style: {profile_style}\n\n"
    "Generate a JSON object with ALL of these keys:\n\n"
    "1. **positive_prompt** (60-100 words): A master SDXL prompt that creates a single stunning hero image. "
    "Structure: [subject] + [environment details] + [lighting] + [atmosphere] + [camera/lens] + [quality boosters]. "
    "Use specific photography terms (f/1.4, 35mm, golden hour, chiaroscuro). "
    "Include texture words (grain, bokeh, haze). "
    "End with quality tags: masterpiece, best quality, 8k, photorealistic, award-winning photography.\n\n"
    "2. **negative_prompt** (8-12 terms): SDXL-optimized rejection terms. "
    "Focus on style-breaking elements for this aesthetic — not generic SD1.5 anatomy lists. "
    "Include: quality issues (blurry, overexposed, flat), style breaks (cartoon, anime, 3d render), "
    "and mood breaks specific to the theme.\n\n"
    "3. **scene_templates** (exactly 8 items, 50-70 words each): Eight distinct cinematic moments from the SAME location. "
    "Each must differ in: camera angle (wide/close/overhead/low), time of day (dawn/golden hour/dusk/night), "
    "and focal element (detail shot vs establishing shot). "
    "Use film language: tracking shot, rack focus, dolly zoom, crane shot. "
    "Each template should feel like a different frame from a film, not a different location.\n\n"
    "4. **music_prompt** (25-40 words): A Suno AI music prompt. "
    "Specify: genre, tempo (BPM), instruments, mood adjectives, and what to avoid. "
    "Example: 'lofi hip hop, 72 BPM, warm piano chords, vinyl crackle, soft rain, mellow bass, no vocals, study focus'\n\n"
    "5. **thumbnail_text** (3-5 words, ALL CAPS): Punchy, curiosity-driving text for YouTube thumbnail overlay. "
    "Use power words that stop scrolling: SECRET, HIDDEN, ULTIMATE, PERFECT, MIDNIGHT, GOLDEN. "
    "Must be readable at small size.\n\n"
    "6. **thumbnail_prompt** (40-60 words): An img2img enhancement prompt specifically for the thumbnail. "
    "Make it more dramatic than the video: boost contrast, add dramatic rim lighting, enhance depth, "
    "increase visual impact. The thumbnail should be the most visually striking frame — "
    "punchier colors, stronger composition, more dramatic than any video frame.\n\n"
    "7. **youtube_title** (50-65 chars): SEO-optimized title using this formula: "
    "[Atmosphere] + [Location/Theme] + [Benefit/Use Case]. "
    "Include 1-2 high-search-volume keywords. Use pipes | or dashes — for separation. "
    "Must trigger curiosity.\n\n"
    "8. **youtube_description** (200-300 words, 4-5 paragraphs): "
    "Para 1: Hook — what the viewer will experience (sensory, emotional). "
    "Para 2: Scene description — paint the visual journey through the video. "
    "Para 3: Use case — who this is for (studying, working, relaxing, sleeping). "
    "Para 4: Technical — what makes this special (AI-generated, 4K, original music). "
    "Para 5: CTA — subscribe, like, comment what they want next. "
    "Naturally embed 5-8 SEO keywords throughout.\n\n"
    "9. **youtube_tags** (exactly 18 tags): Mix of: "
    "3 broad (study with me, lofi, ambient), "
    "5 medium (cozy study room, rain sounds study), "
    "5 specific (cyberpunk server room study, underground lofi beats), "
    "5 long-tail (4 hour study music no ads, relaxing rain sounds for sleeping). "
    "All lowercase.\n\n"
    "Return JSON only."
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
        if not (10 <= len(ytags) <= 25):
            raise PromptGenerationError(
                f"youtube_tags must have 10-25 items, got {len(ytags)}"
            )

    @staticmethod
    def _build_profile_style(config: "PipelineConfig") -> str:
        return config.video.style_prompt


# Module-level alias so callers can import _validate directly
_validate = PromptGenerator._validate

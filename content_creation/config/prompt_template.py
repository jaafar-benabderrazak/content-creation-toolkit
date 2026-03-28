from __future__ import annotations

from typing import Any, Dict, Tuple


class _StrictFormatMap(dict):
    """Raises ValueError on missing key instead of KeyError."""

    def __missing__(self, key: str) -> str:
        raise ValueError(f"Unresolved template variable: {{{key}}}")


class PromptTemplate:

    @staticmethod
    def render(template: str, context: Dict[str, Any], quality_suffix: str = "") -> str:
        """Substitute variables in *template* using *context* and append *quality_suffix*.

        Parameters
        ----------
        template:
            A format string using ``{variable}`` placeholders.
        context:
            Mapping from variable name to replacement value.
        quality_suffix:
            Optional quality tag string (e.g. ``"masterpiece, 8k"``).  When
            non-empty it is appended to the resolved prompt as ``", {suffix}"``.

        Returns
        -------
        str
            Fully resolved prompt string.

        Raises
        ------
        ValueError
            If *template* contains a placeholder whose key is not present in
            *context*.  The message includes the variable name so callers can
            pinpoint the missing field without inspecting the full template.
        """
        resolved = template.format_map(_StrictFormatMap(context))
        if quality_suffix:
            resolved = f"{resolved}, {quality_suffix}"
        return resolved


def build_compel_prompt(
    prompt: str,
    negative: str,
    pipeline: Any,
) -> Tuple[Any, Any, Any, Any]:
    """Build compel conditioning tensors for SDXL prompt weighting.

    Parameters
    ----------
    prompt:
        Positive prompt string, may include compel weight syntax
        e.g. ``"(warm lighting)1.3"``.
    negative:
        Negative prompt string.
    pipeline:
        A ``StableDiffusionXLPipeline`` instance (or mock).  Must expose
        ``tokenizer``, ``tokenizer_2``, ``text_encoder``, ``text_encoder_2``.

    Returns
    -------
    tuple
        ``(conditioning, pooled, negative_conditioning, negative_pooled)``

    Raises
    ------
    ImportError
        When ``compel`` is not installed.
    """
    try:
        from compel import Compel, ReturnedEmbeddingsType
    except ImportError:
        raise ImportError("compel>=2.0.2 required: pip install compel")

    compel_proc = Compel(
        tokenizer=[pipeline.tokenizer, pipeline.tokenizer_2],
        text_encoder=[pipeline.text_encoder, pipeline.text_encoder_2],
        returned_embeddings_type=ReturnedEmbeddingsType.PENULTIMATE_HIDDEN_STATES_NON_NORMALIZED,
        requires_pooled=[False, True],
    )
    conditioning, pooled = compel_proc(prompt)
    negative_conditioning, negative_pooled = compel_proc(negative)
    return conditioning, pooled, negative_conditioning, negative_pooled

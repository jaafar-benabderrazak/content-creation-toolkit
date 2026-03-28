"""Tests for PromptTemplate.render() and build_compel_prompt()."""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# PromptTemplate.render() — happy path
# ---------------------------------------------------------------------------


def test_render_substitutes_two_variables():
    from config.prompt_template import PromptTemplate

    result = PromptTemplate.render("{subject}, {style}", {"subject": "study room", "style": "lofi"})
    assert result == "study room, lofi"


def test_render_plain_prompt_no_variables():
    from config.prompt_template import PromptTemplate

    result = PromptTemplate.render("plain prompt no vars", {})
    assert result == "plain prompt no vars"


def test_render_appends_quality_suffix_when_non_empty():
    from config.prompt_template import PromptTemplate

    result = PromptTemplate.render("{subject}", {"subject": "test"}, quality_suffix="masterpiece, 8k")
    assert result == "test, masterpiece, 8k"


def test_render_no_suffix_when_empty_string():
    from config.prompt_template import PromptTemplate

    result = PromptTemplate.render("{subject}", {"subject": "desk"}, quality_suffix="")
    assert result == "desk"


def test_render_multiple_variables_with_suffix():
    from config.prompt_template import PromptTemplate

    result = PromptTemplate.render(
        "{positive_prompt}, {weather}, {time_of_day}, cinematic composition",
        {
            "positive_prompt": "cozy study room",
            "weather": "rainy",
            "time_of_day": "evening",
        },
        quality_suffix="masterpiece, best quality, 8k, photorealistic",
    )
    assert result == (
        "cozy study room, rainy, evening, cinematic composition, "
        "masterpiece, best quality, 8k, photorealistic"
    )


# ---------------------------------------------------------------------------
# PromptTemplate.render() — error contract
# ---------------------------------------------------------------------------


def test_render_raises_value_error_on_unresolved_variable():
    """Missing key must raise ValueError, not KeyError."""
    from config.prompt_template import PromptTemplate

    with pytest.raises(ValueError) as exc_info:
        PromptTemplate.render("{subject}, {weather}", {"subject": "desk"})

    assert "weather" in str(exc_info.value)


def test_render_raises_value_error_not_key_error():
    from config.prompt_template import PromptTemplate

    with pytest.raises(ValueError):
        PromptTemplate.render("{missing}", {})


def test_render_error_message_contains_variable_name():
    from config.prompt_template import PromptTemplate

    with pytest.raises(ValueError, match="Unresolved template variable"):
        PromptTemplate.render("{some_var}", {})


def test_render_error_names_the_missing_key():
    from config.prompt_template import PromptTemplate

    with pytest.raises(ValueError) as exc_info:
        PromptTemplate.render("{alpha}, {beta}", {"alpha": "ok"})

    assert "beta" in str(exc_info.value)


# ---------------------------------------------------------------------------
# PromptTemplate.render() — quality_suffix interaction with SDXLSettings
# ---------------------------------------------------------------------------


def test_render_uses_quality_suffix_from_sdxl_settings():
    """quality_suffix from SDXLSettings is passed through render() without modification."""
    from config.pipeline_config import SDXLSettings
    from config.prompt_template import PromptTemplate

    sdxl = SDXLSettings(
        negative_prompt="cartoon, anime",
        quality_suffix="masterpiece, best quality, 8k, photorealistic",
    )
    result = PromptTemplate.render("{subject}", {"subject": "cozy room"}, quality_suffix=sdxl.quality_suffix)
    assert result == "cozy room, masterpiece, best quality, 8k, photorealistic"


def test_render_no_suffix_when_sdxl_quality_suffix_is_empty():
    from config.pipeline_config import SDXLSettings
    from config.prompt_template import PromptTemplate

    sdxl = SDXLSettings(negative_prompt="cartoon", quality_suffix="")
    result = PromptTemplate.render("{subject}", {"subject": "room"}, quality_suffix=sdxl.quality_suffix)
    assert result == "room"


# ---------------------------------------------------------------------------
# build_compel_prompt() — mock-based tests (no real pipeline / GPU)
# ---------------------------------------------------------------------------


def _make_mock_pipeline() -> MagicMock:
    """Return a mock object that mimics the SDXL pipeline attributes used by build_compel_prompt."""
    pipeline = MagicMock()
    pipeline.tokenizer = MagicMock()
    pipeline.tokenizer_2 = MagicMock()
    pipeline.text_encoder = MagicMock()
    pipeline.text_encoder_2 = MagicMock()
    return pipeline


def test_build_compel_prompt_returns_four_tuple():
    """With compel mocked, build_compel_prompt must return a 4-tuple."""
    mock_tensor = MagicMock()

    # Build a minimal fake compel module
    fake_compel_mod = types.ModuleType("compel")

    class FakeReturnedEmbeddingsType:
        PENULTIMATE_HIDDEN_STATES_NON_NORMALIZED = "penultimate"

    fake_compel_proc = MagicMock()
    fake_compel_proc.return_value = (mock_tensor, mock_tensor)

    FakeCompel = MagicMock(return_value=fake_compel_proc)
    fake_compel_mod.Compel = FakeCompel
    fake_compel_mod.ReturnedEmbeddingsType = FakeReturnedEmbeddingsType

    with patch.dict(sys.modules, {"compel": fake_compel_mod}):
        from importlib import reload
        import config.prompt_template as pt_module
        reload(pt_module)

        result = pt_module.build_compel_prompt("warm study room", "cartoon, anime", _make_mock_pipeline())

    assert isinstance(result, tuple)
    assert len(result) == 4


def test_build_compel_prompt_raises_import_error_when_compel_missing():
    """When compel is not installed, build_compel_prompt must raise ImportError with install hint."""
    with patch.dict(sys.modules, {"compel": None}):
        from importlib import reload
        import config.prompt_template as pt_module
        reload(pt_module)

        with pytest.raises(ImportError, match="compel>=2.0.2 required"):
            pt_module.build_compel_prompt("prompt", "negative", _make_mock_pipeline())

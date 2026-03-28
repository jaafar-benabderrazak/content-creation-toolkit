# Coding Conventions

**Analysis Date:** 2026-03-28

## Naming Patterns

**Files:**
- Lowercase with underscores: `study_with_me_generator.py`, `animate_scenes.py`, `simple_image_generator.py`
- Descriptive names indicating purpose and domain
- Main scripts use full names: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`, `opencv_study_generator.py`

**Functions:**
- snake_case for all function definitions: `create_gradient_background()`, `add_study_elements()`, `generate_study_images()`, `apply_parallax_effect()`
- Descriptive action verbs as prefix: `create_`, `generate_`, `apply_`, `enhance_`, `load_`, `save_`
- Private/internal functions use leading underscore (not observed in this codebase)

**Variables:**
- snake_case for variables: `output_dir`, `image_paths`, `scene_data`, `total_seconds`, `device`
- Config objects use PascalCase: `VideoConfig`, `AudioConfig`, `EffectsConfig`, `Style`, `RenderCfg`, `BotCfg`
- Module-level constants use UPPER_CASE: `STUDY_SCENES`, `ENHANCED_SCENES`, `STYLE_VARIATIONS`, `WEATHER_EFFECTS`

**Types:**
- Type hints used throughout with `typing` imports: `List`, `Optional`, `Dict`, `Tuple`, `Union`
- Dataclass decorators for configuration objects: `@dataclass`
- Return type annotations on functions: `-> Image.Image`, `-> List[Path]`, `-> AudioSegment`

## Code Style

**Formatting:**
- No linter config detected (no `.eslintrc`, `.flake8`, `.pylintrc`, `.pyproject.toml`)
- Implicit standard Python formatting (PEP 8 guidelines followed loosely)
- 80-120 character line lengths observed
- 4-space indentation throughout

**Linting:**
- No linting tools configured
- Code style consistency varies across files
- Some files use emoji in comments/docstrings for visual clarity (not recommended but present)

## Import Organization

**Order:**
1. `from __future__ import annotations` (compatibility shim)
2. System/stdlib imports: `os`, `sys`, `json`, `time`, `argparse`, `subprocess`, `re`, `math`, `random`, `string`, `logging`, `uuid`, `io`, `base64`
3. Third-party library imports: `numpy`, `PIL/Pillow`, `torch`, `diffusers`, `moviepy`, `pydub`, `requests`, `yaml`, `tqdm`, `cv2`
4. Conditional/optional imports wrapped in try-except: `openai.OpenAI`, `elevenlabs.ElevenLabs`
5. Local module imports (rare)

**Path Aliases:**
- Not used. All imports are direct module paths.

**Patterns:**
- Large try-except blocks for optional dependencies: See `animate_scenes.py` lines 16-56 and `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` lines 70-79
- Environment variable checks before imports: `os.environ["XFORMERS_DISABLED"] = "1"` before import statements

## Error Handling

**Patterns:**
- Try-except with graceful fallbacks common, especially for optional libraries and resource loading
- Example in `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` lines 276-282: Font loading with fallback to default
- Direct RuntimeError raises for API/configuration failures: `raise RuntimeError("ELEVEN_API_KEY not set")`
- Logging used for warnings: `logging.warning(f"ElevenLabs TTS unavailable ({e})")`
- Exception messages include context about what failed and suggested fixes

**Strategies:**
- Conditional feature availability: Check if library imported successfully before using it
- Fallback mechanisms for AI models when primary fails
- Default/minimal implementations for missing dependencies

## Logging

**Framework:** `logging` module (standard library)

**Patterns:**
- Basic setup: `logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")`
- Used for informational steps: Progress tracking, model loading, dependency checks
- Print statements mixed with logging (no strict separation)
- Emoji used in print statements for visual distinction: `print("✅ Success")`, `print("❌ Error")`

**Where:**
- Dependency installation and testing: `fix_dependencies.py`
- Model initialization: `animate_scenes.py` lines 14-56
- Pipeline steps: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` lines 118-119

## Comments

**When to Comment:**
- Docstrings used for module and class documentation
- Section headers with ASCII art: `# ---- Enhanced Configuration --------------------------------------------------`
- Inline comments sparse, mostly for complex logic or workarounds
- Comments explain why, not what code does

**JSDoc/TSDoc:**
- Python docstrings used for functions and classes
- Simple format: Single or multi-line description
- Example in `study_with_me_generator.py` lines 62-75: Dataclass with inline documentation

**Style:**
```python
@dataclass
class VideoConfig:
    """Enhanced video generation configuration"""
    duration_minutes: int = 120
    fps: int = 30
```

## Function Design

**Size:** 20-100+ lines observed. Larger functions for complex algorithms (e.g., `create_study_image()` combines multiple operations)

**Parameters:**
- Mix of positional and keyword arguments
- Config objects passed as single parameter to reduce argument count
- Type hints on all parameters

**Return Values:**
- Single object returns common: `Image.Image`, `AudioSegment`, `List[Path]`
- Tuple returns for coordinate/position data: `Tuple[int, int]`
- Optional returns for fallback scenarios

## Module Design

**Exports:**
- No explicit `__all__` definitions found
- All top-level functions/classes are public
- Dataclasses for configuration bundling

**Barrel Files:**
- Not used. Single-file scripts dominate the codebase.
- No package structure beyond flat directory layout.

**Structure:**
- Monolithic scripts: Each `.py` file is standalone and runnable
- Configuration at top: Dataclass definitions before logic
- Helper functions grouped by functionality
- Main execution logic at bottom with `if __name__ == "__main__":` guard

**Example hierarchy in `study_with_me_generator.py`:**
1. Imports and compatibility fixes (lines 1-60)
2. Configuration dataclasses (lines 62-95)
3. Scene definitions (lines 97-200)
4. Helper/utility functions (image gen, audio, effects, transitions)
5. Main pipeline functions
6. Entry point with argument parsing

---

*Convention analysis: 2026-03-28*

# Codebase Structure

**Analysis Date:** 2026-03-28

## Directory Layout

```
content_creation/
├── study_with_me_generator.py       # Main study video pipeline (2H+ ambient videos)
├── faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py  # TikTok tutorial bot
├── animate_scenes.py                # Stable Video Diffusion animation from images
├── opencv_with_ai_images.py         # Study video with AI-generated backgrounds
├── opencv_study_generator.py        # Study video with procedural backgrounds
├── simplified_study_generator.py    # Lightweight study video generator
├── simple_image_generator.py        # Single/batch image generation
├── test_ai_generation.py            # Quick generation test script
├── fix_dependencies.py              # Dependency installation helper
│
├── AnimateDiff/                     # AnimateDiff model and UI
│   ├── app.py                       # Gradio web interface
│   ├── train.py                     # Model training script
│   ├── animatediff/                 # Core AnimateDiff implementation
│   │   ├── data/
│   │   │   └── dataset.py           # WebVid10M dataset loader
│   │   ├── models/
│   │   │   ├── motion_module.py     # Temporal transformer modules
│   │   │   ├── unet.py              # 3D UNet model
│   │   │   ├── attention.py         # 3D attention mechanisms
│   │   │   └── resnet.py            # Inflated convolutions
│   │   ├── pipelines/
│   │   │   └── pipeline_animation.py # Diffusion inference pipeline
│   │   └── utils/
│   │       └── util.py              # Utilities (model loading, saving)
│   ├── scripts/
│   │   └── animate.py               # CLI animation generation
│   ├── configs/                     # YAML model configs
│   ├── models/                      # Model checkpoint storage
│   └── __assets__/                  # Documentation and demo assets
│
├── study_assets/                    # Example output structure
│   └── images/                      # Generated scene images
├── test_assets/                     # Test generation outputs
│   └── images/
├── preview_enhanced_assets/         # Preview/demo assets
│   └── images/
├── video_assets/                    # Legacy video generation assets
│   └── images/
├── generated/                       # Generated output files
├── study_with_me_generator.ipynb    # Jupyter notebook version
│
├── swm/                             # Python venv (study_with_me)
├── study_env_311/                   # Python venv (study environment)
├── study_video_env/                 # Python venv (legacy)
│
├── .planning/
│   └── codebase/                    # GSD documentation
│       ├── ARCHITECTURE.md
│       └── STRUCTURE.md
│
└── [Various video/asset files]      # Generated MP4s, PNGs from runs
```

## Directory Purposes

**Root Python Scripts:**
- Purpose: Entry points for specific content generation tasks
- Contains: Complete, standalone pipelines with argparse CLI
- Execution: `python {script_name}.py --arg1 value1 --arg2 value2`

**AnimateDiff/:**
- Purpose: Video animation from static images using motion modules
- Contains: Custom diffusion pipeline + training infrastructure
- Key files: `app.py` (UI), `train.py` (training), `scripts/animate.py` (CLI)

**AnimateDiff/animatediff/:**
- Purpose: Core AnimateDiff model implementation
- Contains: Temporal transformer, 3D UNet, dataset loader
- Architecture: Models → Pipelines → Utils structure

**Asset Directories (study_assets/, test_assets/, etc):**
- Purpose: Store generated images/videos from specific runs
- Contains: `.png` images, `.mp4` video files, sometimes temporary files
- Generated: Yes (not committed)
- Committed: Some preview examples only

**Virtual Environments (swm/, study_env_311/, etc):**
- Purpose: Isolated Python dependency installations
- Generated: Yes, created by `python -m venv`
- Committed: No (excluded via .gitignore)

## Key File Locations

**Entry Points:**

- `study_with_me_generator.py`: Primary study video pipeline with 2H+ ambient videos, AI images, music, effects
- `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`: TikTok tutorial bot with script generation, voiceover, posting
- `AnimateDiff/app.py`: Web UI for video animation (Gradio)
- `AnimateDiff/scripts/animate.py`: CLI for video animation

**Core Models:**

- `AnimateDiff/animatediff/models/motion_module.py`: Temporal transformer for video animation
- `AnimateDiff/animatediff/models/unet.py`: 3D UNet encoder-decoder
- `AnimateDiff/animatediff/pipelines/pipeline_animation.py`: Diffusion inference orchestration

**Configuration:**

- Script headers: Dataclass definitions (`VideoConfig`, `AudioConfig`, `EffectsConfig`, `Style`, etc)
- `AnimateDiff/configs/`: YAML model configuration files
- Scene definitions: `ENHANCED_SCENES` array in `study_with_me_generator.py` (lines 99-172)
- Style variations: `STYLE_VARIATIONS` array in `study_with_me_generator.py` (lines 174-181)

**Utilities & Helpers:**

- `AnimateDiff/animatediff/utils/util.py`: Model loading, weight conversion, video saving
- `fix_dependencies.py`: Dependency installation utility
- `test_ai_generation.py`: Quick validation script

## Naming Conventions

**Files:**

- `{domain}_{task}_generator.py`: Full pipeline scripts (study, opencv, simplified)
- `{platform}_fully_automated_python_pipeline.py`: End-to-end bot scripts (TikTok)
- `animate_{task}.py`: Animation/scene scripts
- Snake case: All file names

**Directories:**

- `{service}_assets/`: Asset output directories (study_assets, test_assets)
- `{service}_env/`: Python virtual environments (study_env_311)
- Lowercase with underscores

**Functions:**

- `generate_{output_type}()`: Generation functions (generate_images_enhanced_sd, generate_enhanced_music)
- `create_{output_type}()`: Creation/composition functions (create_study_video, create_fallback_image)
- `apply_{effect_name}()`: Effect functions (apply_parallax_effect, apply_blur_transition)
- `{action}_{target}()`: Generic operations (save_progress, load_progress, add_audio_to_video)
- Snake case: All function names

**Classes:**

- `{Task}Config`: Configuration dataclasses (VideoConfig, AudioConfig, EffectsConfig)
- `{Platform}{Task}`: Model/component classes (StableDiffusionAnimator, AnimationPipeline)
- PascalCase: All class names

**Variables:**

- `{domain}_config`: Configuration instances (video_config, audio_config, effects_config)
- `{output_type}_path`: File path variables (audio_path, out_path, img_dir)
- Snake case: All variable names

## Where to Add New Code

**New Study Video Feature:**
- Primary code: `study_with_me_generator.py`
- Configuration: Add to `VideoConfig`, `AudioConfig`, or `EffectsConfig` dataclass
- Scene definitions: Add to `ENHANCED_SCENES` array (around line 99)
- Effect functions: Add new `apply_{effect_name}()` function (after line 485)

**New TikTok Generation Step:**
- Implementation: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`
- Config: Add fields to `Style`, `BotCfg`, or `RenderCfg` dataclass
- Helper: Add function before `build_one()` (around line 576)

**New Animation Feature:**
- Model changes: `AnimateDiff/animatediff/models/`
- Pipeline changes: `AnimateDiff/animatediff/pipelines/pipeline_animation.py`
- CLI: `AnimateDiff/scripts/animate.py`
- UI: `AnimateDiff/app.py`

**Utilities & Shared Helpers:**
- Location depends on scope:
  - Single script: Add function to that script file
  - Multi-script reuse: Create `utils.py` or `helpers.py` at root level
  - Model utilities: `AnimateDiff/animatediff/utils/util.py`

**Test Scripts:**
- Location: Root level with `test_` prefix
- Example: `test_ai_generation.py` (line 1)

## Special Directories

**Generated Assets Directories:**
- `study_assets/`, `test_assets/`, `video_assets/`, `preview_enhanced_assets/`
- Purpose: Output storage for generated images and videos
- Generated: Yes (created by pipeline runs)
- Committed: No (likely in .gitignore), except preview examples
- Structure: Each contains `images/` subdirectory

**.planning/codebase/:**
- Purpose: GSD orchestrator documentation
- Generated: No (manually written by GSD mapper)
- Committed: Yes

**Virtual Environments:**
- `swm/`, `study_env_311/`, `study_video_env/`
- Purpose: Isolated Python dependency installations
- Generated: Yes (created by `python -m venv`)
- Committed: No (excluded via .gitignore)
- Activation: `source {dir}/bin/activate` (Linux/Mac) or `{dir}\Scripts\activate` (Windows)

## Work Directory Conventions

Generated assets create work directories relative to output:
- Output: `/path/to/output.mp4`
- Work directory: `/path/to/output_enhanced_assets/`
- Image storage: `/path/to/output_enhanced_assets/images/`
- Audio storage: `/path/to/output_enhanced_assets/audio/` (if generated)
- Progress tracking: `/path/to/output_enhanced_assets/progress.json`

Example from `study_with_me_generator.py` lines 866-869:
```python
work_dir = args.out.parent / f"{args.out.stem}_enhanced_assets"
img_dir = work_dir / "images"
audio_path = work_dir / "enhanced_music.wav"
```

---

*Structure analysis: 2026-03-28*

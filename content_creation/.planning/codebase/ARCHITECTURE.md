# Architecture

**Analysis Date:** 2026-03-28

## Pattern Overview

**Overall:** Content generation pipeline with modular task composition

**Key Characteristics:**
- Standalone Python scripts for specific content types (study videos, TikTok tutorials, animation)
- Sequential data flow: generation → processing → rendering → output
- External API integrations (OpenAI, ElevenLabs, TikTok, Hugging Face)
- Configuration-driven behavior via dataclasses and CLI arguments
- Progress tracking and resumable operations

## Layers

**Content Definition Layer:**
- Purpose: Define visual/audio/textual content specifications
- Location: Configuration dataclasses at script headers and scene definitions
- Contains: Scene prompts, mood definitions, style variations, weather effects
- Depends on: None
- Used by: Generation layer

**AI Generation Layer:**
- Purpose: Generate images, audio, and text using external models
- Location: `study_with_me_generator.py`, `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`, `animate_scenes.py`, `simple_image_generator.py`
- Contains: Diffusion pipeline initialization, API calls, model loading
- Depends on: torch, diffusers, transformers, OpenAI SDK, ElevenLabs SDK
- Used by: Processing and composition layers

**Processing Layer:**
- Purpose: Apply effects, enhance quality, and transform generated content
- Location: Helper functions throughout scripts (`enhance_image_quality`, `apply_parallax_effect`, `apply_dynamic_lighting`, `auto_subtitles_from_audio`)
- Contains: Image enhancement, audio processing, effect application
- Depends on: PIL, pydub, numpy, MoviePy
- Used by: Composition layer

**Composition Layer:**
- Purpose: Assemble processed elements into final video output
- Location: `build_enhanced_video`, `assemble_video`, `create_study_video` functions
- Contains: Clip creation, transition application, audio attachment, rendering
- Depends on: MoviePy, FFmpeg
- Used by: Output layer

**Output Layer:**
- Purpose: Write video files and manage external posting
- Location: `write_videofile()` calls and `tiktok_direct_post()` function
- Contains: File I/O, codec configuration, TikTok API posting
- Depends on: MoviePy, requests library
- Used by: CLI main functions

## Data Flow

**Study Video Generation (study_with_me_generator.py):**

1. Parse CLI arguments and load/create VideoConfig, AudioConfig, EffectsConfig
2. Create output work directories (`{out_path}_enhanced_assets`)
3. Generate AI images using Stable Diffusion XL
   - Load model and optimize for device (CUDA/CPU)
   - Apply scene-specific prompts with style variations
   - Post-process images for quality enhancement
4. Generate ambient music using Stable Audio
   - Segment generation with crossfading
   - Audio processing: EQ, compression, normalization
5. Build video composition:
   - Create enhanced image clips with parallax, lighting, time progression effects
   - Apply animated transitions (slide, zoom, blur)
   - Add animated timer overlay
6. Render final video with quality-based codec settings
7. Save progress at each major step (enables resumption)

**TikTok Tutorial Pipeline (faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py):**

1. Generate tutorial script from topic using OpenAI
   - Extract title, bullets, call-to-action, hashtags
2. Synthesize voiceover audio
   - Primary: OpenAI TTS
   - Fallback: ElevenLabs TTS
3. Create poster image:
   - Generate or load background
   - Compose title and bullet text with shadows/styling
4. Auto-generate subtitles:
   - Speech-to-text on voiceover audio
   - Create SRT file aligned with audio timing
5. Assemble final video:
   - Layer: background image clip + subtitle overlay + voiceover audio
   - Apply fade transitions
6. Build caption and hashtags from script
7. Post to TikTok (optional) via Content Posting API

**State Management:**

Progress tracked via JSON file at `{work_dir}/progress.json`:
```json
{
  "image_generation": {
    "completed": true,
    "timestamp": 1711606800,
    "data": { "image_count": 24, "paths": [...] }
  },
  "audio_generation": { ... },
  "video_composition": { ... }
}
```

Resumable operations check progress file before re-running expensive steps.

## Key Abstractions

**VideoConfig:**
- Purpose: Centralize video rendering parameters
- Location: `study_with_me_generator.py` lines 62-76
- Pattern: Dataclass with preset mappings (1080p, 720p, 480p)
- Used in: `build_enhanced_video()`, codec settings calculations

**AudioConfig:**
- Purpose: Centralize audio generation quality parameters
- Location: `study_with_me_generator.py` lines 78-86
- Pattern: Dataclass with quality preset variants
- Used in: `generate_enhanced_music()`, segment generation loops

**EffectsConfig:**
- Purpose: Control visual effect toggles and parameters
- Location: `study_with_me_generator.py` lines 89-95
- Pattern: Dataclass with boolean flags and strength parameters
- Used in: Effect application functions throughout clip processing

**Style (TikTok):**
- Purpose: Encapsulate poster composition dimensions and fonts
- Location: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` lines 82-95
- Pattern: Dataclass with font paths, colors, shadow settings
- Used in: `compose_poster()`, `draw_text_block()`

## Entry Points

**Study Video Generator:**
- Location: `study_with_me_generator.py`
- Triggers: CLI with `--out` flag (required)
- Responsibilities: Parse config, orchestrate generation/processing/composition pipeline, manage resumable progress

**TikTok Pipeline:**
- Location: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`
- Triggers: CLI with topic(s) or `--from-file` flag
- Responsibilities: Script generation, voiceover synthesis, poster composition, video assembly, optional posting

**Animation Pipeline:**
- Location: `AnimateDiff/app.py` (Gradio UI), `AnimateDiff/scripts/animate.py` (CLI)
- Triggers: Web UI or command-line arguments
- Responsibilities: Load motion modules, initialize animation pipeline, generate video from static image

## Error Handling

**Strategy:** Try-except with fallbacks and graceful degradation

**Patterns:**

Image generation failures → Fallback color/gradient image:
```python
try:
    image = pipe(prompt=full_prompt, ...)
except Exception as e:
    print(f"[ERROR] Failed to generate image: {e}")
    path = create_fallback_image(scene_data, i, config.image_size, out_dir)
```

Audio generation → Skip audio or continue without:
```python
try:
    audio_clip = AudioFileClip(str(audio_path))
    final_video = final_video.set_audio(audio_clip)
except Exception as e:
    print(f"[Warning] Failed to attach audio: {e}")
```

OpenAI/API unavailable → Template-based script generation:
```python
def generate_tutorial_script(topic: str, client: Optional[OpenAI]) -> dict:
    if client is None:
        return {
            "title": topic,
            "bullets": [f"Tip {i+1}: {topic}" for i in range(3)],
            "cta": "Learn more today!"
        }
```

## Cross-Cutting Concerns

**Logging:**
- Approach: Print statements with prefix tags (`[SD]`, `[Music]`, `[Video]`, `[ERROR]`)
- Pattern: `print(f"[{TAG}] {message}")` for traceability

**Validation:**
- Input validation: CLI argument parsing with type coercion
- Configuration validation: Implicit via dataclass field types
- Model availability: Try/except imports with fallback mechanisms

**Device Management:**
- Pattern: Check `torch.cuda.is_available()` at initialization
- CUDA fallback: Automatic CPU mode with warnings
- Memory optimization: `pipe.enable_model_cpu_offload()`, VAE slicing, attention slicing

**File Organization:**
- Pattern: Create work directories relative to output path
- Convention: `{output_path}_enhanced_assets/images/`, `{output_path}_enhanced_assets/audio/`
- Progress tracking: `progress.json` at work directory root

---

*Architecture analysis: 2026-03-28*

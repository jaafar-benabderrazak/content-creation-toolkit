# Technology Stack

**Analysis Date:** 2026-03-28

## Languages

**Primary:**
- Python 3.10+ - All source code and scripts

**Secondary:**
- YAML - Configuration files (setup.py configs, pipeline configs)

## Runtime

**Environment:**
- CPython 3.10+ (tested on 3.13)
- Platform: Windows 11 (primary), Linux compatible

**Package Manager:**
- pip - Python package management
- Lockfile: Not detected (no requirements.txt in root, only in AnimateDiff/)

## Frameworks

**Video Generation:**
- MoviePy 1.0.x - Core video editing and composition (`study_with_me_generator.py`, `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`)
- OpenCV (cv2) - Video codec handling and frame processing (`opencv_with_ai_images.py`, `opencv_study_generator.py`)

**Image Generation & Deep Learning:**
- Stable Diffusion (diffusers 0.11.1+) - Image generation via `StableDiffusionPipeline`, `StableDiffusionXLPipeline`
- PyTorch 2.3.1+ (CUDA-compatible) - Deep learning inference
- TorchVision 0.18.1 - Image utilities
- TorchAudio 2.8.0 - Audio processing for models
- Transformers 4.25.1+ - Tokenizers and model loading

**Audio Generation & Processing:**
- Stable Audio Tools - AI music generation with conditioning (`study_with_me_generator.py` line 374)
- pydub 0.25.x+ - Audio segment manipulation (crossfading, normalization, compression)
- FFmpeg - External dependency for audio/video codec handling

**UI/Interactive:**
- Gradio 3.36.1 - Web interface for AnimateDiff pipeline (AnimateDiff/requirements.txt)

**Optimization & ML Infrastructure:**
- xformers 0.0.27 - Memory-efficient attention mechanisms for diffusers
- einops - Tensor dimension manipulation for audio/video processing
- omegaconf 2.3.0 - Configuration management
- accelerate - Distributed training utilities
- safetensors - Safe model weight loading

**Monitoring & Experiment Tracking:**
- Weights & Biases (wandb) - Model training tracking

**Testing & Utilities:**
- decord 0.6.0 - Video decoding (AnimateDiff)
- imageio 0.4.9 - Image I/O operations
- imageio-ffmpeg 0.4.9 - FFmpeg integration for imageio
- tqdm - Progress bars
- numpy - Array operations
- Pillow (PIL) - Image manipulation
- requests - HTTP client for API calls
- pyyaml - YAML parsing

**Third-party API SDKs:**
- OpenAI - ChatGPT/GPT-4 for script generation, TTS (`faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`)
- ElevenLabs - Text-to-speech with voice cloning fallback

## Key Dependencies

**Critical (Pinned Versions):**
- torch==2.3.1 - GPU inference stability
- torchvision==0.18.1 - Paired with torch version
- diffusers==0.11.1 (AnimateDiff) or 0.26.3 - Stable Diffusion pipeline
- transformers==4.25.1 - BERT/CLIPTokenizer compatibility
- xformers==0.0.27 - Memory optimization for inference

**Infrastructure:**
- moviepy - Video composition and frame sequencing
- pydub - Audio segment operations
- opencv-python - FFmpeg integration and codec support
- Pillow - Image post-processing and rendering

**AI/ML Inference:**
- diffusers - Diffusion model inference (SDXL, Stable Video)
- stable-audio-tools - Audio generation conditioning
- transformers - Model tokenizers and embeddings

## Configuration

**Environment:**
- No `.env` detected - API keys passed via environment variables
- Expects: `OPENAI_API_KEY`, `ELEVEN_API_KEY`, `TIKTOK_ACCESS_TOKEN` (in TikTok pipeline)
- GPU auto-detection: Uses CUDA if available, falls back to CPU

**Build:**
- No build config files detected
- Scripts run directly with `python script.py` or `python -m jupyter`
- Dependency isolation via Python venv (mentioned in `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` docstring)

## Platform Requirements

**Development:**
- Python 3.10+ with pip
- FFmpeg system package (required by MoviePy and pydub)
- CUDA Toolkit 11.8+ for GPU acceleration (optional but strongly recommended)
- GPU: NVIDIA with 4GB+ VRAM (6GB+ for SDXL models)

**Production:**
- Local execution on GPU-capable machine
- No cloud deployment detected
- Video generation: 2+ hours for 120-minute study videos on consumer GPUs

## Inference Models

**Pre-trained Models (Hugging Face Hub):**
- `stabilityai/stable-diffusion-xl-base-1.0` - SDXL image generation (1024x1024)
- `stabilityai/stable-diffusion-3.5-large` - Higher quality image generation
- `stabilityai/stable-video-diffusion-img2vid-xt` - Video animation from images
- `stabilityai/stable-audio-open-1.0` or `-small` - Music generation
- CLIP tokenizers and embeddings (auto-downloaded)

**GPU Memory Requirements:**
- SDXL: 6GB+ (with optimizations: `enable_model_cpu_offload()`, `enable_vae_slicing()`)
- Stable Audio: 4GB+
- Fallback to CPU if VRAM insufficient (slow)

---

*Stack analysis: 2026-03-28*

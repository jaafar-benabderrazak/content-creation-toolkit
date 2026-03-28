# External Integrations

**Analysis Date:** 2026-03-28

## APIs & External Services

**Content Generation:**
- OpenAI (ChatGPT/GPT-4)
  - What it's used for: Script generation for tech/AI tutorials, optional TTS
  - SDK/Client: `openai` (official Python SDK)
  - Auth: Environment variable `OPENAI_API_KEY`
  - Implementation: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` lines 72-74
  - Endpoint: `OpenAI.chat.completions.create()` for prompt-based script generation

**Audio/Voice Services:**
- ElevenLabs
  - What it's used for: Natural TTS with voice cloning capabilities (fallback from OpenAI TTS)
  - SDK/Client: `elevenlabs` Python SDK
  - Auth: Environment variable `ELEVEN_API_KEY`
  - Implementation: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py` lines 76-79
  - Fallback: Used when OpenAI TTS fails or for voice variety

**Social Media Distribution:**
- TikTok Content Posting API
  - What it's used for: Direct video publishing to TikTok with captions and hashtags
  - SDK/Client: HTTP requests (custom REST client, no official SDK used)
  - Auth: OAuth access token in `TIKTOK_ACCESS_TOKEN` (requires `video.publish` scope)
  - Implementation: `faceless_tech_ai_tik_tok_fully_automated_python_pipeline.py`
  - Requirements: TikTok Developer app registration, audit for public visibility
  - Endpoints: TikTok's `/v1/video/post/publish` (implied from code comments)

## Data Storage

**Databases:**
- None detected - Pipeline is file-based

**File Storage:**
- Local filesystem only
  - Generated images: `./generated/scene_*.jpg`
  - Generated videos: `./out/*.mp4`
  - Temporary files: `./tmp/` (audio, intermediate frames, metadata)
  - Assets: `./assets/` (background images, music, overlays)
  - Configuration: Pipeline configs stored as JSON/YAML in-memory

**Caching:**
- Hugging Face Hub cache (`~/.cache/huggingface/`)
  - Pre-trained diffusion models cached after first download
  - CLIP tokenizers cached locally
  - Stable Audio model weights cached

## Authentication & Identity

**Auth Provider:**
- Custom (OAuth for TikTok, API keys for OpenAI/ElevenLabs)
  - OpenAI: API key authentication
  - ElevenLabs: API key authentication
  - TikTok: OAuth 2.0 bearer token with `video.publish` scope
  - Implementation: Environment variable retrieval in scripts

**Token Management:**
- No token refresh mechanism detected
- Tokens passed directly via environment variables
- No session management (stateless API calls)

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry, Rollbar, etc.)
- Logging via Python `logging` module and print statements

**Logs:**
- Console output to stdout/stderr
- Suggested cron logging: `>> /var/log/tiktok_bot.log 2>&1` (from docstring)
- Progress tracking: `tqdm` progress bars for generation loops
- No structured logging (JSON, ELK stack, CloudWatch)

## CI/CD & Deployment

**Hosting:**
- Local execution only (no cloud deployment detected)
- Designed for cron scheduling (daily execution example in docstring)

**CI Pipeline:**
- None detected
- Manual execution via Python scripts

**Scheduling:**
- Cron job example: `30 18 * * * /usr/bin/python /path/to/tiktok_ai_tutorial_bot.py --from-file /path/to/topics.txt --count 1 --post`
- No job queue (e.g., Celery, RQ)

## Environment Configuration

**Required env vars:**
- `OPENAI_API_KEY` - OpenAI API authentication
- `ELEVEN_API_KEY` - ElevenLabs API authentication (optional, fallback if missing)
- `TIKTOK_ACCESS_TOKEN` - TikTok OAuth token (only if `--post` flag used)

**Optional env vars:**
- `HUGGINGFACE_HOME` - Custom HF model cache location (defaults to `~/.cache/huggingface/`)
- `CUDA_VISIBLE_DEVICES` - GPU device selection for PyTorch
- `TORCH_HOME` - PyTorch model cache location

**Secrets location:**
- Environment variables (recommended for production)
- Hardcoded in scripts only during development (not committed)
- No `.env` file tracking detected

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- TikTok video publish callback (implicit in POST request)
- No webhook delivery confirmation or retry logic detected

## Model Management

**Model Sources:**
- Hugging Face Hub (primary source)
  - `stabilityai/stable-diffusion-xl-base-1.0`
  - `stabilityai/stable-video-diffusion-img2vid-xt`
  - `stabilityai/stable-audio-open-1.0`
  - Models auto-downloaded on first use

**Model Loading:**
- Lazy loading from `diffusers` library
- GPU memory optimization via:
  - `enable_model_cpu_offload()` - Offload model to CPU between inference steps
  - `enable_vae_slicing()` - Process large images in chunks
  - `enable_attention_slicing()` - Memory-efficient attention

**Inference Configuration:**
- SDXL: 35 steps (high quality), 25 steps (medium), 15 steps (fast)
- Guidance scale: 8.0 (high quality), 7.5 (medium), 7.0 (fast)
- Negative prompt: Standard quality filters
- Seed: Fixed seed (42 + index) for reproducibility

## Rate Limiting & Quotas

**OpenAI:**
- Subject to OpenAI API rate limits and account quotas
- Token-based billing (GPT-4 more expensive than GPT-3.5)

**ElevenLabs:**
- Subject to ElevenLabs API rate limits
- Character-based billing for TTS

**TikTok:**
- Rate limits on video publish endpoint (exact limits not specified in code)
- Audit requirement for automated posting

## Data Flow

**Study Video Generation Pipeline:**
1. Scene prompts → Stable Diffusion SDXL (image generation) → PIL post-processing
2. Images → Stable Video Diffusion (optional animation) → MoviePy/OpenCV composition
3. Audio tracks → Stable Audio generation or file loading → pydub processing (normalization, EQ, compression)
4. Images + audio + text overlays → MoviePy composition → MP4 output

**TikTok Posting Pipeline:**
1. OpenAI generates script → ElevenLabs TTS (or OpenAI TTS) → pydub audio processing
2. Script → PIL caption rendering onto video frames
3. Generated video + captions + hashtags → TikTok API `/video/post/publish`

---

*Integration audit: 2026-03-28*

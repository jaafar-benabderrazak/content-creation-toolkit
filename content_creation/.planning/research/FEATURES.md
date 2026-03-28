# Feature Research

**Domain:** AI content generation pipeline — prompt engineering, music generation, quality presets, image caching
**Researched:** 2026-03-28
**Confidence:** MEDIUM (codebase patterns HIGH; Suno API status LOW due to no official public API)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any serious AI generation pipeline must have. Missing these = the tool feels like a prototype.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Per-scene positive prompt templates | Hardcoded prompts produce identical images; scene variation is the baseline user expectation | LOW | Codebase already has per-scene dict with `"prompt"` keys; needs extraction to config/YAML |
| Negative prompt support | SDXL without negatives produces artifacts (watermarks, bad anatomy, jpeg noise); users expect clean outputs | LOW | Codebase has a single inline negative string; needs to become configurable |
| Quality preset tiers (low/medium/high) | Speed vs quality trade-off is a day-one need; no preset = users tweak inference params manually | LOW | `quality_preset` field already exists in `VideoConfig` and `AudioConfig`; needs to gate all generation params uniformly |
| Instrumental-only music | Vocal tracks clash with study/ambient video content; vocal music is the wrong default | LOW | Suno supports instrumental mode via `make_instrumental` flag in third-party wrappers |
| Deterministic output path (cache key) | Re-running a pipeline that regenerates unchanged scenes is unusable for iteration | MEDIUM | Requires content-hash of prompt + seed + model params per scene |
| Music duration matching video length | Music that ends before video or loops awkwardly breaks the product | MEDIUM | Suno v5 supports up to 8 min; `extend_audio` endpoint chains segments for longer durations |

---

### Differentiators (Competitive Advantage)

Features that put this pipeline ahead of a manual Stable Diffusion + Suno workflow.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Profile-matched prompt templates | "lofi" profile auto-selects warm bokeh scenes; "cinematic" selects dramatic lighting — no manual prompt tuning per video type | MEDIUM | Requires a prompt library keyed by profile slug; templates parameterized with time-of-day, weather, scene type slots |
| Negative prompt library by category | Categorized negatives (anatomy, quality, watermark, NSFW) that can be composed by preset tier — high preset adds anatomy fixes, fast preset skips them | LOW | Per-SDXL-model tuning: SDXL needs shorter negatives than SD 1.5; EasyNegative embedding covers quality tokens in a single token |
| Smart scene caching (skip-if-unchanged) | If a scene's prompt + seed + quality preset hasn't changed, skip generation and reuse cached PNG — cuts re-run time from 15 min to 2 min | MEDIUM | Hash = SHA256(prompt + negative_prompt + seed + steps + cfg_scale + model_id); store in `.cache/images/{hash}.png` |
| Multi-track Suno generation with selection | Generate 2-3 candidate tracks, persist all, allow selection before video compilation — avoids re-generation lottery | MEDIUM | Suno API returns multiple `clips`; store all, add `selected_track_index` to config |
| Profile-matched Suno genre tags | "lofi" profile → `"lofi hip hop, piano, rain, 70 bpm"`; "cinematic" → `"orchestral, dramatic, no vocals, 120 bpm"` — no manual tag entry | LOW | Maps profile slug to Suno `tags` parameter string; lives in profile YAML |
| Quality preset affecting all generation axes | Single `quality_preset=high` sets: SDXL steps=40, cfg=7.5, SDXL resolution=1024, Suno output=WAV, video CRF=18 — not just one param | MEDIUM | Requires a `QualityProfile` dataclass that all generators read from; prevents drift where image is high quality but audio is low quality |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Suno official API integration presented as stable | Suno is the best-quality music generator; devs want clean SDK | Suno has **no official public API** as of 2026-03-28. Every wrapper is reverse-engineered from browser sessions, violates ToS, and can break without notice | Use third-party wrapper (gcui-art/suno-api or piapi.ai) but wrap in an abstraction layer with a fallback to Stable Audio; document the ToS risk explicitly |
| Long negative prompt lists copied from SD 1.5 guides | More negatives = more control (intuition) | SDXL handles anatomy better natively; SD 1.5 negative lists applied to SDXL thin out "avoidance energy" and degrade quality. Each extra token dilutes guidance | Cap negative prompts at 10-15 tokens for SDXL; use EasyNegative embedding for quality baseline |
| Per-frame image generation | Maximum scene variation | 30 frames/sec × N minutes = thousands of SDXL inference calls; completely unworkable locally | Generate 1 image per scene (10-15 scenes per video); animate with parallax/Ken Burns in Remotion |
| Real-time image preview in Gradio during generation | Better UX | GPU is occupied during generation; Gradio streaming of diffusion progress requires significant threading complexity for marginal value | Show progress bar with step count; show final image when done |
| Automatic genre detection from script content | Zero-config music | Requires an LLM call to classify script mood, adds latency and another API call, fails on short scripts | Profile-matched genre tags in YAML are explicit, predictable, and work offline |

---

## Feature Dependencies

```
[Quality Preset Tiers]
    └──gates──> [SDXL inference params (steps, cfg, resolution)]
    └──gates──> [Suno output format (MP3 vs WAV)]
    └──gates──> [Video encoder params (CRF, bitrate)]

[Prompt Template Library]
    └──requires──> [Profile system (existing: pipeline_config.py)]
                       └──requires──> [Profile YAML schema (existing: Phase 1 output)]

[Negative Prompt Library]
    └──enhances──> [Prompt Template Library] (same call site, composed together)

[Smart Image Caching]
    └──requires──> [Prompt Template Library] (need stable prompt string to hash)
    └──requires──> [Quality Preset Tiers] (preset must be part of cache key)

[Suno Integration]
    └──requires──> [Profile-Matched Genre Tags] (otherwise generation is unguided)
    └──requires──> [Duration-Aware Generation] (Suno v5 max 8min; long videos need segment chaining)

[Multi-Track Selection]
    └──requires──> [Suno Integration]
    └──enhances──> [Profile-Matched Genre Tags] (generates N candidates per genre config)
```

### Dependency Notes

- **Smart caching requires stable prompt strings:** Prompts must be fully resolved (template vars substituted, style appended) before hashing. Hashing the template key is wrong — different profiles expand to different prompts.
- **Quality preset must be a single source of truth:** If `steps` is set in three places (VideoConfig, AudioConfig, CLI arg), presets drift. Introduce a `QualityProfile` lookup dict that all generators read.
- **Suno integration is not a hard dependency for music:** The existing Stable Audio path must remain as fallback. Suno ToS risk means the integration could break. Abstraction layer is not optional.

---

## MVP Definition

This is a subsequent milestone (v1.1), not a greenfield MVP. "Launch with" = what ships in this milestone.

### Ship in v1.1

- [ ] **Prompt template library in YAML/JSON** — extract hardcoded scene prompts from `study_with_me_generator.py` into profile-specific template files; parameterize with `style`, `time_of_day`, `weather` slots
- [ ] **Negative prompt config** — move inline negative string to profile YAML; add category-based composition (quality + anatomy tiers per quality preset)
- [ ] **Quality preset as unified gate** — `QualityProfile` dataclass controls SDXL steps/cfg/resolution + Suno format + video CRF from one config value
- [ ] **Smart image cache (hash-based skip)** — SHA256(prompt + seed + steps + cfg + model_id) → `.cache/images/{hash}.png`; skip generation if file exists
- [ ] **Suno integration with instrumental enforcement** — third-party wrapper; `make_instrumental=True`; genre tags from profile YAML; fallback to Stable Audio on failure
- [ ] **Profile-matched Suno genre tags** — `lofi`, `cinematic`, `electronic` profiles each define a `music_tags` string in YAML

### Add After Validation (v1.2+)

- [ ] **Multi-track generation with selection** — generate 2-3 Suno candidates, persist all, expose selection in Gradio UI; trigger: cache fills up with unusable single-track generations
- [ ] **Duration-aware segment chaining** — for videos >8 minutes, chain Suno `extend_audio` calls; trigger: first long-form video exceeds 8 min

### Future Consideration (v2+)

- [ ] **FLUX model support** — FLUX.2 Pro/Dev as SDXL alternative; FLUX uses natural-language prompts (full sentences), not keyword stacks; requires different template format
- [ ] **Per-scene negative prompt override** — some scenes (outdoor, no people) don't need anatomy negatives; adds config complexity; defer until base library is established
- [ ] **Negative embedding support (EasyNegative)** — single-token quality baseline; requires embedding file management and ComfyUI-style loading; low ROI vs explicit token list for v1.1

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Prompt template library (YAML extraction) | HIGH | LOW | P1 |
| Negative prompt config | HIGH | LOW | P1 |
| Quality preset unified gate | HIGH | LOW | P1 |
| Smart image cache | HIGH | MEDIUM | P1 |
| Suno integration + instrumental | HIGH | MEDIUM | P1 |
| Profile-matched genre tags | MEDIUM | LOW | P1 |
| Multi-track Suno selection | MEDIUM | MEDIUM | P2 |
| Duration-aware segment chaining | LOW | HIGH | P2 |
| FLUX model support | MEDIUM | HIGH | P3 |
| Negative embedding (EasyNegative) | LOW | MEDIUM | P3 |

---

## Competitor Feature Analysis

Reference tools analyzed for pattern discovery (not direct competitors — this is a local single-creator tool):

| Feature | ComfyUI workflows | A1111 (WebUI) | This project's approach |
|---------|-------------------|---------------|-------------------------|
| Prompt templates | JSON workflow files; PromptStylers extension for style injection | Prompt presets saved per checkpoint | YAML profile files keyed by profile slug; profile auto-selects scene templates |
| Negative prompts | `easy_negative` node; embedding support (`embedding:EasyNegative`) | Negative embedding via textual inversion; preset negative text per checkpoint | Config field per profile; category composition (quality + anatomy) gated by quality preset |
| Quality presets | Sampler/steps nodes with named workflows | `--quality` CLI flag maps to steps; checkpoint-specific configs | Single `QualityProfile` dataclass consumed by all generators |
| Image caching | ComfyUI caches node outputs by content hash natively | No native caching; re-generates on every run | Explicit SHA256 per-scene cache in `.cache/images/`; checked before every `pipe()` call |
| Music generation | ACE-Step / MusicGen nodes in ComfyUI | No native audio; separate tool | Suno via third-party wrapper with Stable Audio fallback |

---

## Sources

- Codebase: `study_with_me_generator.py` — existing scene dict structure, inline negative prompt, `quality_preset` field (HIGH confidence)
- Codebase: `config/pipeline_config.py` — `style_prompt`, `music_prompt`, `quality_preset` fields (HIGH confidence)
- SDXL negative prompt best practices: [Stable Diffusion Negative Prompts Guide](https://freeaipromptmaker.com/blog/2025-11-29-stable-diffusion-negative-prompts-guide), [SDXL Best Practices](https://neurocanvas.net/blog/sdxl-best-practices-guide/), [Negative Prompts 2026](https://www.aiphotogenerator.net/blog/2026/02/negative-prompts-stable-diffusion-guide) (MEDIUM confidence — multiple sources agree)
- Suno API status: [AI/ML API — Suno API Reality](https://aimlapi.com/blog/the-suno-api-reality), [gcui-art/suno-api GitHub](https://github.com/gcui-art/suno-api), [Suno API Review 2026](https://evolink.ai/blog/suno-api-review-complete-guide-ai-music-generation-integration) (MEDIUM confidence — no official API confirmed by multiple sources; feature capabilities LOW confidence as third-party wrappers can diverge)
- Suno v5 capabilities: [Suno AI Guide 2026](https://aitoolsdevpro.com/ai-tools/suno-guide/), [AI/ML API Suno Review](https://aimlapi.com/blog/suno-api-review) (LOW confidence — third-party summaries, not official docs)
- Prompt template patterns: [LTX Studio Prompt Guide](https://ltx.studio/blog/ai-image-prompt-guide), [Upsampler Prompt Guide](https://upsampler.com/blog/ai-image-generation-prompt-guide) (LOW confidence — pattern discovery only)
- ComfyUI prompt systems: [ComfyUI PromptStylers](https://github.com/wolfden/ComfyUi_PromptStylers), [ComfyUI Wiki — Prompt Techniques](https://comfyui-wiki.com/en/interface/prompt) (MEDIUM confidence)
- Image caching patterns: No authoritative source found for hash-based scene caching in Python SDXL pipelines. Pattern derived from ComfyUI's native node caching behavior + general content-addressable storage patterns. (LOW confidence — flag for phase-specific research)
- MusicGen inference params: [HuggingFace MusicGen docs](https://huggingface.co/docs/transformers/main/model_doc/musicgen), [AWS MusicGen inference](https://aws.amazon.com/blogs/machine-learning/inference-audiocraft-musicgen-models-using-amazon-sagemaker/) (HIGH confidence for MusicGen; not directly applicable to Suno)

---

*Feature research for: AI generation quality — prompt engineering, music, quality presets, image caching*
*Researched: 2026-03-28*

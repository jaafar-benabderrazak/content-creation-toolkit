# Pitfalls Research

**Domain:** AI content generation pipeline — music API integration, SDXL prompt engineering, image caching
**Researched:** 2026-03-28
**Confidence:** MEDIUM (Suno API unofficial status makes official docs unavailable; SDXL and caching patterns are HIGH confidence from verified sources)

## Critical Pitfalls

### Pitfall 1: Suno Has No Official Public API — Every Wrapper Is a Reverse-Engineered ToS Violation

**What goes wrong:**
All third-party "Suno API" packages (gcui-art/suno-api, sunoapi.org, apiframe.ai, AIML API) work by reverse-engineering Suno's private web endpoints. There is no officially published developer API. Any change Suno makes to its web frontend can silently break integrations with zero notice, no changelog, and no migration path. The integration can go from working to dead overnight.

**Why it happens:**
Suno's developer-facing marketing material implies API access exists. Search results surface third-party wrappers as if they are official. Developers assume "Suno API" is a real product.

**How to avoid:**
- Pick one third-party wrapper and version-lock it (`==` not `>=` in requirements)
- Wrap ALL Suno calls in a single `SunoClient` class so the swap surface is one file, not scattered across the pipeline
- Build against a stable third-party provider (AIML API, apiframe.ai) rather than the raw gcui-art wrapper — providers absorb breakage faster
- Write integration tests that hit a local mock, not Suno directly, so pipeline CI does not depend on external availability
- Design the music layer with a swappable interface from day one: `generate_music(prompt, duration, genre) -> AudioSegment` — if Suno breaks, the swap cost is one implementation class

**Warning signs:**
- HTTP 403 or 429 responses that previously worked
- `session_id` or cookie-related authentication errors in the wrapper
- Changelog silence from the wrapper repo while issues pile up

**Phase to address:**
Suno integration phase. Establish the abstraction boundary before writing any Suno-specific code. Test the fallback (silence or pre-bundled track) before shipping.

---

### Pitfall 2: Instrumental Mode Is Not Guaranteed — Vocal Bleed Will Contaminate Study Videos

**What goes wrong:**
Suno's `make_instrumental=True` flag reduces vocal probability but does not enforce silence. Vocal artifacts ("humming," ambient vocal pads, mumbled phrases) regularly appear even with the flag set. For study content where silence or purely ambient music is the product promise, any vocal bleed is a direct quality defect visible to viewers.

**Why it happens:**
The model does not separate vocal from instrumental at generation time — it generates a single audio stream that statistically leans instrumental. There is no post-processing isolation step. The hit rate for truly clean instrumentals is ~70-80% per generation.

**How to avoid:**
- Always generate 2-3 tracks per request and select the cleanest one programmatically or via listening pass
- Run a basic vocal detection heuristic on generated output before accepting it (librosa pitch detection or a lightweight classifier)
- Keep a bank of 3-5 pre-validated fallback tracks per genre profile for when generation fails the quality check
- Expose track selection to the human approval gate in Discord/Slack — include audio preview URLs in the notification

**Warning signs:**
- Single-track generation with no selection step in the implementation
- No audio validation before the track gets handed to the video assembly pipeline
- Approval gate that shows video preview but not the isolated audio

**Phase to address:**
Suno integration phase. Build track selection and validation before connecting to video pipeline.

---

### Pitfall 3: Async Polling Without Timeout Bounds Hangs the Entire Pipeline

**What goes wrong:**
Suno generation is async: the API returns a task ID immediately, then the caller polls a status endpoint until `complete`. If polling is implemented naively (tight loop or no max-wait), a failed generation (status stuck at `processing`) hangs the pipeline indefinitely. On a 2-4 hour video generation run, a hung music step that never resolves kills the whole job.

**Why it happens:**
Developers implement `while status != "complete": sleep(5)` and ship it. The happy path works. The failure path (Suno server-side error, quota exceeded, timeout on their end) is never tested.

**How to avoid:**
- Implement a hard timeout: `max_poll_attempts = 60` (5-minute wall clock at 5s intervals) with an explicit `TimeoutError` raise
- Use exponential backoff from attempt 3 onward: 5s, 10s, 20s, cap at 60s
- Log every poll attempt with elapsed time — makes debugging hung runs trivial
- Treat timeout as a generation failure, not a crash: fall back to cached track, log warning, continue pipeline

**Warning signs:**
- Poll loop with no `max_attempts` or `timeout` variable
- No logging inside the poll loop
- No test for the `status == "error"` response from the API

**Phase to address:**
Suno integration phase. Timeout and fallback must be implemented before the happy path is considered done.

---

### Pitfall 4: Prompt Hash Cache Key Does Not Include All Generation Parameters — Stale Images Served

**What goes wrong:**
Image caching skips re-generation when a cache hit is found. If the cache key only hashes the scene text prompt but not the quality preset, negative prompt template, SDXL seed, or profile name, then changing any of those parameters will silently serve the old image. The video looks correct locally but contains images generated with the previous profile settings.

**Why it happens:**
Cache key design starts simple: `hash(prompt_text)`. Over time, additional parameters are added to generation but not to the cache key. The bug is invisible — the pipeline reports "cache hit, skipping" and the developer assumes that is correct behavior.

**How to avoid:**
Build the cache key as a hash of a normalized dict containing every parameter that affects the output:
```python
import hashlib, json

def make_cache_key(prompt: str, negative_prompt: str, quality_preset: str,
                   profile: str, seed: int | None) -> str:
    params = {
        "prompt": prompt.strip().lower(),
        "negative_prompt": negative_prompt.strip().lower(),
        "quality_preset": quality_preset,
        "profile": profile,
        "seed": seed,
        "model": "sdxl-base-1.0",  # bump this string when upgrading models
    }
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
```
Store the full parameter dict alongside the cached image in a JSON sidecar so cache entries are human-inspectable.

**Warning signs:**
- Cache key is just `hash(scene["prompt"])`
- No sidecar metadata file next to cached images
- No way to force-invalidate cache for a specific profile without wiping everything
- Images look slightly wrong after a profile tweak but the pipeline reports 100% cache hits

**Phase to address:**
Image caching phase. Design the key schema before writing the first cache write path.

---

### Pitfall 5: Negative Prompt Templates That Work for SD1.5 Break SDXL Quality

**What goes wrong:**
Developers port existing negative prompt strings from SD1.5 workflows into SDXL. SDXL has substantially better anatomy and coherence out of the box, so aggressive SD1.5-era negative prompts ("bad anatomy, extra limbs, malformed hands, fused fingers, ...") actively suppress stylistic variation and produce sterile, over-constrained output. Study video backgrounds become bland and repetitive.

**Why it happens:**
SD1.5 negative prompt template collections are widely shared and reused. SDXL-specific guidance is less discoverable. The mistake is hard to see without A/B comparison.

**How to avoid:**
- SDXL negative prompts should be short and style-focused, not anatomy-focused: `"cartoon, anime, 3d render, watermark, logo, text"`
- Profile-specific negative prompts should only add terms that conflict with the profile's aesthetic intent (e.g., for `lofi` profile: add `"harsh lighting, clinical, sterile"`)
- Never copy-paste an SD1.5 mega-negative-prompt into SDXL templates
- Test each profile's positive+negative combination with 5 sample generations before locking the template

**Warning signs:**
- Negative prompt longer than 30 tokens for SDXL
- Negative prompt includes anatomy terms (`bad hands`, `extra fingers`) in profiles that don't generate people
- All profiles share an identical negative prompt string with no profile-specific tuning

**Phase to address:**
SDXL prompt engineering phase. Template design must include validation images for each profile before the template is committed to YAML config.

---

### Pitfall 6: Replacing Stable Audio Without Preserving the AudioSegment Contract Breaks Downstream Callers

**What goes wrong:**
`generate_enhanced_music()` currently returns a `pydub.AudioSegment`. If Suno integration returns a file path (string) or raw bytes instead, every downstream caller (`crossfade`, `mix_with_video`, `audio validation`, etc.) breaks silently at runtime, often producing silent audio or crashes during video assembly.

**Why it happens:**
Suno APIs return an audio URL, not raw audio. Developers fetch the URL and store the file path, then forget to convert to `AudioSegment` before returning. The contract divergence is not caught until assembly.

**How to avoid:**
- Define an explicit interface contract: `generate_music(...) -> AudioSegment` — any Suno implementation must convert the downloaded file before returning
- Write a unit test that asserts the return type before the Suno integration is merged
- The existing `generate_enhanced_music` signature is the right model — preserve it as the interface, implement Suno behind it

**Warning signs:**
- Suno integration function returns `str` (path) or `bytes`
- No type annotation on the music generation function
- Download and return are handled in the same function without a conversion step

**Phase to address:**
Suno integration phase. The existing function signature is already correct — protect it with a type annotation and a test.

---

### Pitfall 7: Profile-to-Genre Mapping Hard-Coded In Logic Instead of Config — Unmaintainable

**What goes wrong:**
`if profile == "lofi": genre = "lofi hip hop"` blocks proliferate across the pipeline. Adding a new profile or changing a genre mapping requires code changes. The existing codebase already has this problem with style variations (`STYLE_VARIATIONS`, `WEATHER_EFFECTS`) hardcoded in the generator. Repeating the pattern for music genre mapping compounds the problem.

**Why it happens:**
Quick implementation shortcuts. Config-driven design requires more upfront structure.

**How to avoid:**
- Genre mapping belongs in the YAML profile config (already designed in v1.1 requirements)
- Profile config should contain: `music.genre`, `music.tempo_hint`, `music.style_tags` as explicit fields
- Suno prompt construction reads these fields — no conditionals in Python for per-profile logic
- New profile = new YAML entry, zero code change

**Warning signs:**
- `if profile ==` anywhere in the music generation code path
- Genre strings hardcoded in Python rather than loaded from config
- Style tags for Suno constructed with string concatenation in the generator function

**Phase to address:**
SDXL prompt engineering phase (establish config-driven template pattern) before the Suno integration phase (apply same pattern to music).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single cache key from prompt text only | Fast to implement | Silent stale images after any parameter change | Never — always include all generation parameters |
| Suno integration directly in the generator file | No new files needed | Swap cost is high when Suno breaks; untestable in isolation | Never — always isolate in a client class |
| Polling without timeout in async generation | Simpler code | Pipeline hangs permanently on any Suno server-side failure | Never — always bound poll loops |
| Copying SD1.5 negative prompts to SDXL | Existing templates reused | Over-constrained output; bland images | Never — SDXL requires separate template design |
| Return file path from music generator instead of AudioSegment | Avoids extra conversion step | Breaks all downstream callers | Never — contract must match existing interface |
| Per-profile genre mapping in Python if/else | Works immediately | Every new profile requires code change | MVP only if config infrastructure not yet built; must be migrated before ship |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Suno API (any wrapper) | Treating wrapper version as stable; no version pin | Pin exact wrapper version; monitor repo for breaking changes |
| Suno API | Polling without backoff or timeout | Exponential backoff, 5-minute hard timeout, explicit error on timeout |
| Suno API | Single track generation with no quality check | Generate 2-3 tracks, validate for vocal bleed, select best |
| Suno API | Expecting `make_instrumental=True` to be absolute | Treat as probabilistic; add validation step |
| SDXL via diffusers | Loading model fresh on every pipeline run | Model is already loaded once per run in current code — preserve this; do not add a second load for the new prompt system |
| SDXL | Negative prompt from SD1.5 template | SDXL-specific short negative prompts; test per profile |
| Image cache | Cache key from prompt text only | Hash all generation parameters into key |
| Image cache | No cache invalidation path when model changes | Include model version string in cache key; provide `--clear-cache` flag |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching Suno audio URL synchronously in the main generation loop | Pipeline blocks for 2-3 minutes waiting for Suno | Download in background thread; continue other pipeline steps | Every run — latency is 1-3 minutes per generation |
| Generating N images sequentially then checking cache | Cache checked too late; model already loaded | Check cache before loading SDXL model | Already an issue per CONCERNS.md — do not worsen it with new caching code |
| Re-hashing all prompts on every run even when cache is warm | Negligible at 24 images; detectable at 200+ | Cache the hash computation itself in a manifest file | At 100+ images per run |
| Downloading Suno audio file on every test run | Slow tests; Suno quota consumed | Mock the HTTP layer in tests; never hit live API in CI | From the first test run |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Suno API key in .env with no scope restriction | Key can be used for unauthorized generation if .env leaks | Document key rotation procedure; never log the key; add to .gitignore audit |
| User-supplied style prompt passed directly to Suno style tag | Prompt injection; unexpected or policy-violating content generated | Validate style prompt against allowlist or character set before sending; length cap |
| Cached images served without checking if the source profile is still valid | Deleted or renamed profile silently uses stale cache | Cache manifest should record the profile name; invalidate if profile no longer exists |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indication during Suno polling (2-3 min wait) | Pipeline appears frozen; user kills process | Log poll status every 30s: "[Music] Waiting for Suno... (45s elapsed)" |
| Approval gate shows video but not the music track separately | Reviewer cannot evaluate audio quality without watching the whole video | Include direct audio file URL/path in Discord/Slack notification message |
| Cache hit/miss ratio not reported at end of run | User cannot tell if caching is working | Log summary: "Images: 18/24 from cache (6 generated)" at end of image step |
| Vocal bleed discovered after full video render | 2-4 hour run wasted | Validate music before starting video assembly; fail fast |

## "Looks Done But Isn't" Checklist

- [ ] **Suno integration:** Verify `make_instrumental=True` actually produces a vocal-free track — listen to the output, do not just check the flag is set
- [ ] **Async polling:** Verify the poll loop has a hard timeout — read the code, not the tests (tests likely mock the response)
- [ ] **Image cache:** Verify cache key includes negative prompt, quality preset, and profile — print the key for two different presets and confirm they differ
- [ ] **AudioSegment contract:** Verify `generate_music()` returns `pydub.AudioSegment`, not a file path — add a `assert isinstance(result, AudioSegment)` check
- [ ] **Profile-genre mapping:** Verify genre values are read from YAML config, not from Python if/else — grep for `if profile ==` in music generation code
- [ ] **Suno wrapper version:** Verify the wrapper package is pinned to an exact version in requirements.txt — `==` not `>=`
- [ ] **Vocal bleed validation:** Verify there is a validation step between music download and music use in video assembly
- [ ] **Fallback music path:** Verify the pipeline completes successfully when Suno returns an error — test with a mocked failure response

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Suno wrapper breaks due to upstream API change | HIGH | Swap to alternative provider (AIML API / apiframe.ai); update `SunoClient` implementation only; all callers unaffected if abstraction was built |
| Cache serves stale images after parameter change | MEDIUM | Wipe cache directory for affected profile; regenerate; add missing parameters to cache key |
| Hung poll loop discovered in production | LOW | Add timeout + kill-switch; no architecture change needed |
| Vocal bleed in shipped video | HIGH | Manual replacement of audio track in post; implement validation gate to prevent recurrence |
| SD1.5 negative prompts degrading SDXL quality | LOW | Replace template strings in YAML config; regenerate affected images |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Suno unofficial API — breakage risk | Suno integration phase | `SunoClient` abstraction class exists; wrapper version pinned |
| Vocal bleed from instrumental mode | Suno integration phase | Track validation step present; fallback tracks defined |
| Async polling without timeout | Suno integration phase | `max_poll_attempts` variable present in poll loop; timeout raises explicit exception |
| Cache key missing generation parameters | Image caching phase | Cache key function hashes full parameter dict; sidecar JSON written |
| SD1.5 negative prompts used in SDXL | SDXL prompt engineering phase | Per-profile negative prompts in YAML; anatomy terms absent from SDXL profiles |
| AudioSegment contract broken by Suno return | Suno integration phase | Type annotation on `generate_music`; return type assertion in tests |
| Profile-genre mapping hardcoded in Python | SDXL prompt engineering phase (config pattern) | No `if profile ==` in music code; genre read from config object |

## Sources

- [The Suno API Reality — AIML API Blog](https://aimlapi.com/blog/the-suno-api-reality) — unofficial API risks, legal status, wrapper fragility (MEDIUM confidence — authoritative third-party analysis)
- [Suno API Review 2026 — AIML API Blog](https://aimlapi.com/blog/suno-api-review) — rate limits (20 req/10s), polling patterns, generation latency (MEDIUM confidence)
- [gcui-art/suno-api GitHub](https://github.com/gcui-art/suno-api) — most widely used unofficial wrapper (MEDIUM confidence — unofficial tool)
- [Suno Terms of Service](https://suno.com/terms-of-service) — ToS restrictions on commercial use and API access (HIGH confidence — official)
- [How to Write Negative Prompts for SDXL — Layer.ai](https://help.layer.ai/en/articles/8120630-how-to-write-negative-prompts-relevant-for-sdxl-only) — SDXL-specific negative prompt guidance (MEDIUM confidence)
- [SDXL Best Practices — Neurocanvas](https://neurocanvas.net/blog/sdxl-best-practices-guide/) — SDXL prompt structure, negative prompt scope (MEDIUM confidence)
- [Stable Diffusion Prompt Guide — Stable Diffusion Art](https://stable-diffusion-art.com/prompt-guide/) — negative prompt mechanics (MEDIUM confidence)
- [Cache Invalidation Strategies — Cachee.ai](https://cachee.ai/blog/posts/2025-12-20-cache-invalidation-strategies-that-actually-work.html) — cache key design, fingerprint patterns (MEDIUM confidence)
- [Suno AI vocal bleed / instrumental reliability — aimusicservice.com](https://aimusicservice.com/blogs/news/how-to-fix-suno-and-udio-ai-song-mistakes) — documented limitation (LOW confidence — community source)
- `.planning/codebase/CONCERNS.md` — existing codebase bugs and tech debt (HIGH confidence — direct codebase audit)

---
*Pitfalls research for: AI generation quality milestone — Suno API, SDXL prompt engineering, image caching*
*Researched: 2026-03-28*

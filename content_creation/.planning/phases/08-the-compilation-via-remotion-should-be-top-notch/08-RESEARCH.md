# Phase 8: Top-Notch Remotion Video Compilation - Research

**Researched:** 2026-03-28
**Domain:** Remotion 4.x — advanced animations, transitions, typography, audio sync, cinematic effects, render quality
**Confidence:** HIGH (primary claims from official Remotion docs; supplemented by verified web sources)

---

## Summary

The project already has Remotion 4.0.441 installed with two compositions (`StudyVideo` at 1920x1080 and `TechTutorial` at 1080x1920). Both use basic linear `interpolate()` for all motion — no spring physics, no transition library, no text stagger, no audio sync. The current renderer in `shared/remotion_renderer.py` passes props via JSON file and invokes `npx remotion render` with hardcoded `--crf 18`.

Phase 8 upgrades these compositions to professional quality by wiring in `@remotion/transitions` (already installed as a transitive dep, needs explicit install), adding spring-physics motion, per-profile effect sets, dynamic text animations, SVG-based film grain and vignette, audio frequency visualization, and output quality flags tuned for YouTube delivery. The Python renderer bridge must be extended to accept a `profile` prop and quality-tier render arguments.

The key insight is that **all cinematic effects run entirely inside React/Remotion as CSS/SVG** — no external shader pipeline, no FFmpeg LUT post-processing, no additional Python dependencies. The profile system maps directly to Remotion props: the Python side passes `profile: "lofi-study" | "tech-tutorial" | "cinematic"` and the TypeScript compositions switch effect sets accordingly.

**Primary recommendation:** Implement a `profile` prop on both compositions that selects a pre-defined effect bundle (transitions, spring config, typography, overlay intensity). Use `@remotion/transitions` `TransitionSeries` for inter-scene cuts, `spring()` for all enter/exit motion, `@remotion/google-fonts` for typography, SVG `feTurbulence` for film grain, and `@remotion/media-utils` `useAudioData` + `visualizeAudio` for beat visualization. Upgrade `--crf` to 16 for cinematic profile and add `--color-space bt709` to all renders.

---

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| remotion | ^4.0.441 | Frame engine, AbsoluteFill, Sequence, interpolate | Already installed; latest stable |
| @remotion/cli | ^4.0.441 | `npx remotion render` subprocess | Already installed |
| @remotion/renderer | ^4.0.441 | Programmatic render API | Already installed |

### Additions Required
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @remotion/transitions | ^4.0.441 | TransitionSeries, wipe/slide/fade/clockWipe/flip/iris presentations | All inter-scene cuts |
| @remotion/google-fonts | ^4.0.441 | loadFont() for Inter, Space Grotesk, JetBrains Mono, etc. | Typography upgrade |
| @remotion/media-utils | ^4.0.441 | useAudioData, visualizeAudio, visualizeAudioWaveform | Audio visualization |

> **Note:** All @remotion/* packages must be pinned to the exact same version. Remove `^` from version numbers after install to prevent drift.

**Installation:**
```bash
cd remotion
npm install @remotion/transitions@4.0.441 @remotion/google-fonts@4.0.441 @remotion/media-utils@4.0.441
```

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @remotion/google-fonts | @remotion/fonts + local .woff2 | Local fonts work offline and avoid network requests during render; use for production if font caching causes timeouts |
| CSS-based film grain (SVG feTurbulence) | Pre-rendered grain overlay PNG sequence | PNG sequence is faster to composite but adds MB of assets; SVG approach is zero-asset |
| useAudioData (full file) | useWindowedAudioData | useWindowedAudioData is recommended for files >5min; lofi-study audio can be 2h so use windowed version |

---

## Architecture Patterns

### Recommended Project Structure
```
remotion/
├── src/
│   ├── index.ts                    # registerRoot (unchanged)
│   ├── Root.tsx                    # Composition declarations
│   ├── StudyVideo.tsx              # Refactored with profile system
│   ├── TechTutorial.tsx            # Refactored with profile system
│   ├── components/
│   │   ├── TransitionScene.tsx     # Wraps Scene in TransitionSeries.Sequence
│   │   ├── FilmGrain.tsx           # SVG feTurbulence overlay component
│   │   ├── Vignette.tsx            # Radial gradient vignette (extracted)
│   │   ├── Timer.tsx               # Timer with spring pop-in (extracted)
│   │   ├── TextReveal.tsx          # Character/word stagger text component
│   │   └── AudioVisualizer.tsx     # Frequency bar visualizer
│   ├── fonts/
│   │   └── index.ts                # loadFont() calls, exports fontFamily strings
│   └── profiles/
│       ├── index.ts                # Profile type + getProfile() selector
│       ├── lofi-study.ts           # Effect config for lofi-study profile
│       ├── tech-tutorial.ts        # Effect config for tech-tutorial profile
│       └── cinematic.ts            # Effect config for cinematic profile
├── public/                         # Static assets (fonts if using local)
└── package.json
```

### Pattern 1: Profile-Driven Effect Bundles

**What:** A TypeScript object per profile defines all effect parameters: spring config, transition type, overlay intensities, font choices, particle density, grain strength.
**When to use:** Whenever a composition needs to behave differently based on the pipeline's selected profile (lofi-study vs. tech-tutorial vs. cinematic).

```typescript
// Source: pattern derived from Remotion docs on parametrized rendering
// remotion/src/profiles/cinematic.ts
export const cinematicProfile = {
  transition: "wipe" as const,
  transitionDuration: 20,
  springConfig: { damping: 12, stiffness: 80, mass: 1 },
  fontFamily: "Space Grotesk",
  grainIntensity: 0.12,
  vignetteStrength: 0.55,
  timerVisible: false,
  particleDensity: 0,
  sceneHoldMultiplier: 1.0,
};

// remotion/src/profiles/index.ts
export type ProfileName = "lofi-study" | "tech-tutorial" | "cinematic";
export const profiles = { "lofi-study": lofiStudyProfile, "tech-tutorial": techTutorialProfile, cinematic: cinematicProfile };
export const getProfile = (name: ProfileName) => profiles[name];
```

### Pattern 2: TransitionSeries for Inter-Scene Cuts

**What:** Replace the current `Sequence` array in `StudyVideo` with `TransitionSeries` so each scene boundary has a professional transition.
**When to use:** Any time consecutive scenes exist (all Study Video scenes).

```typescript
// Source: https://www.remotion.dev/docs/transitions/transitionseries
import { TransitionSeries, linearTiming, springTiming } from "@remotion/transitions";
import { wipe } from "@remotion/transitions/wipe";
import { slide } from "@remotion/transitions/slide";
import { fade } from "@remotion/transitions/fade";

// Usage inside StudyVideo:
<TransitionSeries>
  {images.map((img, i) => (
    <React.Fragment key={i}>
      <TransitionSeries.Sequence durationInFrames={sceneDurationFrames}>
        <Scene src={img} durationFrames={sceneDurationFrames} profile={profile} />
      </TransitionSeries.Sequence>
      {i < images.length - 1 && (
        <TransitionSeries.Transition
          presentation={wipe({ direction: "from-left" })}
          timing={springTiming({ config: { damping: 200 } })}
        />
      )}
    </React.Fragment>
  ))}
</TransitionSeries>
```

**Available built-in presentations (all from `@remotion/transitions`):**
| Presentation | Import | Direction options |
|---|---|---|
| `fade()` | `@remotion/transitions/fade` | none |
| `wipe()` | `@remotion/transitions/wipe` | from-left, from-right, from-top, from-bottom, from-top-left, from-top-right, from-bottom-left, from-bottom-right |
| `slide()` | `@remotion/transitions/slide` | from-left, from-right, from-top, from-bottom |
| `clockWipe()` | `@remotion/transitions/clock-wipe` | none |
| `flip()` | `@remotion/transitions/flip` | none |
| `iris()` | `@remotion/transitions/iris` | none |
| `none()` | `@remotion/transitions/none` | none |

### Pattern 3: Spring Physics for All Motion

**What:** Replace `interpolate(frame, [...], [...])` enter/exit with `spring()` for organic motion feel.
**When to use:** All element entrances, title slides, bullet reveals, timer pop-in.

```typescript
// Source: https://www.remotion.dev/docs/spring
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

// Replace linear translateY with spring
const progress = spring({
  frame,
  fps,
  config: { damping: 14, stiffness: 120, mass: 1 },
  durationInFrames: 30,
});
const translateY = interpolate(progress, [0, 1], [40, 0]);

// To check when spring settles: measureSpring({ fps, config: { damping: 14 } })
```

**Spring presets by profile:**
- **lofi-study:** `{ damping: 18, stiffness: 100 }` — gentle, slow settle
- **tech-tutorial:** `{ damping: 10, stiffness: 200, overshootClamping: true }` — snappy, no bounce
- **cinematic:** `{ damping: 12, stiffness: 80 }` — subtle overshoot, dramatic

### Pattern 4: Dynamic Text Animation (TextReveal Component)

**What:** Word-by-word stagger reveal using `spring()` per word with configurable delay multiplier.
**When to use:** TechTutorial title and bullets, StudyVideo ambient text overlays.

```typescript
// Source: pattern from Remotion docs on animating properties + spring()
const words = text.split(" ");
return (
  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
    {words.map((word, i) => {
      const wordProgress = spring({
        frame: frame - i * 5, // 5-frame stagger per word
        fps,
        config: { damping: 14, stiffness: 150 },
        durationInFrames: 25,
      });
      return (
        <span
          key={i}
          style={{
            opacity: wordProgress,
            transform: `translateY(${interpolate(wordProgress, [0, 1], [20, 0])}px)`,
            display: "inline-block",
          }}
        >
          {word}
        </span>
      );
    })}
  </div>
);
```

> **Pitfall:** Do NOT use per-character opacity toggling (character visible/hidden). Use `string.slice()` for typewriter effects or spring opacity+translateY for individual word entrances. Per-character opacity causes layout reflow on every frame.

### Pattern 5: Film Grain via SVG feTurbulence

**What:** Animated Perlin noise overlay using SVG filter primitives. The seed changes per frame to animate the grain.
**When to use:** All profiles (intensity varies); renders entirely in-browser without external assets.

```typescript
// Source: feTurbulence MDN + film grain GitHub gist pattern
// remotion/src/components/FilmGrain.tsx
import { AbsoluteFill, useCurrentFrame } from "remotion";

export const FilmGrain: React.FC<{ intensity?: number }> = ({ intensity = 0.08 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: intensity }}>
      <svg width="100%" height="100%" style={{ position: "absolute" }}>
        <filter id={`grain-${frame}`}>
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.65"
            numOctaves="3"
            seed={frame}       // seed change = animated grain
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${frame})`} />
      </svg>
    </AbsoluteFill>
  );
};
```

> **Performance note:** SVG filters are GPU-heavy. For 120-minute StudyVideo renders, gate grain behind profile config. The cinematic profile enables it at 0.12 intensity; lofi-study at 0.05; tech-tutorial at 0.

### Pattern 6: Audio Visualization

**What:** Frequency spectrum bars synced to audio using `useWindowedAudioData` + `visualizeAudio`.
**When to use:** StudyVideo lofi-study profile footer bar, TechTutorial outro.

```typescript
// Source: https://www.remotion.dev/docs/audio/visualization
import { useWindowedAudioData, visualizeAudio } from "@remotion/media-utils";
import { useCurrentFrame, useVideoConfig } from "remotion";

export const AudioVisualizer: React.FC<{ src: string }> = ({ src }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // useWindowedAudioData is recommended for files > 5 minutes (WAV files only)
  const audioData = useWindowedAudioData(src);

  if (!audioData) return null;

  const bars = visualizeAudio({ fps, frame, audioData, numberOfSamples: 32 });

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 40 }}>
      {bars.map((amplitude, i) => (
        <div
          key={i}
          style={{
            width: 4,
            height: amplitude * 40,
            backgroundColor: "rgba(255, 255, 255, 0.4)",
            borderRadius: 2,
          }}
        />
      ))}
    </div>
  );
};
```

> **Critical:** `useWindowedAudioData` only works with WAV files. If audio is MP3, either convert to WAV in the Python pipeline before rendering, or use `useAudioData` (loads full file into memory — acceptable for <5min clips, not for 2-hour study videos).

### Pattern 7: Custom Font Loading

**What:** Load Google Fonts or local fonts with render-blocking to ensure no frame renders without the font present.
**When to use:** All text elements in all compositions.

```typescript
// Source: https://www.remotion.dev/docs/google-fonts/load-font
// remotion/src/fonts/index.ts
import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";

export const { fontFamily: spaceGrotesk } = loadSpaceGrotesk("normal", {
  weights: ["400", "600", "700"],
  subsets: ["latin"],
});

export const { fontFamily: jetBrainsMono } = loadJetBrainsMono("normal", {
  weights: ["400"],
  subsets: ["latin"],
});
```

> `loadFont()` from `@remotion/google-fonts` automatically calls `delayRender/continueRender` internally. No manual blocking needed.

### Pattern 8: Scene-Aware Pacing via calculateMetadata

**What:** Python passes per-scene durations as an array. `calculateMetadata()` computes total `durationInFrames` dynamically instead of hardcoding `len(images) * scene_duration`.
**When to use:** When scene durations vary (slower scenes for complex images, faster for simple ones).

```typescript
// Source: https://www.remotion.dev/docs/dynamic-metadata
// In Root.tsx — replace hardcoded durationInFrames with calculateMetadata
<Composition
  id="StudyVideo"
  component={StudyVideo}
  fps={30}
  width={1920}
  height={1080}
  calculateMetadata={({ props }) => {
    const sceneDurations: number[] = props.sceneDurations ??
      Array(props.images.length).fill(props.sceneDuration ?? 25);
    const totalFrames = sceneDurations.reduce(
      (sum, dur) => sum + Math.round(dur * 30),
      0
    );
    return { durationInFrames: Math.max(totalFrames, 1) };
  }}
  defaultProps={{ ... }}
/>
```

The Python side then constructs `sceneDurations` as a list of floats computed per image (e.g., complex images get 35s, simple ones get 20s).

### Anti-Patterns to Avoid

- **Linear interpolate for all motion:** Using `interpolate(frame, [0, 30], [0, 1])` with no easing produces mechanical motion. Replace with `spring()` or `Easing.bezier()` inside interpolate's options.
- **Per-character opacity for typewriter:** Causes layout reflow every frame. Use `text.slice(0, charCount)` with a computed charCount from frame number.
- **Hardcoded durationInFrames in Root.tsx:** The current `30 * 60 * 120` always renders 120 minutes regardless of actual content. Use `calculateMetadata` to compute actual duration from props.
- **useAudioData for long audio files:** Loads entire WAV into memory. 2-hour audio = ~1GB RAM. Use `useWindowedAudioData` instead.
- **SVG grain filter with static seed:** `seed={0}` produces static noise, not animated grain. Must be `seed={frame}` for animated grain.
- **Mixing @remotion package versions:** All `remotion`, `@remotion/cli`, `@remotion/transitions`, etc. must be the exact same version. Version mismatch causes bundler failures. Remove `^` prefix in package.json.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Inter-scene transitions | Custom opacity/translate crossfade logic | `@remotion/transitions` TransitionSeries | Handles dual-scene overlap, timing math, and presentation generics |
| Font loading with render blocking | Manual `delayRender` + `FontFace` | `@remotion/google-fonts` `loadFont()` | Auto-blocks render; handles weight/subset filtering; avoids timeout bugs |
| Audio frequency extraction | Manual FFT on audio buffer | `@remotion/media-utils` `visualizeAudio()` | Handles per-frame frequency binning with correct window function |
| Spring duration calculation | Manual frame-count estimation | `measureSpring({ fps, config })` | Returns exact settle frame so `durationInFrames` can be computed correctly |
| Variable composition duration | Separate render invocations | `calculateMetadata()` on Composition | Single render, dynamic duration, no shell arithmetic needed |

**Key insight:** The `@remotion/transitions` library abstracts the hardest problem in video editing — simultaneously rendering two overlapping scenes with correct z-order and duration math. Hand-rolling this consistently fails at edge cases (last scene, audio sync, reversed transitions).

---

## Common Pitfalls

### Pitfall 1: All @remotion/* versions must match exactly
**What goes wrong:** `@remotion/transitions@4.0.441` with `remotion@4.0.430` throws a bundler error during render about version mismatch.
**Why it happens:** Remotion uses peer dependency enforcement and internal version checks.
**How to avoid:** After `npm install`, verify all `remotion*` packages in `package.json` share the identical version string. Remove `^` caret to prevent future drift.
**Warning signs:** `Error: remotion version mismatch` in render stderr.

### Pitfall 2: useAudioData OOM for long study videos
**What goes wrong:** The `useWindowedAudioData` hook requires WAV format. If the Python pipeline passes an MP3, the hook returns `null` on every frame, producing no visualization.
**Why it happens:** `useWindowedAudioData` uses HTTP Range requests against WAV's predictable byte layout. MP3 VBR encoding breaks byte-offset seeking.
**How to avoid:** In `shared/remotion_renderer.py`, add a WAV conversion step before calling the renderer if audio visualization is enabled. Or use `useAudioData` for short clips and document the MP3/WAV requirement.
**Warning signs:** AudioVisualizer renders as empty; no console error (hook just returns null).

### Pitfall 3: SVG grain filter ID collision on re-render
**What goes wrong:** If two `FilmGrain` components render simultaneously with the same filter ID, one overlays incorrectly or disappears.
**Why it happens:** SVG filter IDs are global in the document. The `grain-${frame}` pattern solves this for single-instance use but breaks with multiple compositions rendering simultaneously.
**How to avoid:** Add a `key` prop string to the ID: `grain-${instanceId}-${frame}`.
**Warning signs:** Vignette/grain disappears on some scenes.

### Pitfall 4: TransitionSeries shortens total duration
**What goes wrong:** Total video is shorter than expected. A 10-scene video with 25s scenes and 1s transitions renders as `10*25 - 9*1 = 241s` instead of `250s`.
**Why it happens:** TransitionSeries overlaps adjacent sequences during transitions, subtracting transition duration from total.
**How to avoid:** When computing `totalFrames` in Python, subtract `(num_transitions * transition_duration_frames)` from the sum. Or use `calculateMetadata()` to derive it from the composition props at render time.
**Warning signs:** Audio ends before video, or video cuts off before audio finishes.

### Pitfall 5: Google Fonts network request failure during render
**What goes wrong:** Render fails with `Unable to load font` or hangs at 0% when the machine has no internet or the font CDN is slow.
**Why it happens:** `@remotion/google-fonts` fetches fonts from Google's CDN at render time.
**How to avoid:** For production renders, use local fonts via `@remotion/fonts` + `.woff2` files in `remotion/public/`. For development, accept the CDN dependency.
**Warning signs:** Render hangs at `0%` frames rendered for >30 seconds.

### Pitfall 6: --color-space bt709 flag required for accurate colors
**What goes wrong:** Video looks desaturated or slightly washed out on YouTube compared to the Remotion Studio preview.
**Why it happens:** Default color space is sRGB; YouTube expects bt709. The difference is subtle but visible on dark scenes.
**How to avoid:** Add `--color-space bt709` to the Python subprocess call. This becomes the Remotion 5.0 default but is not yet default in 4.x.
**Warning signs:** Colors look different between Remotion Studio preview and final MP4.

---

## Code Examples

### Complete render CLI command with quality flags (Python side)
```python
# Source: https://www.remotion.dev/docs/cli/render + https://www.remotion.dev/docs/encoding
cmd = [
    "npx", "remotion", "render",
    "src/index.ts",
    composition,
    str(output_path.absolute()),
    "--props", str(props_file.absolute()),
    "--frames", f"0-{frames - 1}",
    "--fps", str(fps),
    "--width", str(width),
    "--height", str(height),
    "--codec", "h264",
    "--crf", str(crf),                 # 16 for cinematic, 18 for standard, 23 for preview
    "--x264-preset", x264_preset,      # "slow" for quality, "medium" for speed
    "--color-space", "bt709",          # accurate colors for YouTube
    "--concurrency", str(concurrency), # benchmark to find optimal; start with 4
    "--audio-codec", "aac",
    "--audio-bitrate", "320k",
]
```

**Quality tiers per profile:**

| Profile | CRF | x264-preset | Use case |
|---------|-----|-------------|---------|
| cinematic | 16 | slow | Archive / YouTube upload |
| lofi-study | 18 | medium | YouTube upload |
| tech-tutorial | 18 | medium | YouTube upload |
| preview | 28 | veryfast | Local review |

### Easing reference for interpolate()
```typescript
// Source: https://www.remotion.dev/docs/easing
import { Easing, interpolate } from "remotion";

// Cinematic slow ease-out
const value = interpolate(frame, [0, 60], [0, 1], {
  easing: Easing.out(Easing.cubic),
  extrapolateRight: "clamp",
});

// Snappy tech-tutorial entrance
const value2 = interpolate(frame, [0, 20], [0, 1], {
  easing: Easing.bezier(0.33, 1, 0.68, 1), // ease-out-cubic equivalent
  extrapolateRight: "clamp",
});
```

### springTiming vs linearTiming for TransitionSeries
```typescript
// Source: https://www.remotion.dev/docs/transitions/transitionseries
import { springTiming, linearTiming } from "@remotion/transitions";

// Spring: physics-based, duration is variable but natural
const spring = springTiming({ config: { damping: 200 } }); // high damping = no overshoot

// Linear: predictable, exact duration
const linear = linearTiming({ durationInFrames: 20, easing: Easing.out(Easing.quad) });
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `<Sequence>` array with manual fade | `<TransitionSeries>` with presentations | Remotion v4.0.53 | Professional transitions with zero custom code |
| Manual `delayRender` + `FontFace` | `@remotion/google-fonts` auto-blocking | Remotion v3 | Font loading never causes blank-frame issues |
| Hardcoded `durationInFrames` | `calculateMetadata()` async callback | Remotion v4.0 | Composition duration derived from actual data |
| `useEffect` for metadata | `calculateMetadata()` | Remotion v4.0 | `useEffect` triggers on every render worker spawn; metadata should only run once |
| `<Html5Video>` / `<OffthreadVideo>` | `<Video>` component | Remotion v4 | Better performance and frame accuracy |
| `--color-space` default sRGB | `bt709` (will be v5 default) | Remotion v4.0.28 | Must set explicitly now; wrong colors on YouTube otherwise |

**Deprecated/outdated:**
- `useAudioData` for long files: Not deprecated but superseded by `useWindowedAudioData` for >5min audio
- `getInputProps()` in root component: Still works but `calculateMetadata` is the preferred pattern for data-driven duration

---

## Open Questions

1. **Audio format for visualization**
   - What we know: `useWindowedAudioData` requires WAV; the Python pipelines currently output MP3 from the AI audio layer
   - What's unclear: Whether the study video pipeline produces WAV or MP3 — needs inspection of the audio generation code
   - Recommendation: Add a `to_wav()` step in `shared/remotion_renderer.py` when audio visualization is enabled; use `ffmpeg -i input.mp3 output.wav` before render call

2. **Beat detection / beat sync**
   - What we know: `visualizeAudio()` gives per-frame frequency spectrum; no built-in beat detection in Remotion
   - What's unclear: Whether beat-sync transitions (changing scene on beat) are feasible — requires beat timestamps computed in Python and passed as props
   - Recommendation: Defer beat sync to v2; implement basic frequency visualization bar only in Phase 8

3. **LUT-based color grading**
   - What we know: Remotion has no built-in LUT support; REQUIREMENTS.md lists `PROF-01` (FFmpeg LUT filters) as a **v2 requirement**
   - What's unclear: Whether CSS `filter` approximations (sepia, hue-rotate, brightness, contrast) are acceptable substitutes for v1
   - Recommendation: Implement CSS-based color toning per profile (warm for lofi, cool for cinematic) using `filter` on `AbsoluteFill`. True LUT processing stays deferred as v2 per the requirements document.

4. **Render time for 120-minute StudyVideo with grain enabled**
   - What we know: SVG `feTurbulence` is GPU-accelerated but expensive; 120min at 30fps = 216,000 frames
   - What's unclear: Whether grain at 0.05 intensity is perceptibly different from no grain and whether render time doubles
   - Recommendation: Make grain opt-in per profile with default off for lofi-study; cinematic profile defaults to grain-on but allows config override

---

## Sources

### Primary (HIGH confidence)
- `https://www.remotion.dev/docs/transitions/transitionseries` — TransitionSeries API, Transition component, springTiming/linearTiming
- `https://www.remotion.dev/docs/transitions/presentations/wipe` — wipe() API with direction options
- `https://www.remotion.dev/docs/transitions/presentations/slide` — slide() API
- `https://www.remotion.dev/docs/spring` — spring() full API with all config params
- `https://www.remotion.dev/docs/easing` — All Easing functions with signatures
- `https://www.remotion.dev/docs/encoding` — Codec table, CRF ranges, ProRes profiles
- `https://www.remotion.dev/docs/quality` — CRF recommendations, color-space bt709, JPEG quality
- `https://www.remotion.dev/docs/cli/render` — All CLI flags including --color-space, --x264-preset, --concurrency
- `https://www.remotion.dev/docs/google-fonts/load-font` — loadFont() API, weights/subsets params
- `https://www.remotion.dev/docs/fonts` — FontFace API + delayRender/continueRender pattern
- `https://www.remotion.dev/docs/audio/visualization` — useAudioData, visualizeAudio complete workflow
- `https://www.remotion.dev/docs/dynamic-metadata` — calculateMetadata() API and usage pattern
- `https://www.remotion.dev/docs/performance` — Performance tips, GPU CSS pitfalls

### Secondary (MEDIUM confidence)
- WebSearch: @remotion/transitions presentation list (fade, wipe, slide, clockWipe, flip, iris, cube, none) — verified against individual doc pages fetched
- WebSearch: `useWindowedAudioData` WAV-only constraint — consistent across multiple Remotion doc pages

### Tertiary (LOW confidence)
- SVG `feTurbulence` + `seed={frame}` for animated grain — standard web technique applied to Remotion; confirmed film grain GitHub gist pattern but no Remotion-specific doc page

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified against remotion.dev docs; versions match installed package.json
- Architecture patterns: HIGH — TransitionSeries, spring(), calculateMetadata all from official docs with code examples
- Audio visualization: HIGH — useAudioData/visualizeAudio from official docs; WAV constraint from official note
- Film grain: MEDIUM — SVG feTurbulence technique is well-documented web standard; animated seed pattern from community gist, not official Remotion doc
- Pitfalls: HIGH — version mismatch, duration subtraction, color space all sourced from official docs
- LUT/color grading: MEDIUM — confirmed as v2 requirement via REQUIREMENTS.md; CSS filter approximation is author judgment

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (Remotion releases frequently; verify @remotion/transitions presentation list before pinning versions)

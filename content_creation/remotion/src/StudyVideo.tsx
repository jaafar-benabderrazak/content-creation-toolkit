import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const resolveAsset = (src: string): string =>
  src.startsWith("/") ? staticFile(src) : src;
import { TransitionSeries, springTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { wipe } from "@remotion/transitions/wipe";
import { slide } from "@remotion/transitions/slide";
import { getProfile } from "./profiles/index";
import { FilmGrain } from "./components/FilmGrain";
import { Vignette } from "./components/Vignette";
import { AudioVisualizer } from "./components/AudioVisualizer";
// Load fonts so they are available in renders
import "./fonts/index";

interface StudyVideoProps {
  images: string[];
  audioFile: string;
  sceneDuration: number;
  sceneDurations?: number[];
  profile?: string;
  style: string;
  enableParallax: boolean;
  enableParticles: boolean;
  timerEnabled: boolean;
  durationMinutes: number;
}

// Helper: select presentation from profile transition string
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getPresentation = (transitionName: string): any => {
  switch (transitionName) {
    case "wipe":
      return wipe({ direction: "from-left" });
    case "slide":
      return slide({ direction: "from-left" });
    case "fade":
    default:
      return fade();
  }
};

const Scene: React.FC<{
  src: string;
  durationFrames: number;
  enableParallax: boolean;
  profileConfig: ReturnType<typeof getProfile>;
}> = ({ src, durationFrames, enableParallax, profileConfig }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Spring-based parallax — organic feel, not linear pan
  const parallaxProgress = spring({
    frame,
    fps,
    config: profileConfig.springConfig,
    durationInFrames: durationFrames,
  });
  const translateX = enableParallax
    ? interpolate(parallaxProgress, [0, 1], [-20, 20])
    : 0;
  const translateY = enableParallax
    ? interpolate(parallaxProgress, [0, 1], [-10, 10])
    : 0;

  // Zoom: spring in, hold
  const zoomProgress = spring({
    frame,
    fps,
    config: { damping: 20, stiffness: 60, mass: 1 },
    durationInFrames: Math.min(60, durationFrames),
  });
  const scale = interpolate(zoomProgress, [0, 1], [1.05, 1.12]);

  return (
    <AbsoluteFill>
      <Img
        src={resolveAsset(src)}
        style={{
          width: "110%",
          height: "110%",
          objectFit: "cover",
          transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
          position: "absolute",
          top: "-5%",
          left: "-5%",
          filter: profileConfig.cssColorFilter,
        }}
      />
    </AbsoluteFill>
  );
};

const Timer: React.FC<{ durationMinutes: number; fontFamily: string }> = ({
  durationMinutes,
  fontFamily,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalSeconds = durationMinutes * 60;
  const elapsed = Math.floor(frame / fps);
  const remaining = Math.max(0, totalSeconds - elapsed);
  const hours = Math.floor(remaining / 3600);
  const mins = Math.floor((remaining % 3600) / 60);
  const secs = remaining % 60;

  const timeStr =
    hours > 0
      ? `${hours}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`
      : `${mins}:${String(secs).padStart(2, "0")}`;

  const popIn = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 200, overshootClamping: false },
    durationInFrames: 20,
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 40,
        right: 40,
        fontSize: 48,
        fontFamily,
        color: "rgba(255, 255, 255, 0.7)",
        textShadow: "2px 2px 8px rgba(0, 0, 0, 0.5)",
        letterSpacing: 2,
        transform: `scale(${popIn})`,
      }}
    >
      {timeStr}
    </div>
  );
};

const Particles: React.FC<{ density: number }> = ({ density }) => {
  const frame = useCurrentFrame();
  const count = Math.round(20 * density);
  const particles = Array.from({ length: count }, (_, i) => {
    const x = ((i * 97 + frame * 0.3) % 110) - 5;
    const y = ((i * 53 + frame * 0.2) % 110) - 5;
    const size = 2 + (i % 3);
    const opacity = 0.2 + (i % 5) * 0.1;
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: `${x}%`,
          top: `${y}%`,
          width: size,
          height: size,
          borderRadius: "50%",
          backgroundColor: `rgba(255, 255, 220, ${opacity})`,
          filter: "blur(1px)",
        }}
      />
    );
  });
  return <AbsoluteFill>{particles}</AbsoluteFill>;
};

export const StudyVideo: React.FC<StudyVideoProps> = ({
  images,
  audioFile,
  sceneDuration,
  sceneDurations,
  profile,
  enableParallax,
  enableParticles,
  timerEnabled,
  durationMinutes,
}) => {
  const { fps } = useVideoConfig();
  const profileConfig = getProfile(profile ?? "lofi-study");

  const sceneDurationsList =
    sceneDurations && sceneDurations.length > 0
      ? sceneDurations
      : images.map(() => sceneDuration);

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e" }}>
      {/* Scene sequences via TransitionSeries */}
      <TransitionSeries>
        {images.map((img, i) => {
          const durationFrames = Math.round(
            (sceneDurationsList[i] ?? sceneDuration) * fps
          );
          return (
            <React.Fragment key={i}>
              <TransitionSeries.Sequence durationInFrames={durationFrames}>
                <Scene
                  src={img}
                  durationFrames={durationFrames}
                  enableParallax={enableParallax}
                  profileConfig={profileConfig}
                />
              </TransitionSeries.Sequence>
              {i < images.length - 1 && (
                <TransitionSeries.Transition
                  presentation={getPresentation(profileConfig.transition)}
                  timing={springTiming({ config: { damping: 200 } })}
                />
              )}
            </React.Fragment>
          );
        })}
      </TransitionSeries>

      {/* Particle overlay */}
      {enableParticles && profileConfig.particleDensity > 0 && (
        <Particles density={profileConfig.particleDensity} />
      )}

      {/* Timer overlay */}
      {profileConfig.timerVisible && timerEnabled && (
        <Timer
          durationMinutes={durationMinutes}
          fontFamily={profileConfig.fontFamily}
        />
      )}

      {/* Vignette */}
      <Vignette strength={profileConfig.vignetteStrength} />

      {/* Film grain */}
      {profileConfig.grainIntensity > 0 && (
        <FilmGrain intensity={profileConfig.grainIntensity} instanceId="study" />
      )}

      {/* AudioVisualizer in footer — lofi-study only */}
      {audioFile && profile === "lofi-study" && (
        <div style={{ position: "absolute", bottom: 20, left: 20 }}>
          <AudioVisualizer src={audioFile} />
        </div>
      )}

      {/* Audio */}
      {audioFile && <Audio src={resolveAsset(audioFile)} />}
    </AbsoluteFill>
  );
};

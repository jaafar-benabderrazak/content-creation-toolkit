import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const resolveAsset = (src: string): string =>
  src.startsWith("/") ? staticFile(src) : src;
import { getProfile } from "./profiles/index";
import { FilmGrain } from "./components/FilmGrain";
import { Vignette } from "./components/Vignette";
import { TextReveal } from "./components/TextReveal";
import { spaceGrotesk, jetBrainsMono } from "./fonts/index";

interface TechTutorialProps {
  backgroundImage: string;
  audioFile: string;
  title: string;
  bullets: string[];
  subtitlesSrt: string;
  profile?: string;
}

export const TechTutorial: React.FC<TechTutorialProps> = ({
  backgroundImage,
  audioFile,
  title,
  bullets,
  profile,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Profile resolution
  const profileConfig = getProfile(profile ?? "tech-tutorial");
  const fontFamily =
    profileConfig.fontFamily === "JetBrains Mono" ? jetBrainsMono : spaceGrotesk;

  // Title entrance via spring
  const titleSpring = spring({
    frame,
    fps,
    config: profileConfig.springConfig,
    durationInFrames: 25,
  });
  const titleOpacity = titleSpring;
  const titleY = interpolate(titleSpring, [0, 1], [30, 0]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f0f23" }}>
      {/* Background image with dim overlay */}
      {backgroundImage && (
        <>
          <Img
            src={resolveAsset(backgroundImage)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              position: "absolute",
              filter: profileConfig.cssColorFilter,
            }}
          />
          <AbsoluteFill
            style={{ backgroundColor: "rgba(0, 0, 0, 0.6)" }}
          />
        </>
      )}

      {/* Content card */}
      <div
        style={{
          position: "absolute",
          top: "12%",
          left: "8%",
          right: "8%",
          bottom: "12%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 40,
        }}
      >
        {/* Title */}
        <div
          style={{
            fontSize: 64,
            fontWeight: 800,
            color: "white",
            opacity: titleOpacity,
            transform: `translateY(${titleY}px)`,
            lineHeight: 1.2,
            textShadow: "0 4px 20px rgba(0,0,0,0.5)",
            fontFamily,
          }}
        >
          {title}
        </div>

        {/* Bullets — TextReveal per bullet with per-word stagger */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {bullets.map((bullet, i) => {
            const bulletStart = 60 + i * 45;
            return (
              <div
                key={i}
                style={{
                  fontSize: 42,
                  color: "rgba(255, 255, 255, 0.95)",
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  fontFamily,
                }}
              >
                <span style={{ color: "#60a5fa", fontSize: 36 }}>▸</span>
                <TextReveal
                  text={bullet}
                  startFrame={bulletStart}
                  springConfig={profileConfig.springConfig}
                  staggerFrames={4}
                  wordStyle={{ fontSize: 42, color: "rgba(255, 255, 255, 0.95)" }}
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* Vignette overlay */}
      <Vignette strength={profileConfig.vignetteStrength} />

      {/* Film grain — only when profile has grainIntensity > 0 */}
      {profileConfig.grainIntensity > 0 && (
        <FilmGrain intensity={profileConfig.grainIntensity} instanceId="techtutorial" />
      )}

      {/* Fade out at end — eased */}
      <AbsoluteFill
        style={{
          backgroundColor: "black",
          opacity: interpolate(
            frame,
            [durationInFrames - 30, durationInFrames],
            [0, 1],
            {
              easing: Easing.out(Easing.cubic),
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }
          ),
        }}
      />

      {/* Audio */}
      {audioFile && <Audio src={resolveAsset(audioFile)} />}
    </AbsoluteFill>
  );
};

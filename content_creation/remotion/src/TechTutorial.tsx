import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface TechTutorialProps {
  backgroundImage: string;
  audioFile: string;
  title: string;
  bullets: string[];
  subtitlesSrt: string;
}

export const TechTutorial: React.FC<TechTutorialProps> = ({
  backgroundImage,
  audioFile,
  title,
  bullets,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Title fade in
  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 30], [30, 0], {
    extrapolateRight: "clamp",
  });

  // Bullets stagger in
  const bulletDelay = 45; // frames between each bullet
  const bulletStart = 60; // frames before first bullet

  return (
    <AbsoluteFill style={{ backgroundColor: "#0f0f23" }}>
      {/* Background image with dim overlay */}
      {backgroundImage && (
        <>
          <Img
            src={backgroundImage}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              position: "absolute",
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
          }}
        >
          {title}
        </div>

        {/* Bullets */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {bullets.map((bullet, i) => {
            const start = bulletStart + i * bulletDelay;
            const opacity = interpolate(frame, [start, start + 20], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const x = interpolate(frame, [start, start + 20], [40, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });

            return (
              <div
                key={i}
                style={{
                  fontSize: 42,
                  color: "rgba(255, 255, 255, 0.95)",
                  opacity,
                  transform: `translateX(${x}px)`,
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                }}
              >
                <span style={{ color: "#60a5fa", fontSize: 36 }}>▸</span>
                {bullet}
              </div>
            );
          })}
        </div>
      </div>

      {/* Fade out at end */}
      <AbsoluteFill
        style={{
          backgroundColor: "black",
          opacity: interpolate(
            frame,
            [durationInFrames - 30, durationInFrames],
            [0, 1],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          ),
        }}
      />

      {/* Audio */}
      {audioFile && <Audio src={audioFile} />}
    </AbsoluteFill>
  );
};

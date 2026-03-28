import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface StudyVideoProps {
  images: string[];
  audioFile: string;
  sceneDuration: number;
  style: string;
  enableParallax: boolean;
  enableParticles: boolean;
  timerEnabled: boolean;
  durationMinutes: number;
}

const Scene: React.FC<{
  src: string;
  durationFrames: number;
  enableParallax: boolean;
}> = ({ src, durationFrames, enableParallax }) => {
  const frame = useCurrentFrame();

  // Parallax: subtle pan effect
  const translateX = enableParallax
    ? interpolate(frame, [0, durationFrames], [-20, 20], {
        extrapolateRight: "clamp",
      })
    : 0;

  const translateY = enableParallax
    ? interpolate(frame, [0, durationFrames], [-10, 10], {
        extrapolateRight: "clamp",
      })
    : 0;

  // Fade in/out
  const opacity = interpolate(
    frame,
    [0, 30, durationFrames - 30, durationFrames],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  // Subtle zoom
  const scale = interpolate(frame, [0, durationFrames], [1.05, 1.15], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={src}
        style={{
          width: "110%",
          height: "110%",
          objectFit: "cover",
          transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
          position: "absolute",
          top: "-5%",
          left: "-5%",
        }}
      />
    </AbsoluteFill>
  );
};

const Timer: React.FC<{ durationMinutes: number }> = ({ durationMinutes }) => {
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

  return (
    <div
      style={{
        position: "absolute",
        top: 40,
        right: 40,
        fontSize: 48,
        fontFamily: "monospace",
        color: "rgba(255, 255, 255, 0.7)",
        textShadow: "2px 2px 8px rgba(0, 0, 0, 0.5)",
        letterSpacing: 2,
      }}
    >
      {timeStr}
    </div>
  );
};

const Particles: React.FC = () => {
  const frame = useCurrentFrame();
  const particles = Array.from({ length: 20 }, (_, i) => {
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
  enableParallax,
  enableParticles,
  timerEnabled,
  durationMinutes,
}) => {
  const { fps } = useVideoConfig();
  const sceneDurationFrames = Math.round(sceneDuration * fps);

  return (
    <AbsoluteFill style={{ backgroundColor: "#1a1a2e" }}>
      {/* Scene sequences */}
      {images.map((img, i) => {
        const from = i * sceneDurationFrames;
        return (
          <Sequence key={i} from={from} durationInFrames={sceneDurationFrames}>
            <Scene
              src={img}
              durationFrames={sceneDurationFrames}
              enableParallax={enableParallax}
            />
          </Sequence>
        );
      })}

      {/* Particle overlay */}
      {enableParticles && <Particles />}

      {/* Timer overlay */}
      {timerEnabled && <Timer durationMinutes={durationMinutes} />}

      {/* Vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.4) 100%)",
          pointerEvents: "none",
        }}
      />

      {/* Audio */}
      {audioFile && <Audio src={audioFile} />}
    </AbsoluteFill>
  );
};

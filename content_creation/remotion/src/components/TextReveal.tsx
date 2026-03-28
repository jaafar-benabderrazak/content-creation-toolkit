import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface TextRevealProps {
  text: string;
  style?: React.CSSProperties;
  wordStyle?: React.CSSProperties;
  staggerFrames?: number;
  springConfig?: { damping: number; stiffness: number; mass?: number };
  startFrame?: number;
}

export const TextReveal: React.FC<TextRevealProps> = ({
  text,
  style,
  wordStyle,
  staggerFrames = 5,
  springConfig = { damping: 14, stiffness: 150, mass: 1 },
  startFrame = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, ...style }}>
      {words.map((word, i) => {
        const wordProgress = spring({
          frame: frame - startFrame - i * staggerFrames,
          fps,
          config: springConfig,
          durationInFrames: 25,
        });
        return (
          <span
            key={i}
            style={{
              opacity: wordProgress,
              transform: `translateY(${interpolate(wordProgress, [0, 1], [20, 0])}px)`,
              display: "inline-block",
              ...wordStyle,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};

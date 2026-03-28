import React from "react";
import { useWindowedAudioData, visualizeAudio } from "@remotion/media-utils";
import { useCurrentFrame, useVideoConfig } from "remotion";

interface AudioVisualizerProps {
  src: string;
  numberOfSamples?: number;
  barColor?: string;
  height?: number;
  windowInSeconds?: number;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  src,
  numberOfSamples = 32,
  barColor = "rgba(255, 255, 255, 0.4)",
  height = 40,
  windowInSeconds = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { audioData, dataOffsetInSeconds } = useWindowedAudioData({
    src,
    frame,
    fps,
    windowInSeconds,
  });

  if (!audioData) return null;

  const bars = visualizeAudio({
    fps,
    frame,
    audioData,
    numberOfSamples,
    dataOffsetInSeconds,
  });

  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height }}>
      {bars.map((amplitude, i) => (
        <div
          key={i}
          style={{
            width: 4,
            height: amplitude * height,
            backgroundColor: barColor,
            borderRadius: 2,
          }}
        />
      ))}
    </div>
  );
};

import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

export const FilmGrain: React.FC<{ intensity?: number; instanceId?: string }> = ({
  intensity = 0.08,
  instanceId = "default",
}) => {
  const frame = useCurrentFrame();
  const filterId = `grain-${instanceId}-${frame}`;
  return (
    <AbsoluteFill
      style={{ pointerEvents: "none", mixBlendMode: "screen", opacity: intensity }}
    >
      <svg width="100%" height="100%" style={{ position: "absolute" }}>
        <defs>
          <filter id={filterId}>
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.65"
              numOctaves={3}
              seed={frame}
              stitchTiles="stitch"
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
        </defs>
        <rect width="100%" height="100%" filter={`url(#${filterId})`} />
      </svg>
    </AbsoluteFill>
  );
};

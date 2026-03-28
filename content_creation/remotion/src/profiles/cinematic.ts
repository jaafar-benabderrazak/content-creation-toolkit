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
  cssColorFilter: "brightness(0.92) saturate(1.15) contrast(1.05)",
  crf: 16,
  x264Preset: "slow" as const,
};

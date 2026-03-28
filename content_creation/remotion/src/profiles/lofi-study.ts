export const lofiStudyProfile = {
  transition: "fade" as const,
  transitionDuration: 15,
  springConfig: { damping: 18, stiffness: 100, mass: 1 },
  fontFamily: "Space Grotesk",
  grainIntensity: 0.05,
  vignetteStrength: 0.35,
  timerVisible: true,
  particleDensity: 20,
  sceneHoldMultiplier: 1.0,
  cssColorFilter: "brightness(0.95) saturate(0.9) sepia(0.08)",
  crf: 18,
  x264Preset: "medium" as const,
};

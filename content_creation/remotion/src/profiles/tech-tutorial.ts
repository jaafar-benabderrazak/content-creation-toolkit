export const techTutorialProfile = {
  transition: "slide" as const,
  transitionDuration: 12,
  springConfig: { damping: 10, stiffness: 200, mass: 1, overshootClamping: true },
  fontFamily: "JetBrains Mono",
  grainIntensity: 0,
  vignetteStrength: 0.2,
  timerVisible: false,
  particleDensity: 0,
  sceneHoldMultiplier: 1.0,
  cssColorFilter: "brightness(1.02) saturate(1.1) hue-rotate(-5deg)",
  crf: 18,
  x264Preset: "medium" as const,
};

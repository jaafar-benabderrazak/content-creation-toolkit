import { lofiStudyProfile } from "./lofi-study";
import { techTutorialProfile } from "./tech-tutorial";
import { cinematicProfile } from "./cinematic";

export type ProfileName = "lofi-study" | "tech-tutorial" | "cinematic";

export interface ProfileConfig {
  transition: "fade" | "slide" | "wipe";
  transitionDuration: number;
  springConfig: { damping: number; stiffness: number; mass: number; overshootClamping?: boolean };
  fontFamily: string;
  grainIntensity: number;
  vignetteStrength: number;
  timerVisible: boolean;
  particleDensity: number;
  sceneHoldMultiplier: number;
  cssColorFilter: string;
  crf: number;
  x264Preset: "ultrafast" | "superfast" | "veryfast" | "faster" | "fast" | "medium" | "slow" | "slower" | "veryslow";
}

export const profiles: Record<ProfileName, ProfileConfig> = {
  "lofi-study": lofiStudyProfile,
  "tech-tutorial": techTutorialProfile,
  cinematic: cinematicProfile,
};

export const getProfile = (name: string): ProfileConfig => {
  return profiles[name as ProfileName] ?? lofiStudyProfile;
};

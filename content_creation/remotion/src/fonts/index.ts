import { loadFont as loadSpaceGrotesk } from "@remotion/google-fonts/SpaceGrotesk";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";

export const { fontFamily: spaceGrotesk } = loadSpaceGrotesk("normal", {
  weights: ["400", "600", "700"],
  subsets: ["latin"],
});

export const { fontFamily: jetBrainsMono } = loadJetBrainsMono("normal", {
  weights: ["400"],
  subsets: ["latin"],
});

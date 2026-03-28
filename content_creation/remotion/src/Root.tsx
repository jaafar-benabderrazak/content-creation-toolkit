import React from "react";
import { Composition } from "remotion";
import { StudyVideo } from "./StudyVideo";
import { TechTutorial } from "./TechTutorial";
import { getProfile } from "./profiles/index";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="StudyVideo"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={StudyVideo as any}
        fps={30}
        width={1920}
        height={1080}
        calculateMetadata={({ props }: { props: Record<string, unknown> }) => {
          const fps = 30;
          const profile = getProfile(
            typeof props.profile === "string" ? props.profile : "lofi-study"
          );
          const rawDurations = props.sceneDurations as number[] | undefined;
          const rawImages = props.images as string[] | undefined;
          const rawSceneDuration =
            typeof props.sceneDuration === "number" ? props.sceneDuration : 25;
          const sceneDurations: number[] =
            rawDurations && rawDurations.length > 0
              ? rawDurations
              : Array(Math.max(rawImages?.length ?? 1, 1)).fill(rawSceneDuration);
          const totalSceneFrames = sceneDurations.reduce(
            (sum: number, dur: number) => sum + Math.round(dur * fps),
            0
          );
          // TransitionSeries overlaps adjacent sequences during transitions
          const numTransitions = Math.max(sceneDurations.length - 1, 0);
          const transitionFrames = numTransitions * profile.transitionDuration;
          const durationInFrames = Math.max(
            totalSceneFrames - transitionFrames,
            1
          );
          return { durationInFrames };
        }}
        defaultProps={{
          images: [] as string[],
          audioFile: "",
          sceneDuration: 25,
          sceneDurations: [] as number[],
          profile: "lofi-study",
          style: "cinematic",
          enableParallax: true,
          enableParticles: true,
          timerEnabled: true,
          durationMinutes: 120,
        }}
      />
      <Composition
        id="TechTutorial"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={TechTutorial as any}
        durationInFrames={30 * 60} // 1 minute default, overridden by props
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          backgroundImage: "",
          audioFile: "",
          title: "",
          bullets: [] as string[],
          subtitlesSrt: "",
          profile: "tech-tutorial",
        }}
      />
    </>
  );
};

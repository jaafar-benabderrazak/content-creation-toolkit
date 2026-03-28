import { Composition } from "remotion";
import { StudyVideo } from "./StudyVideo";
import { TechTutorial } from "./TechTutorial";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="StudyVideo"
        component={StudyVideo}
        durationInFrames={30 * 60 * 120} // 120 minutes at 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          images: [] as string[],
          audioFile: "",
          sceneDuration: 25,
          style: "cinematic",
          enableParallax: true,
          enableParticles: true,
          timerEnabled: true,
          durationMinutes: 120,
        }}
      />
      <Composition
        id="TechTutorial"
        component={TechTutorial}
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
        }}
      />
    </>
  );
};

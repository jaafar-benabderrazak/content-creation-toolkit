"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
// Artifacts now loaded via Supabase API or pipeline-url fallback

interface ProfileData {
  profile?: string;
  video?: { style_prompt?: string; music_prompt?: string; mood?: string };
  sdxl?: {
    positive_prompt?: string;
    negative_prompt?: string;
    scene_templates?: string[];
  };
  suno?: { genre?: string; prompt_tags?: string };
  publish?: {
    youtube_title?: string;
    youtube_description?: string;
    youtube_tags?: string[];
    thumbnail_text?: string;
  };
  style_ref?: { handle?: string; backend?: string };
}

interface Artifacts {
  video?: { path: string; size_mb: number; name: string } | null;
  thumbnail?: { path: string; name: string } | null;
  image?: { path: string; name: string; count: number } | null;
  audio?: { path: string; size_mb: number; name: string } | null;
}

interface PromptTimelineProps {
  profile: string;
}

const STEP_COLORS: Record<string, string> = {
  tags: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  style: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  image: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  scenes: "bg-teal-500/20 text-teal-400 border-teal-500/30",
  music: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  thumbnail: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  youtube: "bg-red-500/20 text-red-400 border-red-500/30",
};

export function PromptTimeline({ profile }: PromptTimelineProps) {
  const [data, setData] = useState<ProfileData | null>(null);
  const [artifacts, setArtifacts] = useState<Artifacts>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!profile) return;
    setLoading(true);

    const profilePromise = fetch(`/api/config/profiles/${profile.replace("-", "_")}`)
      .then((r) => r.json());
    const artifactsPromise = fetch("/api/artifacts")
      .then((r) => r.json())
      .catch(() => ({}));
    // Try to get latest generated prompts from Supabase
    const supabasePromptsPromise = fetch("/api/history")
      .then((r) => r.json())
      .then((d: any) => {
        // Get the most recent execution to find associated prompts
        const latest = d.entries?.[0];
        if (latest?.id) {
          return fetch(`/api/preview-prompts?video_id=${latest.id}`)
            .then((r) => r.json())
            .catch(() => null);
        }
        return null;
      })
      .catch(() => null);

    Promise.all([profilePromise, artifactsPromise, supabasePromptsPromise])
      .then(([profileData, arts, supabasePrompts]: [any, any, any]) => {
        const cfg = profileData.config || profileData;
        // Merge Supabase prompts into profile data if available
        if (supabasePrompts && supabasePrompts.positive_prompt) {
          if (!cfg.sdxl) cfg.sdxl = {};
          cfg.sdxl.positive_prompt = supabasePrompts.positive_prompt;
          cfg.sdxl.negative_prompt = supabasePrompts.negative_prompt;
          cfg.sdxl.scene_templates = supabasePrompts.scene_templates;
          if (!cfg.suno) cfg.suno = {};
          cfg.suno.prompt_tags = supabasePrompts.music_prompt;
          if (!cfg.publish) cfg.publish = {};
          cfg.publish.thumbnail_text = supabasePrompts.thumbnail_text;
          cfg.publish.youtube_title = supabasePrompts.youtube_title;
          cfg.publish.youtube_description = supabasePrompts.youtube_description;
          cfg.publish.youtube_tags = supabasePrompts.youtube_tags;
        }
        setData(cfg);
        setArtifacts(arts || {});
      })
      .catch(() => setError("Cannot load profile"))
      .finally(() => setLoading(false));
  }, [profile]);

  if (!profile) return null;
  if (loading) return <p className="text-xs text-muted-foreground">Loading prompts...</p>;
  if (error) return <p className="text-xs text-red-500">{error}</p>;
  if (!data) return null;

  const steps = [
    {
      id: "tags",
      label: "Tags Input",
      time: "T+0s",
      content: data.video?.mood || "(user tags)",
      sub: "User provides comma-separated tags → Claude generates everything below",
    },
    ...(data.style_ref?.handle
      ? [{
          id: "style",
          label: "Style Reference",
          time: "T+1s",
          content: `@${data.style_ref.handle} (${data.style_ref.backend})`,
          sub: "Reference images loaded from cache → injected into image generation",
        }]
      : []),
    {
      id: "image",
      label: "SDXL Positive Prompt",
      time: "T+5s",
      content: data.sdxl?.positive_prompt || data.video?.style_prompt || "(not set)",
      sub: data.sdxl?.negative_prompt
        ? `Negative: ${data.sdxl.negative_prompt}`
        : undefined,
      artifact: artifacts.image
        ? `Result: ${artifacts.image.count} images generated (${artifacts.image.name})`
        : undefined,
    },
    {
      id: "scenes",
      label: `Scene Templates (${data.sdxl?.scene_templates?.length || 0})`,
      time: "T+5s",
      content: data.sdxl?.scene_templates?.[0] || "(not set)",
      sub: data.sdxl?.scene_templates && data.sdxl.scene_templates.length > 1
        ? `+ ${data.sdxl.scene_templates.length - 1} more variations`
        : undefined,
    },
    {
      id: "music",
      label: "Music Prompt",
      time: "T+5s (async)",
      content: data.suno?.prompt_tags || data.video?.music_prompt || "(not set)",
      sub: data.suno?.genre ? `Genre: ${data.suno.genre}` : undefined,
      artifact: artifacts.audio
        ? `Result: ${artifacts.audio.name} (${artifacts.audio.size_mb} MB)`
        : undefined,
    },
    {
      id: "thumbnail",
      label: "Thumbnail Text",
      time: "T+render",
      content: data.publish?.thumbnail_text || "(not set)",
      sub: "Best frame → img2img enhance → text overlay",
      artifact: artifacts.thumbnail
        ? `Result: ${artifacts.thumbnail.name}`
        : undefined,
    },
    {
      id: "youtube",
      label: "YouTube Metadata",
      time: "T+publish",
      content: data.publish?.youtube_title || "(not set)",
      sub: data.publish?.youtube_tags
        ? `${data.publish.youtube_tags.length} tags • ${(data.publish.youtube_description || "").length} char description`
        : undefined,
      artifact: artifacts.video
        ? `Result: ${artifacts.video.name} (${artifacts.video.size_mb} MB)`
        : undefined,
    },
  ];

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium">Prompt Chain Timeline</h4>
        <Badge variant="outline" className="text-[10px]">
          {data.profile || profile}
        </Badge>
      </div>

      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-[18px] top-3 bottom-3 w-px bg-border" />

        {steps.map((step, i) => (
          <div key={step.id} className="relative flex gap-3 pb-3">
            {/* Dot */}
            <div
              className={`relative z-10 mt-1.5 h-[10px] w-[10px] rounded-full border-2 shrink-0 ${
                STEP_COLORS[step.id]?.replace("text-", "bg-").split(" ")[0] || "bg-muted"
              } border-border`}
            />

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <Badge
                  className={`text-[10px] px-1.5 py-0 ${STEP_COLORS[step.id] || ""}`}
                >
                  {step.label}
                </Badge>
                <span className="text-[10px] text-muted-foreground font-mono">
                  {step.time}
                </span>
              </div>
              <p className="text-xs mt-0.5 text-foreground/80 truncate">
                {step.content}
              </p>
              {step.sub && (
                <p className="text-[10px] text-muted-foreground truncate">
                  {step.sub}
                </p>
              )}
              {step.artifact && (
                <p className="text-[10px] text-emerald-400 font-mono mt-0.5">
                  {step.artifact}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

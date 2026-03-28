export interface VideoSettings {
  style_prompt: string;
  music_prompt: string;
  mood: string;
  duration_minutes: number;
  resolution: "1080p" | "720p" | "480p";
  quality_preset: "high" | "medium" | "fast";
  scene_count: number;
  scene_duration_seconds: number;
  enable_weather: boolean;
  enable_time_progression: boolean;
  enable_parallax: boolean;
  enable_particles: boolean;
  parallax_strength: number;
}

export interface PostSettings {
  watermark_enabled: boolean;
  watermark_text: string;
  watermark_position: string;
  subtitles_enabled: boolean;
  subtitles_srt_path: string;
  intro_enabled: boolean;
  intro_clip_path: string;
  outro_enabled: boolean;
  outro_clip_path: string;
}

export interface PublishSettings {
  youtube_enabled: boolean;
  youtube_title: string;
  youtube_description: string;
  youtube_tags: string[];
  youtube_category_id: string;
  youtube_privacy: "public" | "unlisted" | "private";
  thumbnail_enabled: boolean;
}

export interface NotifySettings {
  discord_webhook_url: string | null;
  slack_webhook_url: string | null;
  require_approval: boolean;
  approval_timeout_seconds: number;
}

export interface PipelineConfig {
  profile: string;
  video: VideoSettings;
  post: PostSettings;
  publish: PublishSettings;
  notify: NotifySettings;
  sdxl?: Record<string, unknown>;
  suno?: Record<string, unknown>;
}

/** Dotted field path -> "env" | "yaml" */
export type ConfigProvenance = Record<string, "env" | "yaml">;

export interface ProfileWithProvenance {
  config: PipelineConfig;
  provenance: ConfigProvenance;
}

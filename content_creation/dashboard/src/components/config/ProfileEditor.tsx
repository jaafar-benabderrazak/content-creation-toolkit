"use client";

import * as React from "react";
import { FieldGroup } from "./FieldGroup";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import type { PipelineConfig } from "@/types/pipeline";

function EnvBadge() {
  return (
    <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-mono font-medium bg-blue-50 text-blue-600 border border-blue-200 leading-none">
      ENV
    </span>
  );
}

interface ProfileEditorProps {
  profile: string;
  config: PipelineConfig;
  provenance: Record<string, "env" | "yaml">;
  onSave: (config: PipelineConfig) => Promise<void>;
}

export function ProfileEditor({ profile, config, provenance, onSave }: ProfileEditorProps) {
  const [current, setCurrent] = React.useState<PipelineConfig>(config);
  const [saving, setSaving] = React.useState(false);
  const { toast } = useToast();

  // Sync when a different profile is selected
  React.useEffect(() => {
    setCurrent(config);
  }, [config]);

  function setVideo<K extends keyof PipelineConfig["video"]>(
    key: K,
    value: PipelineConfig["video"][K]
  ) {
    setCurrent((prev) => ({ ...prev, video: { ...prev.video, [key]: value } }));
  }

  function setPost<K extends keyof PipelineConfig["post"]>(
    key: K,
    value: PipelineConfig["post"][K]
  ) {
    setCurrent((prev) => ({ ...prev, post: { ...prev.post, [key]: value } }));
  }

  function setPublish<K extends keyof PipelineConfig["publish"]>(
    key: K,
    value: PipelineConfig["publish"][K]
  ) {
    setCurrent((prev) => ({
      ...prev,
      publish: { ...prev.publish, [key]: value },
    }));
  }

  function setNotify<K extends keyof PipelineConfig["notify"]>(
    key: K,
    value: PipelineConfig["notify"][K]
  ) {
    setCurrent((prev) => ({
      ...prev,
      notify: { ...prev.notify, [key]: value },
    }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await onSave(current);
      toast({ title: "Profile saved", description: `${profile} written to disk.` });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      toast({
        title: "Save failed",
        description: message,
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  }

  const v = current.video;
  const po = current.post;
  const pu = current.publish;
  const n = current.notify;

  return (
    <div className="flex flex-col gap-6">
      {/* Video Settings */}
      <FieldGroup title="Video Settings">
        <div className="grid gap-2">
          <Label htmlFor="style_prompt">Style Prompt</Label>
          <Textarea
            id="style_prompt"
            rows={3}
            value={v.style_prompt ?? ""}
            onChange={(e) => setVideo("style_prompt", e.target.value)}
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="music_prompt">Music Prompt</Label>
          <Textarea
            id="music_prompt"
            rows={3}
            value={v.music_prompt ?? ""}
            onChange={(e) => setVideo("music_prompt", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label htmlFor="mood">Mood</Label>
            <Input
              id="mood"
              value={v.mood ?? ""}
              onChange={(e) => setVideo("mood", e.target.value)}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="duration_minutes">Duration (minutes)</Label>
            <Input
              id="duration_minutes"
              type="number"
              min={1}
              value={v.duration_minutes ?? 60}
              onChange={(e) =>
                setVideo("duration_minutes", Number(e.target.value))
              }
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label>Resolution</Label>
            <Select
              value={v.resolution}
              onValueChange={(val) =>
                setVideo("resolution", val as "1080p" | "720p" | "480p")
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1080p">1080p</SelectItem>
                <SelectItem value="720p">720p</SelectItem>
                <SelectItem value="480p">480p</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label>Quality Preset</Label>
            <Select
              value={v.quality_preset}
              onValueChange={(val) =>
                setVideo("quality_preset", val as "high" | "medium" | "fast")
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="fast">Fast</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="grid gap-2">
            <Label htmlFor="scene_count">Scene Count</Label>
            <Input
              id="scene_count"
              type="number"
              min={1}
              value={v.scene_count ?? 12}
              onChange={(e) => setVideo("scene_count", Number(e.target.value))}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="scene_duration_seconds">Scene Duration (s)</Label>
            <Input
              id="scene_duration_seconds"
              type="number"
              min={1}
              value={v.scene_duration_seconds ?? 30}
              onChange={(e) =>
                setVideo("scene_duration_seconds", Number(e.target.value))
              }
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <Switch
              id="enable_weather"
              checked={!!v.enable_weather}
              onCheckedChange={(checked) => setVideo("enable_weather", checked)}
            />
            <Label htmlFor="enable_weather">Weather Effects</Label>
          </div>
          <div className="flex items-center gap-3">
            <Switch
              id="enable_time_progression"
              checked={!!v.enable_time_progression}
              onCheckedChange={(checked) =>
                setVideo("enable_time_progression", checked)
              }
            />
            <Label htmlFor="enable_time_progression">Time Progression</Label>
          </div>
          <div className="flex items-center gap-3">
            <Switch
              id="enable_parallax"
              checked={!!v.enable_parallax}
              onCheckedChange={(checked) =>
                setVideo("enable_parallax", checked)
              }
            />
            <Label htmlFor="enable_parallax">Parallax</Label>
          </div>
          <div className="flex items-center gap-3">
            <Switch
              id="enable_particles"
              checked={!!v.enable_particles}
              onCheckedChange={(checked) =>
                setVideo("enable_particles", checked)
              }
            />
            <Label htmlFor="enable_particles">Particles</Label>
          </div>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="parallax_strength">Parallax Strength</Label>
          <Input
            id="parallax_strength"
            type="number"
            step={0.01}
            min={0}
            max={1}
            value={v.parallax_strength ?? 0.05}
            onChange={(e) =>
              setVideo("parallax_strength", Number(e.target.value))
            }
          />
        </div>
      </FieldGroup>

      {/* Post Processing */}
      <FieldGroup title="Post Processing">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <Switch
              id="watermark_enabled"
              checked={!!po.watermark_enabled}
              onCheckedChange={(checked) =>
                setPost("watermark_enabled", checked)
              }
            />
            <Label htmlFor="watermark_enabled">Watermark</Label>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="watermark_text">Watermark Text</Label>
            <Input
              id="watermark_text"
              value={po.watermark_text ?? ""}
              onChange={(e) => setPost("watermark_text", e.target.value)}
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <Switch
              id="subtitles_enabled"
              checked={!!po.subtitles_enabled}
              onCheckedChange={(checked) =>
                setPost("subtitles_enabled", checked)
              }
            />
            <Label htmlFor="subtitles_enabled">Subtitles</Label>
          </div>
          <div className="flex items-center gap-3">
            <Switch
              id="intro_enabled"
              checked={!!po.intro_enabled}
              onCheckedChange={(checked) => setPost("intro_enabled", checked)}
            />
            <Label htmlFor="intro_enabled">Intro Clip</Label>
          </div>
          <div className="flex items-center gap-3">
            <Switch
              id="outro_enabled"
              checked={!!po.outro_enabled}
              onCheckedChange={(checked) => setPost("outro_enabled", checked)}
            />
            <Label htmlFor="outro_enabled">Outro Clip</Label>
          </div>
        </div>
      </FieldGroup>

      {/* Publish Settings */}
      <FieldGroup title="Publish Settings">
        <div className="flex items-center gap-3">
          <Switch
            id="youtube_enabled"
            checked={!!pu.youtube_enabled}
            onCheckedChange={(checked) =>
              setPublish("youtube_enabled", checked)
            }
          />
          <Label htmlFor="youtube_enabled">YouTube Upload</Label>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="youtube_title">Title</Label>
          <Input
            id="youtube_title"
            value={pu.youtube_title ?? ""}
            onChange={(e) => setPublish("youtube_title", e.target.value)}
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="youtube_description">Description</Label>
          <Textarea
            id="youtube_description"
            rows={4}
            value={pu.youtube_description ?? ""}
            onChange={(e) =>
              setPublish("youtube_description", e.target.value)
            }
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="youtube_tags">
            Tags{" "}
            <span className="text-xs text-muted-foreground">
              (comma-separated)
            </span>
          </Label>
          <Textarea
            id="youtube_tags"
            rows={2}
            value={(pu.youtube_tags ?? []).join(", ")}
            onChange={(e) =>
              setPublish(
                "youtube_tags",
                e.target.value
                  .split(",")
                  .map((t) => t.trim())
                  .filter(Boolean)
              )
            }
          />
        </div>

        <div className="grid gap-2">
          <Label>Privacy</Label>
          <Select
            value={pu.youtube_privacy}
            onValueChange={(val) =>
              setPublish(
                "youtube_privacy",
                val as "public" | "unlisted" | "private"
              )
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="public">Public</SelectItem>
              <SelectItem value="unlisted">Unlisted</SelectItem>
              <SelectItem value="private">Private</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-3">
          <Switch
            id="thumbnail_enabled"
            checked={!!pu.thumbnail_enabled}
            onCheckedChange={(checked) =>
              setPublish("thumbnail_enabled", checked)
            }
          />
          <Label htmlFor="thumbnail_enabled">Generate Thumbnail</Label>
        </div>
      </FieldGroup>

      {/* Notify Settings */}
      <FieldGroup title="Notify Settings">
        <div className="grid gap-2">
          <Label htmlFor="discord_webhook_url">
            Discord Webhook URL{" "}
            {provenance["notify.discord_webhook_url"] === "env" && <EnvBadge />}
          </Label>
          <Input
            id="discord_webhook_url"
            placeholder="https://discord.com/api/webhooks/..."
            value={n.discord_webhook_url ?? ""}
            onChange={(e) =>
              setNotify(
                "discord_webhook_url",
                e.target.value || null
              )
            }
          />
        </div>

        <div className="flex items-center gap-3">
          <Switch
            id="require_approval"
            checked={!!n.require_approval}
            onCheckedChange={(checked) =>
              setNotify("require_approval", checked)
            }
          />
          <Label htmlFor="require_approval">Require Approval Before Publish</Label>
        </div>

        <div className="grid gap-2">
          <Label htmlFor="approval_timeout_seconds">
            Approval Timeout (seconds)
          </Label>
          <Input
            id="approval_timeout_seconds"
            type="number"
            min={60}
            value={n.approval_timeout_seconds ?? 3600}
            onChange={(e) =>
              setNotify("approval_timeout_seconds", Number(e.target.value))
            }
          />
        </div>
      </FieldGroup>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving} className="min-w-28">
          {saving ? "Saving..." : "Save Profile"}
        </Button>
      </div>
    </div>
  );
}

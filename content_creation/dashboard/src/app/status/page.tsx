"use client";

import { useEffect, useState } from "react";
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { GenerationLog } from "@/components/status/GenerationLog";
import { LiveLogs } from "@/components/status/LiveLogs";

interface RoadmapEntry {
  id: string;
  title: string;
  tags: string;
  profile: string;
  status: string;
}

// Per-unit costs from provider pricing pages (March 2026)
const PRICING = {
  // Image generation
  seedream_replicate: 0.035,       // per image, Replicate bytedance/seedream-3
  dalle3_hd: 0.080,                // per image, 1792x1024 HD
  dalle3_standard: 0.040,          // per image, 1024x1024 standard
  local_sd: 0,                     // free, CPU

  // Music generation (kie.ai Suno wrapper)
  suno_per_credit: 0.005,          // $0.005 per kie.ai credit
  suno_credits_per_song: 10,       // ~10 credits per V4.5 generation (2 tracks)
  stable_audio: 0,                 // free, local GPU

  // AI prompt generation
  claude_sonnet_input: 0.003,      // per 1K input tokens
  claude_sonnet_output: 0.015,     // per 1K output tokens
  claude_est_input_tokens: 0.5,    // ~500 tokens system+user prompt
  claude_est_output_tokens: 1.2,   // ~1200 tokens for 8 sections
  openai_gpt4o_mini: 0.002,       // est. per call

  // YouTube
  youtube_quota_per_upload: 1600,   // units (10,000/day free)
  youtube_cost: 0,                  // free within quota

  // Video rendering
  remotion_local: 0,               // free, local CPU
  remotion_cloud: 0.05,            // est. if using Remotion Lambda (future)

  // Notifications
  discord_webhook: 0,              // free
  slack_webhook: 0,                // free

  // Thumbnail
  thumbnail_local: 0,              // free, Pillow
  thumbnail_api: 0,                // extracted from video, no extra cost

  // Post-processing
  ffmpeg_local: 0,                 // free

  // ngrok
  ngrok_free: 0,
};

interface CostLine {
  service: string;
  provider: string;
  detail: string;
  cost: number;
  unit: string;
}

function estimateCost(budget: string, sceneDuration: number = 120): { total: number; lines: CostLine[] } {
  const lines: CostLine[] = [];
  const sceneCount = Math.max(Math.ceil(sceneDuration / 5), 8); // ~1 scene per 5 min, min 8
  const musicTracks = 2;
  const sunoGenerations = Math.ceil(sceneDuration / 240); // 1 gen per 4 min max

  // 1. Prompt generation (always Claude)
  const promptInputCost = PRICING.claude_est_input_tokens * PRICING.claude_sonnet_input;
  const promptOutputCost = PRICING.claude_est_output_tokens * PRICING.claude_sonnet_output;
  const promptTotal = promptInputCost + promptOutputCost;
  lines.push({
    service: "Prompt Generation",
    provider: "Claude Sonnet",
    detail: `~500 in + ~1200 out tokens (8 sections)`,
    cost: promptTotal,
    unit: "per run",
  });

  // 2. Image generation
  if (budget === "free") {
    lines.push({ service: "Image Generation", provider: "Local SD 1.5", detail: `1 base image + ${sceneCount} variants (CPU ~2 min)`, cost: 0, unit: "free" });
  } else if (budget === "budget") {
    lines.push({ service: "Image Generation", provider: "DALL-E 3 Standard", detail: `1 image 1024x1024 + ${sceneCount} PIL variants`, cost: PRICING.dalle3_standard, unit: "per image" });
  } else if (budget === "standard") {
    lines.push({ service: "Image Generation", provider: "Seedream (Replicate)", detail: `1 image 16:9 + ${sceneCount} PIL variants`, cost: PRICING.seedream_replicate, unit: "per image" });
  } else {
    lines.push({ service: "Image Generation", provider: "DALL-E 3 HD", detail: `1 image 1792x1024 HD + ${sceneCount} PIL variants`, cost: PRICING.dalle3_hd, unit: "per image" });
  }

  // 3. Music generation
  if (budget === "free") {
    lines.push({ service: "Music Generation", provider: "Silent (fallback)", detail: "No Suno credits — silent audio", cost: 0, unit: "free" });
  } else {
    const sunoCredits = sunoGenerations * PRICING.suno_credits_per_song;
    const sunoCost = sunoCredits * PRICING.suno_per_credit;
    lines.push({
      service: "Music Generation",
      provider: "Suno V4.5 (kie.ai)",
      detail: `${sunoGenerations} gen x ${PRICING.suno_credits_per_song} credits = ${sunoCredits} credits (${musicTracks} tracks/gen)`,
      cost: sunoCost,
      unit: `${sunoCredits} credits`,
    });
  }

  // 4. Video rendering
  lines.push({
    service: "Video Rendering",
    provider: "Remotion (local)",
    detail: `${sceneCount} scenes, ${sceneDuration} min, 1080p H.264 CRF 16-18`,
    cost: 0,
    unit: "free (local CPU)",
  });

  // 5. Post-processing
  lines.push({
    service: "Post-Processing",
    provider: "FFmpeg (local)",
    detail: "Watermark, subtitles, intro/outro",
    cost: 0,
    unit: "free",
  });

  // 6. Thumbnail
  lines.push({
    service: "Thumbnail",
    provider: "Pillow + OpenCV (local)",
    detail: "Best frame extraction + text composite, 1280x720 JPEG",
    cost: 0,
    unit: "free",
  });

  // 7. Discord notification
  lines.push({
    service: "Notifications",
    provider: "Discord + Slack webhooks",
    detail: "Preview + approval + publish notification",
    cost: 0,
    unit: "free",
  });

  // 8. YouTube upload
  lines.push({
    service: "YouTube Upload",
    provider: "YouTube Data API v3",
    detail: `1,600 quota units (${Math.floor(10000 / 1600)} uploads/day free)`,
    cost: 0,
    unit: "free (within quota)",
  });

  const total = lines.reduce((sum, l) => sum + l.cost, 0);
  return { total, lines };
}

export default function StatusPage() {
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState("lofi_study");
  const [tags, setTags] = useState("");
  const [budget, setBudget] = useState("standard");
  const [roadmapEntries, setRoadmapEntries] = useState<RoadmapEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState("");

  useEffect(() => {
    fetch("/api/roadmap?status=planned")
      .then((r) => r.json())
      .then((data) => setRoadmapEntries(data.entries || []))
      .catch(() => {});
  }, []);

  function onSelectRoadmapEntry(entryId: string) {
    setSelectedEntry(entryId);
    const entry = roadmapEntries.find((e) => e.id === entryId);
    if (entry) {
      setTags(entry.tags);
      setSelectedProfile(entry.profile.replace("-", "_"));
    }
  }

  async function handleTrigger() {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const res = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: selectedProfile, tags, budget }),
      });
      const data = await res.json();
      if (data.triggered) {
        setTriggerResult(`Triggered run ${data.run_id || ""} — watch logs below`);
      } else {
        setTriggerResult(`Error: ${data.error}`);
      }
    } catch {
      setTriggerResult("Error: could not reach trigger endpoint");
    } finally {
      setTriggering(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Pipeline Status</h1>

      {/* Trigger Card */}
      <Card>
        <CardHeader><CardTitle>Trigger Generation</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {/* Roadmap Picker */}
          {roadmapEntries.length > 0 && (
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">
                Pick from Roadmap ({roadmapEntries.length} planned)
              </label>
              <select
                value={selectedEntry}
                onChange={(e) => onSelectRoadmapEntry(e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="">— Select a video —</option>
                {roadmapEntries.slice(0, 50).map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Tags</label>
              <input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="lofi, rain, cozy, study"
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Profile</label>
              <select
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="lofi_study">lofi_study</option>
                <option value="tech_tutorial">tech_tutorial</option>
                <option value="cinematic">cinematic</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Budget</label>
              <select
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="free">Free (local only)</option>
                <option value="budget">Budget (~$0.09)</option>
                <option value="standard">Standard (~$0.06)</option>
                <option value="premium">Premium (~$0.12)</option>
              </select>
            </div>
            <Button onClick={handleTrigger} disabled={triggering}>
              {triggering ? "Triggering..." : "Generate Video"}
            </Button>
          </div>

          {/* Cost Estimate */}
          {(() => {
            const est = estimateCost(budget);
            const paidLines = est.lines.filter(l => l.cost > 0);
            const freeLines = est.lines.filter(l => l.cost === 0);
            return (
              <Card className="bg-muted/30 border-dashed">
                <CardContent className="pt-4 pb-3">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium">Estimated Cost per Video</span>
                    <Badge className={est.total === 0 ? "bg-green-500/20 text-green-400" : "bg-blue-500/20 text-blue-400"}>
                      {est.total === 0 ? "FREE" : `$${est.total.toFixed(3)}`}
                    </Badge>
                  </div>

                  {/* Paid services */}
                  {paidLines.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs font-medium text-muted-foreground mb-1">Paid Services</p>
                      <table className="w-full text-xs">
                        <tbody>
                          {paidLines.map((l, i) => (
                            <tr key={i} className="border-b border-dashed border-muted">
                              <td className="py-1.5 font-medium">{l.service}</td>
                              <td className="py-1.5 text-muted-foreground">{l.provider}</td>
                              <td className="py-1.5 text-muted-foreground">{l.detail}</td>
                              <td className="py-1.5 text-right font-mono">${l.cost.toFixed(3)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Free services */}
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Free Services</p>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                      {freeLines.map((l, i) => (
                        <div key={i} className="flex justify-between text-xs text-muted-foreground">
                          <span>{l.service}</span>
                          <span className="text-green-500">Free</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Totals */}
                  <div className="mt-3 pt-2 border-t flex justify-between text-sm">
                    <span className="font-medium">Total per video</span>
                    <span className="font-bold">${est.total.toFixed(3)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>10 videos</span>
                    <span>${(est.total * 10).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>60 videos (full lofi roadmap)</span>
                    <span>${(est.total * 60).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>210 videos (full roadmap)</span>
                    <span>${(est.total * 210).toFixed(2)}</span>
                  </div>
                </CardContent>
              </Card>
            );
          })()}

          {triggerResult && (
            <p className={triggerResult.startsWith("Error") ? "text-red-500 text-sm" : "text-green-500 text-sm"}>
              {triggerResult}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Live Logs */}
      <Card>
        <CardHeader>
          <CardTitle>Live Pipeline Output</CardTitle>
          <CardDescription>Real-time stdout via ngrok (polls every 2s)</CardDescription>
        </CardHeader>
        <CardContent>
          <LiveLogs />
        </CardContent>
      </Card>

      {/* Event Log */}
      <Card>
        <CardHeader>
          <CardTitle>Event Log</CardTitle>
          <CardDescription>Webhook status callbacks</CardDescription>
        </CardHeader>
        <CardContent>
          <GenerationLog autoRefresh={true} />
        </CardContent>
      </Card>
    </div>
  );
}

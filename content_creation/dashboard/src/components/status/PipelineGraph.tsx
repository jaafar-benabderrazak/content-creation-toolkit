"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

// ─── Types ──────────────────────────────────────────────────────

interface NodeData {
  id: string;
  label: string;
  category: "input" | "ai" | "generate" | "post" | "output";
  prompt: string;        // The actual prompt text used
  sub: string;           // Secondary info
  status: "pending" | "running" | "done" | "failed" | "skipped";
  result?: string;       // Result after completion
  dependencies: string[];
}

interface PipelineGraphProps {
  profile: string;
  logs: string[];         // Live log lines from pipeline
  runStatus: string;      // "idle" | "running" | "done" | "failed"
}

// ─── Status colors ──────────────────────────────────────────────

const STATUS_STYLES: Record<string, { bg: string; border: string; dot: string }> = {
  pending:  { bg: "bg-zinc-900/50",    border: "border-zinc-700",   dot: "bg-zinc-500" },
  running:  { bg: "bg-blue-950/50",    border: "border-blue-500",   dot: "bg-blue-400 animate-pulse" },
  done:     { bg: "bg-emerald-950/50", border: "border-emerald-500", dot: "bg-emerald-400" },
  failed:   { bg: "bg-red-950/50",     border: "border-red-500",    dot: "bg-red-400" },
  skipped:  { bg: "bg-zinc-900/30",    border: "border-zinc-800",   dot: "bg-zinc-600" },
};

const CATEGORY_COLORS: Record<string, string> = {
  input:    "text-violet-400",
  ai:       "text-cyan-400",
  generate: "text-emerald-400",
  post:     "text-amber-400",
  output:   "text-red-400",
};

// ─── Log parser — maps log lines to node status ─────────────────

type NodeStatus = "running" | "done" | "failed" | "skipped";

function parseLogStatus(logs: string[]): Record<string, NodeStatus> {
  const status: Record<string, NodeStatus> = {};
  const text = logs.join("\n");

  // Prompt generation
  if (text.includes("[Tags] Generating prompts")) status["prompts"] = "running";
  if (text.includes("[Tags] Prompts written")) { status["prompts"] = "done"; status["prompt-chain"] = "done"; }

  // Image generation
  if (text.includes("[Images] Generating")) status["images"] = "running";
  if (text.includes("[Images] Using") || text.includes("images for video")) status["images"] = "done";
  if (text.includes("Cache hit")) status["images"] = "done";

  // Music
  if (text.includes("[Music] Submitting Suno")) status["music"] = "running";
  if (text.includes("[Music] Suno track ready") || text.includes("Suno Fallback")) status["music"] = "done";
  if (text.includes("Suno API error") || text.includes("Credits insufficient")) status["music"] = "failed";

  // Video render
  if (text.includes("Assembling enhanced video") || text.includes("Remotion")) status["render"] = "running";
  if (text.includes("DONE") || text.includes("Video rendering completed") || text.includes("Saved to:")) status["render"] = "done";

  // Thumbnail
  if (text.includes("[Thumbnail]")) status["thumbnail"] = "running";
  if (text.includes("Thumbnail] Saved") || text.includes("thumb")) status["thumbnail"] = "done";

  // Post-process
  if (text.includes("[PostProcess]")) status["postprocess"] = "running";
  if (text.includes("PostProcess] Done")) status["postprocess"] = "done";

  // Discord
  if (text.includes("Discord") && text.includes("sent")) status["discord"] = "done";
  if (text.includes("Video preview sent")) status["approval"] = "running";
  if (text.includes("Approved") || text.includes("Exit code: 0")) status["approval"] = "done";

  // YouTube
  if (text.includes("YouTube") && text.includes("Upload complete")) status["youtube"] = "done";
  if (text.includes("YouTube publishing disabled")) status["youtube"] = "skipped";

  return status;
}

// ─── Component ──────────────────────────────────────────────────

export function PipelineGraph({ profile, logs, runStatus }: PipelineGraphProps) {
  const [profileData, setProfileData] = useState<any>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/config/profiles/${profile.replace("-", "_")}`)
      .then((r) => r.json())
      .then((d) => setProfileData(d.config || d))
      .catch(() => {});
  }, [profile]);

  const d = profileData || {};
  const logStatus = parseLogStatus(logs);

  // Determine node statuses based on run state + log parsing
  function nodeStatus(id: string): NodeData["status"] {
    if (runStatus === "idle") return "pending";
    if (logStatus[id]) return logStatus[id] as NodeData["status"];
    // If pipeline is running and this node hasn't started yet
    if (runStatus === "running") return "pending";
    if (runStatus === "done") return "done";
    if (runStatus === "failed") return "pending";
    return "pending";
  }

  const nodes: NodeData[] = [
    {
      id: "tags",
      label: "Tags Input",
      category: "input",
      prompt: d.video?.mood || "(tags from user)",
      sub: "User provides comma-separated tags",
      status: runStatus !== "idle" ? "done" : "pending",
      dependencies: [],
    },
    ...(d.style_ref?.handle ? [{
      id: "style-ref",
      label: "Style Reference",
      category: "input" as const,
      prompt: `@${d.style_ref.handle} (${d.style_ref.backend || "replicate"})`,
      sub: `${d.style_ref.max_reference_images || 6} reference images from .cache/style_reference/`,
      status: nodeStatus("style-ref") || ("pending" as const),
      dependencies: ["tags"],
    }] : []),
    {
      id: "prompts",
      label: "Claude Prompt Gen",
      category: "ai",
      prompt: `System: "World-class AI content director..."\nUser: "Tags: ${d.video?.mood || '...'} → Generate 9 sections"`,
      sub: "Claude Sonnet generates: positive, negative, 8 scenes, music, thumbnail, YT metadata",
      status: nodeStatus("prompts"),
      dependencies: ["tags"],
      result: d.sdxl?.positive_prompt ? `✓ ${d.sdxl.positive_prompt.slice(0, 80)}...` : undefined,
    },
    {
      id: "prompt-chain",
      label: "Prompt Chain (9 outputs)",
      category: "ai",
      prompt: [
        `positive: ${d.sdxl?.positive_prompt?.slice(0, 100) || "(not set)"}...`,
        `negative: ${d.sdxl?.negative_prompt || "(not set)"}`,
        `scenes: ${d.sdxl?.scene_templates?.length || 0} templates`,
        `music: ${d.suno?.prompt_tags || d.video?.music_prompt || "(not set)"}`,
        `thumbnail_text: ${d.publish?.thumbnail_text || "(not set)"}`,
        `thumbnail_prompt: ${(d.publish as any)?.thumbnail_prompt || "(not set)"}`,
        `yt_title: ${d.publish?.youtube_title || "(not set)"}`,
        `yt_desc: ${(d.publish?.youtube_description || "").length} chars`,
        `yt_tags: ${d.publish?.youtube_tags?.length || 0} tags`,
      ].join("\n"),
      sub: "All 9 sections saved to profile YAML",
      status: nodeStatus("prompt-chain"),
      dependencies: ["prompts"],
    },
    {
      id: "images",
      label: "Image Generation",
      category: "generate",
      prompt: d.sdxl?.positive_prompt || d.video?.style_prompt || "(from prompt chain)",
      sub: `1 base image → ${d.video?.scene_count || 8} variants via Seedream/Gemini/SD`,
      status: nodeStatus("images"),
      dependencies: ["prompt-chain"],
      result: logStatus["images"] === "done" ? "✓ Images generated" : undefined,
    },
    {
      id: "music",
      label: "Music Generation",
      category: "generate",
      prompt: d.suno?.prompt_tags || d.video?.music_prompt || "(from prompt chain)",
      sub: `Suno V4.5 (kie.ai) • Genre: ${d.suno?.genre || "?"} • 2 tracks`,
      status: nodeStatus("music"),
      dependencies: ["prompt-chain"],
      result: logStatus["music"] === "done" ? "✓ Music ready" : logStatus["music"] === "failed" ? "✗ Silent fallback" : undefined,
    },
    {
      id: "render",
      label: "Video Render",
      category: "generate",
      prompt: `Remotion: ${d.video?.scene_count || 8} scenes, ${d.video?.duration_minutes || 3} min, cinematic profile`,
      sub: "TransitionSeries + spring physics + parallax + particles + timer",
      status: nodeStatus("render"),
      dependencies: ["images", "music"],
      result: logStatus["render"] === "done" ? "✓ Video rendered" : undefined,
    },
    {
      id: "postprocess",
      label: "Post-Processing",
      category: "post",
      prompt: `Watermark: "${d.post?.watermark_text || "channel name"}" • Subtitles: ${d.post?.subtitles_enabled ? "on" : "off"} • Intro/Outro: ${d.post?.intro_enabled ? "on" : "off"}`,
      sub: "FFmpeg: watermark → subtitle burn-in → intro/outro concat",
      status: nodeStatus("postprocess"),
      dependencies: ["render"],
    },
    {
      id: "thumbnail",
      label: "Thumbnail",
      category: "post",
      prompt: [
        `1. Best frame (OpenCV Laplacian sharpness)`,
        `2. img2img: ${(d.publish as any)?.thumbnail_prompt || "dramatic enhancement"}`,
        `3. Claude Vision analyzes → text: "${d.publish?.thumbnail_text || "?"}"`,
        `   → picks position, color, size, glow, emphasis word`,
      ].join("\n"),
      sub: "Seedream/Gemini img2img → Claude Vision text design → Pillow composite",
      status: nodeStatus("thumbnail"),
      dependencies: ["postprocess"],
      result: logStatus["thumbnail"] === "done" ? "✓ Thumbnail generated" : undefined,
    },
    {
      id: "discord",
      label: "Discord Preview",
      category: "output",
      prompt: "Send video snippet + thumbnail to Discord webhook for approval",
      sub: "15s preview clip + thumbnail image + metadata embed",
      status: nodeStatus("discord"),
      dependencies: ["thumbnail"],
    },
    {
      id: "approval",
      label: "Approval Gate",
      category: "output",
      prompt: "Wait for CLI approval (Enter=approve, r=reject/regenerate)",
      sub: "Up to 5 regeneration attempts before accepting",
      status: nodeStatus("approval"),
      dependencies: ["discord"],
    },
    {
      id: "youtube",
      label: "YouTube Upload",
      category: "output",
      prompt: [
        `Title: ${d.publish?.youtube_title || "(from prompt chain)"}`,
        `Description: ${(d.publish?.youtube_description || "").slice(0, 100)}...`,
        `Tags: ${d.publish?.youtube_tags?.length || 0} SEO tags`,
        `Privacy: ${d.publish?.youtube_privacy || "private"}`,
      ].join("\n"),
      sub: "Resumable upload + thumbnail.set + quota guard",
      status: nodeStatus("youtube"),
      dependencies: ["approval"],
    },
  ];

  // Count statuses
  const counts = { done: 0, running: 0, failed: 0, pending: 0, skipped: 0 };
  nodes.forEach((n) => counts[n.status]++);

  return (
    <div className="space-y-3">
      {/* Header with progress */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-medium">Pipeline Graph</h4>
          <Badge variant="outline" className="text-[10px]">{profile}</Badge>
        </div>
        <div className="flex gap-2 text-[10px]">
          {counts.done > 0 && <span className="text-emerald-400">{counts.done} done</span>}
          {counts.running > 0 && <span className="text-blue-400">{counts.running} running</span>}
          {counts.failed > 0 && <span className="text-red-400">{counts.failed} failed</span>}
          {counts.pending > 0 && <span className="text-zinc-500">{counts.pending} pending</span>}
        </div>
      </div>

      {/* Graph nodes */}
      <div className="space-y-1">
        {nodes.map((node, idx) => {
          const styles = STATUS_STYLES[node.status];
          const catColor = CATEGORY_COLORS[node.category];
          const isExpanded = expanded === node.id;
          const hasMultiDeps = node.dependencies.length > 1;

          return (
            <div key={node.id}>
              {/* Connection lines */}
              {idx > 0 && (
                <div className="flex items-center pl-4 h-4">
                  <div className={`w-px h-full ${styles.border}`} />
                  {hasMultiDeps && (
                    <span className="text-[8px] text-zinc-600 ml-2">
                      ← {node.dependencies.join(" + ")}
                    </span>
                  )}
                </div>
              )}

              {/* Node */}
              <button
                onClick={() => setExpanded(isExpanded ? null : node.id)}
                className={`w-full text-left rounded-lg border p-3 transition-all ${styles.bg} ${styles.border} hover:brightness-110`}
              >
                <div className="flex items-start gap-3">
                  {/* Status dot */}
                  <div className={`mt-1 h-2.5 w-2.5 rounded-full shrink-0 ${styles.dot}`} />

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-medium ${catColor}`}>{node.label}</span>
                      <span className="text-[10px] text-zinc-500">{node.category}</span>
                      {node.result && (
                        <span className="text-[10px] text-emerald-400 font-mono">{node.result}</span>
                      )}
                    </div>

                    {/* Always show first line of prompt */}
                    <p className="text-[11px] text-zinc-400 mt-0.5 truncate">
                      {node.prompt.split("\n")[0]}
                    </p>

                    {/* Expanded: show full prompt + sub */}
                    {isExpanded && (
                      <div className="mt-2 space-y-1.5">
                        <pre className="text-[10px] font-mono text-zinc-300 whitespace-pre-wrap bg-black/30 rounded p-2 max-h-40 overflow-y-auto">
                          {node.prompt}
                        </pre>
                        <p className="text-[10px] text-zinc-500">{node.sub}</p>
                      </div>
                    )}
                  </div>

                  {/* Expand indicator */}
                  <span className="text-zinc-600 text-xs shrink-0">
                    {isExpanded ? "▾" : "▸"}
                  </span>
                </div>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

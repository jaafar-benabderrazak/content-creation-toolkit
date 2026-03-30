"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

// ─── Types ──────────────────────────────────────────────────────

interface GraphNode {
  id: string;
  label: string;
  icon: string;
  category: "input" | "ai" | "generate" | "post" | "output";
  prompt: string;
  sub: string;
  status: "pending" | "running" | "done" | "failed" | "skipped";
  result?: string;
  deps: string[];
  lane: number; // 0=top, 1=bottom (for parallel nodes)
}

interface PipelineGraphProps {
  profile: string;
  logs: string[];
  runStatus: string;
}

// ─── Status styles ──────────────────────────────────────────────

const STATUS_BG: Record<string, string> = {
  pending: "bg-zinc-900 border-zinc-700/50",
  running: "bg-blue-950 border-blue-500 ring-1 ring-blue-500/30",
  done: "bg-emerald-950 border-emerald-600",
  failed: "bg-red-950 border-red-600",
  skipped: "bg-zinc-900/50 border-zinc-800",
};

const STATUS_DOT: Record<string, string> = {
  pending: "bg-zinc-600",
  running: "bg-blue-400 animate-pulse",
  done: "bg-emerald-400",
  failed: "bg-red-400",
  skipped: "bg-zinc-700",
};

const CAT_COLOR: Record<string, string> = {
  input: "bg-violet-500/20 text-violet-300",
  ai: "bg-cyan-500/20 text-cyan-300",
  generate: "bg-emerald-500/20 text-emerald-300",
  post: "bg-amber-500/20 text-amber-300",
  output: "bg-red-500/20 text-red-300",
};

// ─── Log parser ─────────────────────────────────────────────────

type NStatus = "running" | "done" | "failed" | "skipped";

function parseLogStatus(logs: string[]): Record<string, NStatus> {
  const s: Record<string, NStatus> = {};
  const t = logs.join("\n");
  if (t.includes("[Tags] Generating")) s.prompts = "running";
  if (t.includes("[Tags] Prompts written")) { s.prompts = "done"; s.chain = "done"; }
  if (t.includes("[Images] Generating")) s.images = "running";
  if (t.includes("[Images] Using") || t.includes("images for video")) s.images = "done";
  if (t.includes("[Music] Submitting")) s.music = "running";
  if (t.includes("Suno track ready")) s.music = "done";
  if (t.includes("Credits insufficient") || t.includes("Suno API error")) s.music = "failed";
  if (t.includes("Assembling enhanced") || t.includes("Remotion")) s.render = "running";
  if (t.includes("DONE") || t.includes("Saved to:")) s.render = "done";
  if (t.includes("[PostProcess]")) s.post = "running";
  if (t.includes("PostProcess] Done")) s.post = "done";
  if (t.includes("[Thumbnail]")) s.thumb = "running";
  if (t.includes("Thumbnail] Saved")) s.thumb = "done";
  if (t.includes("Discord") && t.includes("sent")) s.discord = "done";
  if (t.includes("Video preview sent")) s.approval = "running";
  if (t.includes("Approved") || t.includes("Exit code: 0")) s.approval = "done";
  if (t.includes("Upload complete")) s.youtube = "done";
  if (t.includes("publishing disabled")) s.youtube = "skipped";
  return s;
}

// ─── Component ──────────────────────────────────────────────────

export function PipelineGraph({ profile, logs, runStatus }: PipelineGraphProps) {
  const [profileData, setProfileData] = useState<any>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/config/profiles/${profile.replace("-", "_")}`)
      .then(r => r.json())
      .then(d => setProfileData(d.config || d))
      .catch(() => {});
  }, [profile]);

  const d = profileData || {};
  const ls = parseLogStatus(logs);

  function ns(id: string): GraphNode["status"] {
    if (runStatus === "idle") return "pending";
    if (ls[id]) return ls[id];
    if (runStatus === "done") return "done";
    return "pending";
  }

  // ─── Build nodes in execution order ──────────────────────────
  // Groups: each group renders as a row, parallel nodes side-by-side

  type Group = { nodes: GraphNode[]; connector?: "split" | "merge" };

  const groups: Group[] = [
    // Row 1: Inputs
    {
      nodes: [
        { id: "tags", label: "Tags Input", icon: "🏷", category: "input", prompt: d.video?.mood || "(user tags)", sub: "Comma-separated keywords → drives everything", status: runStatus !== "idle" ? "done" : "pending", deps: [], lane: 0 },
        ...(d.style_ref?.handle ? [{ id: "style", label: "Style Ref", icon: "🎨", category: "input" as const, prompt: `@${d.style_ref.handle} (${d.style_ref.backend || "replicate"})`, sub: `${d.style_ref.max_reference_images || 6} reference images`, status: "done" as const, deps: [] as string[], lane: 1 }] : []),
      ],
    },
    // Row 2: AI generation
    {
      nodes: [
        { id: "prompts", label: "Claude Prompt Gen", icon: "🤖", category: "ai", prompt: `System: "World-class AI content director"\nInput: tags → Output: 9 prompt sections via Claude Sonnet`, sub: "positive, negative, 8 scenes, music, thumb, YT title/desc/tags", status: ns("prompts"), deps: ["tags"], lane: 0, result: d.sdxl?.positive_prompt ? "✓ 9 sections" : undefined },
      ],
    },
    // Row 3: Prompt chain detail
    {
      nodes: [
        { id: "chain", label: "Prompt Chain", icon: "⛓", category: "ai",
          prompt: [
            `POSITIVE: ${(d.sdxl?.positive_prompt || "(pending)").slice(0, 100)}`,
            `NEGATIVE: ${d.sdxl?.negative_prompt || "(pending)"}`,
            `SCENES: ${d.sdxl?.scene_templates?.length || 0} cinematic templates`,
            `MUSIC: ${(d.suno?.prompt_tags || d.video?.music_prompt || "(pending)").slice(0, 80)}`,
            `THUMB TEXT: ${d.publish?.thumbnail_text || "(pending)"}`,
            `THUMB PROMPT: ${((d.publish as any)?.thumbnail_prompt || "(pending)").slice(0, 80)}`,
            `YT TITLE: ${d.publish?.youtube_title || "(pending)"}`,
            `YT DESC: ${(d.publish?.youtube_description || "").length} chars`,
            `YT TAGS: ${d.publish?.youtube_tags?.length || 0} SEO tags`,
          ].join("\n"),
          sub: "All 9 sections saved to profile YAML", status: ns("chain"), deps: ["prompts"], lane: 0 },
      ],
    },
    // Row 4: Parallel generation (images + music)
    {
      connector: "split",
      nodes: [
        { id: "images", label: "Image Generation", icon: "🖼", category: "generate", prompt: (d.sdxl?.positive_prompt || d.video?.style_prompt || "(from chain)").slice(0, 150), sub: `Seedream → Gemini → DALL-E → SD fallback • 1 base → ${d.video?.scene_count || 8} variants`, status: ns("images"), deps: ["chain"], lane: 0, result: ls.images === "done" ? "✓" : undefined },
        { id: "music", label: "Music Generation", icon: "🎵", category: "generate", prompt: d.suno?.prompt_tags || d.video?.music_prompt || "(from chain)", sub: `Suno V4.5 (kie.ai) • ${d.suno?.genre || "?"} • 2 tracks`, status: ns("music"), deps: ["chain"], lane: 1, result: ls.music === "failed" ? "✗ silent" : ls.music === "done" ? "✓" : undefined },
      ],
    },
    // Row 5: Render (merges images + music)
    {
      connector: "merge",
      nodes: [
        { id: "render", label: "Video Render", icon: "🎬", category: "generate", prompt: `Remotion: ${d.video?.scene_count || 8} scenes • ${d.video?.duration_minutes || 3} min • spring physics + parallax + particles`, sub: "TransitionSeries + wipe/fade transitions + timer overlay", status: ns("render"), deps: ["images", "music"], lane: 0 },
      ],
    },
    // Row 6: Post-process
    {
      nodes: [
        { id: "post", label: "Post-Process", icon: "✂", category: "post", prompt: `Watermark: "${d.post?.watermark_text || "channel"}" at ${d.post?.watermark_position || "bottom-right"}\nSubtitles: ${d.post?.subtitles_enabled ? "ON" : "off"}\nIntro/Outro: ${d.post?.intro_enabled ? "ON" : "off"}`, sub: "FFmpeg: watermark → subtitles → intro/outro", status: ns("post"), deps: ["render"], lane: 0 },
      ],
    },
    // Row 7: Thumbnail
    {
      nodes: [
        { id: "thumb", label: "Thumbnail", icon: "📸", category: "post",
          prompt: [
            `STEP 1: Extract best frame (OpenCV Laplacian sharpness, 10 samples)`,
            `STEP 2: img2img enhance: ${((d.publish as any)?.thumbnail_prompt || "dramatic lighting, vibrant").slice(0, 80)}`,
            `STEP 3: Claude Vision analyzes image → designs text overlay`,
            `  text: "${d.publish?.thumbnail_text || "?"}"`,
            `  → picks position, font_size, color, glow, emphasis word`,
          ].join("\n"),
          sub: "Seedream img2img → Claude Vision text design → Pillow composite", status: ns("thumb"), deps: ["post"], lane: 0 },
      ],
    },
    // Row 8: Parallel outputs (Discord + YouTube prep)
    {
      connector: "split",
      nodes: [
        { id: "discord", label: "Discord Preview", icon: "💬", category: "output", prompt: "Send 15s video snippet + thumbnail image to Discord webhook", sub: "Preview for human approval before publishing", status: ns("discord"), deps: ["thumb"], lane: 0 },
        { id: "approval", label: "Approval Gate", icon: "✅", category: "output", prompt: "CLI: [Enter]=approve, [r]=reject+regenerate (up to 5 attempts)", sub: "Pipeline pauses until human approves", status: ns("approval"), deps: ["discord"], lane: 1 },
      ],
    },
    // Row 9: YouTube
    {
      nodes: [
        { id: "youtube", label: "YouTube Upload", icon: "📺", category: "output",
          prompt: [
            `Title: ${(d.publish?.youtube_title || "(from chain)").slice(0, 60)}`,
            `Description: ${(d.publish?.youtube_description || "").length} chars, ${(d.publish?.youtube_description || "").split("\n\n").length} paragraphs`,
            `Tags: ${d.publish?.youtube_tags?.length || 0} SEO tags`,
            `Privacy: ${d.publish?.youtube_privacy || "private"}`,
            `Thumbnail: uploaded via thumbnails.set API`,
          ].join("\n"),
          sub: "Resumable upload + thumbnail.set + quota guard (1600 units)", status: ns("youtube"), deps: ["approval"], lane: 0 },
      ],
    },
  ];

  const allNodes = groups.flatMap(g => g.nodes);
  const nodeMap = Object.fromEntries(allNodes.map(n => [n.id, n]));
  const selectedNode = selected ? nodeMap[selected] : null;

  const counts = { done: 0, running: 0, failed: 0, pending: 0, skipped: 0 };
  allNodes.forEach(n => { counts[n.status]++; });
  const total = allNodes.length;
  const progress = Math.round((counts.done / total) * 100);

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex gap-2">
            {counts.done > 0 && <span className="text-emerald-400">{counts.done} done</span>}
            {counts.running > 0 && <span className="text-blue-400">{counts.running} running</span>}
            {counts.failed > 0 && <span className="text-red-400">{counts.failed} failed</span>}
            {counts.pending > 0 && <span className="text-zinc-500">{counts.pending} pending</span>}
          </div>
          <span className="text-zinc-500">{progress}%</span>
        </div>
        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${progress}%`,
              background: counts.failed > 0
                ? "linear-gradient(90deg, #22c55e, #ef4444)"
                : counts.running > 0
                  ? "linear-gradient(90deg, #22c55e, #3b82f6)"
                  : "#22c55e",
            }}
          />
        </div>
      </div>

      {/* Graph rows */}
      <div className="space-y-2">
        {groups.map((group, gi) => (
          <div key={gi}>
            {/* Connector line between groups */}
            {gi > 0 && (
              <div className="flex justify-center py-1">
                <div className="flex items-center gap-1 text-zinc-600">
                  {group.connector === "split" && <span className="text-[10px]">splits into parallel</span>}
                  {group.connector === "merge" && <span className="text-[10px]">merges</span>}
                  <svg width="16" height="16" viewBox="0 0 16 16">
                    <path d="M8,2 L8,14 M4,10 L8,14 L12,10" stroke="currentColor" fill="none" strokeWidth="1.5" />
                  </svg>
                </div>
              </div>
            )}

            {/* Node row */}
            <div className={`grid gap-2 ${group.nodes.length > 1 ? "grid-cols-2" : "grid-cols-1"}`}>
              {group.nodes.map(node => {
                const isSelected = selected === node.id;
                return (
                  <button
                    key={node.id}
                    onClick={() => setSelected(isSelected ? null : node.id)}
                    className={`text-left rounded-xl border p-3 transition-all hover:brightness-125 ${STATUS_BG[node.status]} ${isSelected ? "ring-2 ring-white/50" : ""}`}
                  >
                    <div className="flex items-start gap-2.5">
                      {/* Status dot */}
                      <div className={`mt-0.5 h-2.5 w-2.5 rounded-full shrink-0 ${STATUS_DOT[node.status]}`} />

                      <div className="flex-1 min-w-0">
                        {/* Header: icon + label + category + result */}
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-sm">{node.icon}</span>
                          <span className="text-xs font-semibold text-zinc-200">{node.label}</span>
                          <span className={`text-[9px] px-1.5 py-0.5 rounded-md ${CAT_COLOR[node.category]}`}>
                            {node.category}
                          </span>
                          {node.result && (
                            <span className="text-[10px] text-emerald-400 font-mono ml-auto">{node.result}</span>
                          )}
                        </div>

                        {/* Prompt preview (first line) */}
                        <p className="text-[11px] text-zinc-400 mt-1 line-clamp-2 leading-relaxed">
                          {node.prompt.split("\n")[0]}
                        </p>

                        {/* Sub */}
                        <p className="text-[10px] text-zinc-600 mt-0.5">{node.sub}</p>
                      </div>

                      {/* Expand */}
                      <span className="text-zinc-600 text-[10px] shrink-0 mt-1">{isSelected ? "▾" : "▸"}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Selected detail panel */}
      {selectedNode && (
        <div className="rounded-xl border border-zinc-700 bg-zinc-900/80 p-4 space-y-3 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-base">{selectedNode.icon}</span>
              <span className="text-sm font-semibold text-zinc-200">{selectedNode.label}</span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-md ${CAT_COLOR[selectedNode.category]}`}>
                {selectedNode.category}
              </span>
              <Badge variant="outline" className="text-[10px]">{selectedNode.status}</Badge>
            </div>
            <button onClick={() => setSelected(null)} className="text-zinc-500 hover:text-zinc-300">✕</button>
          </div>

          <p className="text-xs text-zinc-400">{selectedNode.sub}</p>

          {selectedNode.deps.length > 0 && (
            <div className="text-[10px] text-zinc-500">
              Depends on: {selectedNode.deps.map(d => (
                <button key={d} onClick={() => setSelected(d)} className="text-blue-400 hover:underline mr-1.5">
                  {nodeMap[d]?.icon} {nodeMap[d]?.label || d}
                </button>
              ))}
            </div>
          )}

          <pre className="text-[11px] font-mono text-zinc-300 whitespace-pre-wrap bg-black/60 rounded-lg p-3 max-h-52 overflow-y-auto border border-zinc-800 leading-relaxed">
            {selectedNode.prompt}
          </pre>

          {selectedNode.result && (
            <p className="text-xs text-emerald-400 font-mono">{selectedNode.result}</p>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";

// ─── Types ──────────────────────────────────────────────────────

interface GraphNode {
  id: string;
  label: string;
  category: "input" | "ai" | "generate" | "post" | "output";
  prompt: string;
  sub: string;
  status: "pending" | "running" | "done" | "failed" | "skipped";
  result?: string;
  deps: string[];
  col: number;  // column position (0-based)
  row: number;  // row position (0-based)
}

interface PipelineGraphProps {
  profile: string;
  logs: string[];
  runStatus: string;
}

// ─── Constants ──────────────────────────────────────────────────

const NODE_W = 220;
const NODE_H = 64;
const COL_GAP = 40;
const ROW_GAP = 24;
const PAD = 20;

const STATUS_COLORS: Record<string, { fill: string; stroke: string; text: string; dot: string }> = {
  pending:  { fill: "#18181b", stroke: "#3f3f46", text: "#a1a1aa", dot: "#71717a" },
  running:  { fill: "#172554", stroke: "#3b82f6", text: "#93c5fd", dot: "#60a5fa" },
  done:     { fill: "#052e16", stroke: "#22c55e", text: "#86efac", dot: "#4ade80" },
  failed:   { fill: "#450a0a", stroke: "#ef4444", text: "#fca5a5", dot: "#f87171" },
  skipped:  { fill: "#18181b", stroke: "#27272a", text: "#52525b", dot: "#3f3f46" },
};

const CAT_BADGE: Record<string, string> = {
  input: "#8b5cf6", ai: "#06b6d4", generate: "#10b981", post: "#f59e0b", output: "#ef4444",
};

// ─── Log parser ─────────────────────────────────────────────────

function parseLogStatus(logs: string[]): Record<string, GraphNode["status"]> {
  const s: Record<string, GraphNode["status"]> = {};
  const t = logs.join("\n");
  if (t.includes("[Tags] Generating")) s["prompts"] = "running";
  if (t.includes("[Tags] Prompts written")) { s["prompts"] = "done"; s["chain"] = "done"; }
  if (t.includes("[Images] Generating")) s["images"] = "running";
  if (t.includes("[Images] Using") || t.includes("images for video")) s["images"] = "done";
  if (t.includes("[Music] Submitting")) s["music"] = "running";
  if (t.includes("Suno track ready")) s["music"] = "done";
  if (t.includes("Credits insufficient") || t.includes("Suno API error")) s["music"] = "failed";
  if (t.includes("Assembling enhanced") || t.includes("Remotion")) s["render"] = "running";
  if (t.includes("DONE") || t.includes("Saved to:")) s["render"] = "done";
  if (t.includes("[PostProcess]")) s["post"] = "running";
  if (t.includes("PostProcess] Done")) s["post"] = "done";
  if (t.includes("[Thumbnail]")) s["thumb"] = "running";
  if (t.includes("Thumbnail] Saved")) s["thumb"] = "done";
  if (t.includes("Discord") && t.includes("sent")) s["discord"] = "done";
  if (t.includes("Video preview sent")) s["approval"] = "running";
  if (t.includes("Approved") || t.includes("Exit code: 0")) s["approval"] = "done";
  if (t.includes("Upload complete")) s["youtube"] = "done";
  if (t.includes("publishing disabled")) s["youtube"] = "skipped";
  return s;
}

// ─── Component ──────────────────────────────────────────────────

export function PipelineGraph({ profile, logs, runStatus }: PipelineGraphProps) {
  const [profileData, setProfileData] = useState<any>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

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
    if (runStatus === "running") return "pending";
    if (runStatus === "done") return "done";
    return "pending";
  }

  // ─── Define graph layout ────────────────────────────────────
  // Col 0: inputs, Col 1: AI, Col 2: parallel gen, Col 3: post, Col 4: output
  const nodes: GraphNode[] = [
    { id: "tags", label: "Tags", category: "input", col: 0, row: 0, deps: [],
      prompt: d.video?.mood || "(user tags)", sub: "Comma-separated keywords", status: runStatus !== "idle" ? "done" : "pending" },
    ...(d.style_ref?.handle ? [{ id: "style", label: "Style Ref", category: "input" as const, col: 0, row: 1, deps: [] as string[],
      prompt: `@${d.style_ref.handle}`, sub: `${d.style_ref.max_reference_images || 6} images`, status: "done" as const }] : []),
    { id: "prompts", label: "Claude Gen", category: "ai", col: 1, row: 0, deps: ["tags"],
      prompt: `System: AI content director\nTags → 9 sections via Claude Sonnet`, sub: "positive, negative, 8 scenes, music, thumb, YT", status: ns("prompts"),
      result: d.sdxl?.positive_prompt ? "✓" : undefined },
    { id: "chain", label: "Prompt Chain", category: "ai", col: 1, row: 1, deps: ["prompts"],
      prompt: [
        `+prompt: ${(d.sdxl?.positive_prompt || "").slice(0, 80)}...`,
        `-prompt: ${d.sdxl?.negative_prompt || "?"}`,
        `scenes: ${d.sdxl?.scene_templates?.length || 0}`,
        `music: ${(d.suno?.prompt_tags || d.video?.music_prompt || "").slice(0, 60)}`,
        `thumb: ${d.publish?.thumbnail_text || "?"}`,
        `thumb_prompt: ${((d.publish as any)?.thumbnail_prompt || "").slice(0, 60)}`,
        `yt_title: ${d.publish?.youtube_title || "?"}`,
        `yt_desc: ${(d.publish?.youtube_description || "").length} chars`,
        `yt_tags: ${d.publish?.youtube_tags?.length || 0}`,
      ].join("\n"),
      sub: "9 outputs saved to YAML", status: ns("chain") },
    { id: "images", label: "Images", category: "generate", col: 2, row: 0, deps: ["chain"],
      prompt: (d.sdxl?.positive_prompt || d.video?.style_prompt || "").slice(0, 120),
      sub: `1 base → ${d.video?.scene_count || 8} variants`, status: ns("images"),
      result: ls["images"] === "done" ? "✓ generated" : undefined },
    { id: "music", label: "Music", category: "generate", col: 2, row: 1, deps: ["chain"],
      prompt: d.suno?.prompt_tags || d.video?.music_prompt || "",
      sub: `Suno ${d.suno?.genre || "?"} • 2 tracks`, status: ns("music"),
      result: ls["music"] === "failed" ? "✗ silent" : ls["music"] === "done" ? "✓ ready" : undefined },
    { id: "render", label: "Remotion", category: "generate", col: 3, row: 0, deps: ["images", "music"],
      prompt: `${d.video?.scene_count || 8} scenes • ${d.video?.duration_minutes || 3}min • spring + parallax`,
      sub: "TransitionSeries + wipe/fade", status: ns("render") },
    { id: "post", label: "Post-Process", category: "post", col: 3, row: 1, deps: ["render"],
      prompt: `Watermark: "${d.post?.watermark_text || "channel"}" • Sub: ${d.post?.subtitles_enabled ? "on" : "off"}`,
      sub: "FFmpeg watermark + subtitles + intro/outro", status: ns("post") },
    { id: "thumb", label: "Thumbnail", category: "post", col: 4, row: 0, deps: ["post"],
      prompt: [
        `1. Best frame (OpenCV sharpness)`,
        `2. img2img: ${((d.publish as any)?.thumbnail_prompt || "dramatic enhance").slice(0, 60)}`,
        `3. Claude Vision → text: "${d.publish?.thumbnail_text || "?"}"`,
      ].join("\n"),
      sub: "Seedream img2img → Claude text → Pillow", status: ns("thumb") },
    { id: "discord", label: "Discord", category: "output", col: 4, row: 1, deps: ["thumb"],
      prompt: "Send 15s snippet + thumbnail to webhook", sub: "Preview for approval", status: ns("discord") },
    { id: "approval", label: "Approve", category: "output", col: 5, row: 0, deps: ["discord"],
      prompt: "CLI: Enter=approve, r=reject (up to 5x)", sub: "Gate before publish", status: ns("approval") },
    { id: "youtube", label: "YouTube", category: "output", col: 5, row: 1, deps: ["approval"],
      prompt: [
        `Title: ${(d.publish?.youtube_title || "").slice(0, 50)}`,
        `Desc: ${(d.publish?.youtube_description || "").length} chars`,
        `Tags: ${d.publish?.youtube_tags?.length || 0}`,
      ].join("\n"),
      sub: "Resumable upload + thumbnail.set", status: ns("youtube") },
  ];

  // ─── Layout calculations ────────────────────────────────────
  const maxCol = Math.max(...nodes.map(n => n.col));
  const maxRow = Math.max(...nodes.map(n => n.row));
  const svgW = (maxCol + 1) * (NODE_W + COL_GAP) + PAD * 2;
  const svgH = (maxRow + 1) * (NODE_H + ROW_GAP) + PAD * 2 + (selected ? 200 : 0);

  function nodeX(col: number) { return PAD + col * (NODE_W + COL_GAP); }
  function nodeY(row: number) { return PAD + row * (NODE_H + ROW_GAP); }
  function nodeCenterX(n: GraphNode) { return nodeX(n.col) + NODE_W / 2; }
  function nodeCenterY(n: GraphNode) { return nodeY(n.row) + NODE_H / 2; }

  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]));
  const selectedNode = selected ? nodeMap[selected] : null;

  // ─── Progress ───────────────────────────────────────────────
  const counts = { done: 0, running: 0, failed: 0, pending: 0, skipped: 0 };
  nodes.forEach(n => { counts[n.status] = (counts[n.status] || 0) + 1; });

  return (
    <div className="space-y-3">
      {/* Progress bar */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2 text-[10px]">
          {counts.done > 0 && <Badge className="bg-emerald-500/20 text-emerald-400 text-[10px]">{counts.done} done</Badge>}
          {counts.running > 0 && <Badge className="bg-blue-500/20 text-blue-400 text-[10px]">{counts.running} running</Badge>}
          {counts.failed > 0 && <Badge className="bg-red-500/20 text-red-400 text-[10px]">{counts.failed} failed</Badge>}
          {counts.pending > 0 && <Badge className="bg-zinc-500/20 text-zinc-400 text-[10px]">{counts.pending} pending</Badge>}
        </div>
        <Badge variant="outline" className="text-[10px]">{profile}</Badge>
      </div>

      {/* SVG Graph */}
      <div className="overflow-x-auto rounded-lg border border-zinc-800 bg-zinc-950">
        <svg ref={svgRef} width={svgW} height={svgH} className="min-w-full">
          <defs>
            <marker id="arrow-done" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <path d="M0,0 L8,3 L0,6" fill="#22c55e" />
            </marker>
            <marker id="arrow-running" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <path d="M0,0 L8,3 L0,6" fill="#3b82f6" />
            </marker>
            <marker id="arrow-pending" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <path d="M0,0 L8,3 L0,6" fill="#3f3f46" />
            </marker>
          </defs>

          {/* Dependency edges */}
          {nodes.map(node =>
            node.deps.map(depId => {
              const dep = nodeMap[depId];
              if (!dep) return null;
              const x1 = nodeX(dep.col) + NODE_W;
              const y1 = nodeY(dep.row) + NODE_H / 2;
              const x2 = nodeX(node.col);
              const y2 = nodeY(node.row) + NODE_H / 2;
              const edgeStatus = dep.status === "done" ? "done" : dep.status === "running" ? "running" : "pending";
              const color = STATUS_COLORS[edgeStatus].stroke;
              // Curved path
              const mx = (x1 + x2) / 2;
              return (
                <path
                  key={`${depId}-${node.id}`}
                  d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
                  fill="none"
                  stroke={color}
                  strokeWidth={edgeStatus === "done" ? 2 : 1}
                  strokeDasharray={edgeStatus === "pending" ? "4,4" : undefined}
                  markerEnd={`url(#arrow-${edgeStatus})`}
                  opacity={edgeStatus === "pending" ? 0.4 : 0.8}
                />
              );
            })
          )}

          {/* Nodes */}
          {nodes.map(node => {
            const x = nodeX(node.col);
            const y = nodeY(node.row);
            const s = STATUS_COLORS[node.status];
            const isSelected = selected === node.id;

            return (
              <g key={node.id} onClick={() => setSelected(isSelected ? null : node.id)} cursor="pointer">
                {/* Node background */}
                <rect
                  x={x} y={y} width={NODE_W} height={NODE_H} rx={8}
                  fill={s.fill} stroke={isSelected ? "#fff" : s.stroke}
                  strokeWidth={isSelected ? 2 : 1}
                />
                {/* Status dot */}
                <circle cx={x + 14} cy={y + 16} r={4} fill={s.dot}>
                  {node.status === "running" && (
                    <animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite" />
                  )}
                </circle>
                {/* Category badge */}
                <rect x={x + 24} y={y + 8} width={50} height={16} rx={4} fill={CAT_BADGE[node.category]} opacity={0.2} />
                <text x={x + 49} y={y + 20} textAnchor="middle" fontSize={8} fill={CAT_BADGE[node.category]} fontFamily="monospace">
                  {node.category}
                </text>
                {/* Label */}
                <text x={x + 80} y={y + 20} fontSize={11} fill={s.text} fontWeight="600">
                  {node.label}
                </text>
                {/* Result badge */}
                {node.result && (
                  <text x={x + NODE_W - 10} y={y + 20} textAnchor="end" fontSize={9} fill="#4ade80" fontFamily="monospace">
                    {node.result}
                  </text>
                )}
                {/* Prompt preview */}
                <text x={x + 14} y={y + 40} fontSize={9} fill={s.text} opacity={0.6}>
                  {node.prompt.split("\n")[0].slice(0, 30)}{node.prompt.length > 30 ? "..." : ""}
                </text>
                {/* Sub text */}
                <text x={x + 14} y={y + 54} fontSize={8} fill={s.text} opacity={0.4}>
                  {node.sub.slice(0, 35)}{node.sub.length > 35 ? "..." : ""}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected node detail panel */}
      {selectedNode && (
        <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full`} style={{ backgroundColor: STATUS_COLORS[selectedNode.status].dot }} />
              <span className="text-sm font-medium" style={{ color: CAT_BADGE[selectedNode.category] }}>
                {selectedNode.label}
              </span>
              <Badge className="text-[10px]" style={{ backgroundColor: CAT_BADGE[selectedNode.category] + "30", color: CAT_BADGE[selectedNode.category] }}>
                {selectedNode.category}
              </Badge>
              <Badge variant="outline" className="text-[10px]">{selectedNode.status}</Badge>
            </div>
            <button onClick={() => setSelected(null)} className="text-zinc-500 hover:text-zinc-300 text-sm">✕</button>
          </div>

          <div className="text-xs text-zinc-400">{selectedNode.sub}</div>

          {selectedNode.deps.length > 0 && (
            <div className="text-[10px] text-zinc-500">
              Dependencies: {selectedNode.deps.map(d => (
                <button key={d} onClick={() => setSelected(d)} className="text-blue-400 hover:underline mr-1">{d}</button>
              ))}
            </div>
          )}

          <pre className="text-[11px] font-mono text-zinc-300 whitespace-pre-wrap bg-black/50 rounded p-3 max-h-48 overflow-y-auto border border-zinc-800">
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

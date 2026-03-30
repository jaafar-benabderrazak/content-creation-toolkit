"use client";

import { useEffect, useRef, useState } from "react";

interface LogData {
  run_id: string;
  status: string;
  total_lines: number;
  offset: number;
  lines: string[];
}

export function LiveLogs() {
  const [logs, setLogs] = useState<string[]>([]);
  const [runId, setRunId] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);

  async function fetchLogs() {
    try {
      // Always fetch ALL lines from offset 0 — no incremental
      const res = await fetch(`/api/logs?offset=0`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || `HTTP ${res.status}`);
        return;
      }
      setError("");
      const data: LogData = await res.json();

      if (data.run_id) setRunId(data.run_id);
      setStatus(data.status || "unknown");

      if (data.lines) {
        setLogs(data.lines.slice(-500)); // Last 500 lines
      }
    } catch {
      setError("Cannot reach pipeline server");
    }
  }

  // Poll every 2s
  useEffect(() => {
    fetchLogs();
    const id = setInterval(fetchLogs, 2000);
    return () => clearInterval(id);
  }, []);

  // Auto-scroll to bottom (only if user hasn't scrolled up)
  useEffect(() => {
    if (containerRef.current && autoScrollRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  function handleScroll() {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    // If user is within 50px of bottom, keep auto-scrolling
    autoScrollRef.current = scrollHeight - scrollTop - clientHeight < 50;
  }

  const statusColor =
    status === "running" ? "text-blue-400"
    : status === "done" ? "text-emerald-400"
    : status === "failed" ? "text-red-400"
    : "text-zinc-500";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="text-zinc-400">Run:</span>
          <code className="text-[10px] text-zinc-300 bg-zinc-800 px-1.5 py-0.5 rounded">{runId || "—"}</code>
        </div>
        <div className="flex items-center gap-3">
          <span className={`font-medium ${statusColor}`}>
            {status === "running" ? "● Running" : status === "done" ? "✓ Done" : status === "failed" ? "✗ Failed" : "○ Idle"}
          </span>
          <span className="text-zinc-500">{logs.length} lines</span>
          <button onClick={fetchLogs} className="text-[10px] text-blue-400 hover:underline">Refresh</button>
        </div>
      </div>

      {error && <p className="text-xs text-red-500 bg-red-500/10 rounded p-2">{error}</p>}

      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-[400px] overflow-y-auto font-mono text-[11px] bg-zinc-950 text-zinc-300 rounded-lg border border-zinc-800 p-3 leading-relaxed"
      >
        {logs.length === 0 ? (
          <span className="text-zinc-600">
            Waiting for pipeline output... Trigger a run to see logs here.
          </span>
        ) : (
          logs.map((line, i) => {
            // Color-code log lines
            let cls = "";
            if (line.includes("WARNING") || line.includes("⚠")) cls = "text-yellow-500";
            else if (line.includes("ERROR") || line.includes("✗") || line.includes("failed")) cls = "text-red-400";
            else if (line.includes("DONE") || line.includes("✓") || line.includes("complete")) cls = "text-emerald-400";
            else if (line.includes("[Tags]") || line.includes("[Config]")) cls = "text-cyan-400";
            else if (line.includes("[Images]") || line.includes("[Music]")) cls = "text-violet-400";
            else if (line.includes("[Video]") || line.includes("Remotion")) cls = "text-amber-400";
            else if (line.includes("Discord") || line.includes("YouTube")) cls = "text-blue-400";
            else if (line.includes("%|")) cls = "text-zinc-500"; // progress bars

            return <div key={i} className={cls}>{line}</div>;
          })
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { usePipelineUrl } from "@/hooks/use-pipeline";

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
  const offsetRef = useRef(0);
  const pipelineUrl = usePipelineUrl();

  async function fetchLogs() {
    const base = pipelineUrl;
    if (!base) return;
    try {
      const res = await fetch(
        `${base}/logs?run_id=${runId}&offset=${offsetRef.current}`,
        { headers: { Accept: "application/json" } }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.error || `HTTP ${res.status}`);
        return;
      }
      setError("");
      const data: LogData = await res.json();

      if (data.run_id && data.run_id !== runId) {
        setRunId(data.run_id);
      }
      setStatus(data.status || "unknown");

      if (data.lines && data.lines.length > 0) {
        setLogs((prev) => {
          const combined = [...prev, ...data.lines];
          return combined.slice(-500);
        });
        offsetRef.current = data.offset + data.lines.length;
      }
    } catch {
      setError("Cannot reach pipeline server");
    }
  }

  useEffect(() => {
    fetchLogs();
    const id = setInterval(fetchLogs, 2000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const statusColor =
    status === "running"
      ? "text-yellow-500"
      : status === "done"
        ? "text-green-500"
        : status === "error" || status === "failed"
          ? "text-red-500"
          : "text-muted-foreground";

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span>
          Run: <code className="text-xs">{runId || "(none)"}</code>
        </span>
        <span className={statusColor}>
          {status === "running" ? "Running..." : status}
        </span>
        <span className="text-muted-foreground">{logs.length} lines</span>
      </div>

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}

      <div
        ref={containerRef}
        className="max-h-[500px] overflow-y-auto font-mono text-xs bg-black text-green-400 rounded border p-3 whitespace-pre-wrap"
      >
        {logs.length === 0 ? (
          <span className="text-muted-foreground">
            Waiting for pipeline output... Trigger a run to see logs here.
          </span>
        ) : (
          logs.map((line, i) => <div key={i}>{line}</div>)
        )}
      </div>
    </div>
  );
}

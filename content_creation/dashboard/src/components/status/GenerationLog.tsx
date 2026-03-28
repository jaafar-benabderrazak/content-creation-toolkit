"use client";

import { useEffect, useRef, useState } from "react";
import type { StatusEntry } from "@/lib/store";

interface GenerationLogProps {
  autoRefresh?: boolean; // default true
}

function formatTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toTimeString().slice(0, 8); // HH:MM:SS
  } catch {
    return isoString;
  }
}

function levelClass(level: StatusEntry["level"]): string {
  if (level === "warning") return "text-yellow-600";
  if (level === "error") return "text-red-600";
  return "";
}

export function GenerationLog({ autoRefresh = true }: GenerationLogProps) {
  const [entries, setEntries] = useState<StatusEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  async function fetchEntries() {
    try {
      const res = await fetch("/api/status");
      const data = await res.json();
      setEntries(data.entries ?? []);
    } catch {
      // silent — keep previous entries on transient network errors
    } finally {
      setLoading(false);
    }
  }

  // Scroll to bottom whenever entries change
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [entries]);

  useEffect(() => {
    fetchEntries();
    if (!autoRefresh) return;
    const id = setInterval(() => fetchEntries(), 3000);
    return () => clearInterval(id);
  }, [autoRefresh]);

  // Show last 20 entries, newest at top
  const display = [...entries].slice(-20).reverse();

  return (
    <div
      ref={containerRef}
      className="max-h-96 overflow-y-auto font-mono text-sm bg-muted/30 rounded border p-3"
    >
      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : display.length === 0 ? (
        <p className="text-muted-foreground">No generation activity yet.</p>
      ) : (
        display.map((entry, i) => (
          <div key={i} className={levelClass(entry.level)}>
            [{formatTime(entry.timestamp)}] [{entry.stage}] {entry.message}
          </div>
        ))
      )}
    </div>
  );
}

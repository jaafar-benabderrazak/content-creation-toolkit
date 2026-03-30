"use client";

import { useEffect, useMemo, useState } from "react";
import { usePipelineUrl, pipelineFetch } from "@/hooks/use-pipeline";

interface RoadmapEntry {
  id: string;
  title: string;
  tags: string;
  profile: string;
  status: string;
}

interface RoadmapPickerProps {
  onSelect: (entry: RoadmapEntry) => void;
}

export function RoadmapPicker({ onSelect }: RoadmapPickerProps) {
  const [entries, setEntries] = useState<RoadmapEntry[]>([]);
  const [search, setSearch] = useState("");
  const [universe, setUniverse] = useState("all");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const pipelineUrl = usePipelineUrl();

  useEffect(() => {
    if (!pipelineUrl) return;
    setLoading(true);
    pipelineFetch(pipelineUrl, "/roadmap?status=planned")
      .then((data: any) => {
        if (data.error) {
          setError(data.error);
        }
        setEntries(data.entries || []);
      })
      .catch((e: Error) => setError(`Fetch failed: ${e.message || e}`))
      .finally(() => setLoading(false));
  }, [pipelineUrl]);

  // Extract universe groups from titles like "[Solarpunk] Solar Garden Study"
  const universes = useMemo(() => {
    const set = new Set<string>();
    set.add("all");
    for (const e of entries) {
      const match = e.title.match(/^\[([^\]]+)\]/);
      if (match) set.add(match[1]);
    }
    // Add "Lofi" for entries without brackets
    const hasNoBracket = entries.some((e) => !e.title.startsWith("["));
    if (hasNoBracket) set.add("Lofi");
    return Array.from(set);
  }, [entries]);

  const filtered = useMemo(() => {
    let list = entries;

    // Universe filter
    if (universe !== "all") {
      if (universe === "Lofi") {
        list = list.filter((e) => !e.title.startsWith("["));
      } else {
        list = list.filter((e) => e.title.startsWith(`[${universe}]`));
      }
    }

    // Search filter
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (e) =>
          e.title.toLowerCase().includes(q) ||
          e.tags.toLowerCase().includes(q)
      );
    }

    return list;
  }, [entries, universe, search]);

  function handleSelect(entry: RoadmapEntry) {
    onSelect(entry);
    setOpen(false);
    setSearch("");
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading roadmap...</p>;
  }

  return (
    <div className="space-y-2">
      {error && (
        <p className="text-xs text-red-500 bg-red-500/10 rounded p-2">{error}</p>
      )}
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-muted-foreground">
          Pick from Roadmap ({entries.length} planned)
        </label>
        <button
          onClick={() => setOpen(!open)}
          className="text-xs text-blue-500 hover:underline"
        >
          {open ? "Close" : "Browse all"}
        </button>
      </div>

      {/* Search + Universe filter (always visible) */}
      <div className="flex gap-2">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setOpen(true); }}
          placeholder="Search videos by title or tags..."
          className="flex-1 h-9 rounded-md border border-input bg-background px-3 text-sm"
          onFocus={() => setOpen(true)}
        />
        <select
          value={universe}
          onChange={(e) => { setUniverse(e.target.value); setOpen(true); }}
          className="h-9 rounded-md border border-input bg-background px-2 text-xs"
        >
          {universes.map((u) => (
            <option key={u} value={u}>
              {u === "all" ? `All (${entries.length})` : `${u} (${entries.filter(
                (e) => u === "Lofi" ? !e.title.startsWith("[") : e.title.startsWith(`[${u}]`)
              ).length})`}
            </option>
          ))}
        </select>
      </div>

      {/* Dropdown results */}
      {open && (
        <div className="max-h-[350px] overflow-y-auto border rounded-md bg-background shadow-lg">
          {filtered.length === 0 ? (
            <p className="p-3 text-sm text-muted-foreground">No matching videos</p>
          ) : (
            filtered.map((entry) => (
              <button
                key={entry.id}
                onClick={() => handleSelect(entry)}
                className="w-full text-left px-3 py-2 hover:bg-accent hover:text-accent-foreground border-b last:border-b-0 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{entry.title}</span>
                  <span className="text-[10px] text-muted-foreground ml-2 shrink-0">{entry.profile}</span>
                </div>
                <p className="text-xs text-muted-foreground truncate">{entry.tags}</p>
              </button>
            ))
          )}
          {filtered.length > 0 && (
            <p className="text-[10px] text-muted-foreground text-center py-1 border-t">
              Showing {filtered.length} of {entries.length}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface RoadmapEntry {
  id: string;
  title: string;
  tags: string;
  profile: string;
  status: string;
  notes: string;
}

const STATUS_COLORS: Record<string, string> = {
  planned: "bg-blue-500/20 text-blue-400",
  producing: "bg-yellow-500/20 text-yellow-400",
  published: "bg-green-500/20 text-green-400",
};

export default function RoadmapPage() {
  const [entries, setEntries] = useState<RoadmapEntry[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Add form
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");
  const [adding, setAdding] = useState(false);

  async function fetchEntries() {
    try {
      const url = filter === "all" ? "/api/roadmap" : `/api/roadmap?status=${filter}`;
      const res = await fetch(url);
      const data = await res.json();
      setEntries(data.entries || []);
      setError("");
    } catch {
      setError("Cannot reach pipeline server");
    } finally {
      setLoading(false);
    }
  }

  async function addEntry() {
    if (!title.trim()) return;
    setAdding(true);
    try {
      await fetch("/api/roadmap", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "add", title, tags, profile: "cinematic" }),
      });
      setTitle("");
      setTags("");
      fetchEntries();
    } catch {
      setError("Failed to add entry");
    } finally {
      setAdding(false);
    }
  }

  async function updateStatus(id: string, status: string) {
    await fetch("/api/roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "update_status", id, status }),
    });
    fetchEntries();
  }

  async function deleteEntry(id: string) {
    await fetch("/api/roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "delete", id }),
    });
    fetchEntries();
  }

  useEffect(() => { fetchEntries(); }, [filter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Content Roadmap</h1>
        <span className="text-sm text-muted-foreground">{entries.length} videos</span>
      </div>

      {/* Add Entry */}
      <Card>
        <CardHeader><CardTitle>Add Video</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Video title"
              className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Tags (comma-separated)"
              className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <Button onClick={addEntry} disabled={adding || !title.trim()}>
              {adding ? "Adding..." : "Add"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex gap-2">
        {["all", "planned", "producing", "published"].map((s) => (
          <Button
            key={s}
            variant={filter === s ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(s)}
          >
            {s}
          </Button>
        ))}
        <Button variant="ghost" size="sm" onClick={fetchEntries}>Refresh</Button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {/* Entries Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-auto max-h-[600px]">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-card border-b">
                <tr>
                  <th className="text-left p-3 font-medium">#</th>
                  <th className="text-left p-3 font-medium">Title</th>
                  <th className="text-left p-3 font-medium">Status</th>
                  <th className="text-left p-3 font-medium">Tags</th>
                  <th className="text-left p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className="p-3 text-muted-foreground">Loading...</td></tr>
                ) : entries.length === 0 ? (
                  <tr><td colSpan={5} className="p-3 text-muted-foreground">No entries</td></tr>
                ) : (
                  entries.map((e, i) => (
                    <tr key={e.id} className="border-b hover:bg-muted/30">
                      <td className="p-3 text-muted-foreground">{i + 1}</td>
                      <td className="p-3 font-medium">{e.title}</td>
                      <td className="p-3">
                        <Badge className={STATUS_COLORS[e.status] || ""}>{e.status}</Badge>
                      </td>
                      <td className="p-3 text-muted-foreground text-xs max-w-[200px] truncate">{e.tags}</td>
                      <td className="p-3">
                        <div className="flex gap-1">
                          {e.status === "planned" && (
                            <Button size="sm" variant="outline" onClick={() => updateStatus(e.id, "producing")}>
                              Start
                            </Button>
                          )}
                          {e.status === "producing" && (
                            <Button size="sm" variant="outline" onClick={() => updateStatus(e.id, "published")}>
                              Publish
                            </Button>
                          )}
                          <Button size="sm" variant="ghost" className="text-red-500" onClick={() => deleteEntry(e.id)}>
                            Del
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

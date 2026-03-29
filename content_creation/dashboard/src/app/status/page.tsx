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

export default function StatusPage() {
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState("lofi_study");
  const [tags, setTags] = useState("");
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
        body: JSON.stringify({ profile: selectedProfile, tags }),
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
            <Button onClick={handleTrigger} disabled={triggering}>
              {triggering ? "Triggering..." : "Generate Video"}
            </Button>
          </div>

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

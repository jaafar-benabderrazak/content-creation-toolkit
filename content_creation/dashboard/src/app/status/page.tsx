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

const COST_TABLE = {
  image: { seedream: 0.04, dalle: 0.08, local: 0 },
  music: { suno: 0.01, fallback: 0 },  // per credit (~100 credits per song)
  prompts: { claude: 0.003, openai: 0.002 },
  youtube: 0, // free (quota-based)
  remotion: 0, // local render
};

function estimateCost(budget: string): { total: number; breakdown: Record<string, number> } {
  const b = budget || "standard";
  const breakdown: Record<string, number> = {};

  if (b === "free") {
    breakdown["Image (Local SD)"] = 0;
    breakdown["Music (Silent)"] = 0;
    breakdown["Prompts (Claude)"] = COST_TABLE.prompts.claude;
  } else if (b === "budget") {
    breakdown["Image (DALL-E)"] = COST_TABLE.image.dalle;
    breakdown["Music (Suno x2)"] = COST_TABLE.music.suno * 2;
    breakdown["Prompts (Claude)"] = COST_TABLE.prompts.claude;
  } else if (b === "standard") {
    breakdown["Image (Seedream)"] = COST_TABLE.image.seedream;
    breakdown["Music (Suno x2)"] = COST_TABLE.music.suno * 2;
    breakdown["Prompts (Claude)"] = COST_TABLE.prompts.claude;
    breakdown["YouTube Upload"] = 0;
  } else if (b === "premium") {
    breakdown["Image (Seedream HD)"] = COST_TABLE.image.seedream * 2;
    breakdown["Music (Suno x4)"] = COST_TABLE.music.suno * 4;
    breakdown["Prompts (Claude)"] = COST_TABLE.prompts.claude;
    breakdown["YouTube Upload"] = 0;
  }

  const total = Object.values(breakdown).reduce((a, b) => a + b, 0);
  return { total, breakdown };
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
          <Card className="bg-muted/30 border-dashed">
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Estimated Cost</span>
                <span className="text-lg font-bold">
                  ${estimateCost(budget).total.toFixed(3)}
                </span>
              </div>
              <div className="space-y-1">
                {Object.entries(estimateCost(budget).breakdown).map(([key, val]) => (
                  <div key={key} className="flex justify-between text-xs text-muted-foreground">
                    <span>{key}</span>
                    <span>{val === 0 ? "Free" : `$${val.toFixed(3)}`}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

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

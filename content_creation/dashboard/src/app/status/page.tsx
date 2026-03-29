"use client";

import { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { GenerationLog } from "@/components/status/GenerationLog";
import { LiveLogs } from "@/components/status/LiveLogs";

export default function StatusPage() {
  const [triggering, setTriggering] = useState(false);
  const [triggerResult, setTriggerResult] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState("");

  async function handleTrigger() {
    setTriggering(true);
    setTriggerResult(null);
    try {
      const res = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: selectedProfile }),
      });
      const data = await res.json();
      if (data.triggered) {
        setTriggerResult("Trigger sent — watch the log below for progress.");
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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Pipeline Status</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Trigger Generation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3 items-end">
            <Select value={selectedProfile} onValueChange={setSelectedProfile}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select profile" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="lofi_study">lofi_study</SelectItem>
                <SelectItem value="tech_tutorial">tech_tutorial</SelectItem>
                <SelectItem value="cinematic">cinematic</SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={handleTrigger}
              disabled={triggering || !selectedProfile}
            >
              {triggering ? "Triggering..." : "Trigger Generation"}
            </Button>
          </div>
          {triggerResult && (
            <p
              className={
                triggerResult.startsWith("Error")
                  ? "text-red-600 text-sm"
                  : "text-green-600 text-sm"
              }
            >
              {triggerResult}
            </p>
          )}
          <p className="text-xs text-muted-foreground">
            Requires PIPELINE_TRIGGER_URL to be configured (local ngrok
            endpoint).
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Live Pipeline Output</CardTitle>
          <CardDescription>
            Real-time stdout from the local pipeline server (polls every 2s via ngrok)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LiveLogs />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Event Log</CardTitle>
          <CardDescription>
            Status events from webhook callbacks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <GenerationLog autoRefresh={true} />
        </CardContent>
      </Card>
    </div>
  );
}

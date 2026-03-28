"use client";

import * as React from "react";
import { ProfileEditor } from "@/components/config/ProfileEditor";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { PipelineConfig, ProfileWithProvenance } from "@/types/pipeline";

export default function ConfigPage() {
  const [profiles, setProfiles] = React.useState<string[]>([]);
  const [selectedProfile, setSelectedProfile] = React.useState<string>("");
  const [config, setConfig] = React.useState<PipelineConfig | null>(null);
  const [provenance, setProvenance] = React.useState<Record<string, "env" | "yaml">>({});
  const [loadError, setLoadError] = React.useState<string | null>(null);
  const [profilesError, setProfilesError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  // Fetch profile list on mount
  React.useEffect(() => {
    fetchProfiles();
  }, []);

  async function fetchProfiles() {
    setProfilesError(null);
    try {
      const res = await fetch("/api/config/profiles");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setProfiles(data.profiles ?? []);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setProfilesError(`Failed to load profiles: ${message}`);
    }
  }

  async function loadProfile(name: string) {
    setSelectedProfile(name);
    setConfig(null);
    setLoadError(null);
    setLoading(true);
    try {
      const res = await fetch(`/api/config/profiles/${name}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error ?? `HTTP ${res.status}`);
      }
      const data: ProfileWithProvenance = await res.json();
      setConfig(data.config);
      setProvenance(data.provenance ?? {});
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setLoadError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(updated: PipelineConfig) {
    const res = await fetch(`/api/config/profiles/${selectedProfile}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error ?? `HTTP ${res.status}`);
    }
    // Reflect saved config locally
    setConfig(updated);
  }

  if (profilesError) {
    return (
      <div className="max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-destructive">
              Failed to load profiles
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">{profilesError}</p>
            <Button variant="outline" onClick={fetchProfiles} className="w-fit">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-1">Config Editor</h2>
        <p className="text-sm text-muted-foreground">
          Select a profile to load and edit its pipeline configuration.
        </p>
      </div>

      <div className="grid gap-2 max-w-xs">
        <Label>Profile</Label>
        <Select
          value={selectedProfile}
          onValueChange={loadProfile}
          disabled={profiles.length === 0}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a profile..." />
          </SelectTrigger>
          <SelectContent>
            {profiles.map((p) => (
              <SelectItem key={p} value={p}>
                {p}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading && (
        <p className="text-sm text-muted-foreground">Loading profile...</p>
      )}

      {loadError && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base text-destructive">
              Error loading profile
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">{loadError}</p>
            <Button
              variant="outline"
              onClick={() => loadProfile(selectedProfile)}
              className="w-fit"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {config && !loading && (
        <ProfileEditor
          profile={selectedProfile}
          config={config}
          provenance={provenance}
          onSave={handleSave}
        />
      )}
    </div>
  );
}

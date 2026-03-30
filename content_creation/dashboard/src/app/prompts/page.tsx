"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface PromptResult {
  positive_prompt?: string;
  negative_prompt?: string;
  scene_templates?: string[];
  music_prompt?: string;
  thumbnail_text?: string;
  youtube_title?: string;
  youtube_description?: string;
  youtube_tags?: string[];
  error?: string;
}

export default function PromptsPage() {
  const [tags, setTags] = useState("");
  const [profile, setProfile] = useState("cinematic");
  const [result, setResult] = useState<PromptResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    if (!tags.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(
        `/api/preview-prompts?tags=${encodeURIComponent(tags)}&profile=${encodeURIComponent(profile)}`
      );
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch {
      setError("Cannot reach pipeline server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Prompt Generator</h1>

      <Card>
        <CardHeader><CardTitle>Generate from Tags</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="lofi, rain, cozy, study, warm lighting"
              className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <select
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="cinematic">cinematic</option>
              <option value="lofi-study">lofi-study</option>
              <option value="tech-tutorial">tech-tutorial</option>
            </select>
            <Button onClick={generate} disabled={loading || !tags.trim()}>
              {loading ? "Generating..." : "Generate Prompts"}
            </Button>
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Generation Prompt (sent to Claude)</CardTitle></CardHeader>
            <CardContent>
              <div className="bg-muted/20 rounded p-3 border border-dashed text-xs font-mono text-muted-foreground space-y-2">
                <p><span className="text-foreground font-medium">System:</span> World-class AI content director. SDXL prompt engineering + YouTube SEO + thumbnail psychology. Style: {profile}</p>
                <p><span className="text-foreground font-medium">User:</span> Tags: &quot;{tags}&quot; → Generate 9 sections: positive_prompt (60-100 words, photography terms, quality boosters) → negative_prompt (8-12 SDXL terms) → 8 scene_templates (cinematic film language) → music_prompt (genre, BPM, instruments) → thumbnail_text (power words) → thumbnail_prompt (img2img dramatic enhancement) → youtube_title (SEO formula) → youtube_description (5 paragraphs) → youtube_tags (18 mixed)</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Image Prompts</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Positive Prompt</label>
                <p className="text-sm bg-muted/30 rounded p-3 mt-1">{result.positive_prompt}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Negative Prompt</label>
                <p className="text-sm bg-muted/30 rounded p-3 mt-1">{result.negative_prompt}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Scene Templates ({result.scene_templates?.length || 0})</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {result.scene_templates?.map((s, i) => (
                  <div key={i} className="text-sm bg-muted/30 rounded p-2">
                    <span className="text-muted-foreground font-mono mr-2">{i + 1}.</span>{s}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Music</CardTitle></CardHeader>
            <CardContent>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Music Prompt (Suno)</label>
                <p className="text-sm bg-muted/30 rounded p-3 mt-1">{result.music_prompt}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Thumbnail</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Thumbnail Text Overlay</label>
                <p className="text-lg font-bold bg-muted/30 rounded p-3 mt-1">{result.thumbnail_text}</p>
              </div>
              {(result as any).thumbnail_prompt && (
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Thumbnail img2img Prompt</label>
                  <p className="text-sm bg-muted/30 rounded p-3 mt-1">{(result as any).thumbnail_prompt}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>YouTube Metadata</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Title</label>
                <p className="text-sm font-medium bg-muted/30 rounded p-3 mt-1">{result.youtube_title}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Description</label>
                <p className="text-sm bg-muted/30 rounded p-3 mt-1 whitespace-pre-wrap">{result.youtube_description}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">Tags ({result.youtube_tags?.length || 0})</label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {result.youtube_tags?.map((t, i) => (
                    <span key={i} className="text-xs bg-muted/50 rounded px-2 py-1">{t}</span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

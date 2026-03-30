export const runtime = "nodejs";
export const maxDuration = 30;

import { pipelineGet } from "@/lib/pipeline-api";
import { supabase } from "@/lib/supabase";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const tags = url.searchParams.get("tags") || "";
  const profile = url.searchParams.get("profile") || "cinematic";
  const videoId = url.searchParams.get("video_id") || "";

  // If video_id provided, try Supabase first (cached prompts)
  if (videoId) {
    const { data } = await supabase
      .from("prompts")
      .select("*")
      .eq("video_id", videoId)
      .order("created_at", { ascending: false })
      .limit(1)
      .single();

    if (data) {
      return Response.json({
        positive_prompt: data.positive_prompt,
        negative_prompt: data.negative_prompt,
        scene_templates: typeof data.scene_templates === "string"
          ? JSON.parse(data.scene_templates) : data.scene_templates,
        music_prompt: data.music_prompt,
        thumbnail_text: data.thumbnail_text,
        youtube_title: data.youtube_title,
        youtube_description: data.youtube_description,
        youtube_tags: typeof data.youtube_tags === "string"
          ? JSON.parse(data.youtube_tags) : data.youtube_tags,
        source: "supabase",
      });
    }
  }

  // Fallback: call pipeline server for live generation (via tunnel)
  if (!tags) {
    return Response.json({ error: "tags parameter required" }, { status: 400 });
  }

  return pipelineGet(
    `/preview-prompts?tags=${encodeURIComponent(tags)}&profile=${encodeURIComponent(profile)}`,
    30000
  );
}

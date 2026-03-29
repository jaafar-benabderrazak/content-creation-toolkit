export const runtime = "nodejs";
import { pipelineGet } from "@/lib/pipeline-api";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const tags = url.searchParams.get("tags") || "";
  const profile = url.searchParams.get("profile") || "cinematic";
  return pipelineGet(`/preview-prompts?tags=${encodeURIComponent(tags)}&profile=${encodeURIComponent(profile)}`);
}

export const runtime = "nodejs";
import { pipelineGet, pipelinePost } from "@/lib/pipeline-api";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const status = url.searchParams.get("status") || "";
  return pipelineGet(`/roadmap${status ? `?status=${status}` : ""}`);
}

export async function POST(req: Request) {
  const body = await req.json();
  return pipelinePost("/roadmap", body);
}

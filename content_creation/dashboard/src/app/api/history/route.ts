export const runtime = "nodejs";
import { pipelineGet } from "@/lib/pipeline-api";

export async function GET() {
  return pipelineGet("/history");
}

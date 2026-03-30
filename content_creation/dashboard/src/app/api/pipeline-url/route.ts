// Returns the pipeline tunnel URL so the client can call it directly
// (bypasses Cloudflare interstitial since browser has the cookie)
export const runtime = "nodejs";

export async function GET() {
  const triggerUrl = process.env.PIPELINE_TRIGGER_URL || "";
  const baseUrl = triggerUrl.replace(/\/trigger\/?$/, "");
  return Response.json({ url: baseUrl || null });
}

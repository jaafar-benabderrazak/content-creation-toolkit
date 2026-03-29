// Proxy to local pipeline server /logs endpoint via ngrok
export const runtime = "nodejs";

export async function GET(request: Request) {
  const triggerUrl = process.env.PIPELINE_TRIGGER_URL;
  if (!triggerUrl) {
    return Response.json({ error: "PIPELINE_TRIGGER_URL not configured" }, { status: 503 });
  }

  // Derive base URL from trigger URL (remove /trigger suffix)
  const baseUrl = triggerUrl.replace(/\/trigger\/?$/, "");
  const url = new URL(request.url);
  const runId = url.searchParams.get("run_id") || "";
  const offset = url.searchParams.get("offset") || "0";

  try {
    const res = await fetch(
      `${baseUrl}/logs?run_id=${runId}&offset=${offset}`,
      { signal: AbortSignal.timeout(5000), cache: "no-store" }
    );
    if (!res.ok) {
      return Response.json({ error: `Pipeline server returned ${res.status}` }, { status: 502 });
    }
    const data = await res.json();
    return Response.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return Response.json(
      { error: `Cannot reach pipeline server: ${message}` },
      { status: 502 }
    );
  }
}

// Triggers the cloud pipeline via Modal web endpoint.
// Set MODAL_TRIGGER_URL to the Modal web endpoint URL.
// Fallback: PIPELINE_TRIGGER_URL for local pipeline server (via tunnel).

export const runtime = "nodejs";

export async function POST(request: Request) {
  const modalUrl = process.env.MODAL_TRIGGER_URL;
  const localUrl = process.env.PIPELINE_TRIGGER_URL;
  const secret = process.env.WEBHOOK_SECRET || "pipeline-local-secret";

  const body = await request.json().catch(() => ({}));

  // Try Modal first (cloud)
  if (modalUrl) {
    try {
      const res = await fetch(modalUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, source: "dashboard" }),
        signal: AbortSignal.timeout(15000),
      });
      if (res.ok) {
        const data = await res.json();
        return Response.json({ triggered: true, cloud: true, ...data });
      }
    } catch {
      // Fall through to local
    }
  }

  // Fallback: local pipeline server (via tunnel)
  if (localUrl) {
    try {
      const res = await fetch(localUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-webhook-secret": secret,
        },
        body: JSON.stringify({ ...body, source: "dashboard" }),
        signal: AbortSignal.timeout(10000),
      });
      if (res.ok) {
        const data = await res.json();
        return Response.json({ triggered: true, cloud: false, ...data });
      }
      const errBody = await res.text().catch(() => "");
      return Response.json({ error: `Pipeline returned ${res.status}` }, { status: 502 });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown";
      return Response.json({ error: `Pipeline unreachable: ${msg}` }, { status: 502 });
    }
  }

  return Response.json(
    { error: "Neither MODAL_TRIGGER_URL nor PIPELINE_TRIGGER_URL configured" },
    { status: 503 }
  );
}

// Triggers the local pipeline server via Cloudflare tunnel.
// Set PIPELINE_TRIGGER_URL to the tunnel URL + /trigger.

export const runtime = "nodejs";

export async function POST(request: Request) {
  const triggerUrl = process.env.PIPELINE_TRIGGER_URL;
  const secret = process.env.WEBHOOK_SECRET || "pipeline-local-secret";

  if (!triggerUrl) {
    return Response.json(
      { error: "PIPELINE_TRIGGER_URL not configured. Run python start.py locally." },
      { status: 503 }
    );
  }

  const body = await request.json().catch(() => ({}));

  try {
    const res = await fetch(triggerUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-webhook-secret": secret,
      },
      body: JSON.stringify({ ...body, source: "dashboard" }),
      signal: AbortSignal.timeout(10000),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      if (text.startsWith("<!") || text.startsWith("<html")) {
        return Response.json({ error: "Tunnel returned interstitial. Retry." }, { status: 502 });
      }
      return Response.json({ error: `Pipeline returned ${res.status}` }, { status: 502 });
    }

    const data = await res.json();
    return Response.json({ triggered: true, ...data });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown";
    return Response.json({ error: `Pipeline unreachable: ${msg}` }, { status: 502 });
  }
}

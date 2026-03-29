// Triggers the local pipeline server (pipeline_server.py) via ngrok tunnel.
// Set PIPELINE_TRIGGER_URL to the ngrok URL (e.g., https://abc123.ngrok.io/trigger)
// Set WEBHOOK_SECRET to match the local server's secret.

export const runtime = "nodejs";

export async function POST(request: Request) {
  const triggerUrl = process.env.PIPELINE_TRIGGER_URL;
  if (!triggerUrl) {
    return Response.json(
      { error: "PIPELINE_TRIGGER_URL not configured. Run pipeline_server.py + ngrok locally." },
      { status: 503 }
    );
  }

  const secret = process.env.WEBHOOK_SECRET || "pipeline-local-secret";
  const body = await request.json().catch(() => ({}));

  try {
    const res = await fetch(triggerUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-webhook-secret": secret,
      },
      body: JSON.stringify({ ...body, source: "dashboard" }),
      signal: AbortSignal.timeout(10_000),
    });

    if (!res.ok) {
      const errBody = await res.text().catch(() => "");
      return Response.json(
        { error: `Pipeline returned ${res.status}: ${errBody.slice(0, 200)}` },
        { status: 502 }
      );
    }

    const data = await res.json();
    return Response.json({
      triggered: true,
      run_id: data.run_id,
      message: data.message,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return Response.json(
      { error: `Failed to reach pipeline server: ${message}. Is pipeline_server.py running?` },
      { status: 502 }
    );
  }
}

/**
 * Proxy helper — all calls to local pipeline server go through this.
 * Reads PIPELINE_TRIGGER_URL env var to derive the base URL.
 */

function getBaseUrl(): string {
  const triggerUrl = process.env.PIPELINE_TRIGGER_URL || "";
  return triggerUrl.replace(/\/trigger\/?$/, "");
}

export async function pipelineGet(path: string, timeoutMs = 30000): Promise<Response> {
  const base = getBaseUrl();
  if (!base) {
    return Response.json({ error: "PIPELINE_TRIGGER_URL not configured", entries: [] }, { status: 503 });
  }
  try {
    const res = await fetch(`${base}${path}`, {
      signal: AbortSignal.timeout(timeoutMs),
      cache: "no-store",
      headers: {
        "User-Agent": "pipeline-dashboard/1.0",
        "Accept": "application/json",
      },
    });
    const text = await res.text();
    // Cloudflare free tunnels sometimes return an HTML interstitial page
    if (text.startsWith("<!") || text.startsWith("<html")) {
      return Response.json(
        { error: "Cloudflare tunnel returned interstitial page. Retry in a few seconds.", entries: [] },
        { status: 502 }
      );
    }
    const data = JSON.parse(text);
    return Response.json(data, { status: res.status });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return Response.json({ error: `Pipeline unreachable: ${msg}`, entries: [] }, { status: 502 });
  }
}

export async function pipelinePost(path: string, body: unknown): Promise<Response> {
  const base = getBaseUrl();
  const secret = process.env.WEBHOOK_SECRET || "pipeline-local-secret";
  if (!base) {
    return Response.json({ error: "PIPELINE_TRIGGER_URL not configured" }, { status: 503 });
  }
  try {
    const res = await fetch(`${base}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-webhook-secret": secret,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10000),
    });
    const text = await res.text();
    if (text.startsWith("<!") || text.startsWith("<html")) {
      return Response.json({ error: "Cloudflare tunnel interstitial page. Retry." }, { status: 502 });
    }
    const data = JSON.parse(text);
    return Response.json(data, { status: res.status });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return Response.json({ error: `Pipeline unreachable: ${msg}` }, { status: 502 });
  }
}

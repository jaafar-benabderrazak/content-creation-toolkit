/**
 * Proxy helper — all calls to local pipeline server go through this.
 * Reads PIPELINE_TRIGGER_URL env var to derive the base URL.
 */

function getBaseUrl(): string {
  const triggerUrl = process.env.PIPELINE_TRIGGER_URL || "";
  return triggerUrl.replace(/\/trigger\/?$/, "");
}

export async function pipelineGet(path: string): Promise<Response> {
  const base = getBaseUrl();
  if (!base) {
    return Response.json({ error: "PIPELINE_TRIGGER_URL not configured" }, { status: 503 });
  }
  const res = await fetch(`${base}${path}`, {
    signal: AbortSignal.timeout(8000),
    cache: "no-store",
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

export async function pipelinePost(path: string, body: unknown): Promise<Response> {
  const base = getBaseUrl();
  const secret = process.env.WEBHOOK_SECRET || "pipeline-local-secret";
  if (!base) {
    return Response.json({ error: "PIPELINE_TRIGGER_URL not configured" }, { status: 503 });
  }
  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-webhook-secret": secret,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10000),
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

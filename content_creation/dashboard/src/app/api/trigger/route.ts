// The local machine must run a Flask/FastAPI endpoint at PIPELINE_TRIGGER_URL.
// Use `ngrok http 8765` to expose it. The endpoint receives the POST and starts
// the Python pipeline via subprocess.
//
// Example local Flask endpoint:
//   from flask import Flask, request
//   import subprocess
//   app = Flask(__name__)
//
//   @app.route('/trigger', methods=['POST'])
//   def trigger():
//       data = request.json
//       subprocess.Popen(['python', 'run_pipeline.py', '--profile', data.get('profile', 'lofi_study')])
//       return {'started': True}

export const runtime = "nodejs";

export async function POST(request: Request) {
  const triggerUrl = process.env.PIPELINE_TRIGGER_URL;
  if (!triggerUrl) {
    return Response.json(
      { error: "PIPELINE_TRIGGER_URL not configured" },
      { status: 503 }
    );
  }

  const body = await request.json().catch(() => ({}));

  try {
    const res = await fetch(triggerUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...body, source: "dashboard" }),
      signal: AbortSignal.timeout(10_000), // 10s — the local endpoint must respond quickly
    });
    if (!res.ok) {
      return Response.json(
        { error: `Trigger endpoint returned ${res.status}` },
        { status: 502 }
      );
    }
    return Response.json({ triggered: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return Response.json(
      { error: `Failed to reach pipeline: ${message}` },
      { status: 502 }
    );
  }
}

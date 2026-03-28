// Local Python pipeline posts status updates to this endpoint using:
//
//   import requests, os
//   requests.post(
//       os.environ["DASHBOARD_STATUS_URL"],  # e.g. https://your-app.vercel.app/api/status
//       json={"stage": "sdxl", "message": "Generating scene 3/18", "level": "info"},
//       headers={"x-webhook-secret": os.environ["PIPELINE_WEBHOOK_SECRET"]}
//   )

import { appendStatus, getStatusLog, type StatusEntry } from "@/lib/store";

export const runtime = "nodejs";
export const revalidate = 0;

export async function GET() {
  return Response.json({ entries: getStatusLog() });
}

export async function POST(request: Request) {
  const secret = process.env.PIPELINE_WEBHOOK_SECRET;
  const authHeader = request.headers.get("x-webhook-secret");
  if (!secret || authHeader !== secret) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();

  const entry: StatusEntry = {
    timestamp: body.timestamp ?? new Date().toISOString(),
    stage: body.stage ?? "unknown",
    message: String(body.message ?? ""),
    level: ["info", "warning", "error"].includes(body.level)
      ? body.level
      : "info",
  };

  appendStatus(entry);
  return Response.json({ ok: true });
}

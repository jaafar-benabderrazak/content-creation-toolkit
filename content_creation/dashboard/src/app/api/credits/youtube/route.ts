export const runtime = "nodejs";
export const revalidate = 0;

import type { CreditResponse } from "../suno/route";

// YouTube Data API v3 has a fixed daily quota of 10,000 units per project.
// The quota cannot be checked programmatically without user OAuth context —
// service accounts are not granted quota access on the Data API.
//
// Instead, the local pipeline is expected to write the current usage into Vercel
// environment variables after each upload run:
//   - YOUTUBE_QUOTA_USED  : integer, units consumed today
//   - YOUTUBE_QUOTA_DATE  : ISO date string (YYYY-MM-DD) of the quota window
//
// Update these via `vercel env add` or the Vercel dashboard after each run.
// If YOUTUBE_QUOTA_DATE does not match today, the remaining value shown may be stale.

export async function GET(): Promise<Response> {
  const quotaUsedRaw = process.env.YOUTUBE_QUOTA_USED ?? "0";
  const quotaDate = process.env.YOUTUBE_QUOTA_DATE ?? null;

  const quotaUsed = parseInt(quotaUsedRaw, 10);
  const remaining = 10000 - (isNaN(quotaUsed) ? 0 : quotaUsed);

  const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
  const isStale = quotaDate !== null && quotaDate !== today;

  const body: CreditResponse = {
    provider: "youtube",
    label: "Daily Quota Remaining",
    value: remaining,
    unit: "units",
    configured: true,
    error: isStale
      ? `Quota data is from ${quotaDate} — update YOUTUBE_QUOTA_USED in Vercel env`
      : undefined,
    topup_url: "https://console.cloud.google.com/iam-admin/quotas",
  };

  return Response.json(body);
}

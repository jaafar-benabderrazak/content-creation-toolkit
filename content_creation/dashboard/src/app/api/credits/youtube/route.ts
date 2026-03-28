export const runtime = "nodejs";
export const revalidate = 0;

export async function GET(): Promise<Response> {
  const quotaUsedRaw = process.env.YOUTUBE_QUOTA_USED ?? "0";
  const quotaDate = process.env.YOUTUBE_QUOTA_DATE ?? null;

  const quotaUsed = parseInt(quotaUsedRaw, 10);
  const remaining = 10000 - (isNaN(quotaUsed) ? 0 : quotaUsed);

  const today = new Date().toISOString().slice(0, 10);
  const isStale = quotaDate !== null && quotaDate !== today;

  return Response.json({
    provider: "youtube",
    label: "YouTube",
    value: remaining,
    unit: "units / day",
    configured: true,
    error: isStale
      ? `Data from ${quotaDate} — may be stale`
      : undefined,
    topup_url: "https://console.cloud.google.com/iam-admin/quotas",
    dashboard_url: "https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas",
  });
}

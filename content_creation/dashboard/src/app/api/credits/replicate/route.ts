export const runtime = "nodejs";
export const revalidate = 0;

export async function GET(): Promise<Response> {
  const apiToken = process.env.REPLICATE_API_TOKEN;
  return Response.json({
    provider: "replicate",
    label: "Replicate",
    value: null,
    unit: "USD",
    configured: !!apiToken,
    error: apiToken ? "Balance not available via API" : undefined,
    topup_url: "https://replicate.com/account/billing",
    dashboard_url: "https://replicate.com/account/billing",
  });
}

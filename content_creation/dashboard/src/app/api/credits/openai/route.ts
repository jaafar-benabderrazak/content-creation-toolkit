export const runtime = "nodejs";
export const revalidate = 0;

export async function GET(): Promise<Response> {
  const apiKey = process.env.OPENAI_API_KEY;

  if (!apiKey) {
    return Response.json({
      provider: "openai",
      label: "OpenAI",
      value: null,
      unit: "USD",
      configured: false,
      topup_url: "https://platform.openai.com/account/billing/overview",
      dashboard_url: "https://platform.openai.com/usage",
    });
  }

  // Try the billing credit_grants endpoint
  try {
    const res = await fetch(
      "https://api.openai.com/dashboard/billing/credit_grants",
      {
        headers: { Authorization: `Bearer ${apiKey}` },
        cache: "no-store",
      }
    );

    if (res.ok) {
      const data = await res.json();
      const value: number | null = data?.total_available ?? null;
      if (value !== null) {
        return Response.json({
          provider: "openai",
          label: "OpenAI",
          value: Math.round(value * 100) / 100,
          unit: "USD",
          configured: true,
          topup_url: "https://platform.openai.com/account/billing/overview",
          dashboard_url: "https://platform.openai.com/usage",
        });
      }
    }
  } catch {
    // Fall through
  }

  // Billing limit reached or usage-based — show dashboard link
  return Response.json({
    provider: "openai",
    label: "OpenAI",
    value: null,
    unit: "USD",
    configured: true,
    error: "Check usage dashboard for balance",
    topup_url: "https://platform.openai.com/account/billing/overview",
    dashboard_url: "https://platform.openai.com/usage",
  });
}

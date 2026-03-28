export const runtime = "nodejs";
export const revalidate = 0;

import type { CreditResponse } from "../suno/route";

export async function GET(): Promise<Response> {
  const apiToken = process.env.REPLICATE_API_TOKEN;

  if (!apiToken) {
    const body: CreditResponse = {
      provider: "replicate",
      label: "Account Status",
      value: null,
      unit: "USD",
      configured: false,
      topup_url: "https://replicate.com/account/billing",
    };
    return Response.json(body);
  }

  try {
    const res = await fetch("https://api.replicate.com/v1/account", {
      headers: { Authorization: `Token ${apiToken}` },
      cache: "no-store",
    });

    if (res.status === 401) {
      const body: CreditResponse = {
        provider: "replicate",
        label: "Account Status",
        value: null,
        unit: "USD",
        configured: false,
        error: "Invalid API token — 401 Unauthorized",
        topup_url: "https://replicate.com/account/billing",
      };
      return Response.json(body);
    }

    if (!res.ok) {
      const body: CreditResponse = {
        provider: "replicate",
        label: "Account Status",
        value: null,
        unit: "USD",
        configured: true,
        error: `HTTP ${res.status}`,
        topup_url: "https://replicate.com/account/billing",
      };
      return Response.json(body);
    }

    // Replicate /account returns { username, type, github_url } — no balance field as of 2026
    // Token is valid (200 OK) but balance is not exposed via API
    const body: CreditResponse = {
      provider: "replicate",
      label: "See dashboard",
      value: null,
      unit: "USD",
      configured: true,
      error: "Balance not available via API",
      topup_url: "https://replicate.com/account/billing",
    };
    return Response.json(body);
  } catch (err) {
    const body: CreditResponse = {
      provider: "replicate",
      label: "Account Status",
      value: null,
      unit: "USD",
      configured: true,
      error: err instanceof Error ? err.message : "Network error",
      topup_url: "https://replicate.com/account/billing",
    };
    return Response.json(body);
  }
}

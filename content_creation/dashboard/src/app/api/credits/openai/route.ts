export const runtime = "nodejs";
export const revalidate = 0;

import type { CreditResponse } from "../suno/route";

export async function GET(): Promise<Response> {
  const apiKey = process.env.OPENAI_API_KEY;

  if (!apiKey) {
    const body: CreditResponse = {
      provider: "openai",
      label: "Credit Balance",
      value: null,
      unit: "USD",
      configured: false,
      topup_url: "https://platform.openai.com/account/billing/overview",
    };
    return Response.json(body);
  }

  try {
    const res = await fetch(
      "https://api.openai.com/dashboard/billing/credit_grants",
      {
        headers: { Authorization: `Bearer ${apiKey}` },
        cache: "no-store",
      }
    );

    if (res.status === 404) {
      // Usage-based orgs do not have credit grants endpoint
      const body: CreditResponse = {
        provider: "openai",
        label: "Credit Balance",
        value: null,
        unit: "USD",
        configured: true,
        error: "Usage-based account — check dashboard",
        topup_url: "https://platform.openai.com/account/billing/overview",
      };
      return Response.json(body);
    }

    if (res.status === 401) {
      const body: CreditResponse = {
        provider: "openai",
        label: "Credit Balance",
        value: null,
        unit: "USD",
        configured: false,
        error: "Invalid API key — 401 Unauthorized",
        topup_url: "https://platform.openai.com/account/billing/overview",
      };
      return Response.json(body);
    }

    if (!res.ok) {
      const body: CreditResponse = {
        provider: "openai",
        label: "Credit Balance",
        value: null,
        unit: "USD",
        configured: true,
        error: `HTTP ${res.status}`,
        topup_url: "https://platform.openai.com/account/billing/overview",
      };
      return Response.json(body);
    }

    const data = await res.json();
    // Response field is total_available (in USD)
    const value: number | null = data?.total_available ?? null;

    const body: CreditResponse = {
      provider: "openai",
      label: "Credit Balance",
      value,
      unit: "USD",
      configured: true,
      error:
        value === null
          ? "Unexpected response shape — check OpenAI dashboard"
          : undefined,
      topup_url: "https://platform.openai.com/account/billing/overview",
    };
    return Response.json(body);
  } catch (err) {
    const body: CreditResponse = {
      provider: "openai",
      label: "Credit Balance",
      value: null,
      unit: "USD",
      configured: true,
      error: err instanceof Error ? err.message : "Network error",
      topup_url: "https://platform.openai.com/account/billing/overview",
    };
    return Response.json(body);
  }
}

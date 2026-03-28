export const runtime = "nodejs";
export const revalidate = 0;

export type CreditResponse = {
  provider: string;
  label: string;
  value: number | null;
  unit: string;
  configured: boolean;
  error?: string;
  topup_url: string;
};

export async function GET(): Promise<Response> {
  const apiKey = process.env.SUNO_API_KEY;

  if (!apiKey) {
    const body: CreditResponse = {
      provider: "suno",
      label: "Credits Remaining",
      value: null,
      unit: "credits",
      configured: false,
      topup_url: "https://kie.ai/pricing",
    };
    return Response.json(body);
  }

  // Attempt primary endpoint: GET /api/v1/account/credits
  try {
    const res = await fetch("https://api.kie.ai/api/v1/account/credits", {
      headers: { Authorization: `Bearer ${apiKey}` },
      cache: "no-store",
    });

    if (res.status === 404) {
      // Credits endpoint not available — fall back to /account
      const accountRes = await fetch("https://api.kie.ai/api/v1/account", {
        headers: { Authorization: `Bearer ${apiKey}` },
        cache: "no-store",
      });

      if (!accountRes.ok) {
        const body: CreditResponse = {
          provider: "suno",
          label: "Credits Remaining",
          value: null,
          unit: "credits",
          configured: true,
          error: `credits endpoint not available — check kie.ai dashboard manually`,
          topup_url: "https://kie.ai/pricing",
        };
        return Response.json(body);
      }

      const accountData = await accountRes.json();
      // Try known field names for balance/credits
      const value: number | null =
        accountData?.credits ?? accountData?.balance ?? null;

      const body: CreditResponse = {
        provider: "suno",
        label: "Credits Remaining",
        value,
        unit: "credits",
        configured: true,
        error:
          value === null
            ? "credits endpoint not available — check kie.ai dashboard manually"
            : undefined,
        topup_url: "https://kie.ai/pricing",
      };
      return Response.json(body);
    }

    if (!res.ok) {
      const body: CreditResponse = {
        provider: "suno",
        label: "Credits Remaining",
        value: null,
        unit: "credits",
        configured: true,
        error: `HTTP ${res.status}`,
        topup_url: "https://kie.ai/pricing",
      };
      return Response.json(body);
    }

    const data = await res.json();
    const value: number | null = data?.data?.credits ?? data?.credits ?? null;

    const body: CreditResponse = {
      provider: "suno",
      label: "Credits Remaining",
      value,
      unit: "credits",
      configured: true,
      error:
        value === null
          ? "Unexpected response shape from kie.ai — check dashboard"
          : undefined,
      topup_url: "https://kie.ai/pricing",
    };
    return Response.json(body);
  } catch (err) {
    const body: CreditResponse = {
      provider: "suno",
      label: "Credits Remaining",
      value: null,
      unit: "credits",
      configured: true,
      error: err instanceof Error ? err.message : "Network error",
      topup_url: "https://kie.ai/pricing",
    };
    return Response.json(body);
  }
}

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
  dashboard_url?: string;
};

export async function GET(): Promise<Response> {
  const apiKey = process.env.SUNO_API_KEY;
  return Response.json({
    provider: "suno",
    label: "Suno (kie.ai)",
    value: null,
    unit: "credits",
    configured: !!apiKey,
    error: apiKey ? "Balance API not available — check kie.ai dashboard" : undefined,
    topup_url: "https://kie.ai/pricing",
    dashboard_url: "https://kie.ai/dashboard",
  });
}

import { NextResponse } from "next/server";

/**
 * Proxy POST requests to the FastAPI checkout-session endpoint.
 *
 * Keeps the Stripe secret key server-side and lets the browser call a
 * same-origin route (/api/stripe/checkout) instead of hitting the backend
 * directly.
 */
export async function POST(req: Request) {
  const authorization = req.headers.get("Authorization") ?? req.headers.get("x-stack-access-token");

  const body = await req.json();

  const apiBase =
    process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (authorization) {
    // Forward whichever auth header the client sent
    if (req.headers.has("x-stack-access-token")) {
      headers["x-stack-access-token"] = authorization;
    } else {
      headers["Authorization"] = authorization;
    }
  }

  const upstream = await fetch(`${apiBase}/api/v1/payments/checkout-session`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  const data = await upstream.json();

  if (!upstream.ok) {
    return NextResponse.json(data, { status: upstream.status });
  }

  return NextResponse.json(data);
}

import { NextResponse } from "next/server";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get("stripe-signature");

  if (!sig) {
    return NextResponse.json({ error: "Missing stripe-signature header" }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(
      body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: `Webhook signature verification failed: ${message}` }, { status: 400 });
  }

  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    const reservationId = session.metadata?.reservation_id;

    if (!reservationId) {
      return NextResponse.json({ error: "Missing reservation_id in session metadata" }, { status: 400 });
    }

    const internalApiBase =
      process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const confirmResponse = await fetch(
      `${internalApiBase}/api/v1/payments/reservations/${reservationId}/confirm`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-Webhook-Secret": process.env.STRIPE_WEBHOOK_SECRET!,
        },
      }
    );

    if (!confirmResponse.ok) {
      const detail = await confirmResponse.text();
      console.error(`Failed to confirm reservation ${reservationId}:`, detail);
      // Return 200 to Stripe so it does not retry — log and investigate separately
      return NextResponse.json({ received: true, warning: "Confirmation call failed" });
    }
  }

  return NextResponse.json({ received: true });
}

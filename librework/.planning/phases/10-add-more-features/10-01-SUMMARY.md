---
phase: 10-add-more-features
plan: "01"
subsystem: payments
tags: [stripe, checkout, webhook, fastapi, nextjs]
dependency_graph:
  requires: []
  provides: [stripe-checkout-session, stripe-webhook-handler, payment-history]
  affects: [reservations]
tech_stack:
  added: [stripe>=10.0.0 (Python), stripe (npm), @stripe/stripe-js (npm)]
  patterns: [webhook-signature-verification, db-sourced-pricing, internal-secret-handshake]
key_files:
  created:
    - librework/backend/app/api/v1/payments.py
    - librework/frontend/src/app/api/stripe/webhook/route.ts
    - librework/frontend/src/app/api/stripe/checkout/route.ts
  modified:
    - librework/backend/app/main.py
    - librework/backend/app/core/config.py
    - librework/backend/requirements.txt
    - librework/frontend/package.json
decisions:
  - "Amount always fetched from DB (cost_credits * 100 EUR cents), never from request body"
  - "Webhook confirm uses shared STRIPE_WEBHOOK_SECRET header so only Next.js handler can call the internal PATCH"
  - "Webhook returns 200 even when confirm call fails to prevent Stripe retries — logs warning instead"
  - "Payment history is v1 reservation data (no separate payments table), amount_eur = cost_credits / 100"
metrics:
  duration: "4 minutes"
  completed: "2026-03-22"
  tasks_completed: 2
  files_changed: 7
---

# Phase 10 Plan 01: Stripe Checkout Payment Flow Summary

Stripe Checkout session creation (DB-sourced pricing), Next.js webhook handler with raw-body signature verification, and reservation status confirmation via internal secret handshake.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create Stripe payments backend and config | 1e33767 | payments.py, main.py, config.py, requirements.txt |
| 2 | Create Next.js Stripe webhook and checkout proxy routes | 83bfe89 | webhook/route.ts, checkout/route.ts, package.json |

## What Was Built

**Backend (FastAPI `payments.py`):**
- `POST /api/v1/payments/checkout-session` — Accepts `reservation_id`, validates reservation belongs to current user and has `pending` status, fetches `cost_credits` from DB (joined with `spaces(name)`), computes `amount_cents = cost_credits * 100`, creates Stripe Checkout session with `customer_email`, `metadata.reservation_id`, success/cancel URLs.
- `PATCH /api/v1/payments/reservations/{id}/confirm` — Internal endpoint; validates `X-Webhook-Secret` header matches `STRIPE_WEBHOOK_SECRET`, updates reservation status to `confirmed` in Supabase.
- `GET /api/v1/payments/history` — Returns confirmed/completed reservations as payment records for current user (no separate payments table in v1).

**Frontend (Next.js API routes):**
- `POST /api/stripe/webhook` — Reads raw body via `req.text()`, verifies Stripe signature, on `checkout.session.completed` extracts `reservation_id` from metadata and calls FastAPI confirm endpoint with `X-Webhook-Secret`. Returns 200 to Stripe even on confirm failure (logs warning) to prevent duplicate retries.
- `POST /api/stripe/checkout` — Same-origin proxy that forwards the client's auth header (`x-stack-access-token` or `Authorization`) to FastAPI, keeping `STRIPE_SECRET_KEY` server-side.

## Key Decisions

1. **DB-sourced pricing only** — `CheckoutSessionRequest` schema has only `reservation_id`. Amount is always computed from `cost_credits` in DB. No amount field accepted from client.
2. **Internal secret handshake** — The PATCH confirm endpoint requires `X-Webhook-Secret == STRIPE_WEBHOOK_SECRET`. This avoids giving the webhook handler direct Supabase credentials.
3. **Webhook 200 on confirm failure** — If the internal confirm call fails (e.g. DB down), the webhook still returns 200 to Stripe and logs a warning. Retrying would cause duplicate confirmation attempts.
4. **v1 payment history from reservations** — No separate `payments` table needed. `amount_eur = cost_credits / 100` is derived from the reservation row.

## User Setup Required

The following env vars must be set before the payment flow works:

| Variable | Where to get it |
|----------|----------------|
| `STRIPE_SECRET_KEY` | Stripe Dashboard > Developers > API keys > Secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe Dashboard > Developers > Webhooks > Signing secret |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Stripe Dashboard > Developers > API keys > Publishable key |
| `INTERNAL_API_URL` or `NEXT_PUBLIC_API_URL` | Backend URL (e.g. `http://localhost:8000`) |

Stripe webhook endpoint must be configured to point to `/api/stripe/webhook` (`checkout.session.completed` event).

## Deviations from Plan

None — plan executed exactly as written.

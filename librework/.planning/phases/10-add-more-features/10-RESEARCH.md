# Phase 10: Add More Features - Research

**Researched:** 2026-03-22
**Domain:** Stripe Checkout, Resend email, next-intl i18n, Recharts analytics, Google Maps Places API
**Confidence:** HIGH (Stripe, Resend, next-intl verified via official docs; recharts and Google Maps via existing code + search)

---

## Summary

Phase 10 bundles five independent features: Stripe Checkout for card payments, transactional email via Resend, French/English i18n via next-intl, enhanced owner analytics charts, and promoting the Google Places integration (already implemented in Phase 9) as the primary data source by retiring mock data fallback.

The project already has `resend==2.4.0` in `requirements.txt` and `recharts` + `@vis.gl/react-google-maps` in `package.json`, so dependency installs are minimal. The critical structural change is next-intl: it requires wrapping the entire `src/app/` tree under `src/app/[locale]/`, which restructures the layout and middleware. This is the highest-risk task in the phase and must be planned carefully around the existing `StackProvider`/`StackTheme` root layout.

The Stripe webhook endpoint must be a Next.js API route (or FastAPI route) that receives the raw body — Next.js App Router `req.text()` pattern is required, not `req.json()`. The owner analytics backend already returns aggregate stats (`/owner/dashboard`); the enhancement is adding time-series endpoints and wiring real data into recharts components.

**Primary recommendation:** Execute features in this order to minimize risk: (1) Google Maps promotion — zero new dependencies, (2) Owner analytics — backend extension only, (3) Resend email — Python-side, no frontend restructure, (4) Stripe — new backend route + Next.js API route, (5) i18n last — it restructures the entire `app/` folder and must be done after all other routes are stable.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PAY-01 | User can pay for a reservation using Stripe Checkout (card payment) | Stripe Checkout session creation pattern; hosted checkout page redirects user off-site |
| PAY-02 | Backend creates Stripe Checkout sessions and handles webhooks for payment confirmation | FastAPI route for session creation; Next.js API route for webhook with raw body + `constructEvent` |
| PAY-03 | Reservation status updates automatically on successful payment (webhook-driven) | `checkout.session.completed` event → update `reservations.status` in Supabase |
| PAY-04 | User can view payment history and receipts | Stripe session metadata stored on reservation; receipt_url from Stripe charge object |
| EMAIL-01 | System sends transactional emails for password reset, booking confirmation, and cancellation | `resend==2.4.0` already in requirements.txt; Python SDK pattern confirmed |
| EMAIL-02 | Email delivery uses Resend instead of printing tokens to console | Replace console/print calls in FastAPI auth and reservation handlers |
| EMAIL-03 | System can send marketing emails to opted-in users | Resend batch send or audience API; opt-in flag needed on user record |
| I18N-01 | next-intl configured with `[locale]` routing (FR/EN) | `npm install next-intl`; routing.ts + middleware.ts + `src/app/[locale]/` tree required |
| I18N-02 | All user-facing UI text translated to French and English | `messages/en.json` + `messages/fr.json`; `useTranslations()` hook in all components |
| OWNER-01 | Owner analytics dashboard showing occupancy rates, revenue, and booking trends | `/owner/dashboard` endpoint exists; extend with time-series query; recharts already installed |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stripe | ^14.x (Node) | Create checkout sessions, verify webhooks | Official Stripe Node SDK; server-side only |
| stripe (Python) | resend==2.4.0 already in backend | Python SDK for Resend email | Already listed in requirements.txt |
| @stripe/stripe-js | ^3.x | Load Stripe.js on client (redirectToCheckout) | Required for hosted checkout redirect |
| resend (Node) | ^3.x | Send email from Next.js API routes if needed | Optional — backend Python already has resend |
| next-intl | ^3.x | App Router i18n with locale routing | Official docs confirmed; works with Next.js 14 |
| recharts | ^2.10.3 | Charts for analytics | Already installed in package.json |
| @vis.gl/react-google-maps | ^1.7.1 | Google Maps Places (APIProvider already used) | Already installed and integrated in Phase 9 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @react-email/components | latest | Styled email component primitives | Building HTML email templates in React |
| react-email | latest | Local dev preview server for emails | Development only — `email dev` command |
| date-fns | ^3.2.0 | Date formatting for analytics ranges | Already installed |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| next-intl | next-i18next | next-intl is built for App Router; next-i18next targets Pages Router |
| Stripe Checkout (hosted) | Stripe Payment Elements (embedded) | Hosted = less code, less PCI scope; Elements = more UI control. PAY-01 specifies hosted. |
| Resend Python SDK | SendGrid (already in requirements.txt) | Resend is already in requirements.txt and is simpler. SendGrid remains as dead code. |
| recharts BarChart+LineChart | Tremor / shadcn charts | recharts already installed; no new dependency needed |

### Installation

Frontend:
```bash
npm install next-intl stripe @stripe/stripe-js
# react-email for local template preview (dev only):
npm install --save-dev react-email @react-email/components
```

Backend (Python — most already present):
```bash
pip install stripe
# resend already in requirements.txt at 2.4.0
```

---

## Architecture Patterns

### Recommended File Structure for Phase 10

```
frontend/src/
├── app/
│   ├── [locale]/              # next-intl locale wrapper (NEW)
│   │   ├── layout.tsx         # Move existing layout.tsx here
│   │   ├── page.tsx           # Move existing page.tsx here
│   │   ├── login/             # Move existing login/ here
│   │   ├── register/          # Move existing register/ here
│   │   └── handler/           # Move existing handler/ here
│   └── api/
│       ├── stripe/
│       │   ├── checkout/route.ts   # Creates Stripe Checkout session
│       │   └── webhook/route.ts    # Handles Stripe webhook (raw body)
│       └── auth/[...nextauth]/     # Existing Stack Auth handler
├── i18n/
│   └── request.ts             # next-intl server config
├── middleware.ts               # next-intl routing middleware
├── components/
│   ├── OwnerAnalyticsDashboard.tsx  # Enhanced with real data + time range
│   └── LanguageSwitcher.tsx         # NEW: FR/EN toggle in Navbar
└── messages/
    ├── en.json                # English strings
    └── fr.json                # French strings

backend/app/api/v1/
├── payments.py                # NEW: Stripe session creation endpoint
├── email.py                   # NEW: Resend transactional email helpers
└── owner.py                   # EXTEND: add time-series analytics endpoints
```

### Pattern 1: Stripe Checkout Session (Server-Side)

**What:** FastAPI creates a Stripe Checkout session; frontend redirects to Stripe's hosted page.
**When to use:** User clicks "Pay" on a reservation.

```python
# Source: https://docs.stripe.com/checkout/quickstart
import stripe
import os

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

@router.post("/payments/checkout")
async def create_checkout_session(
    reservation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "Workspace Booking"},
                "unit_amount": 1500,  # cents — fetch from DB, never from client
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{settings.FRONTEND_URL}/booking/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/booking/cancel",
        metadata={"reservation_id": reservation_id, "user_id": current_user.id},
    )
    return {"checkout_url": session.url}
```

### Pattern 2: Stripe Webhook (Next.js App Router)

**What:** Stripe POSTs `checkout.session.completed` — Next.js API route verifies signature and updates reservation status.
**Critical:** Must use `req.text()` not `req.json()` — App Router does NOT need `export const config` to disable body parsing; the raw body is available via `req.text()`.

```typescript
// Source: https://docs.stripe.com/webhooks
// app/api/stripe/webhook/route.ts
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(req: Request) {
  const body = await req.text()  // raw body — required for signature verification
  const sig = req.headers.get('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err) {
    return new Response(`Webhook Error: ${err}`, { status: 400 })
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session
    const reservationId = session.metadata?.reservation_id
    // Call FastAPI to update reservation status to 'confirmed'
    await fetch(`${process.env.INTERNAL_API_URL}/api/v1/reservations/${reservationId}/confirm`, {
      method: 'PATCH',
      headers: { 'X-Webhook-Secret': process.env.INTERNAL_WEBHOOK_SECRET! },
    })
  }

  return new Response(null, { status: 200 })
}
```

**Alternative:** Webhook handled directly in FastAPI (avoids internal HTTP call). Valid if FastAPI is exposed on a public URL. On Vercel, the Next.js route is simpler.

### Pattern 3: Resend Email from FastAPI

**What:** FastAPI sends booking confirmation email via Resend Python SDK.
**resend 2.4.0 is already in requirements.txt.**

```python
# Source: https://resend.com/docs/send-with-python
import resend
import os

resend.api_key = os.environ["RESEND_API_KEY"]

def send_booking_confirmation(to_email: str, user_name: str, reservation_details: dict):
    params: resend.Emails.SendParams = {
        "from": "LibreWork <bookings@librework.app>",
        "to": [to_email],
        "subject": "Booking Confirmed",
        "html": f"<h1>Hi {user_name}, your booking is confirmed!</h1>",
    }
    return resend.Emails.send(params)
```

For HTML templates, use Python string templates or Jinja2 — React Email is frontend-only and does not work in Python.

### Pattern 4: next-intl Locale Routing

**What:** Wraps all app routes under `[locale]` dynamic segment; middleware detects locale and redirects.

```typescript
// Source: https://next-intl.dev/docs/routing/setup
// src/i18n/routing.ts
import { defineRouting } from 'next-intl/routing'

export const routing = defineRouting({
  locales: ['en', 'fr'],
  defaultLocale: 'en',
})

// middleware.ts (root of project, NOT inside src/app/)
import createMiddleware from 'next-intl/middleware'
import { routing } from './src/i18n/routing'

export default createMiddleware(routing)

export const config = {
  matcher: '/((?!api|_next|_vercel|.*\\..*).*)',
}
```

```typescript
// src/app/[locale]/layout.tsx — replaces current src/app/layout.tsx
import { NextIntlClientProvider, hasLocale } from 'next-intl'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()

  const messages = (await import(`../../../messages/${locale}.json`)).default

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          {/* existing StackProvider + StackTheme wraps go here */}
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
```

**Critical collision:** The existing `src/app/layout.tsx` has `<html>` + `StackProvider` + `StackTheme`. When adding `[locale]`, the root `layout.tsx` must be reduced to a minimal shell (or removed in favor of the locale layout). The `StackProvider` moves into `[locale]/layout.tsx`.

### Pattern 5: Owner Analytics Time-Series (Backend Extension)

**What:** Extend `/owner/dashboard` with time-range queries for charts.

```python
# backend/app/api/v1/owner.py — new endpoint
@router.get("/analytics/revenue")
async def get_revenue_by_period(
    period: str = Query("week", enum=["day", "week", "month"]),
    current_user: UserResponse = Depends(get_current_owner)
):
    """Returns daily revenue totals for the selected period."""
    # Query reservations grouped by date using Supabase RPC or Python aggregation
    # Returns: [{"date": "2026-03-15", "revenue": 450}, ...]
```

### Anti-Patterns to Avoid

- **Passing price from the client to Stripe:** Always fetch price from DB in server action/route handler. Never trust `amount` from the request body.
- **Using `req.json()` in the webhook route:** Stripe signature verification requires the raw body. `req.text()` is mandatory.
- **Adding next-intl middleware matcher that catches `/api` routes:** The matcher must exclude `/api`, `_next`, and static assets — otherwise Stripe webhooks get locale-redirected and fail.
- **Putting React Email templates in the Python backend:** React Email is a JavaScript/TypeScript library. Python uses HTML strings or Jinja2 for email templating.
- **Keeping mock data as the default when NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is set:** The `ExplorePage` already falls back to mock; the phase requirement is to make real data primary when the key exists, which the current code already does. No structural change needed — only verification and documentation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stripe webhook signature verification | Custom HMAC check | `stripe.webhooks.constructEvent()` | Timing attacks, encoding edge cases |
| Payment amount calculation | Client-side price math | Fetch price from DB in server | Price manipulation attacks |
| Email HTML rendering | Raw string concatenation | Jinja2 templates or react-email | Escaping, encoding, deliverability |
| Locale detection and redirect | Custom middleware | `next-intl/middleware` + `createMiddleware` | Cookie/header negotiation edge cases |
| i18n pluralization | `if count > 1 ? 's' : ''` | next-intl `t('key', {count})` with plural rules | ICU message format handles all plural categories |
| Date range aggregation for analytics | Manual JS reduce | Supabase RPC or Python groupby | N+1 queries; use DB aggregation |

**Key insight:** Stripe and next-intl both have significant security and correctness surface area. The official SDKs encode years of edge-case handling that custom implementations always miss.

---

## Common Pitfalls

### Pitfall 1: Stripe Webhook Body Parsing

**What goes wrong:** Webhook signature verification throws `No signatures found matching the expected signature for payload` even with a correct secret.
**Why it happens:** Next.js (or middleware) parses the body as JSON before the route handler runs, mutating the raw bytes that Stripe's HMAC checks against.
**How to avoid:** Use `const body = await req.text()` in the route handler. In Next.js App Router, this is sufficient — no `export const config = { api: { bodyParser: false } }` needed (that is Pages Router syntax).
**Warning signs:** Error message mentions "payload" or "signature"; works in Stripe CLI local testing but fails in production.

### Pitfall 2: next-intl Middleware Intercepting API Routes

**What goes wrong:** Stripe webhook at `/api/stripe/webhook` returns a locale redirect (301/302) instead of processing the event.
**Why it happens:** Middleware matcher is too broad — catches `/api/stripe/webhook` and tries to prefix it with `/en/`.
**How to avoid:** Matcher must be `'/((?!api|_next|_vercel|.*\\..*).*)'` — the `(?!api|...)` negative lookahead excludes all `/api/` paths.
**Warning signs:** Stripe Dashboard shows webhook delivery failures with 3xx response codes.

### Pitfall 3: Root Layout Duplication After next-intl Migration

**What goes wrong:** Two `<html>` tags render — one from the root `src/app/layout.tsx` and one from `src/app/[locale]/layout.tsx`.
**Why it happens:** The original `layout.tsx` is not removed or replaced when adding the `[locale]` layout.
**How to avoid:** When adding `[locale]/layout.tsx`, either (a) delete the root `layout.tsx` and let `[locale]/layout.tsx` be the root, or (b) make root `layout.tsx` a minimal pass-through with no `<html>` tag. Option (a) is standard for fully locale-prefixed apps.
**Warning signs:** React `hydration` warning about `<html>` nesting; layout styles duplicated.

### Pitfall 4: `useTranslations` in Server Components vs Client Components

**What goes wrong:** `useTranslations` called in a Server Component throws a runtime error.
**Why it happens:** `useTranslations` is a Client hook. In Server Components, you must use `getTranslations()` (async).
**How to avoid:** Server Components → `const t = await getTranslations('namespace')`. Client Components → `const t = useTranslations('namespace')`.
**Warning signs:** Error: "useTranslations is not a function" or similar React hooks error in server context.

### Pitfall 5: Stripe Price in Cents

**What goes wrong:** User is charged 100x the intended amount (e.g., €150.00 instead of €1.50).
**Why it happens:** Stripe's `unit_amount` is in the smallest currency unit (cents for EUR). Passing `1.50` instead of `150` causes €0.015 or misparse.
**How to avoid:** Always store prices in the DB as integer cents (or convert: `Math.round(priceInEuros * 100)`). Verify with Stripe test mode before going live.
**Warning signs:** Test charges show incorrect amounts in Stripe Dashboard.

### Pitfall 6: Google Maps Places API Billing SKU

**What goes wrong:** Unexpected charges exceed free tier.
**Why it happens:** `openingHours`, `photos`, or advanced fields trigger the Pro SKU ($32/1000 requests) vs Essentials SKU ($5/1000).
**How to avoid:** Keep fields list to: `['displayName', 'formattedAddress', 'location', 'rating', 'userRatingCount', 'photos', 'types', 'businessStatus']` — already correct in `googlePlaces.ts` from Phase 9. Do not add `openingHours` (confirmed decision from STATE.md).
**Warning signs:** Google Cloud billing alert; STATE.md explicitly documents this decision.

### Pitfall 7: recharts SSR in Next.js App Router

**What goes wrong:** `ReferenceError: window is not defined` during server-side rendering.
**Why it happens:** Recharts uses browser-only APIs internally.
**How to avoid:** All recharts chart components must be in Client Components (`'use client'` at top of file). The `OwnerDashboard.tsx` already does this correctly.
**Warning signs:** Build error mentioning `window` or `document` in a Server Component stack trace.

---

## Code Examples

### Create Stripe Checkout Session (FastAPI)

```python
# Source: https://docs.stripe.com/checkout/quickstart
# backend/app/api/v1/payments.py
import stripe
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])
stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/checkout-session")
async def create_checkout_session(
    reservation_id: str,
    current_user = Depends(get_current_user)
):
    # Fetch reservation and compute amount from DB — never from request body
    supabase = get_supabase()
    res = supabase.table("reservations").select("cost_credits, spaces(name)").eq("id", reservation_id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404)

    amount_cents = res.data["cost_credits"] * 100  # 1 credit = 1 EUR cent, adjust as needed

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": res.data["spaces"]["name"]},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{settings.FRONTEND_URL}/booking/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/booking/cancel",
        metadata={"reservation_id": reservation_id},
        customer_email=current_user.email,
    )
    return {"checkout_url": session.url}
```

### Stripe Webhook Route (Next.js App Router)

```typescript
// Source: https://docs.stripe.com/webhooks
// src/app/api/stripe/webhook/route.ts
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(req: Request) {
  const body = await req.text()
  const sig = req.headers.get('stripe-signature')

  if (!sig) return new Response('No signature', { status: 400 })

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)
  } catch (err: unknown) {
    return new Response(`Webhook signature verification failed: ${err}`, { status: 400 })
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session
    const reservationId = session.metadata?.reservation_id
    if (reservationId) {
      // Update reservation status in Supabase via internal API call or direct SDK
    }
  }

  return new Response(null, { status: 200 })
}
```

### Resend Booking Confirmation (Python)

```python
# Source: https://resend.com/docs/send-with-python
import resend

def send_booking_confirmation(to_email: str, user_name: str, space_name: str, start_time: str):
    resend.api_key = settings.RESEND_API_KEY
    params: resend.Emails.SendParams = {
        "from": "LibreWork <bookings@yourdomain.com>",
        "to": [to_email],
        "subject": f"Booking Confirmed: {space_name}",
        "html": f"""
          <h2>Hi {user_name},</h2>
          <p>Your booking for <strong>{space_name}</strong> on {start_time} is confirmed.</p>
          <p>See you there!</p>
        """,
    }
    result = resend.Emails.send(params)
    return result
```

### next-intl Translation Usage

```typescript
// Source: https://next-intl.dev/docs/getting-started/app-router
// Client Component
'use client'
import { useTranslations } from 'next-intl'

export function Navbar() {
  const t = useTranslations('Navbar')
  return <nav><a href="/">{t('explore')}</a></nav>
}

// Server Component
import { getTranslations } from 'next-intl/server'

export default async function HomePage() {
  const t = await getTranslations('HomePage')
  return <h1>{t('title')}</h1>
}
```

```json
// messages/en.json
{
  "Navbar": { "explore": "Explore", "myBookings": "My Bookings", "login": "Login" },
  "HomePage": { "title": "Find Your Perfect Workspace" }
}
```

```json
// messages/fr.json
{
  "Navbar": { "explore": "Explorer", "myBookings": "Mes Réservations", "login": "Connexion" },
  "HomePage": { "title": "Trouvez votre espace de travail idéal" }
}
```

### Owner Analytics Recharts (Time-Series)

```typescript
// 'use client' required — recharts uses browser APIs
'use client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface RevenuePoint { date: string; revenue: number }

export function RevenueChart({ data }: { data: RevenuePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis dataKey="date" stroke="#6B7280" />
        <YAxis stroke="#6B7280" />
        <Tooltip />
        <Line type="monotone" dataKey="revenue" stroke="#F9AB18" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stripe.js `redirectToCheckout` (deprecated) | `session.url` redirect or embedded Elements | 2023 | `redirectToCheckout` removed; use `session.url` directly |
| next-intl Pages Router setup | App Router `[locale]` dynamic segment | next-intl v3 (2023) | Requires full `app/` restructure |
| Stripe Pages Router `export const config = { api: { bodyParser: false } }` | App Router `req.text()` | Next.js 13+ | No config export needed; raw body via `req.text()` |
| React Email requires `@react-email/render` in API routes | `resend.emails.send({ react: <Template /> })` handles rendering | Resend SDK v2+ | Simplified: pass JSX directly to Resend |

**Deprecated/outdated:**
- `stripe.redirectToCheckout()`: Removed from Stripe.js. Use `window.location.href = session.url` after fetching checkout URL.
- `next-i18next`: Pages Router only. Do not use with App Router.
- `pages/api/stripe/webhook.ts` + `export const config = { api: { bodyParser: false } }`: Pages Router pattern. In App Router, route handlers receive raw body directly.

---

## Open Questions

1. **Where does the Stripe webhook live: Next.js API route or FastAPI?**
   - What we know: Both are valid. FastAPI is at a different URL (may not be public on Vercel free tier). Next.js route at `/api/stripe/webhook` is always publicly accessible.
   - What's unclear: The Vercel deployment topology — is FastAPI deployed as a Vercel service (from vercel-services skill context) or separately?
   - Recommendation: Put webhook in Next.js API route (`app/api/stripe/webhook/route.ts`). It calls FastAPI internally to update reservation. This avoids exposing FastAPI directly to Stripe.

2. **Stripe price unit: credits vs EUR cents**
   - What we know: The system uses `cost_credits` (integer) as the price unit. The existing UI shows "Credits". PAY-01 says "pay with card."
   - What's unclear: Is 1 credit = 1 EUR cent, 1 EUR, or something else? This conversion must be defined before implementing PAY-02.
   - Recommendation: Decide and document the exchange rate in a settings constant before writing Stripe session creation code.

3. **Resend sender domain**
   - What we know: Resend requires a verified sending domain. `resend==2.4.0` is in requirements.txt. The `from` address must use a verified domain.
   - What's unclear: Whether a domain is already verified in the Resend account.
   - Recommendation: Use `onboarding@resend.dev` as the test sender during development. Requires domain verification before going to production.

4. **next-intl and Stack Auth handler route compatibility**
   - What we know: Stack Auth uses `app/handler/[...nextauth]/route.ts`. The next-intl middleware matcher explicitly excludes `/api`. The handler is not under `/api`.
   - What's unclear: Whether the Stack Auth handler at `/handler/` (not `/api/`) will be accidentally locale-prefixed by the middleware.
   - Recommendation: Verify the middleware matcher also excludes `/handler`: `'/((?!api|handler|_next|_vercel|.*\\..*).*)'`.

5. **Google Maps "real data as primary" scope**
   - What we know: `ExplorePage.tsx` already conditionally fetches from Places API when `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is set, and falls back to mock on failure or when the key is absent. This is exactly the "real data primary" behavior described.
   - What's unclear: Whether the phase requirement means more work (e.g., search/filter integration with live data, or server-side caching of Places results).
   - Recommendation: Confirm with the phase description — if "Real Google Maps Places Data" means only what Phase 9 already delivered, this feature may be a no-op. Otherwise scope includes adding user-location-based centering and search-by-address.

---

## Sources

### Primary (HIGH confidence)
- `https://docs.stripe.com/checkout/quickstart?client=next` — Stripe Checkout session creation, success/cancel URL pattern
- `https://docs.stripe.com/webhooks` — Webhook signature verification, `constructEvent`, raw body requirement
- `https://resend.com/docs/send-with-nextjs` — Resend Next.js integration, React Email parameter
- `https://resend.com/docs/send-with-python` — Resend Python SDK, `resend.Emails.SendParams`, `resend.Emails.send()`
- `https://next-intl.dev/docs/getting-started/app-router` — next-intl App Router setup, `NextIntlClientProvider`
- `https://next-intl.dev/docs/routing/setup` — `defineRouting`, middleware setup, `[locale]` folder structure

### Secondary (MEDIUM confidence)
- `https://stripe.com/docs/stripe-js` — `@stripe/stripe-js` package; `redirectToCheckout` deprecation (confirmed by Stripe changelog)
- recharts official docs — `recharts ^2.10.3` already in package.json; `'use client'` requirement for Next.js confirmed by multiple sources

### Tertiary (LOW confidence)
- WebSearch: "Stripe Checkout Next.js 14 App Router webhook 2025" — multiple articles confirming `req.text()` pattern; not individually verified against Stripe docs
- WebSearch: "recharts occupancy heatmap" — recharts does not have a native heatmap; `ScatterChart` with custom cells is the workaround. GitHub issue #237 confirms no official heatmap. For occupancy heatmap, use `ScatterChart` or a colored grid of `div` elements.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified via official docs or already in package.json/requirements.txt
- Architecture patterns: HIGH — Stripe and next-intl patterns from official docs; FastAPI patterns from existing codebase
- Pitfalls: HIGH for Stripe/next-intl (from official docs); MEDIUM for recharts SSR (confirmed by multiple community sources)
- Google Maps enhancement scope: LOW — the open question about what "real data primary" means beyond Phase 9 is unresolved

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (Stripe and next-intl APIs are stable; Resend Python SDK is stable)

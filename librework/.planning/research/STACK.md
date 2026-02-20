# Technology Stack — Additions & Changes

**Project:** LibreWork (coworking reservation platform)
**Context:** Brownfield — extending existing Next.js 14 + FastAPI + Supabase app
**Researched:** 2026-02-20
**Overall confidence:** HIGH

> This document covers **what to add or change**, not the existing stack.
> For the current stack, see `.planning/codebase/STACK.md`.

---

## Recommended Additions

### 1. Authentication — Stack Auth

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `@stackframe/stack` | ^2.8.68 | Frontend | Next.js SDK — hooks, components, providers |
| `httpx` | ^0.28.1 | Backend | Async HTTP client for token verification against Stack Auth API |

**Why Stack Auth:** Already decided (PROJECT.md constraint). Open-source, MIT-licensed, built for Next.js App Router. Provides pre-built `<SignIn>`, `<SignUp>`, `<UserButton>`, `<AccountSettings>` components that replace all three existing auth hooks (`useAuth`, `useSimpleAuth`, `useAuth_replit`) with a single `useUser()` hook. Supports SSO, social login, email/password, and magic link out of the box.

**Frontend integration pattern:**
- `npx @stackframe/init-stack@latest` scaffolds `stack.ts`, provider setup, and handler route
- `StackProvider` wraps the app in the root layout
- `useUser({ or: "redirect" })` replaces all custom auth hooks
- Pre-built components handle sign-in/sign-up UI — no custom forms needed
- Stack Auth supports Teams with hierarchical permissions (maps to customer/owner/admin RBAC)

**Backend integration pattern (FastAPI):**
- Stack Auth does NOT have a Python SDK. Use REST API via `httpx.AsyncClient`
- Frontend sends Stack Auth access token in `x-stack-access-token` header
- Backend verifies token by calling `GET https://api.stack-auth.com/api/v1/users/me` with the token + server keys
- Create a FastAPI dependency (`get_current_user`) that validates tokens and returns user data
- Use `httpx` (not `requests`) because FastAPI is async — `requests` blocks the event loop

**Webhook sync:** Stack Auth fires `user.created` and `user.updated` webhooks. Configure these to sync user data to the Supabase `users` table, replacing the current manual user creation flow.

**Confidence:** HIGH — Official docs verified (last updated 2026-02-11), npm package actively maintained (v2.8.1–v2.8.68 over 12 months), Next.js App Router is the primary supported framework.

**Source:** https://docs.stack-auth.com, https://www.npmjs.com/package/@stackframe/stack

---

### 2. Payments — Stripe

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `stripe` | ^20.3.1 | Backend (Node via Next.js API routes) | Stripe server SDK for creating sessions, handling webhooks |
| `stripe` (Python) | ^14.3.0 | Backend (FastAPI) | Stripe server SDK for payment processing, refunds, webhooks |
| `@stripe/react-stripe-js` | ^5.6.0 | Frontend | React components for Stripe Elements |
| `@stripe/stripe-js` | ^8.7.0 | Frontend | Stripe.js loader (always loads latest Stripe.js at runtime) |

**Recommended flow: Stripe Checkout (Hosted)**
- User selects reservation → backend creates a Stripe Checkout Session → user redirects to Stripe-hosted page → Stripe redirects back on success/cancel
- Why hosted: Handles mobile, SCA (Strong Customer Authentication), PCI compliance, edge cases (declined cards, 3DS). Zero custom payment UI needed.
- Webhook (`checkout.session.completed`) confirms payment → backend marks reservation as paid

**Why both Node and Python Stripe SDKs:**
- The Node SDK (`stripe` npm) runs in Next.js API routes/Server Actions for creating Checkout Sessions (keeps Stripe secret key server-side in the Next.js layer)
- The Python SDK (`stripe` PyPI) runs in FastAPI for webhook processing, refund management, and payment status queries (business logic lives in FastAPI)
- This avoids duplicating business logic — Next.js creates sessions, FastAPI processes outcomes

**Alternative considered: Embedded Elements.** More UI control but vastly more complex — requires handling SCA, error states, card brand detection, mobile keyboards. Not justified for a reservation platform where the payment step should be fast and trustworthy.

**Confidence:** HIGH — Stripe is the industry standard. Both SDKs are first-party, actively maintained. Hosted Checkout is Stripe's recommended approach for most use cases.

**Source:** https://docs.stripe.com/checkout/quickstart, https://www.npmjs.com/package/stripe, https://pypi.org/project/stripe/

---

### 3. Internationalization — next-intl

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `next-intl` | ^4.8.3 | Frontend | i18n for Next.js App Router (routing, translations, formatting) |

**Why next-intl:**
- Built specifically for Next.js App Router from the ground up
- Tiny bundle (~2KB client-side) — only ships the active locale's translations
- Native Server Component support — `getTranslations()` in server components, `useTranslations()` in client components
- ICU message format for plurals, gender, interpolation (critical for French grammar)
- Middleware handles locale detection (URL prefix → cookie → Accept-Language → default)
- Type-safe translation keys with TypeScript

**Setup pattern:**
1. Create `src/i18n/routing.ts` — define `locales: ['fr', 'en']`, `defaultLocale: 'fr'`
2. Create `src/middleware.ts` — locale negotiation + URL rewriting
3. Move pages into `src/app/[locale]/` dynamic segment
4. Wrap layout with `NextIntlClientProvider`
5. Translation JSON files in `messages/fr.json`, `messages/en.json`

**Alternatives rejected:**

| Library | Why Not |
|---------|---------|
| `next-i18next` | Built for Pages Router; requires extra config for App Router; larger bundle (~8KB); react-i18next dependency adds complexity |
| `react-intl` (FormatJS) | Lower-level, no built-in routing; requires more glue code for Next.js |
| `lingui` | Smaller community in Next.js ecosystem; less documentation for App Router patterns |
| Next.js built-in i18n | Pages Router only (`next.config.js` i18n key); no App Router equivalent |

**Confidence:** HIGH — next-intl is the de facto standard for Next.js App Router i18n in 2025-2026. v4.8.3 released 2026-02-16, actively maintained by core contributor. Verified via npm (high download counts) and official Next.js docs recommend it alongside react-intl.

**Source:** https://next-intl.dev/docs/getting-started/app-router, https://www.npmjs.com/package/next-intl

---

### 4. Email Delivery — Resend

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `resend` | ^2.21.0 | Backend (Python) | Transactional email (password reset, booking confirmations, notifications) |

**Why Resend:**
- Simple API — one function call to send email, no SMTP config
- Built-in deliverability (DKIM, SPF, DMARC handled)
- Works directly with FastAPI — `resend.Emails.send(params)` in any endpoint
- Free tier (100 emails/day) covers pre-launch and early users
- Can pair with React Email for templating later if needed

**Why not alternatives:**

| Alternative | Why Not |
|-------------|---------|
| SendGrid | More complex setup, heavier SDK, overkill for transactional-only use |
| AWS SES | Requires AWS account/config; more operational overhead for a pre-launch app |
| Nodemailer/SMTP | Requires managing SMTP credentials, deliverability is your problem |
| Supabase Auth emails | We're removing Supabase Auth dependency |

**Confidence:** HIGH — Resend is well-documented for FastAPI, actively maintained, simple to integrate. Replaces the current "print token to console" password reset flow.

**Source:** https://resend.com/fastapi, https://pypi.org/project/resend/

---

### 5. Structured Logging — structlog

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `structlog` | ^25.5.0 | Backend | Structured JSON logging replacing print statements |

**Why structlog:**
- Drop-in replacement for `print()` and `logging.getLogger()` calls
- JSON output in production, colored console output in development
- Context variables via `structlog.contextvars` — bind `request_id`, `user_id` once per request, they appear in all subsequent log entries
- Integrates with Uvicorn's logging — replaces its default access logs with structured JSON
- Production-ready since 2013, stable API

**Implementation pattern:**
- Configure once in `app/core/logging.py`
- FastAPI middleware binds `request_id` (via `asgi-correlation-id`) and `user_id` per request
- Replace all `print()` calls with `structlog.get_logger()` methods
- JSON in production, ConsoleRenderer in development (toggle via `ENVIRONMENT` env var)

**Confidence:** HIGH — structlog is the standard choice for structured logging in Python. Well-documented FastAPI integration patterns exist. v25.5.0 is stable.

**Source:** https://structlog.org, https://pypi.org/project/structlog/

---

### 6. Frontend Testing — Vitest + React Testing Library

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `vitest` | ^4.0.18 | Frontend | Test runner (fast, Vite-native, Jest-compatible) |
| `@vitejs/plugin-react` | latest | Frontend | React support for Vitest |
| `@testing-library/react` | ^16.3.2 | Frontend | Component testing utilities |
| `@testing-library/dom` | latest | Frontend | DOM testing utilities (peer dep of RTL v16+) |
| `@testing-library/jest-dom` | latest | Frontend | Custom matchers (`.toBeInTheDocument()`, etc.) |
| `jsdom` | latest | Frontend | DOM environment for Vitest |

**Why Vitest over Jest:**
- 10-50x faster startup — uses Vite's transform pipeline, no separate Babel config needed
- Native ESM and TypeScript support — matches the Next.js/React ecosystem
- Jest-compatible API — same `describe/it/expect` syntax, easy for anyone who knows Jest
- Official Next.js docs recommend Vitest for unit/component testing
- Smart watch mode — only reruns tests affected by changed files

**Limitation:** Vitest cannot test async Server Components (new React pattern). Use Playwright for those.

**Confidence:** HIGH — Vitest v4 is stable, Next.js official docs include Vitest setup guide, RTL v16 is the current standard.

**Source:** https://vitest.dev, https://nextjs.org/docs/app/building-your-application/testing/vitest

---

### 7. End-to-End Testing — Playwright

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `@playwright/test` | ^1.58.2 | Frontend/E2E | Browser-based end-to-end testing |

**Why Playwright:**
- Cross-browser (Chromium, Firefox, WebKit) from one test suite
- Native mobile emulation — critical since LibreWork must be mobile-responsive
- Auto-waiting and web-first assertions — fewer flaky tests than Cypress
- Parallel execution built-in — fast CI runs
- Official Next.js docs recommend it alongside Vitest
- Trace viewer for debugging failed tests

**What to test with Playwright (not Vitest):**
- Full auth flow (sign-up → sign-in → redirect)
- Reservation booking flow (search → select → pay → confirm)
- Owner dashboard workflows
- Mobile responsiveness (viewport emulation)
- Async Server Components (Vitest can't handle these)

**Why not Cypress:** Playwright is faster, supports all browsers natively (Cypress needs plugins for Firefox/WebKit), better TypeScript support, and is the direction the Next.js ecosystem is moving.

**Confidence:** HIGH — Playwright v1.58 is the current stable release, 18.4M weekly downloads, Microsoft-maintained.

**Source:** https://playwright.dev, https://nextjs.org/docs/app/building-your-application/testing

---

### 8. Backend Testing Additions

| Package | Version | Side | Purpose |
|---------|---------|------|---------|
| `httpx` | ^0.28.1 | Backend | Also used as FastAPI test client (`httpx.AsyncClient` replaces `TestClient` for async tests) |
| `pytest-cov` | latest | Backend | Test coverage reporting |
| `factory-boy` | latest | Backend | Test data factories (users, reservations, establishments) |
| `respx` | latest | Backend | Mock httpx requests (for mocking Stack Auth API calls in tests) |

**Why these:**
- `httpx` as test client: FastAPI's `TestClient` uses `requests` under the hood (sync). For async endpoint testing, `httpx.AsyncClient` with `ASGITransport` is the recommended pattern.
- `respx`: Mocks `httpx` calls — critical for testing Stack Auth token verification without hitting the real API.
- `factory-boy`: Creates test fixtures declaratively. Better than raw dict creation for complex models (User, Reservation, Establishment with many fields).

**Note:** `pytest` (8.3) and `pytest-asyncio` (0.24) already exist in the project.

**Confidence:** HIGH — All are standard Python testing libraries with established FastAPI patterns.

---

## Packages to REMOVE

These should be removed as part of the auth migration:

| Package | Why Remove |
|---------|------------|
| `next-auth` (^4.24) | Replaced entirely by Stack Auth. next-auth routes, providers, and session logic all go away. |
| `python-jose[cryptography]` (3.3) | No longer needed — Stack Auth handles JWT creation/verification. Backend validates tokens via API call, not local JWT decode. |
| `passlib[bcrypt]` (1.7) | No longer needed — Stack Auth handles password hashing. Backend no longer stores or verifies passwords. |
| `@supabase/supabase-js` auth methods | Keep the package for DB queries, but stop using `supabase.auth.*` methods. Stack Auth replaces Supabase Auth entirely. |

**Confidence:** HIGH — These are direct replacements with clear 1:1 mapping.

---

## Packages to KEEP (no changes needed)

The following existing dependencies are solid and don't need replacement:

| Package | Why Keep |
|---------|---------|
| Next.js 14.2 | Stable, App Router works. Upgrade to 15 is optional and not urgent (no blocking features needed). |
| React 18 | Stable. React 19 adoption is still early; no features needed from it. |
| FastAPI 0.115 | Latest line. No upgrade needed. |
| Tailwind CSS 3.3 | Solid. Tailwind v4 is available but migration cost isn't justified for this milestone. |
| `@tanstack/react-query` ^5.17 | The right tool for server state. No alternative needed. |
| `zustand` ^4.5 | Lightweight client state. Perfect for this app's complexity. |
| `react-hook-form` + `zod` | Form handling is already well-structured. |
| `recharts` ^2.10 | Adequate for owner analytics charts. |
| Radix UI + shadcn/ui | Component library is already in use and consistent. |
| `pydantic` 2.10 | Validation layer is solid. |
| `supabase` (Python, for DB) | Keep for Supabase PostgreSQL queries. Remove auth usage only. |

---

## Installation Commands

### Frontend (npm)

```bash
# Auth
npm install @stackframe/stack

# Payments
npm install stripe @stripe/react-stripe-js @stripe/stripe-js

# i18n
npm install next-intl

# Testing (dev)
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/dom @testing-library/jest-dom jsdom @playwright/test

# Remove legacy auth
npm uninstall next-auth
```

### Backend (pip/uv)

```bash
# Auth (HTTP client for Stack Auth API)
pip install httpx

# Payments
pip install stripe

# Email
pip install resend

# Logging
pip install structlog asgi-correlation-id

# Testing (dev)
pip install httpx pytest-cov factory-boy respx
```

---

## Environment Variables (New)

### Frontend (.env.local)

```env
# Stack Auth
NEXT_PUBLIC_STACK_PROJECT_ID=<from Stack Auth dashboard>
NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=<from Stack Auth dashboard>
STACK_SECRET_SERVER_KEY=<from Stack Auth dashboard>

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=<from Stripe dashboard>
STRIPE_SECRET_KEY=<from Stripe dashboard>
STRIPE_WEBHOOK_SECRET=<from Stripe CLI or dashboard>
```

### Backend (.env)

```env
# Stack Auth (for token verification)
STACK_PROJECT_ID=<from Stack Auth dashboard>
STACK_PUBLISHABLE_CLIENT_KEY=<from Stack Auth dashboard>
STACK_SECRET_SERVER_KEY=<from Stack Auth dashboard>

# Stripe
STRIPE_SECRET_KEY=<from Stripe dashboard>
STRIPE_WEBHOOK_SECRET=<from Stripe dashboard>

# Email
RESEND_API_KEY=<from Resend dashboard>

# Logging
ENVIRONMENT=development  # or "production" for JSON output
```

---

## Decision Summary

| Decision | Choice | Why | Confidence |
|----------|--------|-----|------------|
| Auth SDK | `@stackframe/stack` ^2.8.68 | Project constraint; native App Router support; replaces 3 hooks with 1 | HIGH |
| Auth backend verification | `httpx` → Stack Auth REST API | No Python SDK exists; async HTTP client matches FastAPI's async nature | HIGH |
| Payments | Stripe Hosted Checkout | Industry standard; handles SCA/PCI; fast integration | HIGH |
| i18n | `next-intl` ^4.8.3 | Built for App Router; tiny bundle; ICU format for French grammar | HIGH |
| Email | `resend` ^2.21.0 | Simplest transactional email; free tier; no SMTP config | HIGH |
| Structured logging | `structlog` ^25.5.0 | Standard Python structured logging; context variables for request tracing | HIGH |
| Frontend unit tests | Vitest ^4.0.18 + RTL ^16.3.2 | Fast, Vite-native, officially recommended by Next.js docs | HIGH |
| E2E tests | Playwright ^1.58.2 | Cross-browser, mobile emulation, async server component coverage | HIGH |
| Backend test mocking | `respx` + `factory-boy` | Mock httpx calls to Stack Auth; declarative test data | HIGH |

---

## Open Questions

1. **Stack Auth RBAC mapping:** Stack Auth supports Teams with hierarchical permissions. Need to decide during implementation whether to use Stack Auth Teams to model customer/owner/admin roles, or keep roles in the Supabase users table and sync via webhooks. Recommendation: use Stack Auth's permission system for auth checks, mirror to Supabase for business queries.

2. **Stripe Connect for owners:** If owners receive payouts directly (marketplace model), Stripe Connect is needed. Current PROJECT.md doesn't specify this. If LibreWork collects payment and pays owners separately, basic Stripe Checkout suffices. Clarify during implementation.

3. **Next.js upgrade to 15:** Not required for this milestone, but next-intl v4 and Stack Auth both support Next.js 15. Consider upgrading in a future milestone for Server Actions improvements and Turbopack stability.

4. **Translation workflow:** Who translates? If developer-managed JSON files, next-intl alone is sufficient. If non-technical translators need access, consider adding Crowdin or Lokalise integration later.

---

*Stack research: 2026-02-20*

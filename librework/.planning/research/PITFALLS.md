# Domain Pitfalls

**Domain:** Coworking/shared workspace reservation platform (brownfield migration)
**Researched:** 2026-02-20
**Focus:** Auth migration (custom JWT → Stack Auth), Stripe payments, i18n retrofit, reservation system integrity

---

## Critical Pitfalls

These cause rewrites, data loss, or broken production flows. Address with highest priority.

### Pitfall 1: Auth Migration Leaves Orphaned Token Paths

**What goes wrong:** After migrating to Stack Auth, some backend routes still verify tokens via the old `decode_access_token` (python-jose), while the frontend sends Stack Auth tokens. Requests silently fail with 401s on routes that weren't updated. Worse: the codebase already has *two* `get_current_user` implementations (`dependencies.py` returns `UserResponse`, `auth_enhanced.py` returns `dict`) — migrating only one leaves the other as a live landmine.

**Why it happens:** LibreWork has 19 API route files, each importing auth dependencies from different sources. There's no single import path. Developers update the obvious routes (`auth`, `users`) but miss that `rbac.py`, `admin_audit.py`, `establishments.py`, `reservations.py`, and `owner.py` all import auth deps independently.

**Warning signs:**
- 401 errors on specific routes after auth migration, while others work fine
- `grep` for `from app.core.dependencies import` and `from app.core.auth_enhanced import` shows routes still using old imports
- Frontend works for basic pages but breaks on owner dashboard or admin views

**Prevention:**
1. Before touching any auth code, create a dependency map: which routes import which auth function
2. Replace the *dependency functions* (`get_current_user`, `get_current_owner`, `get_current_admin`) at the source — `dependencies.py` — so all routes using `Depends(get_current_user)` get Stack Auth token verification automatically
3. Add an integration test that hits every protected endpoint with a Stack Auth token
4. Only after all routes pass, delete the old auth modules

**Detection checklist:**
- [ ] Every `.py` file in `api/v1/` uses the same `get_current_user`
- [ ] No imports from `app.core.security.decode_access_token` remain
- [ ] No imports from `app.core.auth_enhanced.get_current_user` remain

**Phase:** Auth Migration (Phase 1 — must be first)
**Confidence:** HIGH — directly observed in codebase

---

### Pitfall 2: User Migration — Password Hashes and Identity Mapping

**What goes wrong:** Existing users in Supabase have bcrypt password hashes. Stack Auth manages its own user store. If you don't migrate existing users into Stack Auth, everyone must re-register. If you migrate but mess up the hash format or user ID mapping, existing reservations, favorites, reviews, and RBAC roles become orphaned (they reference the old user ID).

**Why it happens:** Stack Auth's REST API allows creating users server-side, but documentation on importing password hashes is sparse. The codebase also has a password column naming inconsistency (`hashed_password` vs `password_hash`) that can cause the migration script to read the wrong column.

**Warning signs:**
- After migration, users can't log in with their existing password
- Reservations or reviews show "unknown user" or empty owner fields
- RBAC permissions stop working because `user_id` foreign keys point to old IDs

**Prevention:**
1. Write a migration script that: (a) reads users from Supabase, (b) creates them in Stack Auth via the Admin API, (c) stores a mapping table (`old_id → stack_auth_id`)
2. If Stack Auth doesn't support bcrypt hash import: use progressive migration — on first login via Stack Auth, look up the user in Supabase, verify password against the old hash, then create/link the Stack Auth account
3. Before running migration, verify which column name is actually in the database (`hashed_password` or `password_hash`) — don't trust the code, query the schema
4. Update all foreign key references (reservations, reviews, favorites, RBAC roles, audit logs) to use the new Stack Auth user ID, or keep the same UUID if Stack Auth allows setting custom IDs

**Detection checklist:**
- [ ] Test login with an existing user's credentials after migration
- [ ] Query reservations joined with users — no nulls
- [ ] RBAC role check passes for a migrated admin user

**Phase:** Auth Migration (Phase 1)
**Confidence:** HIGH — password column inconsistency confirmed in CONCERNS.md; user migration is inherent to any auth provider switch

---

### Pitfall 3: Stripe Webhook Events Processed Multiple Times

**What goes wrong:** Stripe delivers webhooks with at-least-once semantics. Without idempotency guards, the same `payment_intent.succeeded` event processes twice, resulting in double credit allocation, duplicate reservation confirmations, or duplicate notification emails.

**Why it happens:** Developers return 200 OK and process the business logic synchronously. If the handler crashes after crediting the user but before returning, Stripe retries. The second delivery succeeds fully, double-crediting. This is especially dangerous for LibreWork's credit system where users pay credits for reservations.

**Warning signs:**
- Users report receiving double credits or double charges
- Duplicate reservation confirmation emails
- `stripe_events` table (if it exists) has duplicate event IDs
- Stripe dashboard shows webhook retries for events that did process

**Prevention:**
1. Create a `processed_webhook_events` table with a UNIQUE constraint on `stripe_event_id`
2. Before processing any webhook: attempt INSERT into this table. If it violates uniqueness, return 200 and skip
3. Wrap business logic in a database transaction: insert event record + apply business effect atomically
4. Always return 200 within 10 seconds — offload heavy work (emails, external calls) to a background queue
5. Verify webhook signatures using the raw request body *before* any JSON parsing

**Implementation pattern:**
```python
async def handle_webhook(request: Request):
    raw_body = await request.body()
    try:
        event = stripe.Webhook.construct_event(raw_body, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    # Idempotency guard
    result = supabase.table("processed_webhook_events").insert(
        {"event_id": event["id"], "event_type": event["type"]}
    ).execute()
    if not result.data:  # Already processed
        return {"status": "already_processed"}

    # Process in transaction...
```

**Phase:** Payments Integration (Phase 2)
**Confidence:** HIGH — Stripe's own documentation explicitly warns about this; credit system makes it high-impact

---

### Pitfall 4: Reservation Double-Booking Race Condition

**What goes wrong:** Two users simultaneously book the same space for the same time slot. Both read "available," both insert a reservation, both succeed. The space is double-booked.

**Why it happens:** The current reservation creation likely does: (1) check availability with a SELECT, (2) insert reservation. Between steps 1 and 2, another request can also pass the availability check. There's no row-level locking or database constraint preventing overlapping bookings. Supabase's REST API (used via the Python client) doesn't support `SELECT ... FOR UPDATE`.

**Warning signs:**
- Two confirmed reservations for the same space and overlapping time
- Owner dashboard shows conflicting bookings
- Users arrive at a space that's already occupied

**Prevention:**
1. Add a PostgreSQL EXCLUSION constraint on `(space_id, tsrange(start_time, end_time))` using the `btree_gist` extension — the database itself rejects overlapping bookings
2. If exclusion constraints aren't possible via Supabase client, use an RPC function that runs the check-and-insert atomically in a single transaction with `SERIALIZABLE` isolation or `SELECT ... FOR UPDATE`
3. Add a unique partial index as a belt-and-suspenders measure for fixed time slots
4. Never rely on application-level availability checks alone

**Phase:** Payments Integration (Phase 2) — must be solved before money is involved
**Confidence:** HIGH — race conditions in booking systems are a well-documented class of bugs; current code uses Supabase REST client with no locking

---

### Pitfall 5: Frontend Auth State Fragmentation During Migration

**What goes wrong:** The frontend has three auth hooks (`useAuth`, `useSimpleAuth`, `useAuth_replit`). During migration, a new Stack Auth hook is added as a fourth. Some pages use the new hook, some still use old ones. The Navbar (hardcoded `isAuthenticated = false`) is forgotten. Users see inconsistent logged-in/logged-out states across pages.

**Why it happens:** Incremental migration is tempting — update one hook at a time. But if the old hooks still exist and some pages import them, you get pages where the user appears logged in (new hook) next to pages where they appear logged out (old hook reading an empty `localStorage` key).

**Warning signs:**
- User logged in on homepage but appears logged out on owner dashboard
- `localStorage` has both `access_token` (old) and Stack Auth cookie/token (new)
- Console errors about missing auth context on some pages

**Prevention:**
1. Do NOT create a fourth hook. Replace `useAuth.tsx` in-place with Stack Auth logic. Make `useSimpleAuth` and `useAuth_replit` re-export from the same source (or delete them with a codemod)
2. Fix the Navbar `isAuthenticated` hardcode in the SAME commit as the auth hook migration — it's the most visible symptom
3. Search for every `localStorage.getItem('token')` and `localStorage.getItem('access_token')` — replace with the Stack Auth SDK's token accessor
4. The owner components (`OwnerReservationsTable`, `EnhancedOwnerDashboard`, `OwnerLoyaltyManager`) use `localStorage.getItem('token')` — these MUST be updated or they'll silently break

**Detection checklist:**
- [ ] `grep -r "useSimpleAuth\|useAuth_replit\|localStorage.getItem('token')\|localStorage.getItem('access_token')" --include="*.tsx" --include="*.ts"` returns zero results
- [ ] Navbar shows correct auth state
- [ ] Owner dashboard works after login

**Phase:** Auth Migration (Phase 1)
**Confidence:** HIGH — all three hooks and the Navbar bug confirmed in codebase

---

## Moderate Pitfalls

These cause significant rework or user-facing bugs but won't corrupt data.

### Pitfall 6: i18n String Concatenation Breaking Non-English Layouts

**What goes wrong:** Developers wrap English strings with `t()` but keep string concatenation patterns like `t('Latest reviews for') + ' ' + establishmentName`. This works in English but breaks in French (and catastrophically in RTL or SOV languages) where word order differs. Date and currency formatting are hardcoded to `en-US` patterns throughout the app.

**Why it happens:** Retrofitting i18n into an existing codebase means touching every component. The temptation is to do a quick find-and-replace, wrapping strings with `t()`. But interpolation, pluralization, and date/currency formatting need ICU message syntax.

**Warning signs:**
- French translations look grammatically wrong despite correct individual word translations
- Dates show "02/20/2026" instead of "20/02/2026" in French locale
- Prices show "$" instead of "€" for French users
- Plural forms are wrong ("1 réservations" instead of "1 réservation")

**Prevention:**
1. Use `next-intl` with ICU message format from the start: `t('reviewsFor', {name: establishmentName})` with message `"Derniers avis pour {name}"`
2. Never concatenate translated strings with variables
3. Use `next-intl`'s `useFormatter` for dates, times, and currencies — not hardcoded `toLocaleDateString()`
4. French has different plural rules than English (0 and 1 are both singular) — test plural forms explicitly
5. Budget 2-3x the estimated time for i18n retrofit; it touches nearly every component

**Phase:** i18n (Phase 3 or 4 — after core features stabilize)
**Confidence:** HIGH — universal i18n pitfall, well-documented in next-intl learning resources

---

### Pitfall 7: Stack Auth Backend Verification Adds Latency to Every Request

**What goes wrong:** Stack Auth token verification via REST API (`GET /api/v1/users/me` with the access token) adds a network round-trip to every authenticated request. On a FastAPI backend, this turns every `Depends(get_current_user)` into an async HTTP call to Stack Auth's servers, adding 50-200ms latency per request.

**Why it happens:** The current `get_current_user` decodes the JWT locally (fast, ~1ms). Stack Auth's recommended Python backend pattern makes an API call to Stack Auth to verify the token and get user data. This is correct for security but slow at scale.

**Warning signs:**
- API response times increase by 100-200ms across the board after migration
- P99 latency spikes during Stack Auth service hiccups
- Users notice the app feels "slower" after the auth migration

**Prevention:**
1. Cache the Stack Auth token verification result for a short TTL (e.g., 30-60 seconds) keyed on the access token hash
2. If Stack Auth issues standard JWTs, verify the signature locally using Stack Auth's public JWKS endpoint (fetched and cached) instead of calling their API per-request
3. Keep user profile data in your Supabase `users` table; only call Stack Auth for token verification, not for user data on every request
4. Add request timing middleware to detect latency regressions early

**Phase:** Auth Migration (Phase 1) — design for this from the start
**Confidence:** MEDIUM — depends on Stack Auth's token format (if standard JWT, local verification is possible); API-based verification is confirmed in their docs

---

### Pitfall 8: Stripe Connect Account Type Lock-In

**What goes wrong:** LibreWork is a marketplace where owners earn revenue from reservations. Choosing the wrong Stripe Connect account type (Standard vs Express vs Custom) at the start creates a migration nightmare later because Stripe doesn't allow changing account types after creation.

**Why it happens:** Standard accounts are easiest to implement but show Stripe's branding and dashboard to owners, reducing platform control. Custom accounts offer full control but require you to handle all compliance, KYC, and dispute management. Express is the sweet spot but still requires building onboarding UI.

**Warning signs:**
- Owners confused by Stripe's dashboard when they expected a LibreWork dashboard
- Compliance issues because Custom account obligations weren't understood
- Need to re-onboard all owners to switch account types

**Prevention:**
1. Use **Express accounts** — they balance control with compliance simplicity
2. Use Stripe's hosted onboarding flow (`account_links`) for owner onboarding rather than building custom KYC forms
3. Decide the charge model early: **Destination Charges** (platform is merchant of record, simplest for a booking platform) vs **Separate Charges and Transfers** (more flexible for complex splits)
4. For a reservation platform, Destination Charges with an `application_fee_amount` is almost certainly the right choice
5. Document this decision in ADR format — it's expensive to change

**Phase:** Payments Integration (Phase 2)
**Confidence:** HIGH — Stripe's own documentation warns about account type lock-in

---

### Pitfall 9: i18n Route Structure Breaks Existing Links and SEO

**What goes wrong:** Adding `[locale]` dynamic segments to the Next.js App Router changes every URL from `/spaces/123` to `/en/spaces/123` or `/fr/spaces/123`. Existing bookmarks, shared links, and any hardcoded internal links break. Search engines see the old URLs as 404s.

**Why it happens:** `next-intl` requires all pages to be nested under `app/[locale]/`. This is a structural change to the route tree, not just a wrapper.

**Warning signs:**
- 404 errors on previously working URLs after deploying i18n
- Internal links in emails, notifications, or external integrations stop working
- Google Search Console shows spike in 404 errors

**Prevention:**
1. Add `next-intl` middleware that detects the locale from `Accept-Language` header or cookie and redirects bare paths (`/spaces/123` → `/en/spaces/123`) with 308 redirects
2. Update all internal link generation (emails, notifications, calendar exports) to include the locale prefix
3. If the app is pre-launch (it is), this is lower risk — but still audit all hardcoded paths in components and API responses
4. Test that the middleware correctly handles: root path, API routes (should NOT be localized), static assets, and webhook endpoints

**Phase:** i18n (Phase 3 or 4)
**Confidence:** HIGH — structural requirement of next-intl with App Router

---

### Pitfall 10: Stripe Payment Authorization Expiry for Reservations

**What goes wrong:** A user books a space for next week. The platform authorizes (but doesn't capture) the payment. The authorization expires after 7 days. When the reservation date arrives, the capture fails — the user's card has released the hold, and the platform can't collect payment.

**Why it happens:** Stripe's authorize-then-capture pattern has brand-specific expiry windows (Visa: 5-7 days, Mastercard/Amex: 7 days). If the reservation is further out than the authorization window, the hold lapses.

**Warning signs:**
- Capture failures for reservations booked more than 5-7 days in advance
- Revenue leakage — users use the space but payment was never collected
- Stripe dashboard shows `canceled` PaymentIntents that should have been `captured`

**Prevention:**
1. For same-day or next-day bookings: authorize + capture immediately at booking time (simplest)
2. For bookings within 7 days: authorize at booking, capture on the day of reservation
3. For bookings beyond 7 days: charge immediately at booking (with clear refund policy), OR save the payment method and create a new PaymentIntent closer to the date
4. Stripe's "extended authorization" (up to 30 days) is available for eligible merchants but requires approval
5. Define and display a clear cancellation/refund policy — this is a UX concern as much as a technical one

**Phase:** Payments Integration (Phase 2)
**Confidence:** HIGH — authorization windows are documented in Stripe's official docs

---

## Minor Pitfalls

These cause friction or technical debt but have limited blast radius.

### Pitfall 11: Removing next-auth Before Confirming No Routes Depend On It

**What goes wrong:** The codebase includes `next-auth` and a `SessionProvider` in `providers.tsx`. Removing it during cleanup breaks any routes or components that implicitly depend on `next-auth`'s session context, even if the main auth flow doesn't use it.

**Prevention:**
1. Search for all imports from `next-auth` across the frontend before removing it
2. Check if any API routes use `getServerSession` or `getSession`
3. Remove `SessionProvider` from `providers.tsx` only after confirming no consumers exist
4. Remove `next-auth` from `package.json` last, after all imports are gone

**Phase:** Auth Migration (Phase 1) — cleanup step after Stack Auth is working
**Confidence:** HIGH — `SessionProvider` confirmed in `providers.tsx`

---

### Pitfall 12: Credit System Conflicts with Stripe Payments

**What goes wrong:** LibreWork has an existing credit system for reservations. Adding Stripe payments creates ambiguity: do users pay with credits, with Stripe, or both? If both paths exist without clear rules, users find exploits (buy credits at a discount, use credits to bypass Stripe fees) or get confused about which payment method applies.

**Prevention:**
1. Decide upfront: are credits being replaced by Stripe, or do they coexist?
2. If coexisting: define clear precedence rules (credits first, Stripe for remainder)
3. If replacing: deprecate credits with a migration path (convert remaining credits to account balance or refund)
4. The credit system likely needs a Stripe-backed purchase flow if it persists

**Phase:** Payments Integration (Phase 2) — decide before building Stripe flows
**Confidence:** MEDIUM — depends on product decision; technical risk is moderate

---

### Pitfall 13: RBAC Permissions Silently Break During Auth Migration

**What goes wrong:** The RBAC system (`rbac.py`) reads roles from the Supabase `users` table and a `custom_roles` JSON field. After migrating to Stack Auth, if the role data isn't synchronized between Stack Auth's user metadata and the Supabase `users` table, `has_permission` returns `{}` (empty) and users lose all permissions without any error message.

**Prevention:**
1. Keep RBAC data in Supabase `users` table — don't move it to Stack Auth's metadata (it's application-specific, not identity-specific)
2. Ensure `get_current_user` still fetches from Supabase after verifying the Stack Auth token — the user's role must come from the application database
3. Write RBAC integration tests before migration; run them after migration
4. The `resolve_user_permissions` function returning `{}` on failure should be changed to raise an exception

**Phase:** Auth Migration (Phase 1)
**Confidence:** HIGH — fragile RBAC behavior confirmed in CONCERNS.md; `{}` silent failure confirmed in `rbac.py`

---

### Pitfall 14: Webhook Endpoint Accidentally Protected by Auth Middleware

**What goes wrong:** Stripe webhooks call your endpoint without authentication (they use signature verification instead). If the webhook endpoint is behind the auth middleware or a catch-all auth wrapper, Stripe's requests get 401'd and payments never process.

**Prevention:**
1. Explicitly exclude the webhook route from auth middleware
2. In FastAPI, mount the webhook handler on a separate router without `Depends(get_current_user)`
3. Use Stripe signature verification as the sole authentication mechanism for webhook endpoints
4. Test with Stripe CLI (`stripe listen --forward-to localhost:8000/webhooks/stripe`) during development

**Phase:** Payments Integration (Phase 2)
**Confidence:** HIGH — common mistake, easy to prevent

---

### Pitfall 15: i18n Message Keys Become Unmaintainable

**What goes wrong:** Without a convention, message keys become inconsistent (`home.title`, `homePageTitle`, `homepage_title`, `Home.Title`). Six months later, nobody knows which keys exist, which are unused, and which are duplicated. French translations drift out of sync with English.

**Prevention:**
1. Establish a key naming convention early: `{page}.{section}.{element}` (e.g., `spaces.search.placeholder`)
2. Use `next-intl`'s `useExtracted` (experimental) to auto-extract messages and keep locales in sync
3. Add a CI check that compares `en.json` and `fr.json` key sets — fail if they diverge
4. Colocate messages with components using namespace conventions rather than one massive file

**Phase:** i18n (Phase 3 or 4)
**Confidence:** HIGH — universal i18n maintenance issue

---

## Phase-Specific Warning Matrix

| Phase | Pitfall | Severity | Mitigation Summary |
|-------|---------|----------|--------------------|
| **Auth Migration** | Orphaned token paths (#1) | CRITICAL | Single dependency replacement + exhaustive route audit |
| **Auth Migration** | User/password migration (#2) | CRITICAL | Migration script with progressive fallback |
| **Auth Migration** | Frontend auth fragmentation (#5) | CRITICAL | Replace in-place, don't add fourth hook |
| **Auth Migration** | Backend verification latency (#7) | MODERATE | Local JWT verification with JWKS cache |
| **Auth Migration** | RBAC silent failure (#13) | MODERATE | Keep roles in Supabase; test before and after |
| **Auth Migration** | next-auth removal (#11) | MINOR | Audit imports before removal |
| **Payments** | Webhook idempotency (#3) | CRITICAL | Deduplication table with unique constraint |
| **Payments** | Double-booking race condition (#4) | CRITICAL | PostgreSQL EXCLUSION constraint |
| **Payments** | Connect account type (#8) | MODERATE | Choose Express + Destination Charges |
| **Payments** | Authorization expiry (#10) | MODERATE | Charge model matched to booking lead time |
| **Payments** | Credit system conflict (#12) | MODERATE | Product decision before implementation |
| **Payments** | Webhook auth bypass (#14) | MINOR | Exclude webhook route from auth middleware |
| **i18n** | String concatenation (#6) | MODERATE | ICU message format from day one |
| **i18n** | Route structure breaks (#9) | MODERATE | Middleware redirects for bare paths |
| **i18n** | Key maintainability (#15) | MINOR | Naming convention + CI sync check |

## Codebase-Specific Risk Map

These are confirmed issues in LibreWork's codebase that amplify the above pitfalls:

| Existing Issue | Amplifies Pitfall | Why It's Worse |
|----------------|-------------------|----------------|
| Two `get_current_user` implementations | #1 (Orphaned token paths) | Must update TWO entry points, not one |
| `hashed_password` vs `password_hash` inconsistency | #2 (User migration) | Migration script may read wrong column |
| Three frontend auth hooks | #5 (Frontend fragmentation) | Three hooks to replace vs one |
| Navbar `isAuthenticated = false` hardcode | #5 (Frontend fragmentation) | Most visible symptom; easy to forget |
| Owner components use `localStorage.getItem('token')` | #5 (Frontend fragmentation) | Breaks silently — 401 on owner dashboard |
| `resolve_user_permissions` returns `{}` on failure | #13 (RBAC silent failure) | No error = no detection |
| No test coverage for auth or RBAC | #1, #2, #5, #13 | No safety net for migration regressions |
| Supabase REST client (no transaction support) | #4 (Double-booking) | Can't use `SELECT ... FOR UPDATE` through REST |
| `SessionProvider` from next-auth in providers | #11 (next-auth removal) | May have hidden consumers |

## Sources

- Stack Auth documentation: https://docs.stack-auth.com/ (setup, backend integration, Python SDK)
- Stripe webhook documentation: https://docs.stripe.com/webhooks
- Stripe Connect marketplace guide: https://docs.stripe.com/connect
- Stripe authorization and capture: https://stripe.com/docs/payments/capture-later
- PostgreSQL double-booking prevention: https://jsupskills.dev/how-to-solve-the-double-booking-problem
- next-intl documentation: https://next-intl.dev/
- next-intl learning course on literals extraction: https://learn.next-intl.dev/
- LibreWork codebase analysis: `.planning/codebase/CONCERNS.md`, `backend/app/core/dependencies.py`, `backend/app/api/v1/` route files, `frontend/src/hooks/`

---

*Pitfalls research: 2026-02-20*

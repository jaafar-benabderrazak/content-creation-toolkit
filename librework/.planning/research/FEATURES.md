# Feature Landscape

**Domain:** Coworking / shared workspace reservation marketplace (two-sided: customers + space owners)
**Researched:** 2026-02-20
**Overall confidence:** HIGH (multiple industry sources, competitor analysis, Stripe documentation, existing codebase audit)

---

## Existing Features (Already Built)

Before mapping new features, here's what LibreWork already has. These are **not re-scoped** but may need hardening as new features layer on top.

| Feature | Status | Quality | Notes |
|---------|--------|---------|-------|
| User registration / login | Exists | Fragile | 3 auth hooks, dual backend auth — migrating to Stack Auth |
| Establishment CRUD | Exists | Functional | Owner creates/manages establishments |
| Space management | Exists | Functional | Types: table, room, desk, booth |
| Reservation creation/management | Exists | Functional | Time-slot booking with overlap detection |
| Credit system | Exists | Functional | Purchase/debit/refund/bonus transactions; 1-10 credits/hour |
| Tiered cancellation refunds | Exists | Functional | >2h = full, >30min = 50%, <30min = 0% (in DB trigger) |
| Reviews & ratings | Exists | Functional | 1-5 stars, one per reservation |
| Favorites | Exists | Functional | Save/unsave establishments |
| Group reservations | Exists | Functional | Creator invites members, split credit cost |
| Loyalty / rewards | Exists | Functional | Backend structure exists |
| Notifications | Exists | Partial | DB tables exist; no email/push delivery |
| Calendar export (iCal) | Exists | Functional | |
| RBAC (customer/owner/admin) | Exists | Functional | |
| Audit logging | Exists | Functional | |
| PostGIS spatial queries | Exists | Partial | Extension enabled, GIST index on location; but frontend uses in-memory filtering |
| QR codes for spaces | Exists | Functional | Validation codes for check-in |

---

## Table Stakes

Features users and owners **expect to exist**. Missing any of these means the platform feels incomplete or untrustworthy. Users will leave for competitors that have them.

### Customer-Facing

| # | Feature | Complexity | Exists? | Why Expected | Notes |
|---|---------|------------|---------|--------------|-------|
| T1 | **Instant booking confirmation** | Low | Partial | Industry standard since 2024. Peerspace, WeWork On Demand, Upflex all confirm instantly. Users abandon platforms with manual approval delays. | Reservation creation exists but no confirmation email/notification delivery. Must work end-to-end. |
| T2 | **Real payment acceptance** | High | No | Credits-only is a walled garden. Users expect to pay with a card, Apple Pay, or Google Pay. Every major competitor accepts real money. | Stripe integration. This is the #1 gap. Credits can coexist as a loyalty/wallet layer on top of real payments. |
| T3 | **Location-based search with map** | Medium | Partial | PostGIS is in the DB. But users expect an Airbnb/Google Maps-style map + list split view. Coworker.com API, Typesense GeoSearch, and every marketplace platform use map-first discovery. | Frontend needs map component (Mapbox or Google Maps), backend needs to expose PostGIS ST_DWithin queries instead of in-memory filtering. |
| T4 | **Filter by amenities, price, availability** | Medium | Partial | Amenities exist on establishments. Price (credits) exists. But no filter UI combining them. Users expect: open now, price range, wifi, quiet, capacity, category. | Backend supports the data; frontend needs filter panel + query params. |
| T5 | **Mobile-responsive design** | Medium | Partial | 70% of coworking searches happen on mobile (FlexSpace AI data). Non-negotiable for a consumer-facing marketplace. | Tailwind + shadcn/ui are responsive-capable but current views need responsive audit. |
| T6 | **Booking confirmation + reminder emails** | Medium | No | Standard across all competitors. WeWork sends 24h reminders. Upflex sends confirmation + reminder. 98% open rate on SMS reminders (Zencal data). | Email delivery doesn't work (prints tokens to console). Needs transactional email provider (Resend, Postmark, or SendGrid). |
| T7 | **Clear cancellation policy display** | Low | Partial | Tiered refund logic exists in DB. But users must see the policy BEFORE booking (Peerspace, FlySpaces, Upflex all display prominently). | Surface existing refund tiers in booking UI. No backend work needed. |
| T8 | **Establishment detail pages with photos** | Low | Exists | Images array exists on establishments. Just needs good presentation — hero image, gallery, amenity icons, reviews section, map pin. | UI polish, not new backend work. |
| T9 | **Receipt / booking history** | Low | Partial | Reservations and credit_transactions exist. Users need a clear "My Bookings" page with status, cost, and downloadable/viewable receipts. | When Stripe is added, receipts become legally required for payments. |
| T10 | **Owner notifications for new bookings** | Medium | No | Owners MUST know when someone books their space. Every coworking management platform (Optix, Spacebring, Nexudus) sends instant owner alerts. | Part of the notification system buildout. |

### Owner-Facing

| # | Feature | Complexity | Exists? | Why Expected | Notes |
|---|---------|------------|---------|--------------|-------|
| T11 | **Reservation management dashboard** | Medium | Partial | Owner endpoint exists but needs proper calendar/list view showing upcoming, active, past bookings. Owners need to confirm, cancel, and view reservation details. | Extend existing owner API; build frontend dashboard. |
| T12 | **Establishment editing** | Low | Exists | CRUD exists. May need polish (image upload, hours picker, amenity selector). | UI improvement. |
| T13 | **Basic revenue/booking stats** | Medium | No | Optix, Cobot, Spacebring all provide utilization and revenue views. Owners won't list on a platform that gives them zero visibility into performance. | New analytics queries + dashboard UI. |
| T14 | **Payout / earnings visibility** | High | No | Once real payments exist, owners must see: earnings, pending payouts, payout history. Stripe Connect dashboard or custom UI over Stripe API. | Depends on T2 (Stripe). Critical for trust. |

---

## Differentiators

Features that set LibreWork apart. Not expected, but valuable. Build these after table stakes are solid.

| # | Feature | Complexity | Value Proposition | Priority | Notes |
|---|---------|------------|-------------------|----------|-------|
| D1 | **Credit wallet + Stripe hybrid** | High | Unique: users can pay with credits (earned via loyalty/bonuses) OR real money, or a mix. No major competitor does credit-wallet + Stripe hybrid well. Peerspace offers "Peerspace Credit" as refund alternative; LibreWork already has a richer credit system. | High | Leverage existing credit_transactions table. Credits become a "balance" alongside Stripe payments. Requires careful UX to avoid confusion. |
| D2 | **Owner analytics dashboard (deep)** | High | Go beyond basic stats. Occupancy heatmaps by hour/day, revenue trends, booking source analysis, cancellation rates, review sentiment. Cobot reports 20% utilization increase from analytics. | Medium | Phase after basic stats (T13). Use existing reservation + review data. |
| D3 | **Multi-location management** | High | Owners with 2+ locations manage everything from one dashboard. Spacebring and inspace offer this. Valuable for growth — turns single-location owners into chain operators. | Medium | Requires: location switcher in owner dashboard, cross-location analytics aggregation, per-location staff permissions. |
| D4 | **Self-service owner onboarding with approval** | Medium | Lower friction than competitors requiring sales calls. Othership model: register > set rules > await approval > go live. Commission-on-booking only (no upfront cost to list). | High | Grows supply side of marketplace. Needs: onboarding wizard, admin approval queue, Stripe Connect onboarding for payouts. |
| D5 | **"Open Now" + real-time availability** | Medium | Differentiator for spontaneous bookers. Show which spaces are available RIGHT NOW with live availability. Combines opening_hours JSONB + current reservation state. | High | Low backend cost (query existing data), high user value for walk-in/spontaneous use cases. |
| D6 | **Smart search with auto-complete + recent** | Medium | City/neighborhood auto-complete, recent searches, saved searches. Reduces time-to-booking. Better than basic text search most competitors offer. | Medium | Needs: geocoding API integration, search history per user, frontend typeahead component. |
| D7 | **Group booking with split payment** | High | Group reservations exist, but adding split payment (each member pays their share via Stripe) is rare in coworking platforms. Most only support single-payer. | Low | Depends on T2 (Stripe). Complex: each member needs their own payment intent. Defer to later phase. |
| D8 | **QR code check-in with live status** | Low | QR codes already exist on spaces. Add: scan to check-in, owner sees live occupancy, auto-complete reservation on check-out. | Medium | Leverage existing qr_code field + checked_in_at column. Needs mobile camera access in PWA or web. |
| D9 | **Bilingual (FR + EN) from day one** | Medium | French market focus with English accessibility. Most French coworking platforms are French-only OR English-only. Bilingual captures both markets. | High | i18n with next-intl or similar. Must be built into all new features from the start — retrofitting is 3x more expensive. |
| D10 | **Calendar sync (Google/Outlook)** | Low | iCal export exists. Upgrade to bi-directional sync or at minimum one-click "Add to Calendar" buttons. Reduces no-shows. | Low | Extend existing calendar.py endpoint. Google Calendar API for write-back is medium complexity. |

---

## Anti-Features

Features to deliberately **NOT build**. Each of these is tempting but either premature, out-of-scope, or actively harmful.

| # | Anti-Feature | Why Avoid | What to Do Instead |
|---|--------------|-----------|-------------------|
| A1 | **Real-time chat between users and owners** | High development cost, moderation burden, support liability. Airbnb needed years and dedicated teams to get messaging right. Users don't need to chat with a coworking space — they need to see availability and book. | Clear establishment descriptions, FAQ section, and contact email/phone on listing. Notifications handle transactional communication. |
| A2 | **AI-powered recommendations** | PROJECT.md explicitly scopes this out. Premature optimization — you need booking volume data before recommendations add value. Cold-start problem is severe. | Build solid search/filter first. Log search behavior and booking patterns. AI recommendations can layer on later with real data. |
| A3 | **Dynamic pricing / surge pricing** | Complex to implement, hard to explain to users, trust-destroying if done poorly. Uber/Airbnb can do it because of massive scale. A new marketplace cannot. | Fixed pricing per space set by owners. Credits provide a soft discount layer. Revisit dynamic pricing only after 10K+ monthly bookings. |
| A4 | **Subscription / membership management** | Different product entirely. Managing recurring memberships, access cards, mail handling, etc. is coworking MANAGEMENT software (Optix, Nexudus, Cobot), not a booking MARKETPLACE. | Stay focused on transactional bookings: search > book > pay > use. If owners want membership management, they use dedicated software alongside LibreWork for discovery/booking. |
| A5 | **Native mobile app** | PROJECT.md scopes this out. PWA or responsive web covers 95% of use cases. App store approval, dual codebases, push notification certificates — all unnecessary friction. | Mobile-responsive web with PWA capabilities (add to home screen, offline-capable listing pages). |
| A6 | **Marketplace for non-workspace services** | Scope creep. Adding event spaces, photography studios, podcast rooms, etc. dilutes the coworking brand and complicates search/filter. | Keep categories tight: cafe, library, coworking, restaurant (existing enum). These all serve "people who need a place to work." |
| A7 | **Cryptocurrency payments** | PROJECT.md scopes this out. Tiny user base, regulatory complexity, Stripe doesn't natively support it. | Stripe handles cards, Apple Pay, Google Pay, SEPA, iDEAL — covers 99%+ of French/English market. |
| A8 | **Owner-to-owner social features** | Community forums, owner networking, benchmarking against other spaces. Distracting from core product. | Focus on individual owner analytics. Anonymized market benchmarks can come much later. |
| A9 | **Complex access control / door integration** | Physical access systems (smart locks, key cards) require hardware partnerships, on-site setup, and ongoing maintenance. Completely different product domain. | QR code check-in (already exists) is the right abstraction. Owners handle physical access themselves. |
| A10 | **Multi-currency support** | Premature. Target market is France (EUR). Adding GBP, USD, CHF multiplies complexity in pricing display, Stripe configuration, and tax handling. | EUR only for launch. Stripe inherently supports multi-currency, so adding more later is a configuration change, not an architecture change. |

---

## Feature Dependencies

Critical ordering constraints. An arrow means "must exist before."

```
Authentication (Stack Auth)
├── T2: Stripe Payments ──────────────────┐
│   ├── T14: Owner Payout Visibility      │
│   ├── D1: Credit + Stripe Hybrid        │
│   ├── D7: Group Split Payment           │
│   └── T9: Receipts (legally required)   │
├── T6: Email Notifications ──────────────┤
│   ├── T1: Booking Confirmations         │
│   └── T10: Owner Booking Alerts         │
├── D4: Owner Onboarding ────────────────┐│
│   └── D3: Multi-location (need owners) ││
└── T5: Mobile Responsive ───────────────┘│
                                           │
T3: Map Search ────────────────────────────┤
├── D5: "Open Now" filter                  │
└── D6: Smart Search / Autocomplete        │
                                           │
T4: Filters ───────────────────────────────┘
└── D5: "Open Now" (is a filter type)

T13: Basic Analytics
└── D2: Deep Analytics Dashboard

D9: i18n (FR+EN) ── should be set up BEFORE building any new UI
```

### Dependency Summary (Build Order)

1. **Auth migration** — everything depends on stable auth
2. **i18n setup** — must exist before new UI work or you'll retrofit painfully
3. **Email delivery** — unlocks notifications, confirmations, password reset
4. **Stripe payments** — unlocks real revenue, receipts, owner payouts
5. **Search/map/filters** — independent of payments; can parallelize
6. **Owner onboarding** — needs Stripe Connect for payout setup
7. **Analytics** — needs booking data volume; build after core flow works
8. **Multi-location** — needs mature owner tooling first

---

## Payment Flow Detail (T2 — Highest Complexity New Feature)

Since Stripe payments is the most impactful new feature, here's the recommended flow based on Stripe docs and coworking industry patterns.

### Recommended Architecture: Stripe Connect (Standard)

**Why Connect:** LibreWork is a two-sided marketplace. Platform collects payment from customer, takes a commission, and pays out to space owner. This is exactly what Stripe Connect is built for.

**Account type:** Standard Connect accounts for owners. Owners complete Stripe's hosted onboarding (KYC, bank details). Reduces LibreWork's compliance burden.

**Charge model:** Destination charges with application fee.
- Customer pays LibreWork (platform is merchant of record for customers)
- Funds route to owner's connected account minus platform fee
- Platform fee is configurable per booking (e.g., 10-15% commission)

### Payment States

```
User selects space + time
  → Price calculated (credits OR EUR OR hybrid)
  → If credits sufficient AND user chooses credits: deduct credits, confirm instantly
  → If EUR payment needed:
      → Create Stripe Checkout Session (or Payment Intent)
      → Redirect to Stripe-hosted payment page
      → On success webhook: confirm reservation, send confirmation email
      → On failure: reservation stays "pending_payment", auto-cancel after 15 min
```

### Credit-Stripe Hybrid (D1)

The unique differentiator: users can apply credit balance to reduce the EUR price.

```
Total cost: €15
User has: 5 credits (€5 value)
  → Apply 5 credits (€5 off)
  → Stripe charges: €10
  → Credit transaction logged + Stripe payment logged
```

### Key Decisions for Roadmap

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Stripe product | Connect (Standard) | Marketplace model; owners need independent payouts |
| Checkout UX | Stripe Checkout (hosted) first | Faster to build, PCI-compliant, supports Apple/Google Pay automatically |
| Pricing unit | EUR with credit offset | Credits = loyalty layer, EUR = real revenue |
| Refunds | Mirror existing tiered policy | >2h full, >30min 50%, <30min 0% — apply to Stripe refunds too |
| Owner payouts | Stripe automatic payouts | Daily or weekly to owner's bank. No manual payout needed. |
| Platform fee | Application fee on each charge | 10-15% configurable. Stripe deducts automatically. |

---

## Owner Analytics Detail (T13 + D2)

### Phase 1: Basic Stats (Table Stakes — T13)

| Metric | Source Data | Complexity |
|--------|------------|------------|
| Total bookings (period) | COUNT reservations WHERE status IN (confirmed, completed) | Low |
| Revenue earned (period) | SUM cost from confirmed/completed reservations | Low |
| Occupancy rate | booked_hours / available_hours per space | Medium |
| Average booking duration | AVG(end_time - start_time) | Low |
| Cancellation rate | cancelled / total reservations | Low |
| Average rating | AVG(rating) from reviews | Low |
| Top-performing spaces | GROUP BY space_id ORDER BY booking count | Low |

### Phase 2: Deep Analytics (Differentiator — D2)

| Metric | Source Data | Complexity |
|--------|------------|------------|
| Occupancy heatmap (hour × day) | Reservation time ranges binned into grid | Medium |
| Revenue trend (weekly/monthly) | Time-series aggregation | Medium |
| Booking lead time distribution | start_time - created_at histogram | Low |
| Repeat customer rate | COUNT DISTINCT users with >1 reservation | Low |
| Review response tracking | Reviews with/without owner replies | Medium (needs reply feature) |
| Cancellation reasons | Needs new field on cancellation | Low (schema change) |
| Comparison across locations | Multi-location GROUP BY establishment_id | Medium (needs D3) |

---

## Search & Discovery Detail (T3 + T4 + D5 + D6)

### Search Architecture

```
User types location / uses "near me"
  → Geocode to lat/lng (browser geolocation or geocoding API)
  → PostGIS ST_DWithin query with radius (default 5km, adjustable)
  → Apply filters: category, amenities, price range, capacity, open-now
  → Return results with distance, sorted by relevance/distance
  → Display as: map pins + list side-by-side (desktop) or toggle (mobile)
```

### Filter Priority (based on user research)

| Filter | Type | Priority | Notes |
|--------|------|----------|-------|
| Location / "Near me" | Geo | Critical | Default search mode |
| Category | Enum | High | cafe, coworking, library, restaurant |
| Open Now | Boolean | High | Compare opening_hours JSONB with current time + timezone |
| Price range | Range slider | High | Min-max credits or EUR per hour |
| Amenities | Multi-select chips | High | wifi, power, quiet, food, drinks, parking, accessible |
| Capacity | Number input | Medium | "Seats for at least N people" |
| Rating | Star threshold | Medium | "4+ stars" |
| Availability (date/time) | Date+time picker | Medium | Check against existing reservations |
| Distance radius | Range slider | Low | Default 5km, adjustable to 1-50km |

### Map Implementation

**Recommended:** Mapbox GL JS (or MapLibre for open-source alternative). Google Maps works but is more expensive at scale and requires API key billing.

Map must support:
- Clustered markers at zoom-out
- Individual pins with price/rating preview on hover
- "Search this area" button when user pans
- Responsive: full-screen map on mobile with bottom sheet for results

---

## MVP Recommendation

Given LibreWork is brownfield with existing credits, reservations, and reviews, the MVP for the "new features" release should prioritize:

### Must Ship (Table Stakes Gap Closers)

1. **T2: Stripe payments** — without real payments, it's not a real product
2. **T6: Email notifications** — booking confirmation, reminders, password reset
3. **T3 + T4: Search with map + filters** — core discovery experience
4. **T5: Mobile responsive** — 70% of traffic
5. **T13: Basic owner stats** — owners need visibility to stay engaged

### Should Ship (High-Value Differentiators)

6. **D4: Owner self-service onboarding** — grows supply side
7. **D1: Credit + Stripe hybrid** — leverages existing credit system uniquely
8. **D5: "Open Now" filter** — high value, low incremental cost if T3/T4 are built
9. **D9: i18n setup** — must be early or retrofitting costs 3x

### Defer

10. **D2: Deep analytics** — needs booking volume first
11. **D3: Multi-location** — needs mature owner tooling
12. **D7: Group split payment** — complex, niche use case
13. **D6: Smart search** — nice-to-have after basic search works
14. **D10: Calendar sync** — iCal export already covers 80%

---

## Sources

- Optix coworking booking systems comparison (optixapp.com/blog) — HIGH confidence
- eOffice "Instant Booking: New Standard for 2026" (eoffice.net) — MEDIUM confidence
- Coworks management tool guide (coworks.com/blog) — HIGH confidence
- Spacebring coworking software guide 2026 (spacebring.com) — HIGH confidence
- Stripe Connect documentation (docs.stripe.com/connect) — HIGH confidence
- Stripe OfficeRnD case study (stripe.com/customers/officernd) — HIGH confidence
- Peerspace cancellation policy (peerspace.com) — HIGH confidence
- WeWork On Demand booking policies (wework.com) — HIGH confidence
- Upflex cancellation policy (help.upflex.com) — HIGH confidence
- Spacebring multi-location features (spacebring.com/features/multilocation) — HIGH confidence
- Cobot analytics documentation (helpcenter.cobot.me) — HIGH confidence
- Nexudus occupancy reports (help.nexudus.com) — HIGH confidence
- Othership listing guide (knowledge.othership.com) — MEDIUM confidence
- Proximity onboarding checklist (docs.proximity.space) — MEDIUM confidence
- Coworker.com API documentation (coworker.com/coworker-api) — HIGH confidence
- Coworking Insights credit systems article (coworkinginsights.com) — MEDIUM confidence
- LibreWork existing schema (supabase/migrations/) — HIGH confidence (direct codebase audit)

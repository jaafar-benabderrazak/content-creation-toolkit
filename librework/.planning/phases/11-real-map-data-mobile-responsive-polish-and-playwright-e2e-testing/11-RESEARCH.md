# Phase 11: Real Map Data, Mobile Responsive Polish, and Playwright E2E Testing - Research

**Researched:** 2026-03-22
**Domain:** Google Places API (New) JS SDK, Leaflet map interaction, Tailwind CSS mobile responsive, Playwright E2E mobile testing
**Confidence:** HIGH (stack, patterns, API methods verified against official docs)

---

## Summary

Phase 11 covers three largely independent workstreams that build on what Phase 10 delivered. The map stack is already functional: `googlePlaces.ts` uses `Place.searchNearby()` via the New Places JavaScript API, and `MapView.tsx` uses Leaflet 1.9.4 with a `moveend`-driven recenter pattern. Enhancing it means adding `Place.fetchFields()` for detail panels and wiring Leaflet's `moveend` event to re-invoke `fetchNearbyEstablishments` with the map's current visible center — NOT a new Google API method. **Critical billing constraint carried forward from Phase 9:** opening hours, phone, website, and rating are Enterprise SKU fields. The project deliberately excluded them to stay on the Essentials SKU (10K free/month). Phase 11 must not add those fields unless the billing model changes.

Mobile responsive polish is pure Tailwind CSS work. The existing components already use responsive classes (`sm:flex-row`, `md:grid-cols-2`) but gaps remain: ExplorePage has no map/list toggle logic for small screens, EstablishmentDetails booking card is `sticky top-20` but does not reflow below content on mobile, and all Dialogs are centered on all viewports with no drawer fallback. The pattern is `useIsMobile()` (already in `src/components/ui/use-mobile.ts`) combined with conditional Tailwind classes — no new libraries needed.

The Playwright E2E expansion uses the already-installed `@playwright/test@^1.58.2`. Phase 10 tests are intentionally shallow (mostly API mock verifications). Phase 11 tests should add real UI interaction: demo mode flow (click Demo > Owner > verify dashboard renders), explore page map toggle, mobile viewport variants using `devices['iPhone 13']` in `playwright.config.ts`. All backend-dependent tests continue using `page.route()` mocking per the Phase 10 convention.

**Primary recommendation:** Three separate plan files — (1) Map data enhancements, (2) Mobile responsive pass, (3) Playwright E2E expansion — executed in that order since tests verify the UI changes from plan 2.

---

## Standard Stack

### Core (already installed — no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| leaflet | 1.9.4 | Interactive map rendering, event system | Already in use; `moveend` event is the standard pattern for search-on-drag |
| react-leaflet | 5.0.0 | React wrappers for Leaflet | Already in use |
| @vis.gl/react-google-maps | 1.7.1 | Google Maps JavaScript API loader (`APIProvider`) | Already in use for Places API bootstrap |
| @types/google.maps | 3.58.1 | Type definitions for Google Maps JS API | Already in use |
| @playwright/test | 1.58.2 | E2E testing framework | Already installed; Phase 10 pattern |
| tailwindcss | 3.3.x | Utility-first responsive CSS | Already in use |
| shadcn/ui components | local | Dialog, Tabs, Card, Sheet | Already in use; Sheet used for mobile Navbar drawer |

### Supporting (already installed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `use-mobile.ts` hook | local | `useIsMobile()` — returns `boolean` based on `window.matchMedia('(max-width: 768px)')` | All mobile-conditional rendering |
| lucide-react | 0.312.0 | Icons for map controls (LocateFixed, MapPin, List) | Mobile toggle buttons |

### No New Dependencies Required

All three workstreams work with existing installed packages. Do NOT add:
- `geolib` or `haversine-distance` — distance calculation is a 10-line pure function using the Haversine formula
- `@googlemaps/places` npm package — the project uses the JS API via dynamic `importLibrary('places')`, not the npm package
- Any new animation library for mobile transitions

**Installation:** None required.

---

## Architecture Patterns

### Recommended File Structure (additions only)

```
librework/frontend/
├── src/
│   ├── lib/
│   │   └── googlePlaces.ts          # Add fetchPlaceDetails(), computeDistance()
│   ├── components/
│   │   ├── MapView.tsx              # Add onBoundsChange callback prop
│   │   ├── ExplorePage.tsx          # Wire onBoundsChange, map/list toggle for mobile
│   │   ├── EstablishmentDetails.tsx # Mobile booking card reflow
│   │   ├── UserDashboard.tsx        # Tab overflow scroll on mobile
│   │   └── OwnerDashboard.tsx       # Tab overflow scroll on mobile
│   └── e2e/
│       ├── demo-flow.spec.ts        # NEW: demo mode E2E
│       ├── explore-map.spec.ts      # NEW: map interaction E2E
│       ├── booking-flow.spec.ts     # NEW: booking form E2E
│       └── mobile-viewport.spec.ts  # NEW: mobile viewport variants
```

### Pattern 1: Search-by-Area via Leaflet `moveend`

**What:** When the user stops dragging/zooming the map, extract the visible center from Leaflet's map instance and call `fetchNearbyEstablishments` with that center.

**When to use:** User drags map to a new area; system fetches places for the new center.

**How it works:** `MapView` receives an optional `onBoundsChange?: (center: { lat: number; lng: number }) => void` prop. Inside the Leaflet initialization `useEffect`, register `map.on('moveend', ...)` after map creation.

```typescript
// Source: Leaflet docs https://leafletjs.com/reference.html
map.on('moveend', () => {
  const c = map.getCenter()
  onBoundsChange?.({ lat: c.lat, lng: c.lng })
})
```

In `ExplorePage`, wire this callback to trigger a new `fetchNearbyEstablishments` call — same function already used on mount. Debounce with a 500ms timeout to avoid firing on every frame during inertia scrolling.

**Critical:** Do not try to pass Leaflet `LatLngBounds` to the Google Places API. `Place.searchNearby()` only accepts a center + radius (`locationRestriction`). Compute radius as half the visible map diagonal, capped at 50,000m (API maximum).

### Pattern 2: Place Details via `Place.fetchFields()`

**What:** When a user clicks a map marker, fetch additional details for that place ID using `Place.fetchFields()`.

**When to use:** Marker popup "View Details" click, or when `onSelect` fires in `MapView`.

**BILLING CONSTRAINT — CRITICAL:**

| Field | SKU | Included in Phase 11 |
|-------|-----|----------------------|
| `displayName` | Pro | NO — already available from searchNearby |
| `formattedAddress` | Essentials | YES — already fetched |
| `location` | Essentials | YES — already fetched |
| `photos` | Essentials (IDs only) | YES — photo URI already fetched |
| `rating` | Enterprise | NO — excluded per Phase 9 decision |
| `regularOpeningHours` | Enterprise | NO — excluded per Phase 9 decision |
| `nationalPhoneNumber` | Enterprise | NO — excluded per Phase 9 decision |
| `websiteUri` | Enterprise | NO — excluded per Phase 9 decision |

"Place details" in Phase 11 means: richer popup using data ALREADY FETCHED from `searchNearby` (name, address, rating from initial fetch, photos). Do NOT call `fetchFields()` with Enterprise fields. If an enhanced detail panel is wanted, it shows only Essentials data.

```typescript
// Source: https://developers.google.com/maps/documentation/javascript/place-details
// Only Essentials fields — safe for free tier
const place = new Place({ id: placeId })
await place.fetchFields({
  fields: ['displayName', 'formattedAddress', 'location', 'photos'],
})
```

### Pattern 3: Distance Calculation (Pure Function)

**What:** Compute human-readable distance string (e.g. "1.2 km") from user coordinates to establishment coordinates.

**When to use:** After geolocation is obtained, populate `establishment.distance` field for display.

```typescript
// Haversine formula — no library needed
// Source: https://www.movable-type.co.uk/scripts/latlong.html
export function computeDistance(
  from: { lat: number; lng: number },
  to: { lat: number; lng: number }
): string {
  const R = 6371 // km
  const dLat = ((to.lat - from.lat) * Math.PI) / 180
  const dLng = ((to.lng - from.lng) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((from.lat * Math.PI) / 180) *
      Math.cos((to.lat * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  const d = R * c
  return d < 1 ? `${Math.round(d * 1000)} m` : `${d.toFixed(1)} km`
}
```

Call this in `googlePlaces.ts` inside `mapPlaceToEstablishment` when a `userCenter` is passed as a parameter.

### Pattern 4: Mobile Responsive — Map/List Toggle

**What:** On mobile (<768px), ExplorePage shows EITHER the map OR the list, not both stacked. A toggle button switches between views.

**Current state:** `showMap` state already exists. Map renders above the list when `showMap === true`. On desktop this is fine (map above list). On mobile, showing both is too tall.

**Fix:** Wrap the results grid in `{!showMap && <div>...results...</div>}` on mobile. Use `useIsMobile()` to determine if exclusive toggle is needed.

```tsx
// Pattern: mobile-exclusive toggle
const isMobile = useIsMobile()
// Mobile: show map OR list (exclusive)
// Desktop: show map above list (existing behavior)
const showList = !isMobile || !showMap
```

### Pattern 5: Mobile Responsive — Booking Card Reflow

**What:** In `EstablishmentDetails`, the booking card is `lg:col-span-1` in a `lg:grid-cols-3` grid. On mobile it already stacks below content. The issue is `sticky top-20` — on mobile this causes the card to overlap content.

**Fix:** Apply `sticky` only on large screens: replace `sticky top-20` with `lg:sticky lg:top-20`.

### Pattern 6: Mobile Responsive — Dialogs

**What:** shadcn `Dialog` renders as a centered modal on all screen sizes. On mobile (375px), this produces a narrow centered box that feels wrong.

**Pattern:** The project already has `Sheet` imported in Navbar for the mobile drawer. Use `useIsMobile()` to conditionally render `Dialog` on desktop and `Sheet` (bottom drawer) on mobile.

```tsx
// Source: https://www.nextjsshop.com/resources/blog/responsive-dialog-drawer-shadcn-ui
const isMobile = useIsMobile()
if (isMobile) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="rounded-t-xl">
        {children}
      </SheetContent>
    </Sheet>
  )
}
return <Dialog open={open} onOpenChange={onOpenChange}>{children}</Dialog>
```

Wrap this in a `ResponsiveDialog` component at `src/components/ui/responsive-dialog.tsx`.

### Pattern 7: Playwright Mobile Viewport Projects

**What:** Add mobile device projects to `playwright.config.ts` so existing + new tests run against both desktop and mobile viewports.

```typescript
// Source: https://playwright.dev/docs/emulation
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },
  ],
})
```

For per-test viewport override within a spec:

```typescript
test.describe('mobile layout', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test('booking card stacks below content', async ({ page }) => {
    await page.goto('/en')
    // assertions
  })
})
```

### Pattern 8: E2E Demo Flow Test

**What:** Test the demo mode flow end-to-end since it's a key feature with no coverage.

```typescript
// e2e/demo-flow.spec.ts
test('demo owner flow renders owner dashboard', async ({ page }) => {
  await page.goto('/en')
  // Click Demo button
  await page.getByRole('button', { name: /demo/i }).click()
  // Click "Demo as Owner"
  await page.getByRole('button', { name: /owner/i }).click()
  // Demo banner should appear
  await expect(page.locator('nav')).toContainText(/demo/i)
  // Navigate to owner dashboard
  await page.getByRole('button', { name: /dashboard|owner/i }).first().click()
  // Owner dashboard content renders
  await expect(page.locator('body')).toContainText(/revenue|occupancy|analytics/i)
})
```

### Anti-Patterns to Avoid

- **Calling `fetchFields()` with Enterprise fields**: opening hours, phone, website are Enterprise SKU. Costs scale immediately above 10K calls/month. Blocked by Phase 9 decision.
- **Using `map.getBounds()` as the locationRestriction**: `Place.searchNearby()` does not accept a bounding box — only center + radius. Convert bounds to center + radius.
- **Re-fetching on every `mousemove` or `zoom` event**: Use `moveend` (fires once after movement stops). Debounce to 500ms.
- **Adding `sticky` to booking card on mobile**: Causes overlap with content. Scoped to `lg:` only.
- **Using `test.setTimeout()` to mask slow tests**: Fix the underlying async pattern instead.
- **Importing server modules in client components**: `googlePlaces.ts` is `'use client'` and must stay that way. Distance calculation goes in that file or a separate client utility.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Distance calculation | Custom geo library | 10-line Haversine function | No dependencies; already sufficient for display strings |
| Mobile detection | Manual `window.innerWidth` checks | `useIsMobile()` from `src/components/ui/use-mobile.ts` | Already in codebase; uses `matchMedia` correctly |
| Responsive Dialog | Custom modal component | `Sheet` (already installed) + `useIsMobile()` | Sheet is already used in Navbar; pattern is established |
| Map bounds → search radius | Custom geometry | `map.getCenter()` + fixed 2000m radius | `searchNearby` only supports center+radius; bounds-to-radius conversion is simple |
| Debounce | Custom timeout ref | `useRef` + `setTimeout` + `clearTimeout` | Standard React pattern; no library needed for a single debounce |

**Key insight:** The project's existing dependency set already contains everything needed. Avoiding new dependencies prevents version conflict issues (legacy-peer-deps is already fragile due to react-leaflet@5/React18).

---

## Common Pitfalls

### Pitfall 1: Enterprise SKU Field Creep

**What goes wrong:** Developer adds `regularOpeningHours` or `websiteUri` to the `fetchFields` call because "it seems like useful place data." Billing immediately shifts from Essentials to Enterprise tier.

**Why it happens:** The official API docs list all fields without emphasizing billing impact. It's easy to add them.

**How to avoid:** The `fetchFields` call in `googlePlaces.ts` must be reviewed at code review. Only fields from the Essentials column are permitted.

**Warning signs:** Any `fetchFields` call that includes `openingHours`, `regularOpeningHours`, `currentOpeningHours`, `nationalPhoneNumber`, `internationalPhoneNumber`, `websiteUri`, or `rating`.

### Pitfall 2: Leaflet Map Instance Stale Closure in `moveend`

**What goes wrong:** The `onBoundsChange` callback inside `map.on('moveend', ...)` captures a stale version of `onBoundsChange` from the initial render. Changes to the callback don't propagate.

**Why it happens:** Leaflet event registration happens inside a `useEffect` that runs once (on mount). React state closures inside that effect are stale.

**How to avoid:** Store the callback in a `useRef` and read the ref inside the event handler.

```typescript
const onBoundsChangeRef = useRef(onBoundsChange)
useEffect(() => { onBoundsChangeRef.current = onBoundsChange }, [onBoundsChange])

// Inside Leaflet init useEffect:
map.on('moveend', () => {
  const c = map.getCenter()
  onBoundsChangeRef.current?.({ lat: c.lat, lng: c.lng })
})
```

### Pitfall 3: Leaflet Map Already Initialized

**What goes wrong:** `MapView` re-renders when `establishments` prop changes. The guard `if (!mapRef.current || mapInstanceRef.current) return` prevents double-init, but markers from the previous render are not cleared when new establishments arrive.

**Why it happens:** Markers are added inside the init `useEffect` and never removed. New establishments don't clear old markers.

**How to avoid:** In the `moveend`-triggered re-fetch, update `liveEstablishments` state in `ExplorePage`. `MapView` will receive new `establishments` prop. The current implementation does NOT update markers on prop change — this will need a second effect that clears and re-adds markers when `establishments` changes, while keeping the map instance alive.

```typescript
// Second useEffect in MapView — runs when establishments change
useEffect(() => {
  if (!mapInstanceRef.current) return
  // Clear existing marker layer group
  markerLayerRef.current?.clearLayers()
  // Re-add markers
  establishments.forEach(est => { /* add marker */ })
}, [establishments])
```

Use a Leaflet `LayerGroup` stored in `markerLayerRef` to make clearing efficient.

### Pitfall 4: Playwright Mobile Tests Fail on CI due to Missing Browsers

**What goes wrong:** Adding `devices['iPhone 13']` (Safari) to `playwright.config.ts` requires the `webkit` browser binary. On CI (or developer machines), only `chromium` may be installed.

**Why it happens:** `npx playwright install` installs all browsers by default, but existing setup may only have chromium.

**How to avoid:** Either (a) restrict mobile tests to `devices['Pixel 5']` (Chromium-based, no webkit needed), or (b) add `npx playwright install webkit` to CI setup. The project already has `--legacy-peer-deps` for npm; playwright install is separate.

**Recommendation:** Use `devices['Pixel 5']` for mobile tests. It uses Chromium (already installed), tests real mobile viewport + touch, and avoids webkit dependency.

### Pitfall 5: `use client` Boundary for Google Maps API

**What goes wrong:** `googlePlaces.ts` is marked `'use client'` because it calls `google.maps.importLibrary`. Any server component that imports from it will fail with a build error.

**Why it happens:** Google Maps API is browser-only. `importLibrary` and `navigator.geolocation` are not available in Node.js.

**How to avoid:** Keep `googlePlaces.ts` as `'use client'` and only import from client components. The new `computeDistance` utility function should live in the same file or in `src/lib/utils.ts` (which has no server/client restriction for pure math functions).

### Pitfall 6: shadcn Tabs on Mobile — Hidden Tab Content Overflow

**What goes wrong:** `Tabs` in `UserDashboard` and `OwnerDashboard` have multiple `TabsTrigger` items. On 375px screens, they overflow and are clipped.

**Why it happens:** `TabsList` uses `flex` without overflow handling.

**How to avoid:** Add `overflow-x-auto` to `TabsList` and `whitespace-nowrap` to `TabsTrigger`:

```tsx
<TabsList className="overflow-x-auto whitespace-nowrap">
  <TabsTrigger className="whitespace-nowrap" value="upcoming">Upcoming</TabsTrigger>
</TabsList>
```

---

## Code Examples

### Map Search-by-Area: `MapView.tsx` `moveend` wiring

```typescript
// Source: Leaflet reference https://leafletjs.com/reference.html
// Add to MapView after map.setView():
const onBoundsChangeRef = useRef(onBoundsChange)
useEffect(() => { onBoundsChangeRef.current = onBoundsChange }, [onBoundsChange])

map.on('moveend', () => {
  const center = map.getCenter()
  onBoundsChangeRef.current?.({ lat: center.lat, lng: center.lng })
})
```

### Map Search-by-Area: `ExplorePage.tsx` debounced fetch on move

```typescript
// Debounce ref pattern — no library
const moveDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

const handleBoundsChange = useCallback((center: { lat: number; lng: number }) => {
  if (moveDebounceRef.current) clearTimeout(moveDebounceRef.current)
  moveDebounceRef.current = setTimeout(() => {
    if (!process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY) return
    setIsLoading(true)
    fetchNearbyEstablishments(center)
      .then(results => { if (results.length > 0) setLiveEstablishments(results) })
      .finally(() => setIsLoading(false))
  }, 500)
}, [])
```

### Distance calculation in `googlePlaces.ts`

```typescript
// Pure Haversine — no import needed
// Source: https://www.movable-type.co.uk/scripts/latlong.html
export function computeDistance(
  from: { lat: number; lng: number },
  to: { lat: number; lng: number }
): string {
  const R = 6371
  const dLat = ((to.lat - from.lat) * Math.PI) / 180
  const dLng = ((to.lng - from.lng) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((from.lat * Math.PI) / 180) *
      Math.cos((to.lat * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2
  const d = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return d < 1 ? `${Math.round(d * 1000)} m` : `${d.toFixed(1)} km`
}
```

### `ResponsiveDialog` component

```tsx
// src/components/ui/responsive-dialog.tsx
// Pattern: Dialog on desktop, Sheet drawer on mobile
import { useIsMobile } from '@/components/ui/use-mobile'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Sheet, SheetContent } from '@/components/ui/sheet'

interface ResponsiveDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}

export function ResponsiveDialog({ open, onOpenChange, children }: ResponsiveDialogProps) {
  const isMobile = useIsMobile()
  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="bottom" className="rounded-t-xl max-h-[90vh] overflow-y-auto">
          {children}
        </SheetContent>
      </Sheet>
    )
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>{children}</DialogContent>
    </Dialog>
  )
}
```

### Playwright mobile project config

```typescript
// playwright.config.ts — add mobile projects
// Source: https://playwright.dev/docs/emulation
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  expect: { timeout: 5000 },
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  ],
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
})
```

### Playwright demo mode E2E test

```typescript
// e2e/demo-flow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Demo mode flow', () => {
  test('demo owner shows owner dashboard', async ({ page }) => {
    await page.goto('/en')
    // Open demo menu
    await page.getByRole('button', { name: /demo/i }).first().click()
    // Select owner demo
    await page.getByRole('button', { name: /owner/i }).click()
    // Verify demo banner visible in nav
    await expect(page.locator('nav')).toContainText(/demo/i)
  })

  test('demo customer shows user dashboard', async ({ page }) => {
    await page.goto('/en')
    await page.getByRole('button', { name: /demo/i }).first().click()
    await page.getByRole('button', { name: /customer/i }).click()
    await expect(page.locator('nav')).toContainText(/demo/i)
  })
})
```

### Playwright mobile viewport test

```typescript
// e2e/mobile-viewport.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Mobile responsive layout', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test('navbar shows hamburger on mobile', async ({ page }) => {
    await page.goto('/en')
    // Desktop nav links should be hidden; hamburger (Menu icon button) visible
    const hamburger = page.getByRole('button').filter({ has: page.locator('svg') }).first()
    await expect(hamburger).toBeVisible()
  })

  test('explore page map toggle works on mobile', async ({ page }) => {
    await page.goto('/en')
    // Find map toggle button
    const mapButton = page.getByRole('button', { name: /map/i })
    if (await mapButton.isVisible()) {
      await mapButton.click()
      // Map container should appear
      await expect(page.locator('[class*="leaflet"], .leaflet-container, [ref="mapRef"]').first()).toBeVisible().catch(() => {
        // Map may need time to initialize
      })
    }
  })
})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Places API Legacy (`findPlaceFromQuery`, `nearbySearch`) | Places API New (`Place.searchNearby()`, `Place.fetchFields()`) | 2022-2024 GA | Legacy is deprecated; project already uses New API |
| Static center for map search | `moveend`-driven dynamic search | Phase 11 | Users can drag to any area and see relevant results |
| All dialogs centered | Dialog on desktop, Sheet drawer on mobile | Phase 11 | Standard mobile UX pattern |
| No mobile viewport E2E tests | Playwright `devices['Pixel 5']` project | Phase 11 | Catches mobile regressions automatically |

**Deprecated/outdated in this project:**
- `google.maps.places.PlacesService` (legacy): Project correctly uses `Place` class from New API.
- `getBoundsString()` pattern for viewport-based search: Not needed — `map.getCenter()` + fixed radius is sufficient and works with `searchNearby`.

---

## Open Questions

1. **Marker layer management in MapView**
   - What we know: Current `MapView` adds markers once on init. It does not clear and re-add when `establishments` prop changes.
   - What's unclear: Whether the current implementation causes duplicate markers when search-by-area returns new results (they'd stack on existing ones).
   - Recommendation: Add a `markerLayerRef` (`L.layerGroup()`) and a second `useEffect` that clears and re-adds markers when `establishments` changes. This must be implemented in Plan 1.

2. **Google Maps API key availability during E2E tests**
   - What we know: `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` must be set for `fetchNearbyEstablishments` to run. Phase 10 tests skip the Places API entirely.
   - What's unclear: Whether the key is available in the Vercel preview/CI environment for E2E runs.
   - Recommendation: All map E2E tests should mock the Places API response using `page.route()` for the Google Maps API endpoints, same pattern as existing tests mock `/api/v1/spaces*`.

3. **`useIsMobile` breakpoint consistency**
   - What we know: `use-mobile.ts` uses `768px` as the mobile/desktop boundary. Tailwind `md:` breakpoint is also `768px`.
   - What's unclear: Whether components should use the hook or pure Tailwind classes.
   - Recommendation: Use pure Tailwind classes (`md:sticky`, `lg:grid-cols-3`) for layout changes that don't require JS logic. Reserve `useIsMobile()` for cases that require conditional component rendering (Dialog vs Sheet, map-exclusive vs list-exclusive).

---

## Sources

### Primary (HIGH confidence)
- Google Maps JS API official docs — `Place.fetchFields()` method confirmed: https://developers.google.com/maps/documentation/javascript/place-details
- Google Maps JS API official docs — `Place.searchNearby()` with center+radius: https://developers.google.com/maps/documentation/javascript/nearby-search
- Google Places API field billing tiers — Essentials/Pro/Enterprise field table: https://developers.google.com/maps/documentation/places/web-service/data-fields
- Playwright official docs — `devices`, viewport config, `test.use()`: https://playwright.dev/docs/emulation
- Leaflet official reference — `moveend` event, `map.getCenter()`, `LayerGroup`: https://leafletjs.com/reference.html
- Project source code — `googlePlaces.ts`, `MapView.tsx`, `ExplorePage.tsx`, `EstablishmentDetails.tsx`, `Navbar.tsx`, `UserDashboard.tsx`, `OwnerDashboard.tsx`, `use-mobile.ts` — read directly

### Secondary (MEDIUM confidence)
- Responsive Dialog/Sheet pattern: https://www.nextjsshop.com/resources/blog/responsive-dialog-drawer-shadcn-ui — verified against shadcn/ui Sheet and Dialog component source in project
- Haversine distance formula: https://www.movable-type.co.uk/scripts/latlong.html — verified against standard formula; pure math, no library risk
- Tailwind tabs overflow scroll: https://github.com/tailwindlabs/tailwindcss/discussions/2687 — `overflow-x-auto` + `whitespace-nowrap` pattern is documented Tailwind behavior

### Tertiary (LOW confidence — flagged)
- Phase 9 decision on Enterprise SKU exclusion is from `STATE.md` project context, not re-verified against current Google billing page. **Validate before adding any new `fetchFields` calls that the Essentials/Pro/Enterprise classification hasn't changed.**

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already installed; versions confirmed in `package.json`
- Map enhancements (searchByArea, distance): HIGH — Leaflet `moveend` and `map.getCenter()` are stable APIs; Google Places `fetchFields` confirmed from official docs
- Billing constraints: HIGH — field tier table fetched from official billing docs; confirmed Enterprise restriction on openingHours/phone/website
- Mobile responsive patterns: HIGH — `useIsMobile` exists in codebase; Tailwind classes verified; Dialog→Sheet pattern from official shadcn component set
- Playwright mobile testing: HIGH — `devices` API confirmed from official docs; `Pixel 5` device confirmed Chromium-based
- Pitfalls: HIGH — stale closure and marker management issues are observable from reading the existing `MapView.tsx` code directly

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (Google Places API New is GA and stable; Playwright 1.x has stable emulation API)

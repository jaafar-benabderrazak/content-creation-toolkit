# Phase 9: Fix Select Visibility Issues and Integrate Google Maps Open Data - Research

**Researched:** 2026-03-21
**Domain:** CSS theming (shadcn/Tailwind CSS variable mismatch) + Google Maps Places API (New)
**Confidence:** HIGH for select fix, MEDIUM for Google Maps integration

## Summary

This phase has two independent sub-problems. The select visibility bug is a CSS variable resolution mismatch that is already fully diagnosable from the source code — no external research is needed to confirm the fix. The Google Maps integration requires adding a new API dependency and designing a data mapping layer between Google Places (New) results and the existing `Establishment` interface.

**Select bug root cause (confirmed from code):** `globals.css` sets `--input: transparent` and `tailwind.config.ts` maps `input: "hsl(var(--input))"`. The `SelectTrigger` in `select.tsx` applies `bg-input-background` which resolves correctly to `#ffffff`, but the `SelectContent` uses `bg-popover` which resolves from `--popover: #ffffff` — correct in light mode but the broader problem is that `--input: transparent` bleeds into any component that uses the `input` color token. Additionally, the tailwind.config.ts uses `hsl(var(--input))` but `globals.css` defines `--input: transparent` as a keyword, not HSL values, causing unpredictable rendering. The `SelectContent` dropdown and `DropdownMenuContent` both use `bg-popover text-popover-foreground` which should work, but the `SelectTrigger` uses `bg-input-background` — a non-standard custom token that may not be registered correctly in the Tailwind v4/v3 boundary this project sits on.

**Google Maps:** The project currently has 5 hardcoded establishments in `mockData.ts` with fake Paris coordinates. Phase 9 replaces or supplements this with real Places API (New) data using `Place.searchNearby()`. The existing `Establishment` interface shape must be preserved because `EstablishmentDetails.tsx`, `ExplorePage.tsx`, and `MapView.tsx` all consume it directly. The integration adds a data-fetching layer that transforms `google.maps.places.Place` results into `Establishment` objects.

**Primary recommendation:** Fix the CSS variables in `globals.css` first (one targeted change), then add `@vis.gl/react-google-maps` + a Google Places fetch utility that maps to `Establishment[]`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@vis.gl/react-google-maps` | ^1.x (npm current) | React wrapper for Maps JavaScript API | Official vis.gl library, TypeScript-native, works with Next.js "use client" pattern, replaces all older google-map-react alternatives |
| Tailwind CSS (existing) | ^3.3 | Style fixes | Already in project, fix is CSS-only |
| shadcn/ui Select (existing) | current in-tree | Booking space selector | Already in `components/ui/select.tsx` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@types/google.maps` | ^3.x | Type definitions for Maps JS API | Needed for `google.maps.places.Place` type safety without loading the full SDK at build time |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@vis.gl/react-google-maps` | `react-google-maps/api` | react-google-maps/api is older, less maintained; vis.gl is the official Google-endorsed library as of 2024 |
| Google Places API (New) | Google Places API (Legacy) | Legacy cannot be enabled for new projects after March 1, 2025. New projects must use Places API (New) |
| Client-side `Place.searchNearby()` | Backend proxy route | Client-side exposes API key in `NEXT_PUBLIC_` var; backend proxy is safer but adds complexity. For a prototype, client-side is acceptable if API key is restricted to HTTP referrers in Google Console |

**Installation:**
```bash
npm install @vis.gl/react-google-maps @types/google.maps
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── lib/
│   ├── mockData.ts           # Existing — keep interface definitions, strip hardcoded data
│   └── googlePlaces.ts       # NEW: Places API fetch utility, returns Establishment[]
├── components/
│   ├── MapView.tsx           # Update: accept real coordinates from Establishment
│   ├── ExplorePage.tsx       # Update: call googlePlaces.ts instead of mockData.establishments
│   └── EstablishmentDetails.tsx  # Minimal changes: already consumes Establishment interface
└── app/
    └── globals.css           # Fix: --input CSS variable
```

### Pattern 1: CSS Variable Fix for Select Visibility

**What:** The `--input` CSS variable is set to `transparent` in `:root`, but `tailwind.config.ts` maps `input: "hsl(var(--input))"`. This causes `bg-input` to render as `background: hsl(transparent)` which is invalid and renders as transparent. The fix is to assign `--input` a valid HSL triple or use a direct hex/color. The `SelectTrigger` uses the custom `bg-input-background` token (which resolves to `#ffffff` and works), but the `--input: transparent` setting cascades into dark mode and other components that reference the input token.

**When to use:** Apply once in `globals.css`. No component changes needed for the select/dropdown visibility fix — it is purely a CSS variable correction.

**The exact problem in code:**

```css
/* globals.css line 26 — THIS CAUSES THE BUG */
--input: transparent;

/* tailwind.config.ts line 23 maps it as: */
input: "hsl(var(--input))"  /* → hsl(transparent) = INVALID */
```

**Fix:**

```css
/* globals.css :root — CORRECT */
--input: 0 0% 100%;         /* white as HSL triple, matches hsl() wrapping in tailwind.config */
--input-background: #ffffff; /* keep for bg-input-background usage in select.tsx trigger */
```

```css
/* globals.css .dark — CORRECT */
--input: 215 28% 17%;        /* dark input background (was: #374151 → HSL triple) */
```

**Why HSL triple without hsl():** `tailwind.config.ts` wraps all color variables with `hsl()`: `"hsl(var(--input))"`. So `--input` must be a bare HSL triple `H S% L%`, not a full color value. This is the shadcn v3 convention. The `--popover`, `--background`, etc. variables must follow the same pattern if they are referenced via tailwind.config.

**Verification of actual affected components:**
- `SelectContent` in `select.tsx`: uses `bg-popover text-popover-foreground` — will work if `--popover` is correct
- `SelectTrigger` in `select.tsx`: uses `bg-input-background` — uses custom var, NOT the broken `--input` token
- `DropdownMenuContent` in `dropdown-menu.tsx`: uses `bg-popover` — same as SelectContent
- Native `<select>` in `AdvancedSearchForm.tsx`: uses inline `bg-white` — not affected by CSS vars
- `globals.css` `:root` defines `--popover: #ffffff` as a full hex, but `tailwind.config.ts` maps `popover: "hsl(var(--popover))"` — `hsl(#ffffff)` is INVALID and causes transparent popover/dropdown backgrounds

**The popover token is also broken:**

```css
/* globals.css :root line 11 — ALSO BROKEN */
--popover: #ffffff;  /* tailwind.config wraps this as hsl(#ffffff) = INVALID */

/* Fix: use HSL triple */
--popover: 0 0% 100%;
```

The same applies to `--background`, `--card`, `--secondary`, `--muted`, `--accent`, `--border`, `--ring`, and ALL color variables that are mapped through `hsl(var(--X))` in `tailwind.config.ts`. The entire `:root` block uses hex values, but the tailwind.config expects bare HSL triples.

### Pattern 2: CSS Variable Audit — Scope of the Fix

The project has a split convention:
- `globals.css` defines vars with hex values (`#ffffff`, `#111827`)
- `tailwind.config.ts` wraps them in `hsl()` (e.g., `"hsl(var(--popover))"`)
- `globals.css` ALSO defines `@theme inline` block that maps vars directly (e.g., `--color-popover: var(--popover)`)

The `@theme inline` block at line 102 in `globals.css` is Tailwind v4 syntax. The `tailwind.config.ts` is Tailwind v3 syntax. **The project is in a Tailwind v3/v4 boundary conflict.** The `@theme inline` directive is a Tailwind v4 feature. In Tailwind v3, it is ignored. The tailwind.config.ts is what actually runs (Tailwind v3 is installed: `"tailwindcss": "^3.3.0"`).

**Conclusion:** The `@theme inline` block in globals.css is inert under Tailwind v3. Only the tailwind.config.ts mappings apply. All tokens mapped as `"hsl(var(--X))"` in tailwind.config require their CSS variables to be bare HSL triples, not hex values.

**Fix strategy:** Convert all `:root` and `.dark` color values in `globals.css` from hex to bare HSL triples for variables that are consumed by tailwind.config via `hsl(var(--X))`. Variables only used in `@theme inline` (which is inert) or directly referenced as CSS vars in components can remain as hex.

**Hex to HSL conversion for critical tokens:**

| Variable | Hex | HSL Triple |
|----------|-----|------------|
| `--background` | `#F9FAFB` | `210 20% 98%` |
| `--foreground` | `#111827` | `222 47% 11%` |
| `--card` | `#ffffff` | `0 0% 100%` |
| `--popover` | `#ffffff` | `0 0% 100%` |
| `--primary` | `#F9AB18` | `38 94% 54%` |
| `--secondary` | `#F9FAFB` | `210 20% 98%` |
| `--muted` | `#E5E7EB` | `220 13% 91%` |
| `--accent` | `#FDE4B8` | `38 95% 86%` |
| `--border` | `#E5E7EB` | `220 13% 91%` |
| `--input` | `transparent` → `#ffffff` | `0 0% 100%` |
| `--ring` | `#F9AB18` | `38 94% 54%` |

### Pattern 3: Google Places Nearby Search Integration

**What:** Call `Place.searchNearby()` from the Maps JavaScript API (loaded via `@vis.gl/react-google-maps`'s `useMapsLibrary` hook) to fetch real establishments near a given location, then map the results to the existing `Establishment` interface.

**When to use:** In `ExplorePage.tsx` and/or a new `googlePlaces.ts` utility. The `MapView.tsx` needs real lat/lng coordinates (currently hardcoded from a static `COORDS` object).

**Place types to search for this app:**
- `cafe` — coffee shops
- `coworking_space` — coworking spaces
- `library` — libraries

**Fields to request (affects billing SKU):**
- Essentials fields (cheaper): `displayName`, `formattedAddress`, `location`, `rating`, `types`, `businessStatus`
- Pro fields (more expensive): `photos`, `openingHours`, `nationalPhoneNumber`, `websiteURI`
- `userRatingCount` for credibility signal

**Billing note:** As of March 1, 2025, Google Maps Platform uses per-SKU free tiers: 10,000 free calls/month for Essentials SKUs, 5,000 for Pro SKUs. Requesting Pro fields (photos, openingHours) bumps the request to the Pro SKU.

**Example fetch utility:**

```typescript
// Source: https://developers.google.com/maps/documentation/javascript/nearby-search
// lib/googlePlaces.ts

import type { Establishment } from './mockData'

export async function fetchNearbyEstablishments(
  center: { lat: number; lng: number },
  radiusMeters: number = 2000
): Promise<Establishment[]> {
  // Requires Maps JS API to be loaded via APIProvider first
  const { Place, SearchNearbyRankPreference } = await google.maps.importLibrary('places') as google.maps.PlacesLibrary

  const results: Establishment[] = []

  for (const placeType of ['cafe', 'coworking_space', 'library'] as const) {
    const { places } = await Place.searchNearby({
      fields: [
        'displayName',
        'formattedAddress',
        'location',
        'rating',
        'userRatingCount',
        'photos',
        'openingHours',
        'types',
        'businessStatus',
      ],
      locationRestriction: {
        center,
        radius: radiusMeters,
      },
      includedPrimaryTypes: [placeType],
      maxResultCount: 10,
      rankPreference: SearchNearbyRankPreference.POPULARITY,
    })

    for (const place of places) {
      results.push(mapPlaceToEstablishment(place, placeType))
    }
  }

  return results
}

function mapPlaceToEstablishment(
  place: google.maps.places.Place,
  category: 'cafe' | 'coworking_space' | 'library'
): Establishment {
  const categoryMap = {
    cafe: 'cafe',
    coworking_space: 'coworking',
    library: 'library',
  } as const

  return {
    id: place.id ?? crypto.randomUUID(),
    name: place.displayName ?? 'Unknown',
    category: categoryMap[category],
    image: place.photos?.[0]?.getURI({ maxWidth: 1080 }) ?? '',
    rating: place.rating ?? 0,
    distance: '',  // computed separately if user location known
    address: place.formattedAddress ?? '',
    description: '',  // Places API does not provide free-text descriptions
    amenities: [],    // Not available from Places API; map from types if needed
    spaces: [],       // Must be seeded or managed separately (not from Places API)
    reviews: [],      // Reviews not available from Places API (New) without extra cost
    coordinates: {    // Add to Establishment interface
      lat: place.location?.lat() ?? 0,
      lng: place.location?.lng() ?? 0,
    },
  }
}
```

**Interface extension needed:**

```typescript
// lib/mockData.ts — add coordinates to Establishment
export interface Establishment {
  // ... existing fields ...
  coordinates?: { lat: number; lng: number }  // NEW: real coords from Places API
}
```

**MapView.tsx update:** Replace the static `COORDS` record with `est.coordinates` from the Establishment object.

### Pattern 4: APIProvider Setup for Next.js

`@vis.gl/react-google-maps` requires wrapping the app (or the relevant page) in `APIProvider`. In Next.js App Router, this must be in a client component.

```typescript
// Source: https://visgl.github.io/react-google-maps/docs/get-started
'use client'
import { APIProvider } from '@vis.gl/react-google-maps'

export function MapsProvider({ children }: { children: React.ReactNode }) {
  return (
    <APIProvider apiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!}>
      {children}
    </APIProvider>
  )
}
```

The existing `providers.tsx` at `src/components/providers.tsx` is the right place to add `MapsProvider`, or wrap only the pages that need maps (ExplorePage/EstablishmentDetails).

**Environment variable needed:**
```bash
# .env.local
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_key_here
```

This variable must also be added to Vercel project environment variables for deployment.

### Anti-Patterns to Avoid

- **Changing the `Establishment` interface shape breaking consumers:** `EstablishmentDetails.tsx`, `ExplorePage.tsx`, `MapView.tsx`, and `OwnerDashboard` all consume this interface. Only add optional fields (`coordinates?`), never remove or rename existing required fields.
- **Requesting all Place fields:** Each additional field category (Pro, Enterprise) increases per-request cost. Request only the fields the UI actually displays.
- **Calling `Place.searchNearby()` before `APIProvider` mounts:** The Maps library must be loaded first. Use `useMapsLibrary('places')` hook pattern inside a component, not at module level.
- **Hardcoding API key in source:** Always use `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` env var, restrict the key to HTTP referrers in Google Cloud Console.
- **Fixing only `--input` without fixing `--popover`:** Both are broken by the same hex-vs-HSL-triple mismatch. Fix the entire `:root` block at once.
- **Using native `<select>` in AdvancedSearchForm.tsx as the fix target:** The native `<select>` in `AdvancedSearchForm.tsx` uses `bg-white` directly and is not broken. The broken components are the shadcn `SelectContent` and `DropdownMenuContent` which use `bg-popover`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Google Maps React integration | Custom script tag + window.google loading | `@vis.gl/react-google-maps` APIProvider | Handles script loading, SSR safety, TypeScript types, React lifecycle |
| Places API type definitions | Manual interface for google.maps.* | `@types/google.maps` | Complete, maintained types for all Places API fields |
| Hex-to-HSL conversion at runtime | JS function to convert CSS vars | Just fix the CSS values directly | It's a one-time static fix, no runtime needed |
| Distance calculation from Places results | Haversine formula | Use `rankPreference: DISTANCE` in Place.searchNearby or compute post-fetch with existing lat/lng | Places API returns distance ranking for free; Haversine is ~5 lines but unnecessary |

**Key insight:** The Places API (New) is a single POST endpoint. No SDK installation is required for the HTTP API itself — but the Maps JavaScript API (loaded via `@vis.gl/react-google-maps`) provides the typed `Place` class that handles auth headers and response parsing, which is safer than a raw fetch to the REST endpoint.

## Common Pitfalls

### Pitfall 1: `--popover` hex value interpreted as `hsl(#ffffff)` = transparent

**What goes wrong:** All `SelectContent`, `DropdownMenuContent`, popover components render with transparent backgrounds. Text is invisible against the page background.
**Why it happens:** `globals.css` sets `--popover: #ffffff` but `tailwind.config.ts` maps `popover: "hsl(var(--popover))"`. CSS `hsl(#ffffff)` is invalid and browsers render it as transparent.
**How to avoid:** All variables referenced in `tailwind.config.ts` via `hsl(var(--X))` must be bare HSL triples in CSS: `0 0% 100%`, not `#ffffff`.
**Warning signs:** Any component using `bg-popover`, `bg-card`, `bg-secondary`, `text-foreground` shows wrong or transparent color.

### Pitfall 2: `@theme inline` in globals.css is Tailwind v3-inert

**What goes wrong:** Developer modifies variables in `@theme inline` block expecting them to take effect. Changes have no visible effect.
**Why it happens:** `@theme inline` is Tailwind v4 syntax. The project uses Tailwind v3 (`"tailwindcss": "^3.3.0"` in package.json). The v4 directive is parsed as an unknown at-rule and ignored.
**How to avoid:** In Tailwind v3, all theme customization lives in `tailwind.config.ts`. The `@theme inline` block can be removed or left as dead code — it does nothing.
**Warning signs:** Changing a variable in `@theme inline` has no effect on rendered output.

### Pitfall 3: `Place.searchNearby()` called outside APIProvider context

**What goes wrong:** Runtime error: `google is not defined` or `Cannot read properties of undefined`.
**Why it happens:** The Maps JavaScript API must be loaded by `APIProvider` before any `google.maps.*` calls. Module-level code runs before React renders.
**How to avoid:** Always call `google.maps.importLibrary('places')` inside a React component that is a descendant of `<APIProvider>`, or use the `useMapsLibrary('places')` hook which returns null until the library is ready.
**Warning signs:** Works in development (where APIProvider may mount before the call) but fails on page refresh or SSR.

### Pitfall 4: `spaces` field is empty from Google Places

**What goes wrong:** User navigates to EstablishmentDetails for a Google-sourced establishment and sees no spaces to book.
**Why it happens:** Google Places API has no concept of "bookable spaces". The `spaces: Space[]` field is LibreWork-specific domain data.
**How to avoid:** For Google-sourced establishments, `spaces` must either be seeded with default spaces (e.g., one "table" type space per cafe), fetched from LibreWork's own backend if the establishment exists there, or the UI must handle `spaces: []` gracefully with a "Contact to book" message.
**Warning signs:** Empty space selector in booking card for real establishments.

### Pitfall 5: Google Places API key exposed without restrictions

**What goes wrong:** `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` is visible in browser source. An unrestricted key can be abused by third parties, resulting in unexpected billing.
**Why it happens:** Next.js `NEXT_PUBLIC_` variables are bundled into the client JS.
**How to avoid:** In Google Cloud Console, restrict the API key to HTTP referrers (your Vercel domain + localhost). Also enable only the Maps JavaScript API and Places API (New) on the key.
**Warning signs:** Unexpected API usage spikes in Google Cloud billing dashboard.

### Pitfall 6: Fixing `--input` but not `--popover` and `--card`

**What goes wrong:** Selects still appear transparent after fixing only `--input`.
**Why it happens:** The symptom is in `SelectContent` which uses `bg-popover`, not `bg-input`. Fixing `--input` does not affect `--popover`.
**How to avoid:** Fix all color variables that tailwind.config.ts wraps in `hsl()` — the entire `:root` block.
**Warning signs:** SelectTrigger background fixed but SelectContent dropdown still transparent.

## Code Examples

### Fix: globals.css `:root` color variables (critical tokens only)

```css
/* Source: shadcn/ui theming convention — https://ui.shadcn.com/docs/theming */
/* Variables consumed by tailwind.config.ts via hsl(var(--X)) must be bare HSL triples */

:root {
  --background: 210 20% 98%;       /* was: #F9FAFB */
  --foreground: 222 47% 11%;       /* was: #111827 */
  --card: 0 0% 100%;               /* was: #ffffff */
  --card-foreground: 222 47% 11%;  /* was: #111827 */
  --popover: 0 0% 100%;            /* was: #ffffff — THIS IS THE PRIMARY BUG FIX */
  --popover-foreground: 222 47% 11%; /* was: #111827 */
  --primary: 38 94% 54%;           /* was: #F9AB18 */
  --primary-foreground: 0 0% 100%; /* was: #ffffff */
  --secondary: 210 20% 98%;        /* was: #F9FAFB */
  --secondary-foreground: 222 47% 11%; /* was: #111827 */
  --muted: 220 13% 91%;            /* was: #E5E7EB */
  --muted-foreground: 220 9% 46%;  /* was: #6B7280 */
  --accent: 38 95% 86%;            /* was: #FDE4B8 */
  --accent-foreground: 222 47% 11%; /* was: #111827 */
  --destructive: 0 84% 60%;        /* was: #EF4444 */
  --destructive-foreground: 0 0% 100%; /* was: #ffffff */
  --border: 220 13% 91%;           /* was: #E5E7EB */
  --input: 0 0% 100%;              /* was: transparent — FIXES SELECT TRIGGER */
  --ring: 38 94% 54%;              /* was: #F9AB18 */
  /* Keep hex values for custom non-tailwind-config vars: */
  --input-background: #ffffff;     /* used directly in select.tsx bg-input-background */
}
```

### Fix: globals.css `.dark` color variables

```css
.dark {
  --background: 222 47% 11%;       /* was: #111827 */
  --foreground: 210 20% 98%;       /* was: #F9FAFB */
  --card: 215 28% 17%;             /* was: #1F2937 */
  --card-foreground: 210 20% 98%;
  --popover: 215 28% 17%;          /* was: #1F2937 */
  --popover-foreground: 210 20% 98%;
  --primary: 38 94% 54%;
  --primary-foreground: 0 0% 100%;
  --secondary: 215 19% 27%;        /* was: #374151 */
  --secondary-foreground: 210 20% 98%;
  --muted: 215 19% 27%;
  --muted-foreground: 217 10% 64%; /* was: #9CA3AF */
  --accent: 215 19% 27%;
  --accent-foreground: 210 20% 98%;
  --destructive: 0 84% 60%;
  --destructive-foreground: 0 0% 100%;
  --border: 215 19% 27%;
  --input: 215 28% 17%;            /* was: #374151 */
  --ring: 38 94% 54%;
}
```

### Google Places integration: useMapsLibrary pattern

```typescript
// Source: https://visgl.github.io/react-google-maps/docs/get-started
// components/ExplorePage.tsx (within APIProvider context)

import { useMapsLibrary } from '@vis.gl/react-google-maps'
import { useEffect, useState } from 'react'
import type { Establishment } from '../lib/mockData'

function usePlacesNearby(center: { lat: number; lng: number } | null) {
  const placesLib = useMapsLibrary('places')  // returns null until loaded
  const [establishments, setEstablishments] = useState<Establishment[]>([])

  useEffect(() => {
    if (!placesLib || !center) return
    fetchNearbyEstablishments(center).then(setEstablishments)
  }, [placesLib, center])

  return establishments
}
```

### MapView.tsx: use coordinates from Establishment

```typescript
// Replace static COORDS lookup with est.coordinates
establishments.forEach((est) => {
  const coords = est.coordinates
    ? [est.coordinates.lat, est.coordinates.lng] as [number, number]
    : null
  if (!coords) return
  // ... rest of marker creation
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Places API (Legacy) `nearbySearch()` | Places API (New) `Place.searchNearby()` | March 1, 2025 (new projects blocked from Legacy) | New API uses POST, requires field mask, returns `Place` class instances not plain objects |
| `$200/month` Google Maps credit | Per-SKU free tiers (10K/5K/1K calls/month) | March 1, 2025 | Essentials SKU (basic fields) = 10K free/month; Pro SKU (photos, hours) = 5K free/month |
| `google-map-react` / `react-google-maps/api` | `@vis.gl/react-google-maps` | 2024 (v1.0 released) | Official Google-endorsed React library, TypeScript-first, hooks-based |
| CSS hex values in shadcn globals.css | Bare HSL triples for tailwind.config-mapped vars | shadcn v3 convention | `tailwind.config.ts` wraps vars as `hsl(var(--X))` so vars must be `H S% L%` not `#hex` |

**Deprecated/outdated:**
- `google.maps.places.PlacesService.nearbySearch()`: Legacy API, cannot be enabled for new projects post March 2025
- `google.maps.places.Autocomplete`: Legacy, replaced by `PlaceAutocompleteElement`

## Open Questions

1. **Should mockData.ts establishments be replaced or supplemented with Google Places data?**
   - What we know: `spaces: Space[]` is LibreWork-specific and cannot come from Google Places
   - What's unclear: Whether Phase 9 goal is to show real venues on the map (replacing fake data) or to actually enable booking of those real venues
   - Recommendation: Replace for display (map/list) with Google data; keep or seed minimal `spaces` for the booking flow. If spaces are empty, show a "Coming soon" state in the booking card rather than crashing.

2. **Does the project need a backend route to proxy Google Places calls?**
   - What we know: `NEXT_PUBLIC_` vars are visible client-side; key restriction by HTTP referrer mitigates abuse
   - What's unclear: Security requirements for this project (prototype vs production)
   - Recommendation: Client-side with HTTP referrer restriction is acceptable for Phase 9. A backend proxy is a Phase 9 "deferred" item.

3. **What happens to `AdvancedSearchForm.tsx` which uses native `<select>` elements?**
   - What we know: Native `<select>` with `bg-white` does not suffer from the CSS var bug
   - What's unclear: Whether the user-reported visibility issue includes native selects or only shadcn Select components
   - Recommendation: Fix the CSS var root cause; native selects will not be affected. Optionally replace native `<select>` with shadcn `Select` for visual consistency (but this is optional scope for Phase 9).

## Sources

### Primary (HIGH confidence)
- Source code audit of `/librework/frontend/src/app/globals.css` + `/tailwind.config.ts` + `components/ui/select.tsx` — direct root cause diagnosis
- https://developers.google.com/maps/documentation/places/web-service/nearby-search — Places API (New) Nearby Search endpoint and parameters
- https://developers.google.com/maps/documentation/javascript/place-class-data-fields — Place class fields list
- https://developers.google.com/maps/documentation/places/web-service/place-types — includedTypes values for cafe, coworking_space, library
- https://visgl.github.io/react-google-maps/docs/get-started — APIProvider setup and useMapsLibrary hook

### Secondary (MEDIUM confidence)
- https://mapsplatform.google.com/pricing/ — New per-SKU free tier model (10K Essentials, 5K Pro, 1K Enterprise per month as of March 1, 2025)
- https://github.com/tailwindlabs/tailwindcss/discussions/17137 — Tailwind v4 + shadcn CSS variable transparency discussion (confirms the HSL triple requirement; project uses v3 but same convention applies)
- https://ui.shadcn.com/docs/theming — shadcn theming convention (HSL triple format for CSS vars)

### Tertiary (LOW confidence)
- https://www.flowql.com/fr/blog/guides/shadcn-select-z-index-dropdown-fix/ — z-index stacking context analysis (relevant if fix #1 doesn't resolve all issues; may indicate overflow-hidden parent problems in addition to CSS var fix)

## Metadata

**Confidence breakdown:**
- Select/dropdown fix: HIGH — root cause confirmed by direct source code reading; the hex-vs-HSL-triple mismatch in globals.css is unambiguous
- Architecture (Google Maps): MEDIUM — `@vis.gl/react-google-maps` API verified via official docs; Places API (New) field names verified via official docs; `useMapsLibrary` hook existence confirmed
- Pitfalls: HIGH — sourced from direct code inspection and verified official docs
- Billing model: MEDIUM — sourced from Google pricing page; specific per-API SKU costs not verified at field-by-field level

**Research date:** 2026-03-21
**Valid until:** 2026-06-21 (stable domain; Google Places API pricing model changed March 2025, unlikely to change again soon)

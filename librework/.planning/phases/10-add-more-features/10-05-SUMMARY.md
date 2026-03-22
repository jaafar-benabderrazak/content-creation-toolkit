---
phase: 10-add-more-features
plan: 05
subsystem: ui
tags: [next-intl, i18n, localization, react, nextjs, typescript]

# Dependency graph
requires:
  - phase: 10-add-more-features
    provides: UserDashboard, Navbar, page components that needed translation

provides:
  - next-intl routing infrastructure with EN/FR locale routing
  - [locale] app directory restructure with NextIntlClientProvider
  - Translation files (en.json, fr.json) with full UI string coverage
  - LanguageSwitcher component in Navbar

affects: [all future ui work, any component using Navbar or locale-aware routing]

# Tech tracking
tech-stack:
  added: [next-intl@4.8.3]
  patterns: [URL-based locale routing, NextIntlClientProvider at [locale] layout level, useTranslations hook for client components]

key-files:
  created:
    - librework/frontend/src/i18n/routing.ts
    - librework/frontend/src/i18n/request.ts
    - librework/frontend/src/middleware.ts
    - librework/frontend/messages/en.json
    - librework/frontend/messages/fr.json
    - librework/frontend/src/app/[locale]/layout.tsx
    - librework/frontend/src/app/[locale]/page.tsx
    - librework/frontend/src/app/[locale]/login/page.tsx
    - librework/frontend/src/app/[locale]/login/layout.tsx
    - librework/frontend/src/app/[locale]/register/page.tsx
    - librework/frontend/src/app/[locale]/register/layout.tsx
    - librework/frontend/src/components/LanguageSwitcher.tsx
  modified:
    - librework/frontend/src/app/layout.tsx
    - librework/frontend/src/components/Navbar.tsx
    - librework/frontend/next.config.js

key-decisions:
  - "next-intl 4.8.3 installed — latest stable with getRequestConfig API"
  - "Root layout.tsx reduced to pass-through (no html tag) to avoid duplicate html"
  - "Middleware matcher excludes api|handler|_next|_vercel|static files to prevent locale-prefixing API routes"
  - "LanguageSwitcher uses pathname manipulation (replace locale segment) + router.replace for locale switch"
  - "home-client.tsx kept at src/app level, [locale]/page.tsx import path fixed to ../home-client"

patterns-established:
  - "Locale layout pattern: [locale]/layout.tsx owns html/body/providers including NextIntlClientProvider"
  - "Translation namespaces: Navbar, HomePage, ExplorePage, UserDashboard, OwnerDashboard, Auth, Common"
  - "Client components use useTranslations('Namespace'), server components use getTranslations"

requirements-completed: [I18N-01, I18N-02]

# Metrics
duration: 20min
completed: 2026-03-22
---

# Phase 10 Plan 05: i18n with next-intl Summary

**next-intl 4.8.3 URL-based locale routing (EN/FR) with [locale] app restructure, NextIntlClientProvider, LanguageSwitcher in Navbar, and full translation files**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-03-22T00:00:00Z
- **Completed:** 2026-03-22
- **Tasks:** 4 of 4 (Task 3 human-verify checkpoint — approved by user)
- **Files modified:** 14

## Accomplishments
- next-intl infrastructure: routing.ts (EN/FR), request.ts (server config), middleware.ts (locale detection excluding /api and /handler)
- App directory restructured under [locale] with NextIntlClientProvider; root layout is minimal pass-through
- en.json and fr.json with 7 namespaces covering all UI strings (Navbar, HomePage, ExplorePage, UserDashboard, OwnerDashboard, Auth, Common)
- LanguageSwitcher pill button in Navbar with useTransition; Navbar fully translated via useTranslations

## Task Commits

1. **Task 1a: Set up next-intl infrastructure** - `13c4189` (feat)
2. **Task 1b: Restructure app directory under [locale]** - `5ca0666` (feat)
3. **Task 2: Add LanguageSwitcher and translate components** - `ea6f2f8` (feat)

## Files Created/Modified
- `frontend/src/i18n/routing.ts` - defineRouting with locales EN/FR
- `frontend/src/i18n/request.ts` - getRequestConfig for server-side message loading
- `frontend/src/middleware.ts` - createMiddleware with api/handler exclusion matcher
- `frontend/next.config.js` - wrapped with withNextIntl plugin
- `frontend/messages/en.json` - English translations (7 namespaces, ~70 keys)
- `frontend/messages/fr.json` - French translations (7 namespaces, ~70 keys)
- `frontend/src/app/[locale]/layout.tsx` - Locale root layout with NextIntlClientProvider + all providers
- `frontend/src/app/[locale]/page.tsx` - Home page (import path fixed for nested dir)
- `frontend/src/app/[locale]/login/page.tsx` - Login page
- `frontend/src/app/[locale]/register/page.tsx` - Register page
- `frontend/src/app/layout.tsx` - Reduced to pass-through
- `frontend/src/components/LanguageSwitcher.tsx` - EN/FR toggle pill with useTransition
- `frontend/src/components/Navbar.tsx` - useTranslations('Navbar') + LanguageSwitcher integration

## Decisions Made
- next-intl 4.8.3 — matches latest stable getRequestConfig API
- Root layout has no html/body tags — only [locale]/layout.tsx renders html with lang={locale}
- Middleware negative lookahead `(?!api|handler|_next|_vercel|.*\\..*)` prevents locale prefix on API/static routes
- LanguageSwitcher manipulates pathname segments directly rather than using next-intl's useRouter (avoids dependency on next-intl navigation exports which differ by version)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed home-client import path after moving page.tsx into [locale]/**
- **Found during:** Task 1b (app directory restructure)
- **Issue:** [locale]/page.tsx inherited `import HomeClient from './home-client'` but home-client.tsx lives at src/app level, not src/app/[locale]
- **Fix:** Changed import to `../home-client`
- **Files modified:** frontend/src/app/[locale]/page.tsx
- **Verification:** TypeScript compiled with no errors after fix
- **Committed in:** 5ca0666 (Task 1b commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Required for compilation. No scope creep.

## Issues Encountered
- login/layout.tsx and register/layout.tsx also existed — copied to [locale] subdirs to preserve metadata exports. Originals deleted with their pages.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- i18n infrastructure verified in browser (Task 3 checkpoint approved)
- All pages render under /en/ and /fr/ prefixes confirmed working
- Other components (HomePage, UserDashboard, etc.) can be incrementally translated using the established namespaces

---
*Phase: 10-add-more-features*
*Completed: 2026-03-22*

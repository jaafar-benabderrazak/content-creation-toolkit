# Codebase Structure

**Analysis Date:** 2025-02-20

## Directory Layout

```
librework/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/              # API routes
│   │   ├── core/               # Config, auth, DB, RBAC, audit
│   │   ├── schemas/            # Pydantic models
│   │   └── main.py             # FastAPI application
│   ├── tests/                  # Backend tests
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # React components
│   │   ├── lib/               # API client, utils, Supabase
│   │   ├── hooks/             # React hooks (useAuth, etc.)
│   │   └── types/             # TypeScript types
│   ├── public/
│   └── package.json
├── supabase/
│   ├── migrations/            # SQL migrations
│   └── seed*.sql, *.sql       # Seeds and fixes
├── docs/                       # Documentation
├── .planning/
│   └── codebase/              # Codebase analysis (this doc)
├── start.sh, setup-local.*     # Scripts
├── docker-compose.yml
├── MIGRATION_GUIDE_AUTH.md
└── README.md
```

## Directory Purposes

**backend/**
- Purpose: FastAPI REST API
- Contains: `app/` (Python package), `tests/`, `requirements.txt`, `Dockerfile`
- Key files: `app/main.py`, `app/core/config.py`, `app/core/supabase.py`

**backend/app/api/v1/**
- Purpose: API route modules
- Contains: `auth.py`, `auth_enhanced.py`, `admin_audit.py`, `rbac.py`, `users.py`, `reservations.py`, `spaces.py`, `establishments.py`, `credits.py`, `reviews.py`, `favorites.py`, `activity.py`, `groups.py`, `loyalty.py`, `notifications.py`, `calendar.py`, `owner.py`, `debug.py`
- Routers are included in `main.py` with prefix `/api/v1`

**backend/app/core/**
- Purpose: Shared services and auth
- Contains: `config.py`, `supabase.py`, `auth_enhanced.py`, `auth_simple.py`, `security.py`, `dependencies.py`, `rbac.py`, `audit.py`, `email.py`
- Used as FastAPI dependencies

**backend/app/schemas/**
- Purpose: Pydantic request/response models
- Contains: `__init__.py` (exports), models for users, reservations, establishments, etc.

**frontend/src/**
- Purpose: Next.js application source
- Contains: `app/`, `components/`, `lib/`, `hooks/`, `types/`
- Path alias: `@/*` → `./src/*` (tsconfig.json)

**frontend/src/app/**
- Purpose: App Router routes and layouts
- Contains: `layout.tsx`, `page.tsx`, `globals.css`, `login/`, `register/`
- Single main route (`page.tsx`) uses conditional rendering for SPA-style navigation

**frontend/src/components/**
- Purpose: React components
- Contains: `HomePage.tsx`, `ExplorePage.tsx`, `EstablishmentDetails.tsx`, `UserDashboard.tsx`, `OwnerDashboard.tsx`, `OwnerAdminPage.tsx`, `Navbar.tsx`, `providers.tsx`, `owner/`, `ui/` (shadcn), `figma/`

**frontend/src/lib/**
- Purpose: API client, utilities
- Contains: `api.ts`, `supabase.ts`, `utils.ts`, `mockData.ts`

**frontend/src/hooks/**
- Purpose: Custom React hooks
- Contains: `useAuth.tsx`, `useSimpleAuth.ts`, `useAuth_replit.ts`

**supabase/**
- Purpose: Database schema and seeds
- Contains: `migrations/`, `seed.sql`, `seed_simple.sql`, various fix/verbose SQL files
- Migrations: `20240101000000_initial_schema.sql`, `20240101000001_row_level_security.sql`, `20240201000000_enhanced_auth_system.sql`, etc.

## Key File Locations

**Entry Points:**
- `librework/backend/app/main.py`: FastAPI app, router mounting
- `librework/frontend/src/app/layout.tsx`: Root layout with Providers
- `librework/frontend/src/app/page.tsx`: Main SPA page (home, explore, details, dashboard, owner-dashboard, owner-admin)

**Configuration:**
- `librework/backend/app/core/config.py`: Pydantic settings (SUPABASE_*, JWT_*, CORS_*, etc.)
- `librework/frontend/tsconfig.json`: Path alias `@/*`
- `librework/frontend/tailwind.config.ts`: Tailwind config
- `librework/frontend/next.config.js`: Next.js config

**Core Logic:**
- `librework/backend/app/core/auth_enhanced.py`: Custom JWT auth, get_current_user, get_current_admin
- `librework/backend/app/core/dependencies.py`: Legacy get_current_user, get_current_owner
- `librework/backend/app/core/rbac.py`: RBAC, permissions, establishment access
- `librework/backend/app/core/supabase.py`: Supabase client factory
- `librework/frontend/src/lib/api.ts`: Axios instance, interceptors
- `librework/frontend/src/hooks/useAuth.tsx`: Auth context, login/register/logout

**Testing:**
- `librework/backend/tests/`: `test_main.py`, `test_auth.py`, etc.
- `librework/test_all_features.py`: Feature-level tests at project root

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g. `auth_enhanced.py`, `admin_audit.py`)
- Components: `PascalCase.tsx` (e.g. `HomePage.tsx`, `UserDashboard.tsx`)
- Hooks: `camelCase.ts` or `camelCase.tsx` (e.g. `useAuth.tsx`, `useSimpleAuth.ts`)
- Utils: `camelCase.ts` or `snake_case.ts` (e.g. `api.ts`, `utils.ts`)

**Directories:**
- `api/v1/`: API version prefix
- `components/owner/`: Domain subfolder for owner-specific components
- `components/ui/`: shadcn/ui primitives

**Path alias:**
- `@/` → `frontend/src/` (e.g. `@/components/Navbar`, `@/lib/api`)

## Where to Add New Code

**New API endpoint:**
- Create or update router in `backend/app/api/v1/`
- Register router in `backend/app/main.py`
- Add Pydantic schemas in `backend/app/schemas/` if needed

**New feature component:**
- Add to `frontend/src/components/` (e.g. `NewFeature.tsx`)
- Use from `frontend/src/app/page.tsx` or a route page

**New page/route:**
- App Router: Add `frontend/src/app/<route>/page.tsx`
- Or extend conditional rendering in `frontend/src/app/page.tsx` with new `Page` type and component

**New utility/hook:**
- Shared helpers: `frontend/src/lib/` or `frontend/src/hooks/`

**New database table:**
- Add migration in `supabase/migrations/` with timestamp prefix (e.g. `20240220000000_new_table.sql`)
- Use Supabase client in backend; no ORM models

**New auth provider (Stack Auth):**
- Replace/adjust `frontend/src/hooks/useAuth.tsx` and `lib/api.ts` interceptors
- Replace/adjust `backend/app/core/auth_enhanced.py` and `dependencies.py` to validate Stack Auth tokens
- See `MIGRATION_GUIDE_AUTH.md` for current auth migration pattern

## Special Directories

**frontend/src/components/ui/**
- Purpose: shadcn/ui primitives (Button, Card, Input, etc.)
- Generated: Yes (via shadcn CLI)
- Committed: Yes

**supabase/**
- Purpose: SQL migrations, seeds, diagnostic scripts
- Generated: Migrations are hand-written; some `.sql` files are one-off fixes
- Committed: Yes

**backend/tests/**
- Purpose: Pytest tests
- Generated: No
- Committed: Yes

---

*Structure analysis: 2025-02-20*

# Technology Stack

**Analysis Date:** 2025-02-20

## Languages

**Primary:**
- TypeScript 5.x - Frontend (`frontend/src/`)
- Python 3.11+ - Backend (`backend/app/`)

**Secondary:**
- SQL - Database migrations (`supabase/migrations/`)

## Runtime

**Environment:**
- Node.js 18+ - Frontend (Next.js)
- Python 3.11+ - Backend (FastAPI)

**Package Manager:**
- npm - Frontend (`frontend/package.json`)
- pip/uv - Backend (`backend/requirements.txt`)
- Lockfile: `package-lock.json` in frontend (not detected at root); no pnpm-lock.yaml

## Frameworks

**Core:**
- Next.js 14.2 - Frontend framework with App Router
- FastAPI 0.115 - Backend API framework
- React 18 - UI library

**Testing:**
- pytest 8.3 / pytest-asyncio 0.24 - Backend unit and async tests
- Not detected - Vitest/Jest for frontend (npm test script exists in README)

**Build/Dev:**
- Tailwind CSS 3.3 - Styling (`frontend/tailwind.config.ts`)
- PostCSS 8 - CSS processing (`frontend/postcss.config.js`)
- black 24.10, ruff 0.8, mypy 1.13 - Python formatting/linting

## Key Dependencies

**Critical:**
- `@supabase/supabase-js` ^2.39 - Database and optional auth client
- `supabase` 2.10, `postgrest` 0.18 - Backend database client
- `python-jose[cryptography]` 3.3 - JWT creation/verification
- `passlib[bcrypt]` 1.7 - Password hashing
- `next-auth` ^4.24 - Frontend session provider (legacy/auth route)
- `pydantic` 2.10, `pydantic-settings` 2.6 - Validation and config

**Infrastructure:**
- `axios` ^1.6 - HTTP client for API calls (`frontend/src/lib/api.ts`)
- `@tanstack/react-query` ^5.17 - Server state management
- `zustand` ^4.5 - Client state
- `uvicorn[standard]` 0.32 - ASGI server

**UI:**
- Radix UI components - Dialog, Dropdown, Tabs, etc.
- `recharts` ^2.10 - Charts
- `lucide-react` ^0.312 - Icons
- `react-hook-form` ^7.49, `@hookform/resolvers` ^3.3, `zod` ^3.22 - Forms and validation

## Configuration

**Environment:**
- `frontend/.env.local.example` - Frontend env template
- `backend/.env.example` - Backend env template
- Config loaded via `process.env` (frontend) and `pydantic-settings` (`backend/app/core/config.py`)

**Build:**
- `frontend/next.config.js` - Next.js config, env vars
- `frontend/tsconfig.json` - Path alias `@/*` → `./src/*`
- `frontend/tailwind.config.ts` - Tailwind, dark mode class, primary palette

## Platform Requirements

**Development:**
- Node.js 18+, npm
- Python 3.11+ (3.13 supported per README)
- uv (optional, recommended for Python)
- Supabase project

**Production:**
- Vercel / Railway suggested (README)
- Docker support via `docker-compose.yml`

---

*Stack analysis: 2025-02-20*

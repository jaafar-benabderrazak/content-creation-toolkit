# External Integrations

**Analysis Date:** 2025-02-20

## APIs & External Services

**Database & Backend:**
- **Supabase** - PostgreSQL database, optional auth, storage
  - Backend: `supabase` Python client (`backend/app/core/supabase.py`)
  - Frontend: `@supabase/supabase-js` (`frontend/src/lib/supabase.ts`)
  - Env: `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

**Email:**
- **SendGrid** - Optional email provider
  - Implementation: `backend/app/core/email.py` via `_send_sendgrid`
  - Env: `EMAIL_PROVIDER=sendgrid`, `SENDGRID_API_KEY`
- **Resend** - Optional email provider
  - Implementation: `backend/app/core/email.py` via `_send_resend`
  - Env: `EMAIL_PROVIDER=resend`, `RESEND_API_KEY`
- **SMTP** - Default provider (smtp.gmail.com, configurable)
  - Env: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`

**Geolocation:**
- **geopy** 2.4 - Distance calculations for nearby space search
  - Used in: `backend/app/api/v1/reservations.py` (geodesic distance)

**Images:**
- **Unsplash** - Allowed image domains in Next.js config
  - Config: `frontend/next.config.js` (`images.domains`)

## Data Storage

**Databases:**
- **Supabase (PostgreSQL)** - Primary database
  - Connection: `SUPABASE_URL`, `SUPABASE_KEY` (anon), `SUPABASE_SERVICE_KEY` (admin)
  - Client: `supabase` Python SDK, PostgREST
  - ORM: None; direct table queries via Supabase client
  - Migrations: `supabase/migrations/*.sql`

**File Storage:**
- **Supabase Storage** - QR code bucket (`QR_CODE_STORAGE_BUCKET=qr-codes`)

**Caching:**
- None - No Redis or similar detected

## Authentication & Identity

**Current Implementation (in use):**
- **Backend JWT** - Custom JWT (python-jose, passlib/bcrypt) via enhanced auth
  - Endpoints: `backend/app/api/v1/auth_enhanced.py`, `backend/app/core/auth_enhanced.py`
  - Token flow: `frontend/src/lib/api.ts` (Bearer in localStorage, refresh on 401)
  - Session: `frontend/src/hooks/useAuth.tsx` uses backend `/auth/login`, `/auth/me`
- **NextAuth** - Present but secondary (`frontend/src/app/api/auth/[...nextauth]/route.ts`, `frontend/src/components/providers.tsx`)
  - Requires `frontend/src/lib/auth.ts` (authOptions) - referenced in route
- **Supabase Auth** - Legacy; backend `auth.py` still offers `sign_up` / `sign_in_with_password` alongside enhanced auth

**Target / Intended (per project context):**
- **Stack Auth** - https://app.stack-auth.com/ - Intended auth provider
  - Not yet implemented; project currently uses backend JWT + NextAuth
  - Stack Auth SDK: `@stackframe/init-stack` or similar; Next.js compatible
  - Migration from NextAuth/backend JWT to Stack Auth would touch `frontend/src/lib/auth.ts`, `frontend/src/hooks/useAuth.tsx`, `frontend/src/components/providers.tsx`, and backend auth endpoints

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Application print/logger; no Sentry or similar

## CI/CD & Deployment

**Hosting:**
- README suggests Vercel (frontend), Railway (backend)
- Docker: `docker-compose.yml` for local/containerized runs

**CI Pipeline:**
- Not detected in repo root

## Environment Configuration

**Required env vars (examples only; do not commit real values):**

Frontend (`frontend/.env.local`):
- `NEXT_PUBLIC_API_URL` - Backend API base URL
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon key

Backend (`backend/.env`):
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`
- `CORS_ORIGINS`, `QR_CODE_STORAGE_BUCKET`
- Optional: `EMAIL_PROVIDER`, `SENDGRID_API_KEY`, `RESEND_API_KEY`, SMTP vars

**Secrets location:**
- Local `.env` / `.env.local` (not committed)
- `.env.example` / `.env.local.example` as templates

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- Email (SendGrid/Resend/SMTP) for reservation confirmations, cancellations, reminders

## Additional Integrations

**Calendar:**
- **icalendar** 6.0 - Calendar export (backend)
- **pytz** 2024.1 - Timezone handling
- Used in: `backend/app/api/v1/calendar.py` (export endpoints)

---

*Integration audit: 2025-02-20*

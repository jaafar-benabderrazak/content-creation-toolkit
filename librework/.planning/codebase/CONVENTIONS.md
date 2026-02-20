# Coding Conventions

**Analysis Date:** 2025-02-20

## Naming Patterns

**Files:**
- Backend: snake_case for Python files (`auth.py`, `establishments.py`, `auth_enhanced.py`)
- Frontend components: PascalCase (`HomePage.tsx`, `OwnerDashboard.tsx`, `SpaceAvailabilityIndicator.tsx`)
- Frontend hooks: camelCase with `use` prefix (`useAuth.tsx`, `useSimpleAuth.ts`, `use-mobile.ts`)
- UI primitives: kebab-case (`toggle-group.tsx`, `dropdown-menu.tsx`, `input-otp.tsx`)
- Types: `index.ts` in types directory

**Functions:**
- Backend: snake_case (`get_current_user`, `create_access_token`, `list_establishments`)
- Frontend: camelCase (`fetchCurrentUser`, `createContext`, `onNavigate`)

**Variables:**
- Backend: snake_case (`establishment_id`, `current_user`, `auth_response`)
- Frontend: camelCase (`spaceId`, `access_token`, `isLoading`)

**Types:**
- Backend: PascalCase for Pydantic models and enums (`UserCreate`, `EstablishmentResponse`, `UserRole`)
- Frontend: PascalCase for interfaces (`User`, `Establishment`, `AuthContextType`)

## Code Style

**Formatting:**
- Backend: Black (24.10.0) — `black app/`
- Frontend: No explicit formatter config (relies on ESLint; no Prettier detected)

**Linting:**
- Backend: Ruff (0.8.4), mypy (1.13.0) — `ruff check app/`
- Frontend: ESLint ^9 with `eslint-config-next` ^16.1.1 — `npm run lint` (runs `next lint`)

**Key backend style:**
- 4-space indentation
- Double quotes for strings (Black default)
- Docstrings in double quotes on endpoints

## Import Organization

**Backend order:**
1. Standard library (`from datetime import ...`, `from typing import ...`)
2. Third-party (`from fastapi import ...`, `from pydantic import ...`)
3. Application (`from app.core.config import ...`, `from app.schemas import ...`)

Example from `backend/app/api/v1/auth.py`:
```python
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas import UserCreate, UserResponse, LoginRequest, Token, UserUpdate
from app.core.supabase import get_supabase
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
```

**Frontend order:**
1. React/external (`import React from 'react'`, `import { useQuery } from '@tanstack/react-query'`)
2. Aliases (`import api from '@/lib/api'`, `import type { User } from '@/types'`)
3. Relative (`import { Button } from './ui/button'`, `import { cn } from "./utils"`)

**Path Aliases:**
- `@/` maps to `frontend/src/` — used for `@/lib/api`, `@/types`, `@/components`
- Relative imports for sibling components within same directory

## Error Handling

**Backend (FastAPI):**
- Use `HTTPException` with appropriate status codes (`status.HTTP_400_BAD_REQUEST`, `status.HTTP_401_UNAUTHORIZED`, `status.HTTP_403_FORBIDDEN`, etc.)
- Pattern: try/except wrapping Supabase or external calls, re-raise as `HTTPException`
- Avoid exposing internal errors in `detail` for production — sometimes `str(e)` is used (e.g. `backend/app/api/v1/auth.py` lines 50–51)

Example from `backend/app/api/v1/auth.py`:
```python
try:
    # Supabase operation
    return UserResponse(**user_response.data[0])
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Registration failed: {str(e)}"
    )
```

**Frontend:**
- Axios interceptors in `frontend/src/lib/api.ts` handle 401 and token refresh
- Silent logout on refresh failure: `localStorage.removeItem`, `window.location.href = '/login'`
- Components often swallow errors in `catch` without user feedback (e.g. `useAuth.tsx` clears tokens and sets loading false)

## Logging

**Framework:** Not systematically used. No central logger configuration detected.
- Backend: No `logging` or `loguru` usage in core API files
- Frontend: `console` for debugging; no structured logging

## Comments

**When to Comment:**
- Docstrings on route handlers: `"""Register a new user."""`
- Section headers: `# Enums`, `# Base schemas`, `# Auth schemas`
- Inline TODOs: `# TODO: Implement actual email sending` (e.g. `backend/app/api/v1/auth_enhanced.py`), `# TODO: Get from auth context` (e.g. `frontend/src/components/Navbar.tsx`)

**JSDoc/TSDoc:** Not used in frontend components or hooks.

## Function Design

**Size:** No strict guideline. Route handlers are typically 10–40 lines; some endpoints are longer.

**Parameters:**
- Backend: Use Pydantic models for request bodies (`UserCreate`, `LoginRequest`); use `Query()` for query params with validation (`radius_km: float = Query(10.0, ge=0.1, le=100)`)
- Frontend: Props via interfaces; destructure in function signature

**Return Values:**
- Backend: Explicit `response_model` on routes; Pydantic models for responses
- Frontend: Components return JSX; hooks return objects/arrays

## Module Design

**Exports:**
- Backend: Routers imported and mounted in `app/main.py`; schemas exported from `app/schemas/__init__.py`
- Frontend: Named exports for components (`export function HomePage`); default export for API client (`export default api`)

**Barrel Files:**
- `backend/app/schemas/__init__.py` — all Pydantic schemas
- `frontend/src/components/owner/index.ts` — owner components

## Schema Conventions (Backend)

**Pydantic v2 patterns in `backend/app/schemas/__init__.py`:**
- Use `Field(..., min_length=8)` for required validated fields
- Use `Optional[X] = None` for optional fields
- `class Config: from_attributes = True` for ORM-compatible response models
- `@validator` used for custom validation (Pydantic v1 style; v2 prefers `field_validator`)
- Enums inherit `str, Enum` for JSON serialization (`UserRole`, `EstablishmentCategory`)

## UI Component Conventions (Frontend)

**Location:** `frontend/src/components/ui/` for shadcn/ui-style primitives

**Pattern:** Use `cn()` from `frontend/src/components/ui/utils.ts` for merging Tailwind classes:
```typescript
import { cn } from "./utils";
// className={cn(baseStyles, variantStyles, className)}
```

**Variant pattern:** `class-variance-authority` (cva) for buttons, toggles, etc.:
```typescript
const buttonVariants = cva("base classes", {
  variants: { variant: {...}, size: {...} },
  defaultVariants: { variant: "default", size: "default" }
});
```

## Configuration

**Backend:** `backend/app/core/config.py` — Pydantic Settings with `env_file = ".env"`
**Frontend:** `NEXT_PUBLIC_*` env vars for client-side; `process.env.NEXT_PUBLIC_API_URL` in `frontend/src/lib/api.ts`

---

*Convention analysis: 2025-02-20*

# Migration Guide: Enhanced Authentication System

This guide explains how to migrate LibreWork from the Supabase Auth + Simple JWT system to the new CivilDocPro-style custom authentication system with RBAC and audit logging.

## Overview

The enhanced authentication system provides:

- **Custom JWT Authentication**: No dependency on Supabase Auth
- **RBAC System**: Granular module/action permissions with custom roles
- **Audit Logging**: ISO/NF compliant audit trail for all operations
- **Password Reset**: Secure token-based password reset
- **Application-level Access Control**: Establishment assignments

## New Files Created

### Core Authentication
- `app/core/auth_enhanced.py` - Enhanced authentication with custom JWT
- `app/core/rbac.py` - Role-based access control system
- `app/core/audit.py` - Audit logging system

### API Endpoints
- `app/api/v1/auth_enhanced.py` - New auth endpoints (register, login, password reset)
- `app/api/v1/rbac.py` - Role and permission management
- `app/api/v1/admin_audit.py` - Audit log viewing and export

### Database
- `supabase/migrations/20240201000000_enhanced_auth_system.sql` - New tables and columns

## Migration Steps

### Step 1: Apply Database Migration

```bash
# Run the migration to add new tables and columns
psql -h your-db-host -d librework -f supabase/migrations/20240201000000_enhanced_auth_system.sql
```

Or if using Supabase CLI:
```bash
supabase db push
```

### Step 2: Update Environment Variables

Add to your `.env` file:

```env
# JWT Configuration (existing, verify these are set)
JWT_SECRET_KEY=your-secret-key-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Optional: Disable Supabase Auth (when fully migrated)
# USE_SUPABASE_AUTH=false
```

### Step 3: Migrate Existing Users

For existing users created via Supabase Auth, you need to set their passwords. Options:

#### Option A: Force Password Reset
Send all users a password reset email:

```python
# Run this script to request password resets for all users
from app.core.auth_enhanced import get_user_by_email
from app.api.v1.auth_enhanced import request_password_reset

# For each user, trigger a password reset
users = get_all_users()  # Implement this
for user in users:
    if not user.get("hashed_password"):
        # User needs to set password
        send_password_reset_email(user["email"])
```

#### Option B: Migration Endpoint
Create a temporary migration endpoint that allows users to set their password once:

```python
@router.post("/auth/migrate-set-password")
async def migrate_set_password(
    email: str,
    new_password: str,
    supabase_token: str  # Verify they have valid Supabase session
):
    # Verify Supabase token
    # Set hashed_password
    # Now they can use enhanced auth
```

### Step 4: Update Frontend

Update your frontend to use the new endpoints:

#### Old (Supabase Auth):
```javascript
// Old way
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password
})
```

#### New (Enhanced Auth):
```javascript
// New way
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})
const { access_token, refresh_token, user } = await response.json()
// Store tokens in localStorage or httpOnly cookies
```

### Step 5: Gradual Rollout

1. **Phase 1**: Deploy new endpoints alongside existing ones
2. **Phase 2**: Migrate users as they log in (dual-write pattern)
3. **Phase 3**: Switch frontend to new endpoints
4. **Phase 4**: Disable Supabase Auth (optional)

## API Endpoint Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login with email/password |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/auth/me/permissions` | GET | Get current user's permissions |
| `/api/v1/auth/me/audit-logs` | GET | Get current user's audit logs |
| `/api/v1/auth/password/change` | POST | Change password |
| `/api/v1/auth/password/reset-request` | POST | Request password reset |
| `/api/v1/auth/password/reset-confirm` | POST | Confirm password reset |

### RBAC (Admin only for writes, read for all)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/rbac/roles` | GET | List custom roles |
| `/api/v1/rbac/roles` | POST | Create custom role |
| `/api/v1/rbac/roles/{id}` | GET | Get role details |
| `/api/v1/rbac/roles/{id}` | PUT | Update role |
| `/api/v1/rbac/roles/{id}` | DELETE | Delete role |
| `/api/v1/rbac/users/assign-role` | POST | Assign role to user |
| `/api/v1/rbac/users/{id}/permissions` | GET | Get user permissions |
| `/api/v1/rbac/establishments/assign` | POST | Assign user to establishment |
| `/api/v1/rbac/permissions/modules` | GET | List available modules/actions |

### Audit Logs (Admin only)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/audit/logs` | GET | Query audit logs |
| `/api/v1/admin/audit/logs/recent` | GET | Recent logs |
| `/api/v1/admin/audit/statistics` | GET | Audit statistics |
| `/api/v1/admin/audit/export` | GET | Export logs |

## Permission System

### Default Role Permissions

| Module | Customer | Owner | Admin |
|--------|----------|-------|-------|
| dashboard | view | view | view |
| establishments | view | full | full |
| spaces | view | full | full |
| reservations | create/view/edit | view/validate | full |
| users | - | view | full |
| billing | view | manage | manage |
| reviews | view | moderate | full |
| admin | - | - | full |

### Custom Roles

Create custom roles with specific permissions:

```json
{
  "name": "Receptionniste",
  "permissions": {
    "dashboard": { "view": true },
    "establishments": { "view": true },
    "reservations": { "view": true, "edit": true, "validate": true }
  }
}
```

## Audit Log Actions

All actions are logged with:
- User ID and email
- IP address and user agent
- Entity type and ID
- Previous and new values (for updates)
- Timestamp

Key actions logged:
- `auth.login`, `auth.logout`, `auth.register`
- `user.create`, `user.update`, `user.deactivate`
- `establishment.create`, `establishment.update`
- `reservation.create`, `reservation.cancel`
- `credit.purchase`, `credit.refund`

## Rollback Plan

If you need to rollback:

1. Keep Supabase Auth enabled during transition
2. Frontend can switch back to Supabase endpoints
3. Users with `hashed_password` set can still use enhanced auth
4. Users without can continue using Supabase Auth

## Testing

### Unit Tests
```bash
cd librework/backend
pytest tests/test_auth_enhanced.py -v
```

### Integration Tests
```bash
# Test login flow
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Test permissions
curl http://localhost:8000/api/v1/auth/me/permissions \
  -H "Authorization: Bearer <token>"

# Test audit logs (admin only)
curl http://localhost:8000/api/v1/admin/audit/logs \
  -H "Authorization: Bearer <admin_token>"
```

## Security Considerations

1. **bcrypt with 12 rounds**: Same as CivilDocPro
2. **JWT tokens**: 30min access, 7-day refresh
3. **Reset tokens**: 24-hour expiry, SHA-256 hashed storage
4. **Audit logs**: Immutable, retained for compliance
5. **RLS policies**: Database-level access control maintained

## Support

For issues or questions:
1. Check the audit logs at `/api/v1/admin/audit/logs`
2. Verify user permissions at `/api/v1/auth/me/permissions`
3. Review the CivilDocPro auth.ts for reference implementation

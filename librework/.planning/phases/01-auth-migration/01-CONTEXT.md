# Phase 1: Auth Migration - Context

**Gathered:** 2026-02-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the entire authentication layer -- 3 frontend hooks (useAuth, useSimpleAuth, useAuth_replit), 2 backend auth systems (legacy Supabase Auth, enhanced custom JWT), and RBAC enforcement -- with a unified Stack Auth integration. After this phase, there is exactly one auth system: Stack Auth.

Requirements: AUTH-01 through AUTH-09, INFRA-03.

</domain>

<decisions>
## Implementation Decisions

### Role & RBAC Mapping
- Roles (customer/owner/admin) live in **Stack Auth only** as user metadata, exposed via token claims. Backend reads roles from the JWT -- no separate Supabase role lookup.
- **3 fixed roles** (customer, owner, admin) -- the existing `custom_roles` table and fine-grained per-establishment permissions are removed/simplified. Custom roles are not needed for v1.
- A user becomes an **owner via self-service** -- they click "Become an owner" and get the role immediately. No admin approval needed at this stage (approval workflow is deferred to v2).
- Admin access is managed through **Stack Auth's admin dashboard** -- no hardcoded email lists.

### Session Behavior
- Session duration: **Claude's discretion** -- use Stack Auth defaults (typically 30 days with refresh).
- Multi-device: **Allow concurrent sessions** -- user can be logged in on phone and laptop simultaneously.
- Logout: **Redirect to login page** after logout.
- Protected routes: **Redirect to login page with return URL** -- after successful login, redirect back to the originally requested page.

### Claude's Discretion
- Session duration / token refresh strategy -- use Stack Auth's default configuration
- User migration approach (force re-registration vs progressive re-auth vs bulk import) -- pick the most practical approach given Stack Auth's capabilities
- Cutover approach (big-bang vs parallel period) -- decide based on implementation complexity

</decisions>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches. The user prioritizes a clean result over a specific migration path.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 01-auth-migration*
*Context gathered: 2026-02-20*

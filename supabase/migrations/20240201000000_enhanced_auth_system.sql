-- ============================================
-- Enhanced Authentication System Migration
-- Based on CivilDocPro Architecture
-- Adds: RBAC, Audit Logging, Password Management
-- ============================================

-- ============================================
-- 1. Enhance Users Table
-- Add password fields and account status
-- ============================================

-- Add new columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS hashed_password TEXT,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS reset_token TEXT,
ADD COLUMN IF NOT EXISTS reset_token_hash TEXT,
ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS login_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS custom_role_id UUID,
ADD COLUMN IF NOT EXISTS phone_number TEXT,
ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Add index for reset token lookups
CREATE INDEX IF NOT EXISTS idx_users_reset_token_hash ON users(reset_token_hash);

-- Add index for active users
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- ============================================
-- 2. Custom Roles Table (RBAC)
-- ============================================

CREATE TABLE IF NOT EXISTS custom_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '{}',
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    color TEXT DEFAULT '#6366f1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Add unique constraint on role names (case-insensitive)
CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_roles_name_lower ON custom_roles(LOWER(name));

-- Add index on system roles
CREATE INDEX IF NOT EXISTS idx_custom_roles_system ON custom_roles(is_system) WHERE is_system = TRUE;

-- Add foreign key constraint to users
ALTER TABLE users
ADD CONSTRAINT fk_users_custom_role
FOREIGN KEY (custom_role_id)
REFERENCES custom_roles(id)
ON DELETE SET NULL;

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_custom_roles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_custom_roles_updated_at ON custom_roles;
CREATE TRIGGER update_custom_roles_updated_at
BEFORE UPDATE ON custom_roles
FOR EACH ROW EXECUTE FUNCTION update_custom_roles_updated_at();

-- ============================================
-- 3. Audit Logs Table (ISO/NF Compliance)
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    entity_label TEXT,
    details JSONB DEFAULT '{}',
    previous_value JSONB,
    new_value JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_composite ON audit_logs(entity_type, action, created_at DESC);

-- ============================================
-- 4. Establishment Assignments
-- Similar to CivilDocPro's project_assignments
-- Allows multiple users to manage an establishment
-- ============================================

DO $$ BEGIN
    CREATE TYPE establishment_assignment_role AS ENUM ('manager', 'staff', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS establishment_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    establishment_id UUID NOT NULL REFERENCES establishments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role establishment_assignment_role NOT NULL DEFAULT 'staff',
    assigned_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(establishment_id, user_id)
);

-- Indexes for establishment assignments
CREATE INDEX IF NOT EXISTS idx_establishment_assignments_establishment ON establishment_assignments(establishment_id);
CREATE INDEX IF NOT EXISTS idx_establishment_assignments_user ON establishment_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_establishment_assignments_role ON establishment_assignments(role);

-- ============================================
-- 5. User Sessions Table
-- For tracking active sessions (optional but recommended)
-- ============================================

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- ============================================
-- 6. Default System Roles
-- Pre-populate with default roles
-- ============================================

-- Insert default custom roles if they don't exist
INSERT INTO custom_roles (name, description, permissions, is_system, color)
VALUES (
    'Gestionnaire',
    'Role par defaut pour les proprietaires avec acces complet',
    '{
        "dashboard": {"view": true},
        "establishments": {"view": true, "create": true, "edit": true, "archive": true, "delete": true},
        "spaces": {"view": true, "create": true, "edit": true, "delete": true},
        "reservations": {"view": true, "edit": true, "cancel": true, "validate": true},
        "users": {"view": true},
        "billing": {"view": true, "manage": true, "export": true},
        "reviews": {"view": true, "moderate": true},
        "admin": {}
    }'::jsonb,
    TRUE,
    '#4f46e5'
)
ON CONFLICT (LOWER(name)) DO NOTHING;

INSERT INTO custom_roles (name, description, permissions, is_system, color)
VALUES (
    'Receptionniste',
    'Acces aux reservations et check-ins',
    '{
        "dashboard": {"view": true},
        "establishments": {"view": true},
        "spaces": {"view": true},
        "reservations": {"view": true, "edit": true, "cancel": true, "validate": true},
        "users": {"view": true},
        "billing": {"view": true},
        "reviews": {"view": true},
        "admin": {}
    }'::jsonb,
    TRUE,
    '#059669'
)
ON CONFLICT (LOWER(name)) DO NOTHING;

INSERT INTO custom_roles (name, description, permissions, is_system, color)
VALUES (
    'Observateur',
    'Acces en lecture seule',
    '{
        "dashboard": {"view": true},
        "establishments": {"view": true},
        "spaces": {"view": true},
        "reservations": {"view": true},
        "users": {},
        "billing": {"view": true},
        "reviews": {"view": true},
        "admin": {}
    }'::jsonb,
    TRUE,
    '#6b7280'
)
ON CONFLICT (LOWER(name)) DO NOTHING;

-- ============================================
-- 7. Functions for Audit Logging
-- ============================================

-- Function to clean old audit logs (retention policy)
CREATE OR REPLACE FUNCTION clean_old_audit_logs(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get audit statistics
CREATE OR REPLACE FUNCTION get_audit_stats(
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE (
    action TEXT,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT al.action, COUNT(*)::BIGINT
    FROM audit_logs al
    WHERE al.created_at BETWEEN start_date AND end_date
    GROUP BY al.action
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 8. Update RLS Policies for Enhanced Tables
-- ============================================

-- Enable RLS on new tables
ALTER TABLE custom_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE establishment_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Custom Roles policies
CREATE POLICY "Custom roles viewable by all authenticated users"
ON custom_roles FOR SELECT
TO authenticated
USING (TRUE);

CREATE POLICY "Custom roles manageable by admins only"
ON custom_roles FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.role = 'admin'
    )
);

-- Audit Logs policies
CREATE POLICY "Users can view their own audit logs"
ON audit_logs FOR SELECT
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Admins can view all audit logs"
ON audit_logs FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.role = 'admin'
    )
);

CREATE POLICY "Audit logs can only be created by system"
ON audit_logs FOR INSERT
TO authenticated
WITH CHECK (TRUE);

-- No UPDATE or DELETE on audit logs (immutable)

-- Establishment Assignments policies
CREATE POLICY "Users can view their own assignments"
ON establishment_assignments FOR SELECT
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Owners can view assignments for their establishments"
ON establishment_assignments FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM establishments
        WHERE establishments.id = establishment_assignments.establishment_id
        AND establishments.owner_id = auth.uid()
    )
);

CREATE POLICY "Admins can manage all assignments"
ON establishment_assignments FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.role = 'admin'
    )
);

CREATE POLICY "Owners can manage assignments for their establishments"
ON establishment_assignments FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM establishments
        WHERE establishments.id = establishment_assignments.establishment_id
        AND establishments.owner_id = auth.uid()
    )
);

-- User Sessions policies
CREATE POLICY "Users can view their own sessions"
ON user_sessions FOR SELECT
TO authenticated
USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own sessions"
ON user_sessions FOR DELETE
TO authenticated
USING (user_id = auth.uid());

-- ============================================
-- 9. Migration Support: Convert existing users
-- ============================================

-- Add comment about migration
COMMENT ON TABLE users IS 'Enhanced users table with password management and RBAC support';
COMMENT ON COLUMN users.hashed_password IS 'bcrypt hashed password (12 rounds)';
COMMENT ON COLUMN users.is_active IS 'Account status - can be disabled by admin';
COMMENT ON COLUMN users.custom_role_id IS 'Optional custom role override for RBAC';

COMMENT ON TABLE audit_logs IS 'Audit trail for compliance - DO NOT MODIFY OR DELETE';
COMMENT ON TABLE custom_roles IS 'Custom RBAC roles with granular permissions';
COMMENT ON TABLE establishment_assignments IS 'Many-to-many relationship for establishment access';

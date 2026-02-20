-- ============================================
-- Stack Auth Migration
-- Decouples users table from Supabase auth.users,
-- adds stack_auth_id for Stack Auth mapping,
-- drops custom_roles (3 fixed roles only),
-- removes password-related columns.
-- ============================================

BEGIN;

-- 1. Drop FK constraint from users.id -> auth.users(id)
-- The initial schema defines: id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE
-- PostgreSQL names this constraint "users_id_fkey"
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_id_fkey;

-- 2. Add Stack Auth user ID column for identity mapping
ALTER TABLE users ADD COLUMN IF NOT EXISTS stack_auth_id TEXT UNIQUE;

-- 3. Index for fast lookups by stack_auth_id
CREATE INDEX IF NOT EXISTS idx_users_stack_auth_id ON users(stack_auth_id);

-- 4. Drop custom_roles FK and table (3 fixed roles only per user decision)
ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_custom_role;
ALTER TABLE users DROP COLUMN IF EXISTS custom_role_id;

DROP TRIGGER IF EXISTS update_custom_roles_updated_at ON custom_roles;
DROP FUNCTION IF EXISTS update_custom_roles_updated_at();
DROP TABLE IF EXISTS custom_roles CASCADE;

-- 5. Standardize and drop password-related columns
-- Rename password_hash to hashed_password if it exists (INFRA-03),
-- then drop all password columns — Stack Auth manages passwords.
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE users RENAME COLUMN password_hash TO hashed_password;
    END IF;
END $$;

ALTER TABLE users DROP COLUMN IF EXISTS hashed_password;
ALTER TABLE users DROP COLUMN IF EXISTS reset_token;
ALTER TABLE users DROP COLUMN IF EXISTS reset_token_hash;
ALTER TABLE users DROP COLUMN IF EXISTS reset_token_expires;

-- Drop index that referenced reset_token_hash
DROP INDEX IF EXISTS idx_users_reset_token_hash;

COMMIT;

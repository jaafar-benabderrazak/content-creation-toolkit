-- Add password field to users table for direct authentication
-- Run this in Supabase SQL Editor

-- 1. Add password_hash column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- 2. Make the foreign key constraint to auth.users optional (deferrable)
-- Drop existing constraint
ALTER TABLE users 
DROP CONSTRAINT IF EXISTS users_id_fkey;

-- Make id column not require auth.users (remove foreign key entirely for direct auth)
-- Users will be created directly in this table

-- 3. Update RLS policies to work with direct authentication
-- Allow users to insert their own profile during registration
DROP POLICY IF EXISTS "Users can create their own profile" ON users;
CREATE POLICY "Users can create their own profile"
    ON users FOR INSERT
    WITH CHECK (TRUE);  -- Allow registration

-- 4. Success message
DO $$
BEGIN
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
    RAISE NOTICE '✅ Direct Authentication Schema Update Complete!';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes:';
    RAISE NOTICE '  • Added password_hash column to users table';
    RAISE NOTICE '  • Removed auth.users foreign key dependency';
    RAISE NOTICE '  • Updated RLS policies for direct registration';
    RAISE NOTICE '';
    RAISE NOTICE 'Users can now register directly without Supabase Auth!';
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
END $$;


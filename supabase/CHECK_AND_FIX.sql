-- Quick check and fix for direct auth
-- Run this in Supabase SQL Editor

-- Check if password_hash exists
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'password_hash'
        ) THEN '✓ password_hash column exists'
        ELSE '❌ password_hash column MISSING - run SAFE_REBUILD_AUTH.sql'
    END as status;

-- Check users table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- Check if there's a foreign key to auth.users
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'users' AND constraint_type = 'FOREIGN KEY';


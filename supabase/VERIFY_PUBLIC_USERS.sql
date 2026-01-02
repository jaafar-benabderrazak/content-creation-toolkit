-- Verify public.users table structure (NOT auth.users)

-- 1. Check public.users columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'users'
ORDER BY ordinal_position;

-- 2. Check if public.users is a table or view
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public' 
  AND table_name = 'users';

-- 3. Check foreign keys on public.users
SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'public.users'::regclass;

-- 4. List all users in public.users
SELECT id, email, full_name, role, password_hash IS NOT NULL as has_password
FROM public.users;


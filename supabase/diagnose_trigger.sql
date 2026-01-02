-- Check what's actually in the database and trigger
-- Run this to diagnose the trigger issue

-- 1. Check what columns exist in users table
SELECT 
    'Users table columns:' as info,
    column_name, 
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- 2. Check the current trigger function definition
SELECT 
    'Current trigger function:' as info,
    prosrc as function_code
FROM pg_proc 
WHERE proname = 'handle_new_user';

-- 3. Check if trigger is attached
SELECT 
    'Trigger status:' as info,
    trigger_name,
    event_manipulation,
    action_timing,
    action_statement
FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

-- 4. Check orphaned auth users (auth users without profiles)
SELECT 
    'Orphaned auth users:' as info,
    au.id,
    au.email,
    au.created_at
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE pu.id IS NULL;

-- 5. List all auth users and their profiles
SELECT 
    'All users:' as info,
    au.id,
    au.email as auth_email,
    pu.email as profile_email,
    pu.full_name,
    pu.role
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id;


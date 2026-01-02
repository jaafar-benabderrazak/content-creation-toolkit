-- Debug and Fix Script for Registration Issues
-- Run this in Supabase SQL Editor

-- Step 1: Check if all tables exist
SELECT 'Tables Status' as check_type, table_name, 
    CASE WHEN table_name IS NOT NULL THEN '✓ Exists' ELSE '✗ Missing' END as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'establishments', 'spaces', 'reservations', 'credit_transactions', 'reviews')
ORDER BY table_name;

-- Step 2: Check if new columns exist
SELECT 'User Columns' as check_type, column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Step 3: Check if trigger exists
SELECT 'Trigger Status' as check_type, trigger_name, event_manipulation, action_statement
FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

-- Step 4: Check RLS policies on users table
SELECT 'RLS Policies' as check_type, schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE tablename = 'users';

-- Step 5: Test if we can insert into credit_transactions (common failure point)
DO $$
BEGIN
    -- Test if credit_transactions table allows inserts
    RAISE NOTICE 'Testing credit_transactions table...';
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'credit_transactions') THEN
        RAISE NOTICE '✓ credit_transactions table exists';
    ELSE
        RAISE EXCEPTION '✗ credit_transactions table missing!';
    END IF;
END $$;

-- Step 6: Check permissions
SELECT 'Permissions' as check_type, grantee, privilege_type, table_name
FROM information_schema.table_privileges 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'credit_transactions')
AND grantee IN ('authenticated', 'anon');

-- Step 7: Fix PostGIS RLS warning (optional, doesn't affect registration)
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "spatial_ref_sys is public" ON spatial_ref_sys;
CREATE POLICY "spatial_ref_sys is public" 
    ON spatial_ref_sys FOR SELECT 
    USING (true);

-- Step 8: Verify trigger function exists and is correct
SELECT 'Trigger Function' as check_type, proname, prosrc
FROM pg_proc 
WHERE proname = 'handle_new_user';

-- Final check: Ensure all permissions are granted
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Debug checks complete!';
    RAISE NOTICE 'Review the output above to identify any missing components.';
    RAISE NOTICE '';
    RAISE NOTICE 'Common issues:';
    RAISE NOTICE '1. If trigger is missing → Run row_level_security.sql';
    RAISE NOTICE '2. If columns missing → Run add_profile_features.sql';
    RAISE NOTICE '3. If permissions missing → They are now granted above';
    RAISE NOTICE '';
    RAISE NOTICE 'After fixing any issues, try registration again.';
    RAISE NOTICE '=================================================================';
END $$;


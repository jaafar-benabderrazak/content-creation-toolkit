-- Final Verification Script
-- Run this to check if everything is set up correctly for registration

-- Check 1: Verify trigger exists
SELECT 
    'Trigger Check' as test,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.triggers 
            WHERE trigger_name = 'on_auth_user_created'
        ) THEN '✓ Trigger exists'
        ELSE '✗ MISSING - Run row_level_security.sql'
    END as status;

-- Check 2: Verify trigger function exists
SELECT 
    'Trigger Function' as test,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_proc WHERE proname = 'handle_new_user'
        ) THEN '✓ Function exists'
        ELSE '✗ MISSING - Run row_level_security.sql'
    END as status;

-- Check 3: Verify users table has all columns
SELECT 
    'Users Table Columns' as test,
    string_agg(column_name, ', ') as columns
FROM information_schema.columns 
WHERE table_name = 'users'
GROUP BY table_name;

-- Check 4: Check RLS policies on users table
SELECT 
    'RLS Policies on users' as test,
    policyname,
    cmd as operation
FROM pg_policies 
WHERE tablename = 'users';

-- Check 5: Check if policy allows INSERT
SELECT 
    'INSERT Policy Status' as test,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = 'users' 
            AND cmd = 'INSERT'
        ) THEN '✓ INSERT policy exists'
        ELSE '✗ MISSING - Run quick_fix_registration.sql'
    END as status;

-- Check 6: Check permissions
SELECT 
    'Permissions Check' as test,
    grantee,
    string_agg(privilege_type, ', ') as privileges
FROM information_schema.table_privileges 
WHERE table_schema = 'public' 
AND table_name = 'users'
AND grantee IN ('authenticated', 'anon')
GROUP BY grantee;

-- Final recommendation
DO $$
DECLARE
    has_trigger boolean;
    has_insert_policy boolean;
BEGIN
    -- Check trigger
    SELECT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'on_auth_user_created'
    ) INTO has_trigger;
    
    -- Check INSERT policy
    SELECT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'users' AND cmd = 'INSERT'
    ) INTO has_insert_policy;
    
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
    RAISE NOTICE 'VERIFICATION RESULTS:';
    RAISE NOTICE '';
    
    IF has_trigger THEN
        RAISE NOTICE '✓ Trigger exists';
    ELSE
        RAISE NOTICE '✗ Trigger MISSING - Run migrations/20240101000001_row_level_security.sql';
    END IF;
    
    IF has_insert_policy THEN
        RAISE NOTICE '✓ INSERT policy exists';
    ELSE
        RAISE NOTICE '✗ INSERT policy MISSING - Run quick_fix_registration.sql';
    END IF;
    
    RAISE NOTICE '';
    
    IF has_trigger AND has_insert_policy THEN
        RAISE NOTICE '✅ ALL CHECKS PASSED - Registration should work!';
        RAISE NOTICE 'Try at: http://localhost:3000/register';
    ELSE
        RAISE NOTICE '⚠️  ISSUES FOUND - Run the missing scripts above';
    END IF;
    
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
END $$;


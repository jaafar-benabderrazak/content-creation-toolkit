-- Detailed Trigger Diagnosis
-- This will show us exactly what's happening with the trigger

-- 1. Check if trigger is attached to auth.users (not just public.users)
SELECT 
    'Trigger on auth.users' as check_item,
    trigger_name,
    event_object_schema,
    event_object_table,
    action_timing,
    event_manipulation,
    action_statement
FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

-- 2. Check the actual function code
SELECT 
    'Function Code' as info,
    prosrc as code
FROM pg_proc 
WHERE proname = 'handle_new_user';

-- 3. Check if the function has SECURITY DEFINER
SELECT 
    'Function Security' as info,
    proname,
    prosecdef as is_security_definer,
    provolatile
FROM pg_proc 
WHERE proname = 'handle_new_user';

-- 4. Manually test the trigger function
-- Create a test to see if function works
DO $$
DECLARE
    test_id uuid := 'bc0f2627-e90d-4f8c-aea9-1e8193c0835b';
    test_email text := 'librework.test@gmail.com';
BEGIN
    RAISE NOTICE 'Testing if user profile exists for recent auth user...';
    
    -- Check if profile exists
    IF EXISTS (SELECT 1 FROM public.users WHERE id = test_id) THEN
        RAISE NOTICE '✓ Profile exists for user: %', test_email;
    ELSE
        RAISE NOTICE '✗ Profile MISSING for user: %', test_email;
        RAISE NOTICE 'Attempting to create profile manually...';
        
        -- Try to create it manually to see if there's an error
        BEGIN
            INSERT INTO public.users (
                id, email, full_name, role, coffee_credits,
                phone_number, avatar_url, preferences
            )
            VALUES (
                test_id,
                test_email,
                'Test Owner',
                'owner'::user_role,
                10,
                NULL,
                NULL,
                '{}'::jsonb
            );
            
            RAISE NOTICE '✓ Profile created successfully!';
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE '✗ Error creating profile: %', SQLERRM;
        END;
    END IF;
END $$;

-- 5. Check recent auth users and their profiles
SELECT 
    'Recent Users' as info,
    au.id,
    au.email,
    au.created_at,
    CASE WHEN pu.id IS NOT NULL THEN '✓ Has profile' ELSE '✗ No profile' END as profile_status
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
ORDER BY au.created_at DESC
LIMIT 10;


-- Quick diagnostic to check database state
-- Run this in Supabase SQL Editor to see current status

-- 1. Check if password_hash column exists
SELECT 
    'Column Check' as test,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- 2. Check RLS policies
SELECT 
    'RLS Policies' as test,
    policyname,
    cmd as operation,
    qual as using_expression,
    with_check
FROM pg_policies 
WHERE tablename = 'users';

-- 3. Check existing users (without passwords!)
SELECT 
    'Existing Users' as test,
    id,
    email,
    full_name,
    role,
    coffee_credits,
    CASE WHEN password_hash IS NOT NULL THEN 'Has password' ELSE 'No password' END as password_status,
    created_at
FROM users
ORDER BY created_at DESC
LIMIT 10;

-- 4. Test if we can insert a test user
DO $$
DECLARE
    test_id uuid := gen_random_uuid();
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Testing user insertion...';
    
    BEGIN
        INSERT INTO users (id, email, full_name, role, coffee_credits, password_hash)
        VALUES (
            test_id,
            'diagnostic.test@example.com',
            'Diagnostic Test',
            'customer',
            10,
            'test_hash_value'
        );
        
        RAISE NOTICE '✓ Test user inserted successfully!';
        RAISE NOTICE 'Test user ID: %', test_id;
        
        -- Clean up
        DELETE FROM users WHERE id = test_id;
        RAISE NOTICE '✓ Test user deleted (cleanup)';
        
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✗ Failed to insert test user: %', SQLERRM;
    END;
    
    RAISE NOTICE '=================================================================';
END $$;


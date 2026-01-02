-- Quick Registration Fix
-- Run this single script to fix registration issues

-- Step 1: Grant all necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Step 2: Allow system/trigger to create user profiles
DROP POLICY IF EXISTS "System can create user profiles" ON users;
CREATE POLICY "System can create user profiles"
    ON users FOR INSERT
    WITH CHECK (TRUE);

-- Step 3: Allow system/trigger to create credit transactions
DROP POLICY IF EXISTS "System can create transactions" ON credit_transactions;
CREATE POLICY "System can create transactions"
    ON credit_transactions FOR INSERT
    WITH CHECK (TRUE);

-- Step 4: Ensure trigger function has SECURITY DEFINER
ALTER FUNCTION public.handle_new_user() SECURITY DEFINER;

-- Note: Ignoring spatial_ref_sys RLS warning - it's a PostGIS system table
-- and doesn't affect registration functionality

-- Success message
DO $$
BEGIN
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
    RAISE NOTICE '✓ Registration fix applied successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'What was fixed:';
    RAISE NOTICE '  • Granted permissions to authenticated users';
    RAISE NOTICE '  • Added policy for system to create user profiles';
    RAISE NOTICE '  • Added policy for system to create credit transactions';
    RAISE NOTICE '  • Ensured trigger function has proper security';
    RAISE NOTICE '';
    RAISE NOTICE 'Note: spatial_ref_sys RLS warning can be safely ignored.';
    RAISE NOTICE '      It is a PostGIS system table and does not affect registration.';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Registration should now work!';
    RAISE NOTICE 'Try it at: http://localhost:3000/register';
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
END $$;


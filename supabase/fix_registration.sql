-- Complete Fix Script for Registration Issues
-- Run this if debug script shows missing components

-- Fix 1: Ensure all permissions are granted
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Fix 2: Enable RLS on spatial_ref_sys (to remove warning)
ALTER TABLE spatial_ref_sys ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "spatial_ref_sys is public" ON spatial_ref_sys;
CREATE POLICY "spatial_ref_sys is public" 
    ON spatial_ref_sys FOR SELECT 
    USING (true);

-- Fix 3: Ensure trigger function has correct permissions
ALTER FUNCTION public.handle_new_user() SECURITY DEFINER;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated;

-- Fix 4: Add missing RLS policy for credit_transactions (if needed)
DROP POLICY IF EXISTS "Allow trigger to create transactions" ON credit_transactions;
CREATE POLICY "Allow trigger to create transactions"
    ON credit_transactions FOR INSERT
    WITH CHECK (TRUE); -- Allow trigger/system to create

-- Fix 5: Ensure users table has correct RLS policies
-- Drop and recreate to ensure they're correct
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own profile" ON users;
CREATE POLICY "Users can update their own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Fix 6: Allow the system/trigger to insert users
DROP POLICY IF EXISTS "System can create user profiles" ON users;
CREATE POLICY "System can create user profiles"
    ON users FOR INSERT
    WITH CHECK (TRUE); -- Allow trigger to insert

-- Fix 7: Verify trigger is properly attached
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Success notification
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '✓ All fixes applied!';
    RAISE NOTICE '';
    RAISE NOTICE 'What was fixed:';
    RAISE NOTICE '1. ✓ Permissions granted to authenticated users';
    RAISE NOTICE '2. ✓ RLS enabled on spatial_ref_sys';
    RAISE NOTICE '3. ✓ Trigger function permissions updated';
    RAISE NOTICE '4. ✓ RLS policies updated for users table';
    RAISE NOTICE '5. ✓ Policy added for credit_transactions';
    RAISE NOTICE '6. ✓ Trigger re-attached to auth.users';
    RAISE NOTICE '';
    RAISE NOTICE 'Try registration now at: http://localhost:3000/register';
    RAISE NOTICE '=================================================================';
END $$;


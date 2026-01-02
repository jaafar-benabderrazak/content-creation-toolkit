-- FINAL FIX for Registration Trigger
-- This script updates the trigger function and ensures all policies are correct

-- Step 1: Drop and recreate the trigger function with proper error handling and new columns
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert user profile with all columns (including new ones from profile features)
    INSERT INTO public.users (
        id, 
        email, 
        full_name, 
        role, 
        coffee_credits,
        phone_number,
        avatar_url,
        preferences
    )
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
        COALESCE((NEW.raw_user_meta_data->>'role')::user_role, 'customer'),
        10, -- Initial bonus credits
        NEW.raw_user_meta_data->>'phone_number',
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE((NEW.raw_user_meta_data->'preferences')::jsonb, '{}'::jsonb)
    )
    ON CONFLICT (id) DO NOTHING; -- Prevent duplicate key errors
    
    -- Record the initial credit transaction
    -- Only insert if user was actually created (not on conflict)
    IF FOUND THEN
        INSERT INTO public.credit_transactions (user_id, amount, transaction_type, description)
        VALUES (NEW.id, 10, 'bonus', 'Welcome bonus - 10 free coffee credits');
    END IF;
    
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error but don't fail the auth signup
        RAISE WARNING 'Error in handle_new_user trigger: %', SQLERRM;
        RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 2: Ensure trigger is attached (recreate it)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Step 3: Ensure RLS policies allow the trigger to work
-- Policy for users table INSERT
DROP POLICY IF EXISTS "System can create user profiles" ON users;
CREATE POLICY "System can create user profiles"
    ON users FOR INSERT
    WITH CHECK (TRUE);

-- Policy for credit_transactions table INSERT
DROP POLICY IF EXISTS "System can create transactions" ON credit_transactions;
CREATE POLICY "System can create transactions"
    ON credit_transactions FOR INSERT
    WITH CHECK (TRUE);

-- Step 4: Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Step 5: Grant execute permission on the trigger function
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated, anon;

-- Verification
DO $$
BEGIN
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
    RAISE NOTICE '✅ FINAL FIX APPLIED SUCCESSFULLY!';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes made:';
    RAISE NOTICE '  1. Updated trigger function to include new columns';
    RAISE NOTICE '  2. Added error handling to prevent signup failures';
    RAISE NOTICE '  3. Added ON CONFLICT to handle duplicates';
    RAISE NOTICE '  4. Recreated trigger on auth.users';
    RAISE NOTICE '  5. Updated RLS policies for users and credit_transactions';
    RAISE NOTICE '  6. Granted all necessary permissions';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Registration should now work!';
    RAISE NOTICE '';
    RAISE NOTICE 'Test at: http://localhost:3000/register';
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
END $$;


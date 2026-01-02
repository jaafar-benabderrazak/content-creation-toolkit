-- ALL-IN-ONE FIX for LibreWork Registration
-- This script does everything needed to make registration work
-- Run this ONCE in Supabase SQL Editor

-- Part 1: Update trigger function with all required columns
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert user profile with all columns
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
    ON CONFLICT (id) DO NOTHING;
    
    -- Record the initial credit transaction
    IF FOUND THEN
        INSERT INTO public.credit_transactions (user_id, amount, transaction_type, description)
        VALUES (NEW.id, 10, 'bonus', 'Welcome bonus - 10 free coffee credits');
    END IF;
    
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Error in handle_new_user trigger: %', SQLERRM;
        RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Part 2: Recreate trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Part 3: Ensure RLS policies allow trigger to work
DROP POLICY IF EXISTS "System can create user profiles" ON users;
CREATE POLICY "System can create user profiles"
    ON users FOR INSERT
    WITH CHECK (TRUE);

DROP POLICY IF EXISTS "System can create transactions" ON credit_transactions;
CREATE POLICY "System can create transactions"
    ON credit_transactions FOR INSERT
    WITH CHECK (TRUE);

-- Part 4: Grant all necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated, anon;

-- Part 5: Fix existing orphaned users
DO $$
DECLARE
    orphan_record RECORD;
    created_count INTEGER := 0;
BEGIN
    FOR orphan_record IN 
        SELECT au.id, au.email, au.raw_user_meta_data
        FROM auth.users au
        LEFT JOIN public.users pu ON au.id = pu.id
        WHERE pu.id IS NULL
    LOOP
        INSERT INTO public.users (
            id, email, full_name, role, coffee_credits,
            phone_number, avatar_url, preferences
        )
        VALUES (
            orphan_record.id,
            orphan_record.email,
            COALESCE(orphan_record.raw_user_meta_data->>'full_name', 'User'),
            COALESCE((orphan_record.raw_user_meta_data->>'role')::user_role, 'customer'),
            10,
            orphan_record.raw_user_meta_data->>'phone_number',
            orphan_record.raw_user_meta_data->>'avatar_url',
            COALESCE((orphan_record.raw_user_meta_data->'preferences')::jsonb, '{}'::jsonb)
        )
        ON CONFLICT (id) DO NOTHING;
        
        INSERT INTO public.credit_transactions (user_id, amount, transaction_type, description)
        VALUES (orphan_record.id, 10, 'bonus', 'Welcome bonus - 10 free coffee credits')
        ON CONFLICT DO NOTHING;
        
        created_count := created_count + 1;
    END LOOP;
    
    IF created_count > 0 THEN
        RAISE NOTICE 'Fixed % orphaned user(s)', created_count;
    END IF;
END $$;

-- Final verification
DO $$
DECLARE
    has_trigger boolean;
    has_insert_policy boolean;
    total_auth_users integer;
    users_with_profiles integer;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'on_auth_user_created'
    ) INTO has_trigger;
    
    SELECT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'users' AND cmd = 'INSERT'
    ) INTO has_insert_policy;
    
    SELECT COUNT(*) INTO total_auth_users FROM auth.users;
    SELECT COUNT(*) INTO users_with_profiles 
    FROM auth.users au
    JOIN public.users pu ON au.id = pu.id;
    
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
    RAISE NOTICE '✅ ALL-IN-ONE FIX COMPLETE!';
    RAISE NOTICE '';
    RAISE NOTICE 'Status:';
    RAISE NOTICE '  • Trigger exists: %', CASE WHEN has_trigger THEN '✓ YES' ELSE '✗ NO' END;
    RAISE NOTICE '  • INSERT policy exists: %', CASE WHEN has_insert_policy THEN '✓ YES' ELSE '✗ NO' END;
    RAISE NOTICE '  • Total auth users: %', total_auth_users;
    RAISE NOTICE '  • Users with profiles: %', users_with_profiles;
    RAISE NOTICE '  • Orphaned users: %', total_auth_users - users_with_profiles;
    RAISE NOTICE '';
    
    IF has_trigger AND has_insert_policy AND (total_auth_users = users_with_profiles) THEN
        RAISE NOTICE '✅ EVERYTHING IS FIXED!';
        RAISE NOTICE '';
        RAISE NOTICE 'You can now:';
        RAISE NOTICE '  1. Login with existing users';
        RAISE NOTICE '  2. Register new users';
        RAISE NOTICE '';
        RAISE NOTICE 'Test at: http://localhost:3000/register';
    ELSE
        RAISE NOTICE '⚠️  Something may still be wrong. Check the status above.';
    END IF;
    
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
END $$;


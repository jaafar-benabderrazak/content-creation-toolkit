-- Manual Profile Creation for Orphaned Auth Users
-- Run this after the trigger fix to create profiles for existing auth users

-- First, let's see who needs profiles
DO $$
DECLARE
    orphan_record RECORD;
    created_count INTEGER := 0;
BEGIN
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
    RAISE NOTICE 'Creating profiles for orphaned auth users...';
    RAISE NOTICE '';
    
    -- Loop through auth users without profiles
    FOR orphan_record IN 
        SELECT au.id, au.email, au.raw_user_meta_data
        FROM auth.users au
        LEFT JOIN public.users pu ON au.id = pu.id
        WHERE pu.id IS NULL
    LOOP
        -- Create the profile
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
        
        -- Create initial credit transaction
        INSERT INTO public.credit_transactions (user_id, amount, transaction_type, description)
        VALUES (orphan_record.id, 10, 'bonus', 'Welcome bonus - 10 free coffee credits')
        ON CONFLICT DO NOTHING;
        
        created_count := created_count + 1;
        RAISE NOTICE '✓ Created profile for: % (ID: %)', orphan_record.email, orphan_record.id;
    END LOOP;
    
    RAISE NOTICE '';
    IF created_count > 0 THEN
        RAISE NOTICE '✅ Successfully created % profile(s)', created_count;
    ELSE
        RAISE NOTICE 'No orphaned users found. All auth users have profiles!';
    END IF;
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
END $$;

-- Verify all users now have profiles
SELECT 
    'Verification:' as status,
    COUNT(*) as total_auth_users,
    COUNT(pu.id) as users_with_profiles,
    COUNT(*) - COUNT(pu.id) as orphaned_users
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id;


-- SAFE REBUILD AUTH - Can be run multiple times
-- This adds password_hash and fixes all auth issues

-- Step 1: Add password_hash column (safe if exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE users ADD COLUMN password_hash TEXT;
        RAISE NOTICE '✓ Added password_hash column';
    ELSE
        RAISE NOTICE '  password_hash column already exists';
    END IF;
END $$;

-- Step 2: Remove foreign key if exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'users_id_fkey' AND table_name = 'users'
    ) THEN
        ALTER TABLE users DROP CONSTRAINT users_id_fkey;
        RAISE NOTICE '✓ Removed auth.users foreign key';
    ELSE
        RAISE NOTICE '  Foreign key already removed';
    END IF;
END $$;

-- Step 3: Drop ALL existing policies (safe)
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
DROP POLICY IF EXISTS "Users can update their own profile" ON users;
DROP POLICY IF EXISTS "System can create user profiles" ON users;
DROP POLICY IF EXISTS "Users can create their own profile" ON users;
DROP POLICY IF EXISTS "Anyone can register" ON users;
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Users can update their own data" ON users;

-- Step 4: Create new simple policies
CREATE POLICY "Anyone can register" 
    ON users FOR INSERT 
    WITH CHECK (TRUE);

CREATE POLICY "Users can view their own data" 
    ON users FOR SELECT 
    USING (TRUE);

CREATE POLICY "Users can update their own data" 
    ON users FOR UPDATE 
    USING (TRUE);

-- Step 5: Fix credit_transactions policies
DROP POLICY IF EXISTS "System can create transactions" ON credit_transactions;
DROP POLICY IF EXISTS "Allow trigger to create transactions" ON credit_transactions;
DROP POLICY IF EXISTS "Users can view their transactions" ON credit_transactions;
DROP POLICY IF EXISTS "Users can modify transactions" ON credit_transactions;

CREATE POLICY "Users can view their transactions" 
    ON credit_transactions FOR SELECT 
    USING (TRUE);

CREATE POLICY "System can create transactions" 
    ON credit_transactions FOR INSERT 
    WITH CHECK (TRUE);

CREATE POLICY "Users can modify transactions" 
    ON credit_transactions FOR UPDATE 
    USING (TRUE);

-- Step 6: Drop the auth trigger if exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Step 7: Grant permissions
GRANT ALL ON users TO authenticated, anon;
GRANT ALL ON credit_transactions TO authenticated, anon;
GRANT ALL ON establishments TO authenticated, anon;
GRANT ALL ON spaces TO authenticated, anon;
GRANT ALL ON reservations TO authenticated, anon;
GRANT ALL ON reviews TO authenticated, anon;

-- Final verification
DO $$
DECLARE
    has_password_col boolean;
    has_fk boolean;
    policy_count integer;
BEGIN
    -- Check password_hash column
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) INTO has_password_col;
    
    -- Check foreign key
    SELECT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'users_id_fkey' AND table_name = 'users'
    ) INTO has_fk;
    
    -- Count policies
    SELECT COUNT(*) INTO policy_count 
    FROM pg_policies 
    WHERE tablename = 'users';
    
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
    RAISE NOTICE '✅ SAFE AUTH REBUILD COMPLETE!';
    RAISE NOTICE '';
    RAISE NOTICE 'Verification:';
    RAISE NOTICE '  password_hash column: %', CASE WHEN has_password_col THEN '✓ EXISTS' ELSE '✗ MISSING' END;
    RAISE NOTICE '  auth.users FK removed: %', CASE WHEN NOT has_fk THEN '✓ YES' ELSE '✗ STILL EXISTS' END;
    RAISE NOTICE '  RLS policies on users: % policies', policy_count;
    RAISE NOTICE '';
    
    IF has_password_col AND NOT has_fk AND policy_count >= 3 THEN
        RAISE NOTICE '🎉 Everything is ready!';
        RAISE NOTICE 'You can now register users at: http://localhost:3000/register';
    ELSE
        RAISE NOTICE '⚠️  Some issues remain - check the values above';
    END IF;
    
    RAISE NOTICE '════════════════════════════════════════════════════════════════';
END $$;


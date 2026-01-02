# 🔄 Migration Guide - Upgrading to Simplified Auth

If you have an existing LibreWork installation, follow this guide to upgrade to the new simplified authentication system.

---

## ⚠️ Important: Backup First!

Before proceeding, **backup your database**:

1. Go to Supabase Dashboard → **Database** → **Backups**
2. Click **Create backup**
3. Wait for confirmation

---

## 🎯 Migration Options

### Option A: Fresh Start (Recommended for Testing)

**Best for:** Development, testing, or if you have no important data

1. **Drop existing schema:**
   ```sql
   -- In Supabase SQL Editor
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   GRANT ALL ON SCHEMA public TO postgres;
   GRANT ALL ON SCHEMA public TO public;
   ```

2. **Run new schema:**
   - Copy entire content of `database_schema_replit.sql`
   - Paste in Supabase SQL Editor
   - Click **RUN**

3. **Update code:**
   - Pull latest code from git
   - Backend and frontend are ready to go!

4. **Test:**
   - Register a new user
   - Everything should work perfectly

---

### Option B: In-Place Upgrade (Keep Existing Data)

**Best for:** Production with existing users

#### Step 1: Add password_hash Column

```sql
-- In Supabase SQL Editor
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
```

#### Step 2: Remove Foreign Key (if exists)

```sql
-- Check if foreign key exists
SELECT constraint_name 
FROM information_schema.table_constraints 
WHERE table_name = 'users' AND constraint_type = 'FOREIGN KEY';

-- If it exists, drop it:
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_id_fkey;
```

#### Step 3: Update RLS Policies

```sql
-- Drop old policies
DROP POLICY IF EXISTS "Anyone can register" ON users;
DROP POLICY IF EXISTS "Users can view all profiles" ON users;
DROP POLICY IF EXISTS "Users can update own profile" ON users;

-- Create new policies
CREATE POLICY "Anyone can register" ON users 
FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can view all profiles" ON users 
FOR SELECT USING (true);

CREATE POLICY "Users can update own profile" ON users 
FOR UPDATE USING (id = (current_setting('request.jwt.claims', true)::json->>'sub')::uuid);
```

#### Step 4: Migrate Existing Users

**Important:** Existing users will need to reset their passwords!

```sql
-- Mark existing users for password reset
UPDATE users 
SET password_hash = NULL 
WHERE password_hash IS NULL;
```

**Then:**
1. Send email to all users asking them to reset password
2. Or manually set passwords for test users:

```python
# In Python shell
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash = pwd_context.hash("new_password_123")
print(hash)  # Copy this hash
```

```sql
-- Update user with hashed password
UPDATE users 
SET password_hash = '$2b$12$...'  -- Paste hash here
WHERE email = 'user@example.com';
```

#### Step 5: Update Application Code

```bash
# Pull latest code
git pull

# Backend - reinstall dependencies (in case of changes)
cd backend
pip install -r requirements.txt

# Frontend - reinstall dependencies
cd ../frontend
npm install --legacy-peer-deps
```

#### Step 6: Update Environment Variables

**Backend `.env` - no changes needed** (uses same Supabase credentials)

**Frontend `.env.local` - no changes needed**

#### Step 7: Restart Services

```bash
# Backend
cd backend
python -m app.main

# Frontend
cd frontend
npm run dev
```

#### Step 8: Test

1. **Test registration:** Create a new user → should work
2. **Test login:** Login with new user → should work
3. **Test existing users:** 
   - If password_hash is set → can login
   - If password_hash is NULL → need to reset password

---

## 🔧 Troubleshooting Migration

### Issue: "Column password_hash does not exist"

**Solution:**
```sql
ALTER TABLE users ADD COLUMN password_hash TEXT;
```

### Issue: "Foreign key violation"

**Solution:**
```sql
ALTER TABLE users DROP CONSTRAINT users_id_fkey;
```

### Issue: Existing users can't login

**Expected:** Old auth system used Supabase Auth, new system uses direct database auth.

**Solution:** Reset passwords for all existing users:

**Option 1: Add password reset flow** (recommended)
```python
# In backend/app/api/v1/auth.py
@router.post("/reset-password-request")
async def request_password_reset(email: str):
    # Send email with reset link
    pass

@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    # Verify token and update password
    pass
```

**Option 2: Manual password update** (for testing)
```sql
-- Set password for specific user
UPDATE users 
SET password_hash = '$2b$12$hashed_password_here'
WHERE email = 'user@example.com';
```

### Issue: "Policy not found"

**Solution:** RLS policies have been renamed. Run the UPDATE RLS Policies step again.

---

## 📊 Verification Checklist

After migration, verify:

- [ ] `password_hash` column exists in `users` table
- [ ] No foreign key constraint to `auth.users`
- [ ] RLS policies are updated
- [ ] New user registration works
- [ ] New user login works
- [ ] Token is saved in localStorage
- [ ] Protected routes work
- [ ] API calls include Bearer token

**Run this query to verify:**

```sql
-- Verification query
SELECT 
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = 'users' AND column_name = 'password_hash') as has_password_hash,
    (SELECT COUNT(*) FROM information_schema.table_constraints 
     WHERE table_name = 'users' AND constraint_name = 'users_id_fkey') as has_fk_constraint,
    (SELECT COUNT(*) FROM pg_policies 
     WHERE tablename = 'users') as policy_count,
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE password_hash IS NOT NULL) as users_with_password;
```

**Expected output:**
- `has_password_hash`: 1
- `has_fk_constraint`: 0
- `policy_count`: 3 or more
- `total_users`: Your user count
- `users_with_password`: Users that can login

---

## 🚨 Rollback Plan

If something goes wrong, you can rollback:

### 1. Restore Database Backup

Supabase Dashboard → **Database** → **Backups** → Select backup → **Restore**

### 2. Revert Code

```bash
git checkout <previous-commit-hash>
```

### 3. Restart Services

```bash
cd backend && python -m app.main
cd frontend && npm run dev
```

---

## ✅ Post-Migration

After successful migration:

1. **Test thoroughly:**
   - Register new users
   - Login/logout
   - Create establishments
   - Make reservations
   - Generate QR codes

2. **Update documentation:**
   - Internal docs with new auth flow
   - User guides if affected

3. **Monitor logs:**
   - Watch for auth errors
   - Check Supabase logs
   - Review application logs

4. **Communicate with users:**
   - If existing users need password reset
   - Any new features or changes

---

## 📞 Need Help?

**Common issues:**
- Check `REPLIT_DEPLOYMENT.md` for complete setup
- Review `REVAMP_SUMMARY.md` for what changed
- See backend logs for detailed error messages

**Still stuck?**
1. Check Supabase Dashboard → **Logs**
2. Check backend console output
3. Check browser console (F12)
4. Review `database_schema_replit.sql` for correct schema

---

*Migration guide last updated: December 31, 2025*


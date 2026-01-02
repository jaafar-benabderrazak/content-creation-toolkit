# 🚀 LibreWork - Replit Deployment Guide

Complete guide to deploy LibreWork on Replit with Supabase PostgreSQL.

---

## ✅ Quick Start (15 minutes)

### Step 1: Set Up Supabase Database (5 min)

1. **Go to [Supabase](https://supabase.com)** and create a new project
   - Project name: `librework`
   - Database password: Save this securely!
   - Region: Choose closest to you

2. **Wait for project to provision** (~2 minutes)

3. **Run the database schema:**
   - Go to **SQL Editor** in Supabase dashboard
   - Copy the entire content of `database_schema_replit.sql`
   - Paste and click **RUN**
   - You should see: ✅ "Success. No rows returned" or similar

4. **Get your credentials:**
   - Go to **Settings** → **API**
   - Copy:
     - `Project URL` (looks like: `https://xxxxx.supabase.co`)
     - `anon public` key (long JWT token)
     - `service_role` key (long JWT token)

---

### Step 2: Set Up Replit (5 min)

1. **Go to [Replit](https://replit.com)** and create a new Repl
   - Choose: **Import from GitHub**
   - OR: **Upload** your project folder

2. **Configure Environment Variables (Secrets)**
   
   Click **Tools** → **Secrets** and add these:

```env
# Supabase Configuration
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_KEY=YOUR_ANON_KEY_HERE
SUPABASE_SERVICE_KEY=YOUR_SERVICE_ROLE_KEY_HERE

# JWT Configuration
JWT_SECRET_KEY=generate-a-random-32-character-string-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://YOUR-REPL-NAME.YOUR-USERNAME.repl.co,http://localhost:3000

# Frontend Configuration
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=YOUR_ANON_KEY_HERE
NEXT_PUBLIC_API_URL=https://YOUR-REPL-NAME.YOUR-USERNAME.repl.co
```

**Important:**
- Replace `YOUR_PROJECT`, `YOUR_ANON_KEY_HERE`, etc. with actual values
- Generate JWT secret: Run `openssl rand -hex 32` or use any 32+ character random string
- Update `CORS_ORIGINS` with your actual Repl URL after deployment

---

### Step 3: Deploy on Replit (5 min)

1. **Click the green "Run" button** at the top

2. **Wait for installation** (2-3 minutes):
   - Python dependencies installing...
   - Node.js dependencies installing...
   - Frontend building...

3. **Check the console output:**
   ```
   ✅ LibreWork is running!
      Backend:  http://0.0.0.0:8000
      Frontend: http://0.0.0.0:3000
   ```

4. **Open the application:**
   - Click **"Open in new tab"** or visit your Repl URL
   - You should see the LibreWork homepage!

---

## 🎯 Test the Application

### 1. Register a Space Owner

1. Go to **Sign Up** page
2. Fill in:
   - Email: `owner@gmail.com`
   - Password: `test123456`
   - Full Name: `Test Owner`
   - Role: **Space Owner**
3. Click **Create Account**

**Expected:**
- ✅ Account created
- ✅ Automatically logged in
- ✅ Redirected to owner dashboard

### 2. Create an Establishment

1. From Owner Dashboard, click **"Add Establishment"**
2. Fill in:
   - Name: `Demo Café`
   - Description: `A cozy workspace café`
   - Address: `123 Main St`
   - City: `Paris`
   - Services: `wifi, coffee, quiet_spaces`
3. Click **Save**

### 3. Add a Space

1. Click on your establishment
2. Click **"Add Space"**
3. Fill in:
   - Name: `Table 1`
   - Type: `Desk`
   - Capacity: `1`
   - Credits per hour: `2`
4. Click **Save**

### 4. Generate QR Code

1. Click on your space
2. Click **"Generate QR Code"**
3. Download the QR code image
4. Print it or save for testing

### 5. Test as Customer

1. **Logout** (or open incognito window)
2. **Register** as a customer:
   - Email: `customer@gmail.com`
   - Role: **Customer**
3. **Browse** establishments
4. **Make a reservation**
5. **Scan QR code** (or enter manually) to validate

---

## 🔧 Troubleshooting

### Backend won't start

**Check:**
1. All environment variables are set in Replit Secrets
2. Database schema was run successfully in Supabase
3. Supabase project is active (not paused)

**Debug:**
- Check console for error messages
- Go to **Shell** tab and run:
  ```bash
  cd backend
  python -m app.main
  ```

### Frontend won't build

**Check:**
1. `NEXT_PUBLIC_*` variables are set
2. Node.js version is 20+

**Debug:**
- Go to **Shell** tab and run:
  ```bash
  cd frontend
  npm install --legacy-peer-deps
  npm run build
  ```

### "Database error" during registration

**Check:**
1. Database schema was run completely
2. Verify `password_hash` column exists:
   ```sql
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'users' AND column_name = 'password_hash';
   ```
3. Check RLS policies are enabled:
   ```sql
   SELECT tablename, policyname FROM pg_policies 
   WHERE tablename = 'users';
   ```

### CORS errors in browser

**Fix:**
1. Update `CORS_ORIGINS` in Replit Secrets to include your actual Repl URL
2. Restart the application

---

## 📁 File Structure

```
librework/
├── .replit                          # Replit configuration
├── replit.nix                       # Nix packages
├── start.sh                         # Startup script
├── database_schema_replit.sql       # Database schema
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app
│   │   ├── core/
│   │   │   ├── auth_simple.py      # ✨ NEW: Simple JWT auth
│   │   │   ├── config.py
│   │   │   └── supabase.py
│   │   └── api/v1/
│   │       ├── auth_replit.py      # ✨ NEW: Auth endpoints
│   │       ├── establishments.py
│   │       ├── spaces.py
│   │       └── ...
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── hooks/
    │   │   └── useAuth_replit.ts   # ✨ NEW: Simple auth hook
    │   ├── app/
    │   │   ├── login/page.tsx
    │   │   ├── register/page.tsx
    │   │   └── ...
    │   └── components/
    └── package.json
```

---

## 🔐 Security Notes

### For Production:

1. **Change JWT Secret:**
   - Generate a strong 64-character random string
   - Never commit it to git

2. **Use Environment-Specific URLs:**
   - Development: `http://localhost:8000`
   - Production: Your actual domain

3. **Enable SSL:**
   - Replit provides HTTPS by default
   - Always use HTTPS in production

4. **Rate Limiting:**
   - Add rate limiting to auth endpoints
   - Use Supabase's built-in rate limiting

5. **Database Backups:**
   - Enable automatic backups in Supabase
   - Download periodic manual backups

---

## 🎨 Customization

### Change Initial Credits

Edit `backend/app/api/v1/auth_replit.py`:

```python
initial_credits = 10 if data.role == "owner" else 50
```

### Modify JWT Expiration

Update Replit Secrets:
```env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 hour
```

### Add Custom Fields

1. Update database schema:
   ```sql
   ALTER TABLE users ADD COLUMN custom_field TEXT;
   ```

2. Update Pydantic schemas in `backend/app/schemas/__init__.py`

3. Update frontend types in `frontend/src/types/index.ts`

---

## 📊 Monitoring

### Backend Health Check

Visit: `https://YOUR-REPL-URL.repl.co/health`

Expected response:
```json
{
  "status": "healthy"
}
```

### API Documentation

Visit: `https://YOUR-REPL-URL.repl.co/docs`

Interactive Swagger UI for testing all endpoints.

### Database Monitoring

Supabase Dashboard → **Database** → **Replication**
- Monitor query performance
- Check table sizes
- View active connections

---

## 🚀 Next Steps

1. **Add Payment Integration:**
   - Stripe for credit purchases
   - Update `credits.py` endpoints

2. **Add Email Notifications:**
   - Supabase Auth with email templates
   - Reservation confirmations

3. **Add Real-Time Features:**
   - Supabase Realtime for live availability
   - WebSocket for instant updates

4. **Deploy to Custom Domain:**
   - Configure DNS
   - Update CORS origins
   - Update environment variables

---

## 📞 Support

**Issues?**
- Check Replit console logs
- Check Supabase logs (Dashboard → Logs)
- Review `ARCHITECTURE.md` for system design

**Need help?**
- Open an issue on GitHub
- Check Replit community forums
- Review Supabase documentation

---

## ✅ Deployment Checklist

Before going live:

- [ ] Database schema applied
- [ ] All environment variables set
- [ ] JWT secret is strong and unique
- [ ] CORS origins configured correctly
- [ ] Application runs without errors
- [ ] Registration flow tested
- [ ] Login flow tested
- [ ] Establishment creation tested
- [ ] Space creation tested
- [ ] QR code generation tested
- [ ] Reservation flow tested
- [ ] SSL/HTTPS enabled
- [ ] Database backups configured

---

**🎉 Congratulations! Your LibreWork application is now deployed on Replit!**


# LibreWork - Quick Deployment Guide

## 🚀 Quick Start (15 minutes)

This guide will get your LibreWork platform deployed and running in production.

### Prerequisites
- GitHub account
- Supabase account (free)
- Railway account (free) OR Render.com account
- Vercel account (free)

---

## Step 1: Supabase Database Setup (5 min)

### 1.1 Create Project
1. Go to [supabase.com](https://supabase.com) → Sign up/Login
2. Click "New Project"
3. Fill in:
   - Name: `librework`
   - Database Password: (generate strong password)
   - Region: Choose closest to your users
4. Click "Create new project" (takes ~2 minutes)

### 1.2 Get Credentials
1. Go to **Settings** → **API**
2. Copy and save:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public**: `eyJhbG...` (under "Project API keys")
   - **service_role**: `eyJhbG...` (keep this SECRET!)

### 1.3 Run Migrations
1. Go to **SQL Editor** in left sidebar
2. Click "New query"
3. Copy entire contents of `supabase/migrations/20240101000000_initial_schema.sql`
4. Paste and click "Run"
5. Repeat for `supabase/migrations/20240101000001_row_level_security.sql`
6. Repeat for `supabase/migrations/20240102000000_add_profile_features.sql`
7. ⚠️ **Skip seed.sql** - It's easier to create data through your app!

### 1.4 Create Storage Bucket
1. Go to **Storage** in left sidebar
2. Click "New bucket"
3. Name: `qr-codes`
4. Public bucket: **Yes**
5. Click "Create bucket"

✅ **Supabase is ready!**

---

## Step 2: Deploy Backend (5 min)

### Option A: Railway (Recommended)

1. **Sign Up**
   - Go to [railway.app](https://railway.app)
   - Click "Login" → Sign in with GitHub

2. **Create Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub
   - Select your `librework` repository

3. **Configure Service**
   - Railway auto-detects Python
   - Click on the service → **Settings**
   - **Root Directory**: Leave empty or set to `backend`
   - **Start Command**: 
     ```bash
     cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

4. **Add Environment Variables**
   - Go to **Variables** tab
   - Click "New Variable" and add each:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key_from_step_1.2
   SUPABASE_SERVICE_KEY=your_service_role_key_from_step_1.2
   JWT_SECRET_KEY=your_random_secret_here
   DEBUG=False
   CORS_ORIGINS=["https://your-app-name.vercel.app"]
   ```

   **Generate JWT Secret:**
   ```bash
   # Run this locally:
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~2-3 minutes)
   - Copy your backend URL: `https://your-app.up.railway.app`
   - Test: Visit `https://your-app.up.railway.app/docs`

✅ **Backend is live!**

### Option B: Render.com

1. Go to [render.com](https://render.com) → Sign in with GitHub
2. Click "New +" → "Web Service"
3. Connect your repository
4. Configure:
   - **Name**: `librework-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (same as Railway)
6. Click "Create Web Service"

---

## Step 3: Deploy Frontend (5 min)

### Using Vercel

1. **Sign Up**
   - Go to [vercel.com](https://vercel.com)
   - Click "Sign Up" → Continue with GitHub

2. **Import Project**
   - Click "Add New..." → "Project"
   - Import your `librework` repository
   - Click "Import"

3. **Configure Build**
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto)
   - **Output Directory**: `.next` (auto)
   - **Install Command**: `npm install` (auto)

4. **Add Environment Variables**
   Click "Environment Variables" and add:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_from_step_1.2
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build (~2-3 minutes)
   - Your app is live at: `https://your-app.vercel.app`

6. **Update Backend CORS**
   - Go back to Railway → Variables
   - Update `CORS_ORIGINS`:
     ```
     CORS_ORIGINS=["https://your-app.vercel.app"]
     ```
   - Railway will auto-redeploy

✅ **Frontend is live!**

---

## Step 4: Test Your Deployment

### 1. Visit Your App
Open `https://your-app.vercel.app`

### 2. Register an Account
1. Click "Sign Up"
2. Register as **Owner** (to test all features)
3. Email: `owner@test.com`
4. Password: `test123456`

### 3. Create Test Establishment
1. Go to Owner Dashboard
2. Click "Manage Spaces"
3. Create your first cafe/coworking space
4. Add spaces and generate QR codes

### 4. Test as Customer
1. Logout
2. Register new account as **Customer**
3. Browse establishments
4. Make a test reservation

✅ **Everything works!**

---

## 🎉 You're Done!

Your LibreWork platform is now live in production!

### Your URLs:
- **Frontend**: `https://your-app.vercel.app`
- **Backend API**: `https://your-backend.up.railway.app`
- **API Docs**: `https://your-backend.up.railway.app/docs`
- **Database**: `https://your-project.supabase.co`

---

## Next Steps

### Optional Improvements

1. **Custom Domain**
   - **Frontend**: Vercel → Settings → Domains → Add
   - **Backend**: Railway → Settings → Networking → Add domain

2. **Monitoring**
   - Railway: Built-in metrics dashboard
   - Vercel: Analytics tab
   - Supabase: Database → Performance

3. **Error Tracking**
   - Set up [Sentry](https://sentry.io) for error monitoring
   - Add Sentry DSN to environment variables

4. **Analytics**
   - Add Google Analytics to frontend
   - Set up PostHog for product analytics

5. **Email Notifications**
   - Configure Supabase Auth emails
   - Settings → Authentication → Email Templates

---

## Troubleshooting

### Frontend can't connect to backend
**Problem**: CORS errors in browser console

**Solution**:
1. Check `CORS_ORIGINS` in Railway includes your Vercel URL
2. Format: `["https://your-app.vercel.app"]` (with brackets and quotes)
3. Railway will auto-redeploy after changing

### Database connection failed
**Problem**: Backend logs show Supabase connection errors

**Solution**:
1. Verify `SUPABASE_URL` and keys are correct
2. Check Supabase project is active (not paused)
3. Ensure RLS policies are enabled

### Build failures
**Problem**: Deployment fails during build

**Backend Solution**:
- Check `requirements.txt` is valid
- Ensure Python 3.11+ is specified
- Review Railway build logs

**Frontend Solution**:
- Check `package.json` dependencies
- Ensure all environment variables are set
- Review Vercel build logs

### Can't register/login
**Problem**: Authentication not working

**Solution**:
1. Check Supabase Auth is enabled
2. Verify email confirmation settings
3. Check JWT_SECRET_KEY is set in backend
4. Test with Supabase → Authentication → Users

---

## Cost Estimate

All services offer generous free tiers:

- **Supabase**: Free (500MB database, 50MB storage, 50K MAU)
- **Railway**: $5/month credit free, then ~$5-20/month
- **Vercel**: Free (100GB bandwidth, unlimited deployments)

**Total**: $0-25/month depending on traffic

---

## Support

Need help?
1. Check full deployment guide: `docs/DEPLOYMENT.md`
2. Review API documentation: `docs/API.md`
3. Check GitHub issues
4. Read troubleshooting section above

---

## Security Checklist

Before launching to real users:

- [x] Generated strong JWT secret
- [ ] Configured custom domain with HTTPS
- [ ] Set `DEBUG=False` in production
- [ ] Enabled database backups in Supabase
- [ ] Reviewed RLS policies
- [ ] Changed default test accounts
- [ ] Set up error monitoring
- [ ] Configured rate limiting
- [ ] Added privacy policy & terms

---

**Congratulations! Your LibreWork platform is live! 🎉**


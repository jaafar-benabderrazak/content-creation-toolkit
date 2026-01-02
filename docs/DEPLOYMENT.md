# LibreWork - Deployment Guide

## Overview

This guide covers multiple deployment options for the LibreWork platform:
1. **Quick Deploy** (Vercel + Railway) - Recommended for most users
2. **Docker Compose** - For self-hosting
3. **Manual Deployment** - For custom infrastructure
4. **Cloud Platforms** - AWS, Google Cloud, Azure

## Prerequisites

- Node.js 18+ installed
- Python 3.11+ installed (3.13 supported)
- Supabase account (free tier available)
- Git installed
- Deployment platform account (Vercel/Railway/Render)

---

## Option 1: Quick Deploy (Recommended)

### Step 1: Supabase Setup

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Click "New Project"
   - Choose organization and set project name
   - Select region closest to your users
   - Set a strong database password

2. **Get Credentials**
   Navigate to Settings > API and note:
   - Project URL: `https://xxxxx.supabase.co`
   - `anon` public key (starts with `eyJ...`)
   - `service_role` key (keep secret!)

3. **Run Database Migrations**
   - Go to SQL Editor in Supabase Dashboard
   - Create new query
   - Copy contents of `supabase/migrations/20240101000000_initial_schema.sql`
   - Run query
   - Repeat for `20240101000001_row_level_security.sql`
   - Optionally run `supabase/seed.sql` for test data

4. **Create Storage Bucket**
   - Go to Storage section
   - Create new bucket: `qr-codes`
   - Set to Public
   - Add policy for public read access:
   ```sql
   create policy "QR codes are publicly readable"
   on storage.objects for select
   using ( bucket_id = 'qr-codes' );
   ```

### Step 2: Backend Deployment (Railway)

1. **Sign up for Railway**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your LibreWork repository
   - Select the repository

3. **Configure Build**
   - Root directory: Leave as `/` or set to `backend`
   - Build command (auto-detected):
   ```bash
   cd backend && pip install -r requirements.txt
   ```
   - Start command:
   ```bash
   cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**
   In Railway Dashboard > Variables, add:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key_here
   SUPABASE_SERVICE_KEY=your_service_role_key_here
   JWT_SECRET_KEY=generate_strong_random_key
   DEBUG=False
   CORS_ORIGINS=["https://your-app.vercel.app"]
   ```

   Generate JWT secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Deploy**
   - Railway will automatically deploy
   - Note your backend URL: `https://your-app.up.railway.app`
   - Test health: `https://your-app.up.railway.app/health`
   - View API docs: `https://your-app.up.railway.app/docs`

### Step 3: Frontend Deployment (Vercel)

1. **Sign up for Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub

2. **Import Project**
   - Click "Add New" > "Project"
   - Import your LibreWork repository
   - Framework Preset: Next.js (auto-detected)
   - Root Directory: `frontend`

3. **Configure Build**
   Vercel auto-detects Next.js settings:
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

4. **Add Environment Variables**
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at: `https://your-app.vercel.app`

6. **Update Backend CORS**
   Go back to Railway and update:
   ```env
   CORS_ORIGINS=["https://your-app.vercel.app"]
   ```
   Railway will auto-redeploy.

---

## Option 2: Docker Compose (Self-Hosting)

### 1. Update CORS Origins

In your backend `.env` or Railway environment variables:
```env
CORS_ORIGINS=["https://your-app.vercel.app","https://your-custom-domain.com"]
```

### 2. Set Up Custom Domain (Optional)

**Frontend (Vercel):**
1. Go to Project Settings > Domains
2. Add your custom domain
3. Configure DNS records as instructed

**Backend (Railway):**
1. Go to Project Settings > Networking
2. Add custom domain
3. Configure DNS records

### 3. Generate JWT Secret Key

For production, generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Database Maintenance

### Backups

Supabase automatically backs up your database daily. Configure backup schedule in:
- Supabase Dashboard > Settings > Database > Backups

### Monitoring

Monitor your database:
1. Supabase Dashboard > Database > Performance
2. Check query performance
3. Review slow queries
4. Optimize indexes if needed

## Environment Variables Reference

### Backend

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SUPABASE_URL` | Supabase project URL | Yes | - |
| `SUPABASE_KEY` | Supabase anon key | Yes | - |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes | - |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens | Yes | - |
| `JWT_ALGORITHM` | Algorithm for JWT | No | HS256 |
| `DEBUG` | Enable debug mode | No | False |
| `CORS_ORIGINS` | Allowed CORS origins | No | ["http://localhost:3000"] |

### Frontend

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes | http://localhost:8000 |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Yes | - |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | Yes | - |

## Troubleshooting

### Backend Issues

**Issue: CORS errors**
- Solution: Add frontend URL to `CORS_ORIGINS` in backend env vars

**Issue: Database connection failed**
- Solution: Check Supabase credentials and project status

**Issue: JWT token errors**
- Solution: Ensure `JWT_SECRET_KEY` is set and consistent

### Frontend Issues

**Issue: API calls failing**
- Solution: Check `NEXT_PUBLIC_API_URL` points to correct backend

**Issue: Authentication not working**
- Solution: Verify Supabase credentials are correct

**Issue: Build errors**
- Solution: Run `npm install` and check for missing dependencies

## Security Checklist

Before going to production:

- [ ] Change all default passwords and keys
- [ ] Generate strong JWT secret key
- [ ] Enable HTTPS/SSL for all endpoints
- [ ] Configure proper CORS origins (no wildcards)
- [ ] Set `DEBUG=False` in production
- [ ] Enable Row Level Security policies in Supabase
- [ ] Set up database backups
- [ ] Configure rate limiting (via Railway/CDN)
- [ ] Review and test all API endpoints
- [ ] Set up error monitoring (e.g., Sentry)
- [ ] Configure logging

## Monitoring and Maintenance

### Health Checks

Backend health endpoint: `GET /health`

### Logs

- **Backend (Railway)**: View logs in Railway dashboard
- **Frontend (Vercel)**: View logs in Vercel dashboard
- **Database**: View logs in Supabase dashboard

### Performance Monitoring

- Monitor API response times
- Track database query performance
- Watch for memory/CPU usage spikes
- Set up alerts for downtime

## Scaling Considerations

### Database
- Supabase auto-scales storage
- Upgrade plan for more connections
- Add read replicas for heavy read workloads

### Backend
- Railway auto-scales horizontally
- Add more instances for high traffic
- Consider caching layer (Redis) for frequent queries

### Frontend
- Vercel CDN handles scaling automatically
- Optimize images with Next.js Image
- Use ISR for static content
- Implement client-side caching

## Support

For issues:
1. Check logs in respective dashboards
2. Review this documentation
3. Check GitHub issues
4. Contact support channels

## Updates and Migrations

### Database Migrations

1. Create new migration file in `supabase/migrations/`
2. Test locally
3. Run in Supabase SQL Editor (production)
4. Verify changes

### Application Updates

1. Test changes locally
2. Push to GitHub
3. Automatic deployment via CI/CD
4. Verify deployment success
5. Monitor for errors


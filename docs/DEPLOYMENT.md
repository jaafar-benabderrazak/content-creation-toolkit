# LibreWork - Deployment Guide

## Prerequisites

- Node.js 18+ installed
- Python 3.11+ installed
- Supabase account
- Railway/Fly.io account (for backend deployment)
- Vercel account (for frontend deployment)

## Supabase Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note down:
   - Project URL
   - `anon` public key
   - `service_role` key (keep secret!)

### 2. Run Migrations

1. Navigate to SQL Editor in Supabase Dashboard
2. Copy and run the contents of `supabase/migrations/20240101000000_initial_schema.sql`
3. Then run `supabase/migrations/20240101000001_row_level_security.sql`
4. Optionally run `supabase/seed.sql` for test data

### 3. Create Storage Bucket

1. Go to Storage in Supabase Dashboard
2. Create a new public bucket named `qr-codes`
3. Set appropriate policies for public read access

## Backend Deployment

### Local Development

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Fill in environment variables:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
JWT_SECRET_KEY=generate_a_strong_random_key
DEBUG=True
```

6. Run the server:
```bash
python -m app.main
# Or with uvicorn:
uvicorn app.main:app --reload
```

7. API will be available at http://localhost:8000
8. API docs at http://localhost:8000/docs

### Production Deployment (Railway)

1. Create a new project on Railway
2. Connect your GitHub repository
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Railway dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`
   - `JWT_SECRET_KEY`
   - `DEBUG=False`
   - `CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]`
6. Deploy!

### Alternative: Docker Deployment

1. Build Docker image:
```bash
cd backend
docker build -t librework-backend .
```

2. Run container:
```bash
docker run -p 8000:8000 \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  -e SUPABASE_SERVICE_KEY=your_service_key \
  -e JWT_SECRET_KEY=your_secret \
  librework-backend
```

## Frontend Deployment

### Local Development

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

4. Fill in environment variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

5. Run development server:
```bash
npm run dev
```

6. App will be available at http://localhost:3000

### Production Deployment (Vercel)

1. Push your code to GitHub
2. Import project in Vercel
3. Set root directory to `frontend`
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. Deploy!

Vercel will automatically:
- Install dependencies
- Build the Next.js app
- Deploy to CDN
- Provide a production URL

## Post-Deployment Configuration

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


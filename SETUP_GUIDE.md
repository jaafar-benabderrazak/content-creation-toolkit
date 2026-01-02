# 🚀 LibreWork Setup Guide - Complete Feature Set

This guide will help you set up LibreWork with all the new features enabled.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Feature Configuration](#feature-configuration)
6. [Testing](#testing)
7. [Deployment](#deployment)

---

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+ (Python 3.13 supported)
- **Supabase Account** (free tier available)
- **Git**

### Optional for Email Notifications
- SMTP server credentials (Gmail, etc.) OR
- SendGrid API key OR
- Resend API key

### Optional for Push Notifications
- VAPID keys ([generate here](https://vapidkeys.com/))

---

## Database Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and API keys

### 2. Run Migrations

In Supabase SQL Editor, run these files in order:

```sql
-- 1. Initial schema
supabase/migrations/20240101000000_initial_schema.sql

-- 2. Row Level Security
supabase/migrations/20240101000001_row_level_security.sql

-- 3. New Features
supabase/migrations/20240103000000_add_new_features.sql
```

### 3. Enable PostGIS (if not already enabled)

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

---

## Backend Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd librework/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create `backend/.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
APP_NAME=LibreWork
APP_VERSION=2.0.0
DEBUG=True
API_V1_PREFIX=/api/v1

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# Email Configuration (Choose one provider)
EMAIL_PROVIDER=smtp  # Options: smtp, sendgrid, resend
EMAIL_FROM=noreply@librework.app
EMAIL_FROM_NAME=LibreWork

# SMTP Settings (if using smtp)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# SendGrid (if using sendgrid)
# SENDGRID_API_KEY=your-sendgrid-api-key

# Resend (if using resend)
# RESEND_API_KEY=your-resend-api-key
```

### 5. Start Backend Server

```bash
python -m app.main
```

Backend runs on `http://localhost:8000`

Check health: `http://localhost:8000/health`
API Docs: `http://localhost:8000/docs`

---

## Frontend Setup

### 1. Navigate to Frontend

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment

Create `frontend/.env.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase (for direct client queries if needed)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Push Notifications (Optional)
NEXT_PUBLIC_VAPID_PUBLIC_KEY=your-vapid-public-key
```

### 4. Start Development Server

```bash
npm run dev
```

Frontend runs on `http://localhost:3000`

---

## Feature Configuration

### 1. Email Notifications

**Using Gmail SMTP:**

1. Enable 2FA on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use this password in `SMTP_PASSWORD`

**Using SendGrid:**

1. Sign up at [sendgrid.com](https://sendgrid.com)
2. Create an API key
3. Set `EMAIL_PROVIDER=sendgrid`
4. Set `SENDGRID_API_KEY`

**Using Resend:**

1. Sign up at [resend.com](https://resend.com)
2. Create an API key
3. Set `EMAIL_PROVIDER=resend`
4. Set `RESEND_API_KEY`

### 2. Push Notifications

1. Generate VAPID keys at [vapidkeys.com](https://vapidkeys.com/)
2. Add public key to `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_VAPID_PUBLIC_KEY=your-public-key-here
   ```
3. Store private key securely for backend (for production)

### 3. Calendar Integration

No additional setup required! Uses standard iCal format.

### 4. Loyalty Program

Tiers are automatically created by the migration. Customize in:
```sql
-- Edit: supabase/migrations/20240103000000_add_new_features.sql
-- Lines: 163-167 (INSERT INTO loyalty_tiers)
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Manual Feature Testing

1. **Register a new user**
   - Email: `test@yourdomain.com` (use a real domain, not example.com)
   - Password: `Test123!`
   - Role: Customer

2. **Test Real-Time Availability**
   - Navigate to any space
   - Observe the availability indicator
   - Make a reservation
   - Indicator should update

3. **Test Favorites**
   - Click the heart icon on an establishment
   - Go to Favorites page
   - Should see the saved establishment

4. **Test Email Notifications**
   - Make a reservation
   - Check your email for confirmation
   - Cancel the reservation
   - Check email for cancellation notice

5. **Test Advanced Search**
   - Use the search filters
   - Try "Near Me" with location permission
   - Filter by services and rating

6. **Test Activity Heatmap**
   - Make several reservations
   - Navigate to Activity page
   - See your visit pattern visualized

7. **Test Loyalty Points**
   - Complete reservations
   - Check loyalty dashboard
   - Points should accumulate
   - Try redeeming points

8. **Test Push Notifications**
   - Enable push notifications
   - Send a test notification
   - Should receive browser notification

9. **Test Calendar Export**
   - Make a reservation
   - Export to calendar
   - Open in calendar app
   - Verify details are correct

10. **Test Group Reservations**
    - Create a group reservation
    - Invite friends (use real emails)
    - Accept as invited user
    - Confirm as creator

---

## Deployment

### Quick Deploy Options

#### Option 1: Replit (Easiest)
Follow [`REPLIT_DEPLOYMENT.md`](../REPLIT_DEPLOYMENT.md)

#### Option 2: Railway + Vercel

**Backend on Railway:**
```bash
cd backend
railway up
```

Set environment variables in Railway dashboard.

**Frontend on Vercel:**
```bash
cd frontend
vercel deploy
```

Set environment variables in Vercel dashboard.

#### Option 3: Docker Compose

```bash
# From project root
docker-compose up
```

---

## Post-Deployment Checklist

- [ ] Database migrations applied
- [ ] Environment variables set correctly
- [ ] Email provider configured and tested
- [ ] Push notifications enabled (HTTPS required)
- [ ] API endpoints accessible
- [ ] Frontend connects to backend
- [ ] CORS configured for production domain
- [ ] SSL/TLS enabled (required for push notifications)
- [ ] DNS configured
- [ ] Backup strategy in place

---

## Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check for port conflicts
# Windows:
netstat -ano | findstr :8000
# Mac/Linux:
lsof -i :8000
```

### Frontend Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Database Connection Issues

1. Verify Supabase project is active
2. Check URL and keys are correct
3. Ensure IP is allowed in Supabase dashboard
4. Test connection:
   ```python
   from supabase import create_client
   client = create_client("your-url", "your-key")
   print(client.table("users").select("count").execute())
   ```

### Email Not Sending

1. Check SMTP credentials
2. Test with a simple script:
   ```python
   from app.core.email import email_service
   result = email_service.send_email(
       "test@example.com",
       "Test",
       "<h1>Test Email</h1>"
   )
   print(f"Sent: {result}")
   ```
3. Check spam folder
4. Review backend logs

### Push Notifications Not Working

1. Ensure HTTPS (required)
2. Check browser permissions
3. Verify VAPID keys
4. Test service worker:
   ```javascript
   navigator.serviceWorker.getRegistration().then(reg => {
       console.log('Service Worker:', reg);
   });
   ```

---

## Performance Optimization

### Backend

1. Enable caching:
   ```python
   # Add Redis for caching
   pip install redis
   ```

2. Use connection pooling for database

3. Implement rate limiting:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

### Frontend

1. Enable Next.js image optimization
2. Implement lazy loading for components
3. Use React.memo for expensive components
4. Enable service worker caching

### Database

1. Add indexes for frequently queried fields:
   ```sql
   CREATE INDEX idx_reservations_user_start 
   ON reservations(user_id, start_time);
   ```

2. Use EXPLAIN ANALYZE for slow queries
3. Enable Supabase connection pooling

---

## Security Checklist

- [ ] Change all default secrets/keys
- [ ] Enable HTTPS in production
- [ ] Configure CORS properly
- [ ] Validate all user inputs
- [ ] Use parameterized queries (done by ORM)
- [ ] Enable RLS in Supabase
- [ ] Rate limit API endpoints
- [ ] Sanitize email templates
- [ ] Secure push subscription data
- [ ] Use environment variables (never commit secrets)
- [ ] Enable database backups
- [ ] Set up monitoring/alerting

---

## Getting Help

- **Documentation**: Check `/docs` folder
- **API Docs**: http://localhost:8000/docs
- **Feature Guide**: `docs/NEW_FEATURES.md`
- **Issues**: Open a GitHub issue

---

## Next Steps

1. ✅ Complete setup
2. ✅ Test all features
3. ✅ Deploy to production
4. 📱 Consider building mobile app
5. 🤖 Explore AI recommendations
6. 💰 Integrate payment processing
7. 📊 Advanced analytics dashboard

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**License**: MIT


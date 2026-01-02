# LibreWork - Quick Start Guide

## What You've Got

A complete reservation platform with:
- **Backend**: FastAPI (Python) with full REST API
- **Frontend**: Next.js 14 (React/TypeScript)
- **Database**: Supabase (PostgreSQL with PostGIS)
- **Features**: QR codes, credits system, geospatial search

## Prerequisites

Install these first:
1. **Node.js 18+**: https://nodejs.org/
2. **Python 3.11+**: https://www.python.org/downloads/
3. **uv** (Fast Python package manager): https://github.com/astral-sh/uv#installation
   ```bash
   # Quick install
   pip install uv
   # Or on Windows PowerShell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   # Or on macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
4. **Git**: https://git-scm.com/downloads

## Setup in 5 Minutes

### Step 1: Get Supabase Credentials

1. Go to https://supabase.com and sign up (free)
2. Create a new project
3. Go to **Settings > API** and copy:
   - Project URL
   - `anon` public key
   - `service_role` secret key

### Step 2: Set Up Database

1. Open Supabase SQL Editor
2. Copy & paste contents of `supabase/migrations/20240101000000_initial_schema.sql`
3. Execute
4. Copy & paste contents of `supabase/migrations/20240101000001_row_level_security.sql`
5. Execute
6. (Optional) Run `supabase/seed.sql` for sample data

### Step 3: Run Backend

Open terminal in project root:

```bash
# Go to backend folder
cd backend

# Create virtual environment with uv (much faster!)
uv venv

# Activate it
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Mac/Linux:
source .venv/bin/activate

# Install dependencies (lightning fast with uv!)
uv pip install -r requirements.txt

# Create .env file
copy .env.example .env   # Windows
# OR
cp .env.example .env     # Mac/Linux

# Edit .env and add your Supabase credentials:
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_KEY=eyJxxx...
# SUPABASE_SERVICE_KEY=eyJxxx...
# JWT_SECRET_KEY=make-up-a-long-random-string

# Run the server
python -m app.main
```

**Alternative: Using traditional pip**
```bash
cd backend
python -m venv venv
# Windows PowerShell: venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Step 4: Run Frontend

Open **NEW** terminal in project root:

```bash
# Go to frontend folder
cd frontend

# Install dependencies (takes 2-3 minutes)
npm install

# Create .env.local file
copy .env.local.example .env.local   # Windows
# OR
cp .env.local.example .env.local     # Mac/Linux

# Edit .env.local and add:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...

# Run the app
npm run dev
```

Frontend runs at: http://localhost:3000

## Using the App

### 1. Register an Account

1. Go to http://localhost:3000
2. Click "Sign Up"
3. Create account (you get 10 free credits!)

### 2. Browse Establishments

1. Click "Browse" or "Explore Spaces"
2. View cafes, libraries, etc.
3. Click on one to see details

### 3. Make a Reservation

1. Choose a space (table, room, desk)
2. Select date/time
3. Confirm (credits will be deducted)
4. You'll get a 6-digit validation code

### 4. As an Owner (Optional)

Register with email ending in `@owner.com` or manually change role in database:

```sql
-- In Supabase SQL Editor
UPDATE users SET role = 'owner' WHERE email = 'your@email.com';
```

Then:
1. Create your establishment
2. Add spaces (tables, rooms)
3. Generate QR codes for each space
4. Print QR codes and place on tables
5. View/manage reservations

## Testing the System

### Quick Test Flow

1. **Register** as a customer
2. **Browse** establishments (sample data from seed.sql)
3. **Reserve** a space for tomorrow
4. Check **My Reservations**
5. View your **Credits** balance

### Testing QR Code Flow

1. Go to http://localhost:8000/docs
2. Find `/api/v1/spaces/{space_id}/qr-code` endpoint
3. Try it with a space ID from seed data
4. Download the QR code image
5. Scan with your phone (should show validation URL)

## Common Issues

### Backend won't start

**Error: "ModuleNotFoundError"**
```bash
# Make sure you're in venv:
cd backend
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate

# Reinstall with uv:
uv pip install -r requirements.txt

# Or with pip:
pip install -r requirements.txt
```

**Error: "Connection refused"**
- Check your Supabase credentials in `.env`
- Make sure project is active in Supabase dashboard

### Frontend won't start

**Error: "Cannot find module"**
```bash
# Delete node_modules and reinstall:
cd frontend
rm -rf node_modules .next   # Mac/Linux
# Windows: delete node_modules and .next folders manually
npm install
```

**Error: "API calls failing"**
- Make sure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

### Database errors

**Error: "relation does not exist"**
- You didn't run the migration SQL files
- Go back to Step 2 and run them in Supabase SQL Editor

## Project Structure

```
librework/
├── backend/              ← FastAPI backend
│   ├── app/
│   │   ├── api/v1/      ← All API endpoints
│   │   ├── core/        ← Config & auth
│   │   └── main.py      ← Start here
│   └── requirements.txt
├── frontend/             ← Next.js frontend
│   ├── src/
│   │   ├── app/         ← Pages (routes)
│   │   ├── components/  ← React components
│   │   └── lib/         ← API client
│   └── package.json
├── supabase/            ← Database
│   └── migrations/      ← SQL files
└── docs/                ← Documentation
```

## Next Steps

### Learn the System

1. **Read** `ARCHITECTURE.md` for system design
2. **Browse** `docs/API.md` for API reference
3. **Explore** code starting from:
   - Backend: `backend/app/main.py`
   - Frontend: `frontend/src/app/page.tsx`

### Customize

1. Change colors in `frontend/tailwind.config.ts`
2. Modify credit costs in `backend/app/core/config.py`
3. Add new features to API endpoints

### Deploy

See `docs/DEPLOYMENT.md` for:
- Railway (backend)
- Vercel (frontend)
- Production configuration

## Getting Help

1. Check error message first
2. Look in relevant file/folder
3. Search in `docs/` folder
4. Check `ARCHITECTURE.md`
5. Review API docs at http://localhost:8000/docs

## Development Tips

### Hot Reload

Both frontend and backend auto-reload on file changes:
- **Backend**: uvicorn `--reload` flag
- **Frontend**: Next.js dev server

### Testing API

Use the interactive docs:
1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Login to get token
4. Paste token
5. Test any endpoint

### Viewing Database

Use Supabase Table Editor:
1. Go to your Supabase project
2. Click "Table Editor"
3. Browse all tables
4. Edit data directly

## Sample Credentials

If you ran `seed.sql`, there are sample establishments with IDs:
- Café Central: `11111111-1111-1111-1111-111111111111`
- Bibliothèque Moderne: `22222222-2222-2222-2222-222222222222`
- WorkHub Coworking: `33333333-3333-3333-3333-333333333333`

Note: You still need to create user accounts through registration.

## Clean Restart

If things get messy:

```bash
# Backend
cd backend
deactivate  # exit venv
rm -rf .venv venv __pycache__  # delete venv
uv venv  # recreate with uv
# Then follow Step 3 again

# Frontend
cd frontend
rm -rf node_modules .next  # delete node_modules
npm install  # reinstall
# Then follow Step 4 again
```

## Success Indicators

You're all set when:
- ✅ Backend responds at http://localhost:8000/health
- ✅ API docs load at http://localhost:8000/docs
- ✅ Frontend loads at http://localhost:3000
- ✅ You can register and login
- ✅ You can see establishments list

Enjoy building with LibreWork! 🚀


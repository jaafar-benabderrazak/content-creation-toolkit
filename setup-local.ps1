# LibreWork - Quick Local Test

Write-Host ""
Write-Host "LibreWork - Local Test Setup" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  OK Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Step 1: Backend Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Backend setup
Write-Host ""
Write-Host "Setting up backend virtual environment..." -ForegroundColor Yellow
Set-Location backend

if (!(Test-Path "venv")) {
    python -m venv venv
    Write-Host "  OK Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  OK Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet --disable-pip-version-check
Write-Host "  OK Python dependencies installed" -ForegroundColor Green

# Check .env file
Write-Host "Checking environment variables..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "  WARNING .env file not found!" -ForegroundColor Red
    Write-Host "  Please copy .env.example to .env and fill in your Supabase credentials" -ForegroundColor Yellow
    Set-Location ..
    exit 1
} else {
    Write-Host "  OK .env file exists" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Step 2: Frontend Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Frontend setup
Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend

if (!(Test-Path "node_modules")) {
    npm install --legacy-peer-deps --silent
    Write-Host "  OK Node.js dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  OK Node.js dependencies already installed" -ForegroundColor Green
}

# Check .env.local file
Write-Host "Checking frontend environment variables..." -ForegroundColor Yellow
if (!(Test-Path ".env.local")) {
    Write-Host "  WARNING .env.local file not found!" -ForegroundColor Red
    Write-Host "  Please copy .env.local.example to .env.local and fill in your configuration" -ForegroundColor Yellow
    Set-Location ..
    exit 1
} else {
    Write-Host "  OK .env.local file exists" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Make sure your database schema is set up in Supabase:" -ForegroundColor White
Write-Host "   -> Run database_schema_replit.sql in Supabase SQL Editor" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the backend (in a new terminal):" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   python -m app.main" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the frontend (in another new terminal):" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Open your browser:" -ForegroundColor White
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Backend API docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Register your first user and start testing!" -ForegroundColor White
Write-Host ""
Write-Host "For deployment to Replit, see: REPLIT_DEPLOYMENT.md" -ForegroundColor Yellow
Write-Host ""


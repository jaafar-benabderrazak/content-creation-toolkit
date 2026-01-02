# LibreWork v2.0 Installation Script (Windows)
# This script helps set up all the new features

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🚀 LibreWork v2.0 Installation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 3 is not installed" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version
    Write-Host "✓ npm installed: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm is not installed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🔧 Setting up Backend" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Backend setup
Set-Location backend

# Create virtual environment
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if (!(Test-Path .env)) {
    Write-Host "⚠️  No .env file found in backend\" -ForegroundColor Yellow
    Write-Host "Creating .env from example..." -ForegroundColor Yellow
    
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "✓ Created .env file" -ForegroundColor Green
        Write-Host "⚠️  Please edit backend\.env with your Supabase credentials" -ForegroundColor Yellow
    } else {
        Write-Host "❌ No .env.example file found" -ForegroundColor Red
        Write-Host "Please create backend\.env manually"
    }
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🎨 Setting up Frontend" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Frontend setup
Set-Location frontend

# Install dependencies
Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

# Check for .env.local file
if (!(Test-Path .env.local)) {
    Write-Host "⚠️  No .env.local file found in frontend\" -ForegroundColor Yellow
    Write-Host "Creating .env.local from example..." -ForegroundColor Yellow
    
    if (Test-Path .env.local.example) {
        Copy-Item .env.local.example .env.local
        Write-Host "✓ Created .env.local file" -ForegroundColor Green
        Write-Host "⚠️  Please edit frontend\.env.local with your configuration" -ForegroundColor Yellow
    } else {
        Write-Host "❌ No .env.local.example file found" -ForegroundColor Red
        Write-Host "Please create frontend\.env.local manually"
    }
} else {
    Write-Host "✓ .env.local file exists" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 🗄️  Set up your Supabase database:" -ForegroundColor White
Write-Host "   - Go to https://supabase.com"
Write-Host "   - Create a new project"
Write-Host "   - Run the migrations in SQL Editor:"
Write-Host "     • supabase\migrations\20240101000000_initial_schema.sql"
Write-Host "     • supabase\migrations\20240101000001_row_level_security.sql"
Write-Host "     • supabase\migrations\20240103000000_add_new_features.sql"
Write-Host ""
Write-Host "2. ⚙️  Configure your environment:" -ForegroundColor White
Write-Host "   - Edit backend\.env with your Supabase credentials"
Write-Host "   - Edit frontend\.env.local with your API URL"
Write-Host ""
Write-Host "3. 📧 Configure email provider (optional but recommended):" -ForegroundColor White
Write-Host "   - Set EMAIL_PROVIDER in backend\.env"
Write-Host "   - Add SMTP/SendGrid/Resend credentials"
Write-Host ""
Write-Host "4. 🔔 Generate VAPID keys for push notifications (optional):" -ForegroundColor White
Write-Host "   - Visit https://vapidkeys.com/"
Write-Host "   - Add public key to frontend\.env.local"
Write-Host ""
Write-Host "5. 🚀 Start the development servers:" -ForegroundColor White
Write-Host ""
Write-Host "   Terminal 1 (Backend):" -ForegroundColor Cyan
Write-Host "   PS> cd backend"
Write-Host "   PS> .\venv\Scripts\Activate.ps1"
Write-Host "   PS> python -m app.main"
Write-Host ""
Write-Host "   Terminal 2 (Frontend):" -ForegroundColor Cyan
Write-Host "   PS> cd frontend"
Write-Host "   PS> npm run dev"
Write-Host ""
Write-Host "6. 🌐 Open your browser:" -ForegroundColor White
Write-Host "   - Frontend: http://localhost:3000"
Write-Host "   - Backend API: http://localhost:8000"
Write-Host "   - API Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "- Setup Guide: SETUP_GUIDE.md"
Write-Host "- Feature Guide: docs\NEW_FEATURES.md"
Write-Host "- Feature Summary: FEATURE_SUMMARY.md"
Write-Host "- Main README: README.md"
Write-Host ""
Write-Host "Happy coding! 🎉" -ForegroundColor Green
Write-Host ""


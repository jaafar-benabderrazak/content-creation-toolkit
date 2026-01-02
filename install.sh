#!/bin/bash

# LibreWork v2.0 Installation Script
# This script helps set up all the new features

set -e

echo "========================================="
echo "🚀 LibreWork v2.0 Installation"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 installed${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js installed${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm installed${NC}"

echo ""
echo "========================================="
echo "🔧 Setting up Backend"
echo "========================================="

# Backend setup
cd backend

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found in backend/${NC}"
    echo "Creating .env from example..."
    
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  Please edit backend/.env with your Supabase credentials${NC}"
    else
        echo -e "${RED}❌ No .env.example file found${NC}"
        echo "Please create backend/.env manually"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

cd ..

echo ""
echo "========================================="
echo "🎨 Setting up Frontend"
echo "========================================="

# Frontend setup
cd frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

# Check for .env.local file
if [ ! -f .env.local ]; then
    echo -e "${YELLOW}⚠️  No .env.local file found in frontend/${NC}"
    echo "Creating .env.local from example..."
    
    if [ -f .env.local.example ]; then
        cp .env.local.example .env.local
        echo -e "${GREEN}✓ Created .env.local file${NC}"
        echo -e "${YELLOW}⚠️  Please edit frontend/.env.local with your configuration${NC}"
    else
        echo -e "${RED}❌ No .env.local.example file found${NC}"
        echo "Please create frontend/.env.local manually"
    fi
else
    echo -e "${GREEN}✓ .env.local file exists${NC}"
fi

cd ..

echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. 🗄️  Set up your Supabase database:"
echo "   - Go to https://supabase.com"
echo "   - Create a new project"
echo "   - Run the migrations in SQL Editor:"
echo "     • supabase/migrations/20240101000000_initial_schema.sql"
echo "     • supabase/migrations/20240101000001_row_level_security.sql"
echo "     • supabase/migrations/20240103000000_add_new_features.sql"
echo ""
echo "2. ⚙️  Configure your environment:"
echo "   - Edit backend/.env with your Supabase credentials"
echo "   - Edit frontend/.env.local with your API URL"
echo ""
echo "3. 📧 Configure email provider (optional but recommended):"
echo "   - Set EMAIL_PROVIDER in backend/.env"
echo "   - Add SMTP/SendGrid/Resend credentials"
echo ""
echo "4. 🔔 Generate VAPID keys for push notifications (optional):"
echo "   - Visit https://vapidkeys.com/"
echo "   - Add public key to frontend/.env.local"
echo ""
echo "5. 🚀 Start the development servers:"
echo ""
echo "   Terminal 1 (Backend):"
echo "   $ cd backend"
echo "   $ source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo "   $ python -m app.main"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   $ cd frontend"
echo "   $ npm run dev"
echo ""
echo "6. 🌐 Open your browser:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "========================================="
echo "📚 Documentation:"
echo "========================================="
echo "- Setup Guide: SETUP_GUIDE.md"
echo "- Feature Guide: docs/NEW_FEATURES.md"
echo "- Feature Summary: FEATURE_SUMMARY.md"
echo "- Main README: README.md"
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"
echo ""


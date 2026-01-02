#!/bin/bash

echo ""
echo "🚀 LibreWork - Local Test Setup"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "  ${GREEN}✓ $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "  ${GREEN}✓ $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "  ${RED}✗ Python not found. Please install Python 3.11+${NC}"
    exit 1
fi

# Check Node.js
echo -e "${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "  ${GREEN}✓ Node.js $NODE_VERSION${NC}"
else
    echo -e "  ${RED}✗ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Step 1: Backend Setup${NC}"
echo -e "${CYAN}============================================${NC}"

# Backend setup
echo ""
echo -e "${YELLOW}Setting up backend virtual environment...${NC}"
cd backend

if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo -e "  ${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "  ${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet --disable-pip-version-check
echo -e "  ${GREEN}✓ Python dependencies installed${NC}"

# Check .env file
echo -e "${YELLOW}Checking environment variables...${NC}"
if [ ! -f ".env" ]; then
    echo -e "  ${RED}⚠ .env file not found!${NC}"
    echo -e "  ${YELLOW}Please copy .env.example to .env and fill in your Supabase credentials${NC}"
    cd ..
    exit 1
else
    echo -e "  ${GREEN}✓ .env file exists${NC}"
fi

cd ..

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Step 2: Frontend Setup${NC}"
echo -e "${CYAN}============================================${NC}"

# Frontend setup
echo ""
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    npm install --legacy-peer-deps --silent
    echo -e "  ${GREEN}✓ Node.js dependencies installed${NC}"
else
    echo -e "  ${GREEN}✓ Node.js dependencies already installed${NC}"
fi

# Check .env.local file
echo -e "${YELLOW}Checking frontend environment variables...${NC}"
if [ ! -f ".env.local" ]; then
    echo -e "  ${RED}⚠ .env.local file not found!${NC}"
    echo -e "  ${YELLOW}Please copy .env.local.example to .env.local and fill in your configuration${NC}"
    cd ..
    exit 1
else
    echo -e "  ${GREEN}✓ .env.local file exists${NC}"
fi

cd ..

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  ✅ Setup Complete!${NC}"
echo -e "${CYAN}============================================${NC}"

echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo -e "${NC}1. Make sure your database schema is set up in Supabase:${NC}"
echo -e "   ${CYAN}→ Run database_schema_replit.sql in Supabase SQL Editor${NC}"
echo ""
echo -e "${NC}2. Start the backend (in a new terminal):${NC}"
echo -e "   cd backend"
echo -e "   source venv/bin/activate"
echo -e "   python -m app.main"
echo ""
echo -e "${NC}3. Start the frontend (in another new terminal):${NC}"
echo -e "   cd frontend"
echo -e "   npm run dev"
echo ""
echo -e "${NC}4. Open your browser:${NC}"
echo -e "   ${CYAN}Frontend: http://localhost:3000${NC}"
echo -e "   ${CYAN}Backend API docs: http://localhost:8000/docs${NC}"
echo ""
echo -e "${NC}5. Register your first user and start testing! 🎉${NC}"
echo ""
echo -e "${YELLOW}For deployment to Replit, see: REPLIT_DEPLOYMENT.md${NC}"
echo ""


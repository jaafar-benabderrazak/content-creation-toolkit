#!/bin/bash

echo "🚀 Starting LibreWork Application..."

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt --quiet

# Start backend in background
echo "🔧 Starting Backend API..."
python -m app.main &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend..."
sleep 5

# Install frontend dependencies
echo "📦 Installing Node.js dependencies..."
cd ../frontend
npm install --legacy-peer-deps --quiet

# Build and start frontend
echo "🎨 Building Frontend..."
npm run build

echo "🌐 Starting Frontend..."
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ LibreWork is running!"
echo "   Backend:  http://0.0.0.0:8000"
echo "   Frontend: http://0.0.0.0:3000"
echo ""

# Keep script running
wait $BACKEND_PID $FRONTEND_PID


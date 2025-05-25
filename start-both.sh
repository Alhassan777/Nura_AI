#!/bin/bash

# Start Both Frontend and Backend Services
echo "🚀 Starting Nura Full Stack Application..."

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Get the current directory to ensure we can return to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start backend in background
echo "🔧 Starting Backend Services..."
(cd "$SCRIPT_DIR/backend" && ./start-backend.sh) &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "🌐 Starting Frontend..."
(cd "$SCRIPT_DIR/frontend" && ./start-frontend.sh) &
FRONTEND_PID=$!

echo ""
echo "✅ Both services are starting..."
echo "📍 Backend: http://localhost:8000"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Test Chat: http://localhost:3000/test-chat"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 
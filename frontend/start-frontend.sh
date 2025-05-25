#!/bin/bash

# Start Nura Frontend
echo "🚀 Starting Nura Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Load environment variables from .env.local if it exists
if [ -f ".env.local" ]; then
    echo "📄 Loading environment variables from .env.local..."
fi

# Start the Next.js development server
echo "🌐 Starting Next.js development server on port 3000..."
echo "📍 Frontend: http://localhost:3000"
echo "📍 Test Chat: http://localhost:3000/test-chat"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev

echo "�� Frontend started!" 
#!/bin/bash

# Start Nura Backend Services
echo "🚀 Starting Nura Backend Services..."

# Navigate to backend directory
cd "$(dirname "$0")"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "📦 Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

echo "✅ Redis is running"

# Check if Python virtual environment exists
if [ ! -d "myenv" ]; then
    echo "❌ Virtual environment 'myenv' not found!"
    echo "Please run: python -m venv myenv && source myenv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source myenv/bin/activate

# Check if required environment variables are set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  GOOGLE_API_KEY not set. Please set it in your .env file or environment."
    echo "You can get one from: https://ai.google.dev/"
fi

if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "⚠️  GOOGLE_CLOUD_PROJECT not set. Please set it in your .env file or environment."
fi

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the memory service
echo "🧠 Starting Memory Service on port ${MEMORY_SERVICE_PORT:-8000}..."
echo "📍 Health check: http://localhost:${MEMORY_SERVICE_PORT:-8000}/health"
echo "📍 API docs: http://localhost:${MEMORY_SERVICE_PORT:-8000}/docs"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

python -m uvicorn services.memory.api:app --host ${MEMORY_SERVICE_HOST:-0.0.0.0} --port ${MEMORY_SERVICE_PORT:-8000} --reload

echo "🎉 Backend Services started!" 
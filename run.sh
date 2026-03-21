#!/bin/bash
# Start both backend and frontend

echo "🚀 Starting Resume Analyzer..."
echo ""

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Edit .env to add your AI provider API key, then re-run."
    exit 1
fi

# Start FastAPI backend in background
echo "🔧 Starting FastAPI backend on port 8000..."
python -m uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

sleep 2

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend on port 8501..."
streamlit run frontend/app.py --server.port 8501

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT

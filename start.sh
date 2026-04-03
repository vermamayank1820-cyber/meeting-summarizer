#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Meeting Summarizer — Start Script
# Launches both the FastAPI backend and React UI in parallel
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "═══════════════════════════════════════════════════"
echo "   🎙️  Meeting Summarizer — Starting..."
echo "═══════════════════════════════════════════════════"
echo ""

# Check .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env and add your API key, then re-run this script."
    exit 1
fi

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Start FastAPI backend
echo "▶ Starting FastAPI backend (port 8000)..."
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "  PID: $API_PID"

# Wait a moment for API to start
sleep 2

# Check Node.js + frontend deps
if ! command -v npm &>/dev/null; then
    echo "❌ npm not found. Install Node.js 18+ to run the React frontend."
    kill $API_PID 2>/dev/null
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies are missing."
    echo "   Run: cd frontend && npm install"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start React UI
echo "▶ Starting React UI (port 5173)..."
cd "$SCRIPT_DIR/frontend"
npm run dev -- --host 0.0.0.0 &
UI_PID=$!
cd "$SCRIPT_DIR"
echo "  PID: $UI_PID"

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ System is running!"
echo ""
echo "  📱 UI:  http://localhost:5173"
echo "  🔌 API: http://localhost:8000"
echo "  📚 Docs: http://localhost:8000/docs"
echo ""
echo "  📂 Drop recordings into: ./recordings/"
echo "     (auto-processed in real time)"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "═══════════════════════════════════════════════════"
echo ""

# Wait and handle Ctrl+C
trap 'echo ""; echo "Stopping..."; kill $API_PID $UI_PID 2>/dev/null; echo "Stopped."; exit 0' INT TERM

wait

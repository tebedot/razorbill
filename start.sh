#!/bin/bash

# ==========================================
# RAZOR BILL - MASTER START SCRIPT
# ==========================================

echo "Initializing Razor Bill Ecosystem..."

# Function to cleanly kill all background processes on exit
cleanup() {
    echo ""
    echo "Shutting down all Razor Bill subsystems..."
    kill $(jobs -p) 2>/dev/null
    echo "Shutdown complete. Goodbye, Sir."
    exit
}

# Catch termination signals to run cleanup
trap cleanup EXIT

echo ""
echo "========================================================"
echo " 🌐 DASHBOARD: Open http://localhost:5173 in browser"
echo "========================================================"
echo ""

# 1. Start Frontend (Vite)
echo "[1/3] Starting Frontend UI (Vite)..."
cd frontend || exit
npm run dev > /dev/null 2>&1 &
cd ..

# 2. Start Backend API (Uvicorn)
echo "[2/3] Starting Backend API (Uvicorn on Port 8001)..."
cd backend || exit
source venv/bin/activate
uvicorn main:app --port 8001 > /dev/null 2>&1 &

# 3. Start Audio Engine (wake_word.py)
echo "[3/3] Starting Audio Engine & WebSockets (Port 8000)..."
# We run this in the foreground so the user can see the STT/TTS logs and Wake Word detection
python wake_word.py

# Wait for all background processes (only reached if wake_word.py crashes/exits)
wait

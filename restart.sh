#!/bin/bash

echo "Killing existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

echo "Ports cleared!"
echo ""
echo "Starting backend..."
cd /home/tunghv/Desktop/Dashboard/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

echo "Starting frontend..."
cd /home/tunghv/Desktop/Dashboard/frontend
npm run dev &

echo ""
echo "Services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"

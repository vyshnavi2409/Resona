#!/bin/bash

# Start FastAPI backend in the background on internal port 8000
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
cd ..

# Start Streamlit frontend in the foreground
cd frontend
export PORT="${PORT:-8501}"

echo "Waiting for backend to be ready..."
while ! python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" 2>/dev/null; do
    sleep 1
done
echo "Backend is up!"

streamlit run app.py --server.port $PORT --server.address 0.0.0.0

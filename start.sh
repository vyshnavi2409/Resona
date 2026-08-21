#!/bin/bash

# Start FastAPI backend in the background on internal port 8000
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
cd ..

# Start Streamlit frontend in the foreground
cd frontend
# Use the PORT provided by Render, or default to 8501 locally
export PORT="${PORT:-8501}"
streamlit run app.py --server.port $PORT --server.address 0.0.0.0

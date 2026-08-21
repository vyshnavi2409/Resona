FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install uv

# Copy requirements
COPY backend/requirements.txt backend_reqs.txt
COPY frontend/requirements.txt frontend_reqs.txt

# Install PyTorch CPU and all dependencies
RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system --no-cache -r backend_reqs.txt
RUN uv pip install --system --no-cache -r frontend_reqs.txt

# Copy all source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY start.sh .

# Make the start script executable
RUN chmod +x start.sh

# Start the services
CMD ["./start.sh"]

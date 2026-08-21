FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for some document loaders
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install uv for extremely fast dependency resolution
RUN pip install uv

# Install CPU-only version of torch to prevent massive NVIDIA CUDA downloads
RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

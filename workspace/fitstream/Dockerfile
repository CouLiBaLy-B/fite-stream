# =============================================================
# FitStream Dockerfile
# Multi-stage build optimized for NVIDIA GPU inference
# =============================================================

# Stage 1: Base with CUDA
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-venv python3-pip \
    ffmpeg libsm6 libxext6 libgl1-mesa-glx \
    git wget curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

WORKDIR /app

# Stage 2: Dependencies
FROM base AS deps

# Install PyTorch with CUDA 12.4
RUN pip install --no-cache-dir \
    torch==2.5.1 torchvision==0.20.1 \
    --index-url https://download.pytorch.org/whl/cu124

# Copy and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Stage 3: Application
FROM deps AS app

# Copy application code
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Create directories
RUN mkdir -p models outputs uploads jobs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run API server
CMD ["python", "-m", "fitstream.api.server"]

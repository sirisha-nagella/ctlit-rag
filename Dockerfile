# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# System deps some Python packages (torch, chromadb) need to build/run cleanly
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install deps first so this layer is cached unless requirements.txt changes
COPY requirements.txt .
# Fargate has no GPU: install the CPU-only torch build first (the default CUDA
# wheel is ~2GB of libraries that would never run here). 2.12.0+cpu satisfies
# the `torch==2.12.0` pin in requirements.txt, so the next step won't re-fetch it.
RUN pip install --no-cache-dir torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Now bring in only what the running app needs (rest excluded via .dockerignore)
COPY app.py .
COPY scripts/ ./scripts/
COPY rag/ ./rag/
COPY chroma_store/ ./chroma_store/

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

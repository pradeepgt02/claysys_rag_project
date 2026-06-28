FROM python:3.11-slim

# Set up non-root user for Hugging Face Spaces
RUN useradd -m -u 1000 user

WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and system dependencies
RUN playwright install --with-deps chromium

# Copy the entire repository
COPY --chown=user:user . .

# Ensure data directory exists and has correct permissions
RUN mkdir -p backend/data/indexes && chown -R user:user backend/data

# Switch to the non-root user
USER user

WORKDIR /app/backend

# The PORT environment variable is set by Hugging Face
ENV HOST=0.0.0.0

CMD ["sh", "-c", "uvicorn app.main:app --host $HOST --port $PORT"]
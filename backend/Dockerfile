FROM python:3.10-slim

# Set up non-root user for Hugging Face Spaces
RUN useradd -m -u 1000 user

# Set working directory
WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and its system dependencies (needs to run as root)
RUN playwright install --with-deps chromium

# Copy the rest of the application code
COPY --chown=user:user . .

# Ensure data directory exists and has correct permissions
RUN mkdir -p data/indexes && chown -R user:user data

# Switch to the non-root user
USER user

# Set environment variables for Hugging Face Spaces
ENV PORT=7860
ENV HOST=0.0.0.0

# Expose port
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]

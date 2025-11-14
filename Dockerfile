# Dockerfile for HF Spaces deployment
# Optimized for production FastAPI deployment with ML model

# Use Python 3.11 slim for smaller image size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for some Python packages
# - gcc, g++: For compiling some Python packages
# - libgomp1: Required for XGBoost
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
# (dependencies change less frequently than code)
COPY requirements-prod.txt .

# Install Python dependencies
# --no-cache-dir: Don't cache pip packages (saves space)
# --upgrade: Ensure pip is up to date
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy application source code
COPY src/ ./src/

# Copy trained model artifacts
COPY model/ ./model/

# Copy README for HF Spaces description (optional)
COPY README.md .

# Create non-root user for security (optional but recommended)
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app

# Switch to non-root user
USER apiuser

# Expose port 7860 (HF Spaces standard port)
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

# Health check (optional - helps HF Spaces monitor the app)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/health')" || exit 1

# Run the FastAPI application with uvicorn
# --host 0.0.0.0: Listen on all network interfaces
# --port 7860: HF Spaces standard port
# --workers 1: Single worker (HF Spaces handles scaling)
CMD ["uvicorn", "src.oc5_ml_deployment.api.main:app", "--host", "0.0.0.0", "--port", "7860"]

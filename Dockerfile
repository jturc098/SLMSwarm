FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (including all subdirectories)
COPY src/ ./src/

# Verify all modules copied
RUN ls -la /app/src/ && \
    ls -la /app/src/memory/ && \
    ls -la /app/src/monitoring/

# Create necessary directories
RUN mkdir -p /app/specs /app/memory /app/logs /app/.hydra

# Expose ports
EXPOSE 8090 8091

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Run the application
CMD ["python", "src/hydra_control.py", "--serve"]
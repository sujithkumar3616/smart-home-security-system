# Secure, multi-stage / non-root Dockerfile for IoT Smart Home Security System
FROM python:3.11-slim

# Set environment variables for security and Python optimizations
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_ENV=production

# Set working directory
WORKDIR /app

# Install system dependencies required for compilation and curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create dedicated non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy application source code
COPY . .

# Initialize development database and set ownership to non-root user
RUN python seed.py && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose internal port
EXPOSE 5000

# Health check configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:5000/login || exit 1

# Entrypoint execution
CMD ["python", "run.py"]

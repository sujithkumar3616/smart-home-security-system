# Secure, lightweight Dockerfile for IoT Smart Home Security System
FROM python:3.11-slim

# Python and application settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_ENV=production

# Application directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create dedicated non-root user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy application
COPY . .

# Initialize database and give ownership to non-root user
RUN python seed.py && \
    chown -R appuser:appgroup /app

# Run as non-root user
USER appuser

# Application port
EXPOSE 5000

# Health check without installing curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/login', timeout=3)" || exit 1

# Start application
CMD ["python", "run.py"]
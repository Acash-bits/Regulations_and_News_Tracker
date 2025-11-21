# ===================================================================
# Dockerfile for Automated News Fetcher
# ===================================================================
# Multi-stage build for optimized image size
# ===================================================================

FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ===================================================================
# Final stage
# ===================================================================
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY news_fetcher.py .
COPY config_template.py config.py

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 newsuser && \
    chown -R newsuser:newsuser /app

# Switch to non-root user
USER newsuser

# Health check
HEALTHCHECK --interval=5m --timeout=3s \
    CMD python -c "import mysql.connector; mysql.connector.connect(host='mysql')" || exit 1

# Default command
CMD ["python", "news_fetcher.py"]
FROM python:3.12-slim

WORKDIR /app

# Update apt and install minimal system dependencies for Playwright
# Only installing essential packages - removed packages that don't exist in slim image
RUN apt-get update --fix-missing -qq \
    && apt-get install -y --no-install-recommends -qq \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxrender1 \
    libxshmfence1 \
    libxss1 \
    libxtst6 \
    libnss3 \
    libnspr4 \
    libxkbcommon0 \
    libasound2 \
    xdg-utils \
    ca-certificates \
    && apt-get clean -qq \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -q -r requirements.txt

# Install Playwright browsers (chromium only - lightweight)
RUN playwright install chromium

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs data

# Expose API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV PLAYWRIGHT_HEADLESS=True

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

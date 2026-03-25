FROM python:3.12-slim

WORKDIR /app

# Set python path
ENV PYTHONPATH=/app

# Install dependencies first (cache optimization)
COPY conversion_workers/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY conversion_workers/ ./conversion_workers
COPY common_logging/ ./common_logging
COPY shared_database/ ./shared_database

# Optional system deps (if needed)
# RUN apt-get update && apt-get install -y libreoffice poppler-utils && rm -rf /var/lib/apt/lists/*

CMD ["python3", "-m", "conversion_workers.main"]
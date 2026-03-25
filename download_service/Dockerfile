FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Install Python deps
COPY download_service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY download_service/ ./download_service
COPY common_logging/ ./common_logging
COPY shared_database/ ./shared_database

CMD ["uvicorn", "download_service.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]

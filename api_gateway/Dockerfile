FROM python:3.12-slim

WORKDIR /app

COPY api_gateway/ ./api_gateway
COPY common_logging/ ./common_logging

COPY api_gateway/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
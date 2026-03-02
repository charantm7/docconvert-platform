FROM python:3.12-slim

WORKDIR /app

COPY api_provider/ ./api_provider
COPY common_logging/ ./common_logging
COPY shared_database/ ./shared_database

COPY api_provider/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "api_provider.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
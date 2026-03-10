FROM python:3.12-slim


WORKDIR /app

COPY upload_service/ ./upload_service
COPY common_logging/ ./common_logging
COPY shared_database/ ./shared_database

COPY upload_service/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "upload_service.run:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
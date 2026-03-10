FROM python:3.12-slim

WORKDIR /app

COPY shared_database/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY shared_database/ ./shared_database
COPY common_logging/ ./common_logging

CMD ["alembic", "upgrade", "head"]
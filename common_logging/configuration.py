import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
from pythonjsonlogger.json import JsonFormatter
from common_logging.request_context import request_id_ctx


LOG_DIR = Path("/var/log/docconversion")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class ContexFilter(logging.Filter):

    "It ensures all log records contains the required structured field"

    def __init__(self, service_name: str, environment: str):
        super().__init__()
        self.service_name = service_name
        self.environmnet = environment


    def filter(self, record):
        record.service = self.service_name
        record.environment = self.environmnet
        record.request_id = request_id_ctx.get()
        
        record.job_id = getattr(record, "job_id", None )
        record.stage = getattr(record, "stage", None)

        if not hasattr(record, "stage"):
            record.stage = None

        return True


def setup_logging(service_name: str):
    environment = os.getenv("ENVIRONMENT", "development")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.handlers.clear()

    # JSON FORMATER

    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(service)s %(environment)s "
        "%(request_id)s %(job_id)s %(stage)s %(message)s "
    )

    # File Handler
    file_handler = RotatingFileHandler(
        LOG_DIR / f"{service_name}.log",
        maxBytes= 10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Error File Handler
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes= 10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # add context filter
    context_filter = ContexFilter(service_name, environment)

    file_handler.addFilter(context_filter)
    error_handler.addFilter(context_filter)
    console_handler.addFilter(context_filter)

    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


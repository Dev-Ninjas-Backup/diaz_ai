import logging
import os
from datetime import datetime

from app.config import configs



log_dir = configs["logger"]["log_dir"]

## Make dir
os.makedirs(log_dir, exist_ok=True)

## Log file name
LOG_FILE_NAME = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name : str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logging.basicConfig(
            filename=LOG_FILE_NAME,
            format=LOG_FORMAT,
            datefmt=DATE_FORMAT,
            level=logging.INFO
        )

    return logger

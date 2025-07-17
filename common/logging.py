import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from atlas_schemas.config import settings

LOG_FILE: Path = settings.LOG_FILE
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

logger = logging.getLogger("ModelAtlas")

if not logger.handlers:
    logger.setLevel(logging.INFO)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

import logging
import logging.handlers
import sys
from config import LOGGING_CONFIG

def setup_logger():
    logger = logging.getLogger("zhaba")
    logger.setLevel(getattr(logging, LOGGING_CONFIG["log_level"]))

    formatter = logging.Formatter(
        LOGGING_CONFIG["format"],
        datefmt=LOGGING_CONFIG["date_format"]
    )

    file_handler = logging.handlers.RotatingFileHandler(
        LOGGING_CONFIG["log_file"],
        maxBytes=LOGGING_CONFIG["max_bytes"],
        backupCount=LOGGING_CONFIG["backup_count"],
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    error_handler = logging.handlers.RotatingFileHandler(
        "error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger

logger = setup_logger()

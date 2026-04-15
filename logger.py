import logging
from logging.handlers import RotatingFileHandler
import os
from config import LOGGING_CONFIG

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOGGING_CONFIG['log_level']))
    
    formatter = logging.Formatter(
        LOGGING_CONFIG['format'],
        datefmt=LOGGING_CONFIG['date_format']
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if LOGGING_CONFIG['log_file']:
        try:
            file_handler = RotatingFileHandler(
                LOGGING_CONFIG['log_file'],
                maxBytes=LOGGING_CONFIG['max_bytes'],
                backupCount=LOGGING_CONFIG['backup_count'],
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Не удалось создать файл лога: {e}")
    
    return logger

logger = setup_logger()

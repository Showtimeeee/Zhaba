import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'email_from': os.getenv('EMAIL_FROM'),
    'email_password': os.getenv('EMAIL_PASSWORD'),
    'email_to': os.getenv('EMAIL_TO'),
}

WEBSOCKET_CONFIG = {
    'host': os.getenv('WS_HOST', 'localhost'),
    'port': int(os.getenv('WS_PORT', 8765)),
    'max_connections': int(os.getenv('WS_MAX_CONNECTIONS', 100)),
}

APP_CONFIG = {
    'debug': os.getenv('DEBUG', 'true').lower() == 'true',
    'max_message_size': int(os.getenv('MAX_MESSAGE_SIZE', 1024)),
}

LOGGING_CONFIG = {
    'log_file': os.getenv('LOG_FILE', 'zhaba.log'),
    'log_level': os.getenv('LOG_LEVEL', 'DEBUG'),
    'max_bytes': int(os.getenv('LOG_MAX_BYTES', 10485760)),
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

import json
import logging
from datetime import datetime
from pathlib import Path


class LoggingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger("zhaba")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler with rotation
        log_file = Path("zhaba.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, component: str, message: str, context: dict = None):
        self._log("INFO", component, message, context)

    def debug(self, component: str, message: str, context: dict = None):
        self._log("DEBUG", component, message, context)

    def warning(self, component: str, message: str, context: dict = None):
        self._log("WARNING", component, message, context)

    def error(self, component: str, message: str, context: dict = None):
        self._log("ERROR", component, message, context)

    def critical(self, component: str, message: str, context: dict = None):
        self._log("ERROR", component, message, {"CRITICAL": True, **(context or {})})

    def _log(self, level: str, event_type: str, message: str, context: dict = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "event_type": event_type,
            "message": message,
            "context": context or {}
        }
        
        log_message = f"[{event_type}] {message}"
        if context:
            log_message += f" | Context: {json.dumps(context, ensure_ascii=False)}"
        
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)

    # Connection events
    def client_connected(self, client_id: str, ip: str):
        self._log("INFO", "CONNECTION", f"Client connected", {"client_id": client_id, "ip": ip})

    def client_disconnected(self, client_id: str, reason: str = ""):
        self._log("INFO", "CONNECTION", f"Client disconnected", {"client_id": client_id, "reason": reason})

    def connection_limit_reached(self, client_id: str):
        self._log("WARNING", "CONNECTION", "Connection limit reached", {"client_id": client_id})

    def auth_failed(self, client_id: str, reason: str = ""):
        self._log("WARNING", "AUTH", "Authentication failed", {"client_id": client_id, "reason": reason})

    # Message events
    def message_received(self, client_id: str, message_id: int, subject: str = ""):
        self._log("DEBUG", "MESSAGE", f"Message received", {"client_id": client_id, "message_id": message_id, "subject": subject})

    def message_processed(self, client_id: str, message_id: int, status: str, duration_ms: float = 0):
        self._log("INFO", "MESSAGE", f"Message processed: {status}", {"client_id": client_id, "message_id": message_id, "status": status, "duration_ms": duration_ms})

    def message_queued(self, client_id: str, message_id: int, queue_size: int):
        self._log("INFO", "MESSAGE", f"Message queued", {"client_id": client_id, "message_id": message_id, "queue_size": queue_size})

    def message_validation_failed(self, client_id: str, errors: list):
        self._log("WARNING", "MESSAGE", f"Message validation failed", {"client_id": client_id, "errors": errors})

    def message_too_large(self, client_id: str, size: int, max_size: int):
        self._log("WARNING", "MESSAGE", f"Message too large", {"client_id": client_id, "size": size, "max_size": max_size})

    # Rate limiting events
    def rate_limit_exceeded(self, client_id: str, current: int, limit: int):
        self._log("WARNING", "RATE_LIMIT", "Rate limit exceeded", {"client_id": client_id, "current": current, "limit": limit})

    # Email events
    def email_sent(self, subject: str, recipients: list, success: bool, duration_ms: float = 0):
        status = "success" if success else "failed"
        self._log("INFO" if success else "ERROR", "EMAIL", f"Email {status}", {"subject": subject, "recipients": recipients, "duration_ms": duration_ms})

    def email_queued(self, subject: str, recipients: list):
        self._log("INFO", "EMAIL", "Email queued for retry", {"subject": subject, "recipients": recipients})

    # Webhook events
    def webhook_received(self, ip: str, path: str):
        self._log("DEBUG", "WEBHOOK", f"Webhook received", {"ip": ip, "path": path})

    def webhook_response(self, ip: str, status: int, message: str):
        self._log("INFO", "WEBHOOK", f"Webhook response: {status}", {"ip": ip, "status": status, "message": message})

    # Queue events
    def queue_overflow_warning(self, current_size: int, max_size: int):
        self._log("WARNING", "QUEUE", f"Queue near capacity", {"current_size": current_size, "max_size": max_size})

    def queue_processed(self, processed: int, remaining: int):
        self._log("DEBUG", "QUEUE", f"Queue processed", {"processed": processed, "remaining": remaining})

    def queue_retry_failed(self, message_id: int, attempt: int, max_retries: int):
        self._log("WARNING", "QUEUE", f"Queue retry failed", {"message_id": message_id, "attempt": attempt, "max_retries": max_retries})

    # Server events
    def server_started(self, host: str, port: int, ssl_enabled: bool, queue_enabled: bool):
        self._log("INFO", "SERVER", f"Server started", {"host": host, "port": port, "ssl_enabled": ssl_enabled, "queue_enabled": queue_enabled})

    def server_stopped(self, uptime_seconds: int, total_messages: int, total_errors: int):
        self._log("INFO", "SERVER", f"Server stopped", {"uptime_seconds": uptime_seconds, "total_messages": total_messages, "total_errors": total_errors})

    # Error events
    def error(self, error_type: str, message: str, context: dict = None):
        self._log("ERROR", "ERROR", f"{error_type}: {message}", context)

    def critical(self, error_type: str, message: str, context: dict = None):
        self._log("ERROR", "CRITICAL", f"{error_type}: {message}", context)

    # Notification events
    def notification_sent(self, notification_type: str, subject: str):
        self._log("INFO", "NOTIFICATION", f"Notification sent: {notification_type}", {"type": notification_type, "subject": subject})


# Global instance
log = LoggingService()
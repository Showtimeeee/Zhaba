import asyncio
from datetime import datetime
from src.core.logging_service import log


class NotificationManager:
    def __init__(self, email_sender, admin_email=None):
        self.email_sender = email_sender
        self.admin_email = admin_email
        self._last_queue_warning = None
        self._last_error_warning = None
        self.queue_threshold_warning = 0.8  # 80% of max size
        log.info("NotificationManager", f"Initialized with admin_email={admin_email}")

    async def notify_queue_overflow(self, current_size: int, max_size: int):
        now = datetime.now()
        if self._last_queue_warning:
            if (now - self._last_queue_warning).total_seconds() < 300:
                return
        
        self._last_queue_warning = now
        log.queue_overflow_warning(current_size, max_size)
        
        subject = "CRITICAL: Queue Overflow"
        message = f"""
Queue is near capacity!

Current size: {current_size}
Max size: {max_size}
Time: {now.strftime('%Y-%m-%d %H:%M:%S')}

Please check the application immediately.
"""
        success = await self.email_sender.send_email(subject, message)
        log.notification_sent("queue_overflow", subject)

    async def notify_critical_error(self, error_message: str, context: dict = None):
        now = datetime.now()
        if self._last_error_warning:
            if (now - self._last_error_warning).total_seconds() < 60:
                return
        
        self._last_error_warning = now
        log.critical("Notification", error_message, context)
        
        subject = "ERROR: Critical Error in Zhaba-App"
        message = f"""
A critical error occurred!

Error: {error_message}
Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
"""
        if context:
            message += "\nContext:\n"
            for key, value in context.items():
                message += f"  {key}: {value}\n"

        success = await self.email_sender.send_email(subject, message)
        log.notification_sent("critical_error", subject)

    async def notify_config_issue(self, issue: str):
        log.warning("Notification", f"Configuration issue: {issue}")
        
        subject = "WARNING: Configuration Issue"
        message = f"""
Configuration issue detected:

{issue}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        success = await self.email_sender.send_email(subject, message)
        log.notification_sent("config_issue", subject)

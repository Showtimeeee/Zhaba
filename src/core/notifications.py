import asyncio
from datetime import datetime


class NotificationManager:
    def __init__(self, email_sender, admin_email=None):
        self.email_sender = email_sender
        self.admin_email = admin_email
        self._last_queue_warning = None
        self._last_error_warning = None
        self.queue_threshold_warning = 0.8  # 80% of max size

    async def notify_queue_overflow(self, current_size: int, max_size: int):
        now = datetime.now()
        if self._last_queue_warning:
            if (now - self._last_queue_warning).total_seconds() < 300:  # 5 min cooldown
                return
        
        self._last_queue_warning = now
        subject = "CRITICAL: Queue Overflow"
        message = f"""
Queue is near capacity!

Current size: {current_size}
Max size: {max_size}
Time: {now.strftime('%Y-%m-%d %H:%M:%S')}

Please check the application immediately.
"""
        await self.email_sender.send_email(subject, message)

    async def notify_critical_error(self, error_message: str, context: dict = None):
        now = datetime.now()
        if self._last_error_warning:
            if (now - self._last_error_warning).total_seconds() < 60:  # 1 min cooldown
                return
        
        self._last_error_warning = now
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

        await self.email_sender.send_email(subject, message)

    async def notify_config_issue(self, issue: str):
        subject = "WARNING: Configuration Issue"
        message = f"""
Configuration issue detected:

{issue}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await self.email_sender.send_email(subject, message)
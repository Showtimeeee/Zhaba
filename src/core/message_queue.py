import asyncio
import json
from collections import deque
from datetime import datetime
from typing import Optional
from src.email import EmailSender


class MessageQueue:
    def __init__(self, max_size: int = 1000, max_retries: int = 3):
        self.max_size = max_size
        self.max_retries = max_retries
        self.queue = deque()
        self._processing = False

    def enqueue(self, subject: str, message: str, metadata: dict, html: bool = False) -> bool:
        if len(self.queue) >= self.max_size:
            return False

        self.queue.append({
            "subject": subject,
            "message": message,
            "metadata": metadata,
            "html": html,
            "retries": 0
        })
        return True

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    async def process_queue(self, email_sender: EmailSender, logger):
        if self._processing or self.is_empty():
            return

        self._processing = True

        try:
            while self.queue:
                item = self.queue[0]
                success = email_sender.send_email(
                    item["subject"],
                    item["message"],
                    html=item["html"],
                    metadata=item["metadata"]
                )

                if success:
                    self.queue.popleft()
                else:
                    item["retries"] += 1
                    if item["retries"] >= self.max_retries:
                        logger.error(f"Message failed after {self.max_retries} retries")
                        self.queue.popleft()
                    else:
                        break
        finally:
            self._processing = False

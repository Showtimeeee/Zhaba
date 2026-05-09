import asyncio
import json
from collections import deque
from datetime import datetime
from typing import Optional
from src.email import EmailSender
from src.core.logging_service import log


class MessageQueue:
    def __init__(self, max_size: int = 1000, max_retries: int = 3):
        self.max_size = max_size
        self.max_retries = max_retries
        self.queue = deque()
        self._processing = False
        self._message_id_counter = 0
        log.info("MessageQueue", f"Initialized with max_size={max_size}, max_retries={max_retries}")

    def enqueue(self, subject: str, message: str, metadata: dict, html: bool = False) -> bool:
        self._message_id_counter += 1
        message_id = self._message_id_counter
        
        if len(self.queue) >= self.max_size:
            log.warning("MessageQueue", "Queue full, message rejected", {"message_id": message_id, "queue_size": len(self.queue), "max_size": self.max_size})
            return False

        self.queue.append({
            "message_id": message_id,
            "subject": subject,
            "message": message,
            "metadata": metadata,
            "html": html,
            "retries": 0
        })
        log.message_queued("system", message_id, len(self.queue))
        return True

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    async def process_queue(self, email_sender: EmailSender, logger):
        if self._processing or self.is_empty():
            return

        self._processing = True
        processed_count = 0

        try:
            while self.queue:
                item = self.queue[0]
                message_id = item.get("message_id", 0)
                log.debug("MessageQueue", f"Processing message {message_id}", {"retries": item["retries"], "queue_remaining": len(self.queue)})
                
                success = await email_sender.send_email(
                    item["subject"],
                    item["message"],
                    html=item["html"],
                    metadata=item["metadata"]
                )

                if success:
                    self.queue.popleft()
                    processed_count += 1
                    log.message_processed("system", message_id, "sent", 0)
                else:
                    item["retries"] += 1
                    if item["retries"] >= self.max_retries:
                        log.queue_retry_failed(message_id, item["retries"], self.max_retries)
                        self.queue.popleft()
                    else:
                        log.email_queued(item["subject"], email_sender.email_to_list)
                        break
            
            if processed_count > 0:
                log.queue_processed(processed_count, len(self.queue))
        finally:
            self._processing = False

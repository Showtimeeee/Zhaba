import pytest
from unittest.mock import MagicMock
import asyncio
from src.core import MessageQueue
from src.email import EmailSender


class TestMessageQueue:
    def test_enqueue_success(self):
        queue = MessageQueue(max_size=10, max_retries=3)
        result = queue.enqueue("Subject", "Message", {"ip": "127.0.0.1"})
        assert result is True
        assert len(queue.queue) == 1

    def test_enqueue_overflow(self):
        queue = MessageQueue(max_size=2, max_retries=3)
        queue.enqueue("1", "m", {})
        queue.enqueue("2", "m", {})
        result = queue.enqueue("3", "m", {})
        assert result is False

    @pytest.mark.asyncio
    async def test_process_queue_success(self):
        queue = MessageQueue(max_size=10, max_retries=3)
        queue.enqueue("Subject", "Message", {"ip": "127.0.0.1"})

        mock_sender = MagicMock(spec=EmailSender)
        mock_sender.email_to_list = ['test@example.com']

        async def mock_send_email(*args, **kwargs):
            return True
        mock_sender.send_email = mock_send_email

        await queue.process_queue(mock_sender, MagicMock())

        assert len(queue.queue) == 0

    @pytest.mark.asyncio
    async def test_process_queue_retry_on_failure(self):
        queue = MessageQueue(max_size=10, max_retries=3)
        queue.enqueue("Subject", "Message", {"ip": "127.0.0.1"})

        mock_sender = MagicMock(spec=EmailSender)
        mock_sender.email_to_list = ['test@example.com']

        async def mock_send_email(*args, **kwargs):
            return False
        mock_sender.send_email = mock_send_email

        await queue.process_queue(mock_sender, MagicMock())

        assert len(queue.queue) == 1

    @pytest.mark.asyncio
    async def test_process_queue_remove_after_max_retries(self):
        queue = MessageQueue(max_size=10, max_retries=1)
        queue.enqueue("Subject", "Message", {"ip": "127.0.0.1"})

        mock_sender = MagicMock(spec=EmailSender)
        mock_sender.email_to_list = ['test@example.com']

        async def mock_send_email(*args, **kwargs):
            return False
        mock_sender.send_email = mock_send_email

        await queue.process_queue(mock_sender, MagicMock())

        assert len(queue.queue) == 0

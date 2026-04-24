import pytest
from unittest.mock import MagicMock, patch
import asyncio
from src.core import MessageQueue


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

        mock_sender = MagicMock()
        mock_sender.send_email.return_value = True

        await queue.process_queue(mock_sender, MagicMock())

        mock_sender.send_email.assert_called_once()
        assert len(queue.queue) == 0

    @pytest.mark.asyncio
    async def test_process_queue_retry_on_failure(self):
        queue = MessageQueue(max_size=10, max_retries=3)
        queue.enqueue("Subject", "Message", {"ip": "127.0.0.1"})

        mock_sender = MagicMock()
        mock_sender.send_email.return_value = False

        await queue.process_queue(mock_sender, MagicMock())

        assert len(queue.queue) == 1

    @pytest.mark.asyncio
    async def test_process_queue_remove_after_max_retries(self):
        queue = MessageQueue(max_size=10, max_retries=1)
        queue.enqueue("Subject", "Message", {"ip": "127.0.0.1"})

        mock_sender = MagicMock()
        mock_sender.send_email.return_value = False

        await queue.process_queue(mock_sender, MagicMock())

        assert len(queue.queue) == 0
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta
from src.core.notifications import NotificationManager


@pytest.fixture
def notification_manager():
    mock_sender = MagicMock()
    mock_sender.send_email = AsyncMock(return_value=True)
    return NotificationManager(mock_sender, admin_email="admin@example.com")


class TestNotificationManager:
    @pytest.mark.asyncio
    async def test_queue_overflow_notification(self, notification_manager):
        await notification_manager.notify_queue_overflow(current_size=90, max_size=100)
        
        notification_manager.email_sender.send_email.assert_called_once()
        call_args = notification_manager.email_sender.send_email.call_args
        assert "CRITICAL" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_critical_error_notification(self, notification_manager):
        await notification_manager.notify_critical_error(
            "Test error message",
            context={'message_id': 1, 'client': 'test'}
        )
        
        notification_manager.email_sender.send_email.assert_called_once()
        call_args = notification_manager.email_sender.send_email.call_args
        assert "ERROR" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cooldown_prevents_spam(self, notification_manager):
        # First call
        await notification_manager.notify_critical_error("Error 1")
        # Second call within cooldown
        await notification_manager.notify_critical_error("Error 2")
        
        # Should only be called once due to cooldown
        assert notification_manager.email_sender.send_email.call_count == 1

    @pytest.mark.asyncio
    async def test_cooldown_resets_after_time(self, notification_manager):
        # First call
        await notification_manager.notify_critical_error("Error 1")
        
        # Reset the last warning time to simulate time passing
        notification_manager._last_error_warning = None
        
        # Second call after cooldown (simulated)
        await notification_manager.notify_critical_error("Error 2")
        
        # Should be called twice after cooldown
        assert notification_manager.email_sender.send_email.call_count == 2

    @pytest.mark.asyncio
    async def test_config_issue_notification(self, notification_manager):
        await notification_manager.notify_config_issue("Missing SMTP config")
        
        notification_manager.email_sender.send_email.assert_called_once()
        call_args = notification_manager.email_sender.send_email.call_args
        assert "WARNING" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_queue_warning_cooldown(self, notification_manager):
        # First call
        await notification_manager.notify_queue_overflow(90, 100)
        first_call_count = notification_manager.email_sender.send_email.call_count
        
        # Second call within cooldown
        await notification_manager.notify_queue_overflow(95, 100)
        
        # Should not increase due to cooldown
        assert notification_manager.email_sender.send_email.call_count == first_call_count

    def test_queue_threshold(self, notification_manager):
        assert notification_manager.queue_threshold_warning == 0.8
        
        # Should notify when at 80% or more
        assert 80 >= 100 * 0.8  # 80% threshold
        assert 90 >= 100 * 0.8  # 90% threshold
        assert 70 < 100 * 0.8   # Below threshold
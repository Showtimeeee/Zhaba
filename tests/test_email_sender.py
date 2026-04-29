import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.email import EmailSender


class TestEmailSender:
    @patch('src.email.sender.aiosmtplib.SMTP')
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_smtp, email_config):
        email_sender = EmailSender(email_config)
        mock_instance = AsyncMock()
        mock_smtp.return_value = mock_instance

        result = await email_sender.send_email("Test Subject", "Test Message")

        assert result == True
        mock_instance.login.assert_called_once_with('test@example.com', 'password123')

    @patch('src.email.sender.aiosmtplib.SMTP')
    @pytest.mark.asyncio
    async def test_send_email_auth_failure(self, mock_smtp, email_config):
        from aiosmtplib.errors import SMTPAuthenticationError
        email_sender = EmailSender(email_config)
        mock_instance = AsyncMock()
        mock_instance.login = AsyncMock(side_effect=SMTPAuthenticationError(535, b'Auth failed'))
        mock_smtp.return_value = mock_instance

        result = await email_sender.send_email("Test", "Message")

        assert result == False

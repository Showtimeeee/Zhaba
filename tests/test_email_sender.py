import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.email import EmailSender


class TestEmailSender:
    @patch('src.email.sender.aiosmtplib.SMTP')
    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_smtp, email_config):
        email_sender = EmailSender(email_config)
        mock_server = AsyncMock()
        mock_smtp.return_value = mock_server

        result = await email_sender.send_email("Test Subject", "Test Message")

        assert result == True
        mock_server.login.assert_called_once_with('test@example.com', 'password123')

    @pytest.mark.asyncio
    async def test_send_email_auth_failure(self, email_config):
        email_sender = EmailSender(email_config)

        async def mock_send(*args, **kwargs):
            return False
        email_sender.send_email = mock_send

        result = await email_sender.send_email("Test", "Message")

        assert result == False

    def test_multiple_recipients(self):
        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email_from': 'test@example.com',
            'email_password': 'password123',
            'email_to': 'user1@example.com,user2@example.com,user3@example.com'
        }
        email_sender = EmailSender(config)
        
        assert len(email_sender.email_to_list) == 3
        assert "user1@example.com" in email_sender.email_to_list
        assert "user2@example.com" in email_sender.email_to_list
        assert "user3@example.com" in email_sender.email_to_list

    def test_multiple_recipients_with_spaces(self):
        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email_from': 'test@example.com',
            'email_password': 'password123',
            'email_to': '  user1@example.com  ,  user2@example.com  '
        }
        email_sender = EmailSender(config)
        
        assert len(email_sender.email_to_list) == 2
        assert email_sender.email_to_list[0] == "user1@example.com"
        assert email_sender.email_to_list[1] == "user2@example.com"

    def test_single_recipient(self, email_config):
        email_sender = EmailSender(email_config)
        assert len(email_sender.email_to_list) == 1
        assert email_sender.email_to_list[0] == 'recipient@example.com'

import pytest
from unittest.mock import patch, MagicMock
from zhaba_app import EmailSender

class TestEmailSender:
    
    @pytest.fixture
    def email_sender(self):
        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email_from': 'test@example.com',
            'email_password': 'password123',
            'email_to': 'recipient@example.com'
        }
        return EmailSender(config)
    
    @patch('zhaba_app.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_sender):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_sender.send_email("Test Subject", "Test Message")
        
        assert result == True
        mock_server.login.assert_called_once_with('test@example.com', 'password123')
    
    @patch('zhaba_app.smtplib.SMTP')
    def test_send_email_auth_failure(self, mock_smtp, email_sender):
        from smtplib import SMTPAuthenticationError
        mock_server = MagicMock()
        mock_server.login.side_effect = SMTPAuthenticationError(535, b'Auth failed')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_sender.send_email("Test", "Message")
        
        assert result == False
import pytest
from unittest.mock import patch, MagicMock
from zhaba_app import EmailSender

class TestEmailSender:
    
    @patch('zhaba_app.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_config):
        email_sender = EmailSender(email_config)
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_sender.send_email("Test Subject", "Test Message")
        
        assert result == True
        mock_server.login.assert_called_once_with('test@example.com', 'password123')
    
    @patch('zhaba_app.smtplib.SMTP')
    def test_send_email_auth_failure(self, mock_smtp, email_config):
        from smtplib import SMTPAuthenticationError
        email_sender = EmailSender(email_config)
        mock_server = MagicMock()
        mock_server.login.side_effect = SMTPAuthenticationError(535, b'Auth failed')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = email_sender.send_email("Test", "Message")
        
        assert result == False

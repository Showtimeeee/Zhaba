import pytest


class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.remote_address = ('127.0.0.1', 12345)
    
    async def send(self, message):
        self.sent_messages.append(message)


class MockEmailSender:
    def __init__(self, fail=False):
        self.sent_emails = []
        self.fail = fail
    
    async def send_email(self, subject, message, html=False, metadata=None):
        self.sent_emails.append((subject, message))
        return not self.fail

@pytest.fixture
def mock_websocket():
    return MockWebSocket()

@pytest.fixture
def mock_email_sender():
    return MockEmailSender()

@pytest.fixture
def mock_failing_email_sender():
    return MockEmailSender(fail=True)

@pytest.fixture
def email_config():
    return {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'email_from': 'test@example.com',
        'email_password': 'password123',
        'email_to': 'recipient@example.com'
    }

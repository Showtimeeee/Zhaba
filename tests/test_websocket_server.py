import pytest
import asyncio
import json
from zhaba_app import WebSocketServer

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
    
    def send_email(self, subject, message):
        self.sent_emails.append((subject, message))
        return not self.fail

@pytest.mark.asyncio
async def test_process_json_message():
    email_sender = MockEmailSender()
    server = WebSocketServer(email_sender, 'localhost', 8765)
    websocket = MockWebSocket()
    
    message = json.dumps({
        'subject': 'Test',
        'message': 'Hello',
        'sender': 'Client'
    })
    
    await server.process_message(websocket, message, '127.0.0.1')
    
    assert len(email_sender.sent_emails) == 1
    assert email_sender.sent_emails[0][0] == 'Test'
    assert 'Client' in email_sender.sent_emails[0][1]

@pytest.mark.asyncio
async def test_process_text_message():
    email_sender = MockEmailSender()
    server = WebSocketServer(email_sender, 'localhost', 8765)
    websocket = MockWebSocket()
    
    await server.process_message(websocket, 'Plain text', '127.0.0.1')
    
    assert email_sender.sent_emails[0][0] == 'Новое сообщение из WebSocket'

@pytest.mark.asyncio
async def test_email_failure_handling():
    email_sender = MockEmailSender(fail=True)
    server = WebSocketServer(email_sender, 'localhost', 8765)
    websocket = MockWebSocket()
    
    message = json.dumps({'subject': 'Test', 'message': 'Test'})
    
    await server.process_message(websocket, message, '127.0.0.1')
    
    response = json.loads(websocket.sent_messages[0])
    assert response['status'] == 'error'
    assert server.error_count == 1
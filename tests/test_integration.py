import pytest
import asyncio
import json
from zhaba_app import WebSocketServer

class MockWebSocket:
    def __init__(self):
        self.responses = []
        self.remote_address = ('127.0.0.1', 12345)
    
    async def send(self, message):
        self.responses.append(json.loads(message))

class MockEmailSender:
    def __init__(self):
        self.emails = []
    
    def send_email(self, subject, message):
        self.emails.append({'subject': subject, 'message': message})
        return True

@pytest.mark.asyncio
async def test_complete_message_flow():
    email_sender = MockEmailSender()
    server = WebSocketServer(email_sender, 'localhost', 8765)
    websocket = MockWebSocket()
    
    message = json.dumps({
        'subject': 'Alert',
        'message': 'System error',
        'sender': 'Monitor'
    })
    
    await server.process_message(websocket, message, '10.0.0.1:8080')
    
    assert len(email_sender.emails) == 1
    assert email_sender.emails[0]['subject'] == 'Alert'
    assert 'Monitor' in email_sender.emails[0]['message']
    assert '10.0.0.1' in email_sender.emails[0]['message']
    assert websocket.responses[0]['status'] == 'success'

@pytest.mark.asyncio
async def test_multiple_messages_count():
    email_sender = MockEmailSender()
    server = WebSocketServer(email_sender, 'localhost', 8765)
    websocket = MockWebSocket()
    
    for i in range(3):
        msg = json.dumps({'subject': f'Test {i}', 'message': 'Hi'})
        await server.process_message(websocket, msg, '127.0.0.1')
    
    assert server.message_count == 3
    assert len(email_sender.emails) == 3
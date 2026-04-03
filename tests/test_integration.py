import pytest
import json
from zhaba_app import WebSocketServer


@pytest.mark.asyncio
async def test_complete_message_flow(mock_websocket):
    from tests.conftest import MockEmailSender
    email_sender = MockEmailSender()
    server = WebSocketServer(email_sender, 'localhost', 8765)
    
    message = json.dumps({
        'subject': 'Alert',
        'message': 'System error',
        'sender': 'Monitor'
    })
    
    await server.process_message(mock_websocket, message, '10.0.0.1:8080')
    
    assert len(email_sender.sent_emails) == 1
    assert email_sender.sent_emails[0][0] == 'Alert'
    assert 'Monitor' in email_sender.sent_emails[0][1]
    assert '10.0.0.1' in email_sender.sent_emails[0][1]
    
    response = json.loads(mock_websocket.sent_messages[0])
    assert response['status'] == 'success'

@pytest.mark.asyncio
async def test_multiple_messages_count(mock_websocket):
    from tests.conftest import MockEmailSender
    email_sender = MockEmailSender()
    server = WebSocketServer(email_sender, 'localhost', 8765)
    
    for i in range(3):
        msg = json.dumps({'subject': f'Test {i}', 'message': 'Hi'})
        await server.process_message(mock_websocket, msg, '127.0.0.1')
    
    assert server.message_count == 3
    assert len(email_sender.sent_emails) == 3

@pytest.mark.asyncio
async def test_client_info_preserved(mock_websocket, mock_email_sender):
    server = WebSocketServer(mock_email_sender, 'localhost', 8765)
    
    await server.process_message(mock_websocket, 'Test message', '192.168.1.100:5555')
    
    assert '192.168.1.100' in mock_email_sender.sent_emails[0][1]
    assert '5555' in mock_email_sender.sent_emails[0][1]

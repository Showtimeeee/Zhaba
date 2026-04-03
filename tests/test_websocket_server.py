import pytest
import json
from zhaba_app import WebSocketServer


@pytest.mark.asyncio
async def test_process_json_message(mock_websocket, mock_email_sender):
    server = WebSocketServer(mock_email_sender, 'localhost', 8765)
    
    message = json.dumps({
        'subject': 'Test',
        'message': 'Hello',
        'sender': 'Client'
    })
    
    await server.process_message(mock_websocket, message, '127.0.0.1')
    assert len(mock_email_sender.sent_emails) == 1
    assert mock_email_sender.sent_emails[0][0] == 'Test'
    assert 'Client' in mock_email_sender.sent_emails[0][1]

@pytest.mark.asyncio
async def test_process_text_message(mock_websocket, mock_email_sender):
    server = WebSocketServer(mock_email_sender, 'localhost', 8765)
    
    await server.process_message(mock_websocket, 'Plain text', '127.0.0.1')
    assert mock_email_sender.sent_emails[0][0] == 'Новое сообщение из WebSocket'

@pytest.mark.asyncio
async def test_email_failure_handling(mock_websocket, mock_failing_email_sender):
    server = WebSocketServer(mock_failing_email_sender, 'localhost', 8765)
    message = json.dumps({'subject': 'Test', 'message': 'Test'})
    await server.process_message(mock_websocket, message, '127.0.0.1')
    
    response = json.loads(mock_websocket.sent_messages[0])
    assert response['status'] == 'error'
    assert server.error_count == 1

@pytest.mark.asyncio
async def test_message_counter_increments(mock_websocket, mock_email_sender):
    server = WebSocketServer(mock_email_sender, 'localhost', 8765)
    message = json.dumps({'subject': 'Test', 'message': 'Test'})
    
    await server.process_message(mock_websocket, message, '127.0.0.1')
    await server.process_message(mock_websocket, message, '127.0.0.1')
    await server.process_message(mock_websocket, message, '127.0.0.1')
    
    assert server.message_count == 3

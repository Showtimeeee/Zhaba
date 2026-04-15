import pytest
import json
from zhaba_app import WebSocketServer

@pytest.mark.asyncio
async def test_message_counter_increments(mock_websocket, mock_email_sender):
    server = WebSocketServer(mock_email_sender, 'localhost', 8765)
    
    message = json.dumps({'subject': 'Test', 'message': 'Test'})
    
    await server.process_message(mock_websocket, message, '127.0.0.1')
    await server.process_message(mock_websocket, message, '127.0.0.1')
    await server.process_message(mock_websocket, message, '127.0.0.1')
    
    assert server.message_count == 3

@pytest.mark.asyncio
async def test_client_info_preserved(mock_websocket, mock_email_sender):
    server = WebSocketServer(mock_email_sender, 'localhost', 8765)
    
    await server.process_message(mock_websocket, 'Test message', '192.168.1.100:5555')
    
    assert '192.168.1.100' in mock_email_sender.sent_emails[0][1]
    assert '5555' in mock_email_sender.sent_emails[0][1]

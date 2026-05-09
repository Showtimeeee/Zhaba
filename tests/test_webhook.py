import pytest
from aiohttp import test_utils, web
from unittest.mock import MagicMock, AsyncMock
from src.webhook.handler import WebhookHandler


@pytest.fixture
def app(webhook_handler):
    return webhook_handler.get_app()


@pytest.fixture
def webhook_handler():
    mock_sender = MagicMock()
    mock_sender.send_email = AsyncMock(return_value=True)
    mock_sender.email_to_list = ['recipient@example.com']
    
    mock_rate_limiter = MagicMock()
    mock_rate_limiter.is_allowed.return_value = True
    mock_rate_limiter.get_remaining.return_value = 0
    mock_rate_limiter.max_per_minute = 60
    
    mock_server = MagicMock()
    mock_server.email_sender = mock_sender
    mock_server.rate_limiter = mock_rate_limiter
    mock_server.db = MagicMock()
    mock_server.db.add_message.return_value = 1
    mock_server.db.update_message_status = MagicMock()
    mock_server.message_queue = None
    mock_server.queue_enabled = False
    
    return WebhookHandler(mock_server)


class TestWebhookHandler:
    @pytest.mark.asyncio
    async def test_get_request(self, aiohttp_client, app):
        client = await aiohttp_client(app)
        resp = await client.get('/webhook')
        assert resp.status == 200
        data = await resp.json()
        assert data['service'] == 'Zhaba-App Webhook'

    @pytest.mark.asyncio
    async def test_valid_post(self, aiohttp_client, app):
        payload = {
            'subject': 'Test Subject',
            'message': 'Test Message',
            'sender': 'Test Sender',
            'html': False
        }
        client = await aiohttp_client(app)
        resp = await client.post('/webhook', json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data['status'] == 'success'

    @pytest.mark.asyncio
    async def test_invalid_json(self, aiohttp_client, app):
        client = await aiohttp_client(app)
        resp = await client.post('/webhook', data=b'invalid json')
        assert resp.status == 400
        data = await resp.json()
        assert data['status'] == 'error'

    @pytest.mark.asyncio
    async def test_invalid_data(self, aiohttp_client, app, webhook_handler):
        webhook_handler.rate_limiter.is_allowed.return_value = True
        payload = {
            'subject': 'x' * 101,  # Too long
            'message': 'Test'
        }
        client = await aiohttp_client(app)
        resp = await client.post('/webhook', json=payload)
        assert resp.status == 400
        data = await resp.json()
        assert data['status'] == 'error'

    @pytest.mark.asyncio
    async def test_rate_limit(self, aiohttp_client, app, webhook_handler):
        webhook_handler.rate_limiter.is_allowed.return_value = False
        client = await aiohttp_client(app)
        resp = await client.post('/webhook', json={'message': 'test'})
        assert resp.status == 429
        data = await resp.json()
        assert data['status'] == 'error'

    @pytest.mark.asyncio
    async def test_email_failure(self, aiohttp_client, app, webhook_handler):
        webhook_handler.email_sender.send_email = AsyncMock(return_value=False)
        client = await aiohttp_client(app)
        resp = await client.post('/webhook', json={'subject': 'Test', 'message': 'Test'})
        assert resp.status == 500
        data = await resp.json()
        assert data['status'] == 'error'

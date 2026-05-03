import json
from datetime import datetime
from aiohttp import web

from src.core import MessageValidator, Database
from src.email import EmailSender
from src.core.message_queue import MessageQueue


class WebhookHandler:
    def __init__(self, websocket_server):
        self.server = websocket_server
        self.email_sender = websocket_server.email_sender
        self.rate_limiter = websocket_server.rate_limiter
        self.db = websocket_server.db
        self.message_queue = websocket_server.message_queue
        self.queue_enabled = websocket_server.queue_enabled

    async def handle_post(self, request):
        client_ip = request.remote or "unknown"

        if not self.rate_limiter.is_allowed(client_ip):
            return web.json_response(
                {"status": "error", "message": "Rate limit exceeded"},
                status=429
            )

        try:
            data = await request.json()
        except:
            return web.json_response(
                {"status": "error", "message": "Invalid JSON"},
                status=400
            )

        validation = MessageValidator.validate(data)
        if not validation["valid"]:
            return web.json_response(
                {"status": "error", "message": "; ".join(validation["errors"])},
                status=400
            )

        data = MessageValidator.sanitize(data)
        subject = data.get("subject", "HTTP Webhook сообщение")
        content = data.get("message", "")
        sender = data.get("sender", "HTTP Client")
        send_html = data.get("html", False)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {
            "timestamp": timestamp,
            "sender": sender,
            "ip": client_ip
        }

        message_id = self.db.add_message(
            subject=subject,
            message=content,
            sender=sender,
            ip=client_ip,
            html=send_html,
            status='pending'
        )

        if self.queue_enabled and self.message_queue:
            queued = self.message_queue.enqueue(subject, content, metadata, send_html)
            if queued:
                self.db.update_message_status(message_id, 'queued')
                return web.json_response({
                    "status": "queued",
                    "message": "Сообщение поставлено в очередь",
                    "message_id": message_id
                })
            else:
                self.db.update_message_status(message_id, 'failed', 'Queue overflow')
                return web.json_response(
                    {"status": "error", "message": "Очередь переполнена"},
                    status=503
                )

        success = await self.email_sender.send_email(
            subject, content, html=send_html, metadata=metadata
        )

        if success:
            self.db.update_message_status(message_id, 'sent')
            return web.json_response({
                "status": "success",
                "message": "Сообщение отправлено",
                "message_id": message_id
            })
        else:
            self.db.update_message_status(message_id, 'failed', 'Email send failed')
            return web.json_response(
                {"status": "error", "message": "Ошибка при отправке"},
                status=500
            )

    async def handle_get(self, request):
        return web.json_response({
            "service": "Zhaba-App Webhook",
            "status": "running",
            "endpoints": {
                "POST /webhook": "Send message via HTTP POST"
            }
        })

    def get_app(self):
        app = web.Application()
        app.router.add_post('/webhook', self.handle_post)
        app.router.add_get('/webhook', self.handle_get)
        return app
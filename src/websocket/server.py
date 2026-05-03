import asyncio
import json
import ssl
import traceback
from datetime import datetime

import websockets

from src.core import RateLimiter, MessageValidator, Database
from src.core.message_queue import MessageQueue
from src.email import EmailSender


class WebSocketServer:
    def __init__(self, email_sender: EmailSender, host: str, port: int, max_connections: int = 100,
                 max_message_size: int = 1048576, rate_limit_per_minute: int = 10,
                 auth_required: bool = False, auth_token: str = "",
                 ssl_enabled: bool = False, ssl_cert: str = "", ssl_key: str = ""):
        self.email_sender = email_sender
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.max_message_size = max_message_size
        self.connected_clients = set()
        self.message_count = 0
        self.error_count = 0
        self.server = None
        self.start_time = datetime.now()
        self.rate_limiter = RateLimiter(rate_limit_per_minute)
        self.auth_required = auth_required
        self.auth_token = auth_token
        self.ssl_enabled = ssl_enabled
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.message_queue = None
        self.queue_enabled = False
        self._shutdown_event = asyncio.Event()
        self._is_shutting_down = False
        self.db = Database()

    def enable_queue(self, max_size: int = 1000, max_retries: int = 3):
        self.message_queue = MessageQueue(max_size, max_retries)
        self.queue_enabled = True

    def check_auth(self, token: str) -> bool:
        if not self.auth_required:
            return True
        return token == self.auth_token

    async def handle_client(self, websocket, path):
        client_address = websocket.remote_address
        client_id = f"{client_address[0]}:{client_address[1]}"

        if self._is_shutting_down:
            await websocket.close(1001, "Server shutting down")
            return

        if len(self.connected_clients) >= self.max_connections:
            await websocket.close(1008, "Too many connections")
            return

        try:
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10)
            auth_data = json.loads(auth_message)
            if not self.check_auth(auth_data.get("token", "")):
                await websocket.close(1008, "Authentication required")
                return
        except asyncio.TimeoutError:
            if self.auth_required:
                await websocket.close(1008, "Authentication required")
                return
        except Exception:
            pass

        self.connected_clients.add(websocket)

        try:
            async for message in websocket:
                if self._is_shutting_down:
                    break
                await self.process_message(websocket, message, client_id)

        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception:
            self.error_count += 1
        finally:
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)

    async def process_message(self, websocket, message, client_id: str):
        self.message_count += 1

        if not self.rate_limiter.is_allowed(client_id):
            await websocket.send(json.dumps({
                "status": "error",
                "message": "Rate limit exceeded"
            }, ensure_ascii=False))
            return

        if len(message) > self.max_message_size:
            await websocket.send(json.dumps({
                "status": "error",
                "message": f"Message exceeds {self.max_message_size} bytes"
            }, ensure_ascii=False))
            return

        try:
            data = json.loads(message)
            validation = MessageValidator.validate(data)
            if not validation["valid"]:
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "; ".join(validation["errors"])
                }, ensure_ascii=False))
                return

            data = MessageValidator.sanitize(data)
            subject = data.get("subject", "WebSocket сообщение")
            content = data.get("message", message)
            sender = data.get("sender", "Unknown")
            send_html = data.get("html", False)

        except json.JSONDecodeError:
            subject = "Новое сообщение из WebSocket"
            content = message
            sender = "Unknown"
            send_html = False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sender_prefix = f"Отправитель: {sender}\n\n" if sender != "Unknown" else ""
        formatted_message = f"Получено: {timestamp}\nОт клиента: {client_id}\n\n{sender_prefix}{content}"

        metadata = {
            "timestamp": timestamp,
            "sender": sender,
            "ip": client_id
        }

        message_id = self.db.add_message(
            subject=subject,
            message=content,
            sender=sender,
            ip=client_id,
            html=send_html,
            status='pending'
        )

        if self.queue_enabled and self.message_queue:
            queued = self.message_queue.enqueue(subject, formatted_message, metadata, send_html)
            if queued:
                self.db.update_message_status(message_id, 'queued')
                response = {
                    "status": "queued",
                    "message": "Сообщение поставлено в очередь",
                    "timestamp": timestamp,
                    "message_id": self.message_count,
                    "queue_size": len(self.message_queue.queue),
                }
                await websocket.send(json.dumps(response, ensure_ascii=False))
                return
            else:
                self.db.update_message_status(message_id, 'failed', 'Queue overflow')
                response = {
                    "status": "error",
                    "message": "Очередь переполнена",
                }
                await websocket.send(json.dumps(response, ensure_ascii=False))
                return

        success = await self.email_sender.send_email(subject, formatted_message, html=send_html, metadata=metadata)

        if success:
            self.db.update_message_status(message_id, 'sent')
        else:
            self.db.update_message_status(message_id, 'failed', 'Email send failed')

        response = {
            "status": "success" if success else "error",
            "message": "Сообщение отправлено" if success else "Ошибка при отправке",
            "timestamp": timestamp,
            "message_id": self.message_count,
            "rate_limit_remaining": self.rate_limiter.get_remaining(client_id),
        }
        await websocket.send(json.dumps(response, ensure_ascii=False))

        if not success:
            self.error_count += 1

    async def get_health(self):
        uptime = (datetime.now() - self.start_time).total_seconds()
        health = {
            "status": "healthy",
            "uptime_seconds": int(uptime),
            "message_count": self.message_count,
            "error_count": self.error_count,
            "connected_clients": len(self.connected_clients),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            db_stats = self.db.get_stats()
            health.update(db_stats)
        except:
            pass

        if self.queue_enabled and self.message_queue:
            health["queue_size"] = len(self.message_queue.queue)

        return health

    async def start(self, queue_enabled: bool = False, queue_max_size: int = 1000):
        from logger import logger

        if queue_enabled:
            self.enable_queue(queue_max_size)
            logger.info(f"Message queue enabled, max size: {queue_max_size}")

        ssl_context = None
        if self.ssl_enabled and self.ssl_cert and self.ssl_key:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(self.ssl_cert, self.ssl_key)

        logger.info("=" * 60)
        logger.info("ZHABA-APP SERVER STARTING")
        logger.info("=" * 60)
        logger.info(f"Host: {self.host}")
        logger.info(f"Port: {self.port}")
        logger.info(f"Max connections: {self.max_connections}")
        logger.info(f"Max message size: {self.max_message_size}")
        logger.info(f"SSL: {'enabled' if self.ssl_enabled else 'disabled'}")
        logger.info(f"Queue: {'enabled' if queue_enabled else 'disabled'}")
        logger.info("=" * 60)

        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            max_size=self.max_message_size,
            ping_interval=20,
            ping_timeout=60,
            ssl=ssl_context
        )

        protocol = "wss" if self.ssl_enabled else "ws"
        logger.info(f"Server started: {protocol}://{self.host}:{self.port}")
        logger.info("Waiting for connections...")

        asyncio.create_task(self.monitor_stats())
        asyncio.create_task(self.health_check_server())

        self.webhook = WebhookHandler(self)
        webhook_app = self.webhook.get_app()
        webhook_runner = web.AppRunner(webhook_app)
        await webhook_runner.setup()
        webhook_site = web.TCPSite(webhook_runner, '127.0.0.1', 8080)
        asyncio.create_task(webhook_site.start())
        logger.info("Webhook server started: http://127.0.0.1:8080/webhook")

        if self.queue_enabled:
            asyncio.create_task(self._process_queue_loop())

        await self.server.wait_closed()

    async def _process_queue_loop(self):
        from logger import logger
        while True:
            await asyncio.sleep(10)
            if self.message_queue and not self.message_queue.is_empty():
                await self.message_queue.process_queue(self.email_sender, logger)

    async def health_check_server(self):
        from aiohttp import web

        async def health_handler(request):
            health = await self.get_health()
            return web.json_response(health)

        app = web.Application()
        app.router.add_get("/health", health_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 8766)
        await site.start()

    async def graceful_shutdown(self):
        self._is_shutting_down = True

        for client in list(self.connected_clients):
            try:
                await client.close(1001, "Server shutting down")
            except Exception:
                pass

        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def monitor_stats(self):
        while True:
            await asyncio.sleep(60)

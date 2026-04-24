import argparse
import asyncio
import smtplib
import traceback
import sys
from datetime import datetime

from config import EMAIL_CONFIG, WEBSOCKET_CONFIG, APP_CONFIG
from logger import logger
from src.email import EmailSender
from src.websocket import WebSocketServer


async def main():
    parser = argparse.ArgumentParser(description="Zhaba-App WebSocket Server")
    parser.add_argument("--host", default=None, help="WebSocket host")
    parser.add_argument("--port", type=int, default=None, help="WebSocket port")
    args = parser.parse_args()

    if args.host:
        WEBSOCKET_CONFIG["host"] = args.host
    if args.port:
        WEBSOCKET_CONFIG["port"] = args.port

    logger.info("Zhaba-App starting...")

    if not EMAIL_CONFIG.get("email_from") or not EMAIL_CONFIG.get("email_password") or not EMAIL_CONFIG.get("email_to"):
        logger.error("Missing required email configuration")
        return

    email_sender = EmailSender(
        EMAIL_CONFIG,
        max_retries=APP_CONFIG.get("email_max_retries", 3),
        retry_delay=APP_CONFIG.get("email_retry_delay", 2)
    )

    try:
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=10) as test_server:
            test_server.starttls()
            test_server.login(EMAIL_CONFIG["email_from"], EMAIL_CONFIG["email_password"])
            logger.info("SMTP connection verified")
    except Exception as e:
        logger.warning(f"SMTP verification failed: {e}")

    websocket_server = WebSocketServer(
        email_sender,
        WEBSOCKET_CONFIG["host"],
        WEBSOCKET_CONFIG["port"],
        max_connections=WEBSOCKET_CONFIG.get("max_connections", 100),
        max_message_size=APP_CONFIG.get("max_message_size", 1048576),
        rate_limit_per_minute=APP_CONFIG.get("rate_limit_per_minute", 10),
        auth_required=APP_CONFIG.get("auth_required", False),
        auth_token=APP_CONFIG.get("auth_token", ""),
        ssl_enabled=APP_CONFIG.get("ssl_enabled", False),
        ssl_cert=APP_CONFIG.get("ssl_cert", ""),
        ssl_key=APP_CONFIG.get("ssl_key", ""),
    )

    queue_enabled = APP_CONFIG.get("queue_enabled", False)
    queue_max_size = APP_CONFIG.get("queue_max_size", 1000)

    protocol = "wss" if APP_CONFIG.get("ssl_enabled") else "ws"
    logger.info(f"WebSocket server: {protocol}://{WEBSOCKET_CONFIG['host']}:{WEBSOCKET_CONFIG['port']}")
    if queue_enabled:
        logger.info(f"Message queue enabled, max size: {queue_max_size}")

    try:
        await websocket_server.start(queue_enabled=queue_enabled, queue_max_size=queue_max_size)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await websocket_server.graceful_shutdown()
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Zhaba-App stopped")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)

import asyncio
import websockets
import smtplib
import json
import traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG, WEBSOCKET_CONFIG, APP_CONFIG, LOGGING_CONFIG
from logger import logger

class EmailSender:
    def __init__(self, config):
        self.config = config
        self.smtp_server = config["smtp_server"]
        self.smtp_port = config["smtp_port"]
        self.email_from = config["email_from"]
        self.email_password = config["email_password"]
        self.email_to = config["email_to"]

        logger.info(f"Email отправитель инициализирован: {self.email_from} -> {self.email_to}")

    def send_email(self, subject, message):
        start_time = datetime.now()
        logger.debug(f"Начало отправки email. Тема: {subject}")

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_from
            msg["To"] = self.email_to
            msg["Subject"] = subject[:100] if len(subject) > 100 else subject
            msg.attach(MIMEText(message, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)

            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Email успешно отправлен на {self.email_to} за {elapsed_time:.2f} сек")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Ошибка аутентификации SMTP: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP ошибка: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке email: {e}")
            logger.error(traceback.format_exc())
            return False

class WebSocketServer:
    def __init__(self, email_sender, host, port):
        self.email_sender = email_sender
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.message_count = 0
        self.error_count = 0
        self.server = None

        logger.info(f"WebSocket сервер инициализирован: {host}:{port}")

    async def handle_client(self, websocket, path):
        client_address = websocket.remote_address
        client_id = f"{client_address[0]}:{client_address[1]}"

        if len(self.connected_clients) >= WEBSOCKET_CONFIG["max_connections"]:
            logger.warning(f"Превышен лимит подключений. Отказ клиенту {client_id}")
            await websocket.close(1008, "Too many connections")
            return

        logger.info(f"Новый клиент подключился: {client_id}")
        self.connected_clients.add(websocket)

        try:
            async for message in websocket:
                self.message_count += 1
                await self.process_message(websocket, message, client_id)

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Клиент отключился: {client_id}, код: {e.code}")
        except Exception as e:
            logger.error(f"Ошибка при обработке клиента {client_id}: {e}")
            logger.error(traceback.format_exc())
            self.error_count += 1
        finally:
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)
            logger.debug(f"Клиент {client_id} удалён. Осталось клиентов: {len(self.connected_clients)}")

    async def process_message(self, websocket, message, client_id):
        try:
            if len(message) > APP_CONFIG["max_message_size"]:
                logger.warning(f"Сообщение от {client_id} превышает максимальный размер")
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": f"Сообщение превышает максимальный размер {APP_CONFIG['max_message_size']} байт"
                }, ensure_ascii=False))
                return

            try:
                data = json.loads(message)
                subject = data.get("subject", "WebSocket сообщение")
                content = data.get("message", message)
                if "sender" in data:
                    content = f"Отправитель: {data['sender']}\n\n{content}"
                logger.debug(f"JSON сообщение от {client_id}: subject={subject}")
            except json.JSONDecodeError:
                subject = "Новое сообщение из WebSocket"
                content = message
                logger.debug(f"Текстовое сообщение от {client_id}")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"Получено: {timestamp}\nОт клиента: {client_id}\n\n{content}"

            logger.info(f"Обработка сообщения от {client_id}, тема: {subject}")
            success = self.email_sender.send_email(subject, formatted_message)

            response = {
                "status": "success" if success else "error",
                "message": "Сообщение отправлено на email" if success else "Ошибка при отправке email",
                "timestamp": timestamp,
                "message_id": self.message_count,
            }
            await websocket.send(json.dumps(response, ensure_ascii=False))

            if success:
                logger.info(f"Сообщение #{self.message_count} успешно обработано для {client_id}")
            else:
                logger.warning(f"Сообщение #{self.message_count} не удалось отправить на email")
                self.error_count += 1

        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения от {client_id}: {e}")
            logger.error(traceback.format_exc())
            error_response = {
                "status": "error",
                "message": f"Ошибка: {str(e)}",
                "message_id": self.message_count,
            }
            try:
                await websocket.send(json.dumps(error_response, ensure_ascii=False))
            except:
                logger.error(f"Не удалось отправить ответ клиенту {client_id}")

    async def start(self):
        logger.info("=" * 60)
        logger.info("ЗАПУСК WEBHOOK СЕРВЕРА")
        logger.info("=" * 60)
        logger.info(f"Хост: {self.host}")
        logger.info(f"Порт: {self.port}")
        logger.info(f"Максимум клиентов: {WEBSOCKET_CONFIG['max_connections']}")
        logger.info(f"Максимальный размер сообщения: {APP_CONFIG['max_message_size']} байт")
        logger.info(f"Режим отладки: {APP_CONFIG['debug']}")
        logger.info("=" * 60)

        try:
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                max_size=APP_CONFIG["max_message_size"],
                ping_interval=20,
                ping_timeout=60
            )
        except OSError as e:
            logger.error(f"Не удалось запустить сервер на {self.host}:{self.port}: {e}")
            raise

        logger.info(f"✅ WebSocket сервер запущен на ws://{self.host}:{self.port}")
        logger.info("Ожидание подключений...")

        asyncio.create_task(self.monitor_stats())
        await self.server.wait_closed()

    async def monitor_stats(self):
        while True:
            await asyncio.sleep(60)
            logger.info(
                f"📊 Статистика: Сообщений: {self.message_count}, "
                f"Ошибок: {self.error_count}, "
                f"Клиентов: {len(self.connected_clients)}"
            )

async def main():
    logger.info("🚀 Запуск приложения Zhaba...")

    if not EMAIL_CONFIG.get("email_from") or not EMAIL_CONFIG.get("email_password") or not EMAIL_CONFIG.get("email_to"):
        logger.error("❌ Ошибка: Отсутствуют обязательные настройки email в config.py")
        logger.error("Проверьте переменные EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO в файле .env")
        return

    try:
        email_sender = EmailSender(EMAIL_CONFIG)
        logger.info("✅ Email отправитель инициализирован")

        try:
            with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=10) as test_server:
                test_server.starttls()
                test_server.login(EMAIL_CONFIG["email_from"], EMAIL_CONFIG["email_password"])
                logger.info("✅ SMTP соединение успешно проверено")
                
                if APP_CONFIG["debug"]:
                    test_msg = f"Сервер Zhaba запущен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    email_sender.send_email("Zhaba Server Started", test_msg)
        except Exception as e:
            logger.warning(f"⚠️ Предупреждение: SMTP проверка не удалась: {e}")
            logger.warning("Проверьте правильность настроек email в .env файле")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации email отправителя: {e}")
        logger.error(traceback.format_exc())
        return

    websocket_server = WebSocketServer(
        email_sender,
        WEBSOCKET_CONFIG["host"],
        WEBSOCKET_CONFIG["port"],
    )

    try:
        await websocket_server.start()
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("🛑 Приложение остановлено пользователем")
        logger.info(f"📊 Итоговая статистика:")
        logger.info(f"   Всего сообщений: {websocket_server.message_count}")
        logger.info(f"   Всего ошибок: {websocket_server.error_count}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при работе приложения: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение завершено")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")
        logger.critical(traceback.format_exc())

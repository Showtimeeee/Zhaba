import asyncio
import websockets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import logging
import logging.handlers
import sys
import traceback
from config import EMAIL_CONFIG, WEBSOCKET_CONFIG, APP_CONFIG, LOGGING_CONFIG

def setup_logger():
    """Настройка логирования с ротацией файлов"""
    
    # Создаем логгер
    logger = logging.getLogger('zhaba')
    logger.setLevel(getattr(logging, LOGGING_CONFIG['log_level']))
    
    # Создаем форматтер
    formatter = logging.Formatter(
        LOGGING_CONFIG['format'],
        datefmt=LOGGING_CONFIG['date_format']
    )
    
    # Обработчик для файла с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        LOGGING_CONFIG['log_file'],
        maxBytes=LOGGING_CONFIG['max_bytes'],
        backupCount=LOGGING_CONFIG['backup_count'],
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if APP_CONFIG['debug'] else logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Добавляем обработчик для ошибок
    error_handler = logging.handlers.RotatingFileHandler(
        'error.log',
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

# Инициализируем логгер
logger = setup_logger()

class EmailSender:
    """Класс для отправки email сообщений"""
    
    def __init__(self, config):
        self.config = config
        self.smtp_server = config['smtp_server']
        self.smtp_port = config['smtp_port']
        self.email_from = config['email_from']
        self.email_password = config['email_password']
        self.email_to = config['email_to']
        
        logger.info(f"Email отправитель инициализирован: {self.email_from} -> {self.email_to}")
        logger.debug(f"SMTP сервер: {self.smtp_server}:{self.smtp_port}")
    
    def send_email(self, subject, message):
        """Отправка email с указанной темой и сообщением"""
        start_time = datetime.now()
        logger.debug(f"Начало отправки email. Тема: {subject}")
        
        try:
            # Создаем сообщение
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = subject
            
            # Добавляем тело сообщения
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # Отправляем email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Включаем шифрование
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Email успешно отправлен на {self.email_to} за {elapsed_time:.2f} сек")
            logger.debug(f"Размер сообщения: {len(message)} символов")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Ошибка аутентификации SMTP: {e}")
            logger.error("Проверьте логин и пароль")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP ошибка: {e}")
            logger.debug(traceback.format_exc())
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке email: {e}")
            logger.debug(traceback.format_exc())
            return False

class WebSocketServer:
    """Класс WebSocket сервера"""
    
    def __init__(self, email_sender, host, port):
        self.email_sender = email_sender
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.message_count = 0
        self.error_count = 0
        
        logger.info(f"WebSocket сервер инициализирован: {host}:{port}")
    
    async def handle_client(self, websocket, path):
        """Обработка подключения клиента"""
        client_address = websocket.remote_address
        client_id = f"{client_address[0]}:{client_address[1]}"
        
        # Проверяем лимит подключений
        if len(self.connected_clients) >= WEBSOCKET_CONFIG['max_connections']:
            logger.warning(f"Превышен лимит подключений. Отказ клиенту {client_id}")
            await websocket.close(1008, "Too many connections")
            return
        
        logger.info(f"Новый клиент подключился: {client_id}")
        logger.debug(f"Всего клиентов: {len(self.connected_clients) + 1}")
        self.connected_clients.add(websocket)
        
        try:
            async for message in websocket:
                self.message_count += 1
                message_size = len(message)
                
                logger.info(f"Получено сообщение #{self.message_count} от {client_id}")
                logger.debug(f"Размер сообщения: {message_size} байт")
                
                # Обрабатываем полученное сообщение
                await self.process_message(websocket, message, client_id)
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Клиент отключился: {client_id}, код: {e.code}")
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket ошибка для клиента {client_id}: {e}")
            logger.debug(traceback.format_exc())
            self.error_count += 1
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке клиента {client_id}: {e}")
            logger.debug(traceback.format_exc())
            self.error_count += 1
        finally:
            self.connected_clients.remove(websocket)
            logger.debug(f"Клиент {client_id} удален. Осталось клиентов: {len(self.connected_clients)}")
    
    async def process_message(self, websocket, message, client_id):
        """Обработка полученного сообщения"""
        try:
            # Пытаемся распарсить JSON
            try:
                data = json.loads(message)
                # Если JSON, то можно извлечь тему и сообщение
                subject = data.get('subject', 'WebSocket сообщение')
                content = data.get('message', message)
                # Добавляем дополнительную информацию из JSON
                if 'sender' in data:
                    content = f"Отправитель: {data['sender']}\n\n{content}"
                logger.debug(f"JSON сообщение от {client_id}: subject={subject}")
                
            except json.JSONDecodeError:
                # Если не JSON, используем сообщение как есть
                subject = "Новое сообщение из WebSocket"
                content = message
                logger.debug(f"Текстовое сообщение от {client_id}")
            
            # Добавляем временную метку
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"Получено: {timestamp}\nОт клиента: {client_id}\n\n{content}"
            
            logger.info(f"Обработка сообщения от {client_id}, тема: {subject}")
            
            # Отправляем email
            success = self.email_sender.send_email(subject, formatted_message)
            
            # Отправляем ответ клиенту
            response = {
                'status': 'success' if success else 'error',
                'message': 'Сообщение отправлено на email' if success else 'Ошибка при отправке email',
                'timestamp': timestamp,
                'message_id': self.message_count
            }
            await websocket.send(json.dumps(response, ensure_ascii=False))
            
            if success:
                logger.info(f"Сообщение #{self.message_count} успешно обработано для {client_id}")
            else:
                logger.warning(f"Сообщение #{self.message_count} не удалось отправить на email")
                self.error_count += 1
            
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения от {client_id}: {e}")
            logger.debug(traceback.format_exc())
            error_response = {
                'status': 'error',
                'message': f'Ошибка: {str(e)}',
                'message_id': self.message_count
            }
            try:
                await websocket.send(json.dumps(error_response, ensure_ascii=False))
            except:
                logger.error(f"Не удалось отправить ответ клиенту {client_id}")
    
    async def start(self):
        """Запуск WebSocket сервера"""
        logger.info("=" * 60)
        logger.info("ЗАПУСК WEBHOOK СЕРВЕРА")
        logger.info("=" * 60)
        logger.info(f"Хост: {self.host}")
        logger.info(f"Порт: {self.port}")
        logger.info(f"Максимум клиентов: {WEBSOCKET_CONFIG['max_connections']}")
        logger.info(f"Максимальный размер сообщения: {APP_CONFIG['max_message_size']} байт")
        logger.info(f"Режим отладки: {APP_CONFIG['debug']}")
        logger.info("=" * 60)
        
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            max_size=APP_CONFIG['max_message_size']
        )
        
        logger.info(f"✅ WebSocket сервер запущен на ws://{self.host}:{self.port}")
        logger.info("Ожидание подключений...")
        
        # Запускаем мониторинг
        asyncio.create_task(self.monitor_stats())
        
        # Держим сервер запущенным
        await server.wait_closed()
    
    async def monitor_stats(self):
        """Мониторинг статистики сервера"""
        while True:
            await asyncio.sleep(60)  # Каждую минуту
            logger.info(f"📊 Статистика: Сообщений: {self.message_count}, "
                       f"Ошибок: {self.error_count}, "
                       f"Клиентов: {len(self.connected_clients)}")

async def main():
    """Главная функция запуска приложения"""
    logger.info("🚀 Запуск приложения Zhaba...")
    
    # Проверяем конфигурацию
    logger.debug("Проверка конфигурации...")
    logger.debug(f"Email конфиг: {EMAIL_CONFIG['email_from']} -> {EMAIL_CONFIG['email_to']}")
    logger.debug(f"WebSocket конфиг: {WEBSOCKET_CONFIG['host']}:{WEBSOCKET_CONFIG['port']}")
    
    # Создаем экземпляр EmailSender
    try:
        email_sender = EmailSender(EMAIL_CONFIG)
        logger.info("✅ Email отправитель инициализирован")
        
        # Тестовая проверка SMTP соединения
        logger.debug("Проверка SMTP соединения...")
        try:
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as test_server:
                test_server.starttls()
                test_server.login(EMAIL_CONFIG['email_from'], EMAIL_CONFIG['email_password'])
                logger.info("✅ SMTP соединение успешно проверено")
        except Exception as e:
            logger.warning(f"⚠️ Предупреждение: SMTP проверка не удалась: {e}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации email отправителя: {e}")
        logger.debug(traceback.format_exc())
        return
    
    # Создаем и запускаем WebSocket сервер
    websocket_server = WebSocketServer(
        email_sender,
        WEBSOCKET_CONFIG['host'],
        WEBSOCKET_CONFIG['port']
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
        logger.info(f"   Пиковое количество клиентов: {len(websocket_server.connected_clients)}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при работе приложения: {e}")
        logger.debug(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение завершено")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")
        logger.critical(traceback.format_exc())

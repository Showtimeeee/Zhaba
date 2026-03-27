import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def test_websocket():
    uri = "ws://localhost:8765"
    
    logger.info(f"Подключение к {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Подключено к WebSocket серверу")
            
            test_message = {
                "subject": "Тестовое сообщение",
                "message": f"Привет! Это тестовое сообщение из WebSocket клиента. Время: {datetime.now()}",
                "sender": "Тестовый клиент"
            }
            
            logger.info(f"📤 Отправка JSON сообщения: {test_message['subject']}")
            await websocket.send(json.dumps(test_message, ensure_ascii=False))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"📥 Ответ сервера: {response_data}")
            
            text_message = f"Простое текстовое сообщение без JSON - {datetime.now()}"
            logger.info(f"📤 Отправка текстового сообщения: {text_message[:50]}...")
            await websocket.send(text_message)
            
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"📥 Ответ сервера: {response_data}")
            
            logger.info("Отправка серии сообщений...")
            for i in range(3):
                test_msg = {
                    "subject": f"Серийное сообщение #{i+1}",
                    "message": f"Это серийное сообщение номер {i+1}",
                    "sender": "Тестовый клиент"
                }
                await websocket.send(json.dumps(test_msg, ensure_ascii=False))
                response = await websocket.recv()
                logger.debug(f"Сообщение {i+1} отправлено, ответ: {response[:100]}")
                await asyncio.sleep(1)
            
            logger.info("✅ Все тестовые сообщения отправлены")
            
    except websockets.exceptions.ConnectionRefused:
        logger.error("❌ Не удалось подключиться к серверу. Убедитесь, что сервер запущен.")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    logger.info("Запуск тестового клиента...")
    asyncio.run(test_websocket())
    logger.info("Тестирование завершено")

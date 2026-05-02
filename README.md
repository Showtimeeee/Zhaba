# Zhaba-App

<img width="387" height="218" alt="zhaba_logo" src="https://github.com/user-attachments/assets/9a083e69-ef48-40ec-a76a-0eb347718776" />

**WebSocket микросервис для отправки сообщений на email.**

---

## Описание

Zhaba-App принимает сообщения через WebSocket и пересылает их на email. Простой, надёжный микросервис с поддержкой очередей, SSL, аутентификации и валидации.

- **WebSocket сервер** — принимает сообщения в реальном времени
- **Отправка email** — через SMTP с поддержкой HTML
- **Очередь сообщений** — автоматический ретрай при недоступности SMTP
- **Rate limiting** — защита от спама и DDoS
- **JSON валидация** — защита от некорректных данных
- **SSL/TLS** — шифрованное WebSocket соединение (wss://)
- **Аутентификация** — опциональный токен для клиентов
- **Health check** — endpoint для мониторинга
- **Логирование** — настраиваемый уровень логов

---

## Установка

```bash
pip install -r requirements.txt
```

---

## Запуск

```bash
python zhaba_app.py
```

С параметрами:
```bash
python zhaba_app.py --host 0.0.0.0 --port 8765
```

---

## Конфигурация

Создайте файл `.env` в корневой директории:

```ini
# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com

# WebSocket
WS_HOST=localhost
WS_PORT=8765
WS_MAX_CONNECTIONS=100

# Безопасность
AUTH_REQUIRED=false
AUTH_TOKEN=your_secret_token
SSL_ENABLED=false
SSL_CERT=path/to/cert.pem
SSL_KEY=path/to/key.pem

# Очередь
QUEUE_ENABLED=false
QUEUE_MAX_SIZE=1000

# Лимиты
RATE_LIMIT_PER_MINUTE=10
MAX_MESSAGE_SIZE=1048576

# Email
EMAIL_MAX_RETRIES=3
EMAIL_RETRY_DELAY=2

# Логирование
LOG_FILE=zhaba.log
LOG_LEVEL=DEBUG
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Database
# Database path is automatically set to data/zhaba.db
# No need to configure, it will be created in the data volume
```

---

## API

### WebSocket

**Адрес:** `ws://localhost:8765`

**Формат сообщения:**
```json
{
  "subject": "Тема письма",
  "message": "Текст сообщения",
  "sender": "Отправитель",
  "html": false
}
```

**Ответ сервера:**
```json
{
  "status": "success",
  "message": "Сообщение отправлено",
  "timestamp": "2024-01-01 12:00:00",
  "message_id": 1,
  "rate_limit_remaining": 9
}
```

**Статусы:**
- `success` — сообщение отправлено
- `queued` — сообщение поставлено в очередь
- `error` — ошибка

### Health Check

**Адрес:** `http://127.0.0.1:8766/health`

**Ответ:**
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "message_count": 100,
  "error_count": 2,
  "connected_clients": 5,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

---

## Тесты

```bash
pytest tests/ -v
```

---

## Примеры

### Простое сообщение

```python
import asyncio
import websockets
import json

async def main():
    async with websockets.connect('ws://localhost:8765') as ws:
        await ws.send(json.dumps({
            'subject': 'Тест',
            'message': 'Привет мир!'
        }))
        response = await ws.recv()
        print(response)

asyncio.run(main())
```

### С HTML

```python
await ws.send(json.dumps({
    'subject': 'HTML Email',
    'message': '<h1>Привет!</h1><p>Это HTML</p>',
    'sender': 'Bot',
    'html': True
}))
```

---

## Лицензия

MIT

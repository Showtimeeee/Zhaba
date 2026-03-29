# Zhaba-App

<img width="387" height="218" alt="zhaba_logo" src="https://github.com/user-attachments/assets/9a083e69-ef48-40ec-a76a-0eb347718776" />

**Микросервис, ловит WebSocket-сообщения с порта и отправляет их на email.**

```bash
pip install -r requirements.txt

python zhaba_app.py
```

---

## `.env`:

```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_password
EMAIL_TO=recipient@example.com

WS_HOST=localhost
WS_PORT=8765
WS_MAX_CONNECTIONS=100

LOG_FILE=zhaba.log
LOG_LEVEL=DEBUG
```

---

`ws://localhost:8765`

---

```json
   {
     "subject": "Тема письма",
     "message": "Текст сообщения",
     "sender": "Отправитель"
   }
```

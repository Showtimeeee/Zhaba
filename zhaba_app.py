import asyncio
import smtplib
import traceback
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_CONFIG
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
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
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
            return False

async def main():
    logger.info("🚀 Запуск приложения Zhaba...")

    try:
        email_sender = EmailSender(EMAIL_CONFIG)
        logger.info("✅ Email отправитель инициализирован")

        try:
            with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as test_server:
                test_server.starttls()
                test_server.login(EMAIL_CONFIG["email_from"], EMAIL_CONFIG["email_password"])
                logger.info("✅ SMTP соединение успешно проверено")
        except Exception as e:
            logger.warning(f"⚠️ Предупреждение: SMTP проверка не удалась: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка инициализации email отправителя: {e}")
        return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение завершено")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")

import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSender:
    def __init__(self, config, max_retries=3, retry_delay=2):
        self.config = config
        self.smtp_server = config["smtp_server"]
        self.smtp_port = config["smtp_port"]
        self.email_from = config["email_from"]
        self.email_password = config["email_password"]
        self.email_to = config["email_to"]
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.html_template = self._get_html_template()

    def _get_html_template(self):
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background: #4F46E5; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 24px; }
        .content { padding: 20px; }
        .meta { background: #f9fafb; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
        .meta-item { margin: 5px 0; color: #6b7280; font-size: 14px; }
        .message { line-height: 1.6; color: #1f2937; }
        .footer { padding: 15px; text-align: center; color: #9ca3af; font-size: 12px; border-top: 1px solid #e5e7eb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{subject}</h1>
        </div>
        <div class="content">
            <div class="meta">
                <div class="meta-item"><strong>Получено:</strong> {timestamp}</div>
                <div class="meta-item"><strong>От:</strong> {sender}</div>
                <div class="meta-item"><strong>IP:</strong> {ip}</div>
            </div>
            <div class="message">
                {message}
            </div>
        </div>
        <div class="footer">
            Отправлено через Zhaba-App
        </div>
    </div>
</body>
</html>"""

    def send_email(self, subject, message, html=False, metadata=None):
        start_time = datetime.now()

        if metadata is None:
            metadata = {}

        for attempt in range(self.max_retries):
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = self.email_from
                msg["To"] = self.email_to
                msg["Subject"] = subject[:100] if len(subject) > 100 else subject

                if html:
                    html_content = self.html_template.format(
                        subject=subject,
                        timestamp=metadata.get("timestamp", ""),
                        sender=metadata.get("sender", "Unknown"),
                        ip=metadata.get("ip", "Unknown"),
                        message=message.replace("\n", "<br>")
                    )
                    msg.attach(MIMEText(message, "plain", "utf-8"))
                    msg.attach(MIMEText(html_content, "html", "utf-8"))
                else:
                    msg.attach(MIMEText(message, "plain", "utf-8"))

                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.email_from, self.email_password)
                    server.send_message(msg)

                elapsed_time = (datetime.now() - start_time).total_seconds()
                return True

            except smtplib.SMTPAuthenticationError:
                return False
            except (smtplib.SMTPException, OSError):
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return False
            except Exception:
                return False

        return False
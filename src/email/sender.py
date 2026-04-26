import os
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
        self.html_template = self._load_template()

    def _load_template(self):
        template_path = os.path.join(os.path.dirname(__file__), "template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

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

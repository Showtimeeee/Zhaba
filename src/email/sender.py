import os
import time
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from src.core.logging_service import log


class EmailSender:
    def __init__(self, config, max_retries=3, retry_delay=2):
        self.config = config
        self.smtp_server = config["smtp_server"]
        self.smtp_port = config["smtp_port"]
        self.email_from = config["email_from"]
        self.email_password = config["email_password"]
        email_to_raw = config["email_to"]
        self.email_to_list = [addr.strip() for addr in email_to_raw.split(',') if addr.strip()]
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.html_template = self._load_template()
        log.info("EmailSender", f"Initialized with {len(self.email_to_list)} recipient(s)", {"smtp_server": self.smtp_server, "smtp_port": self.smtp_port})

    def _load_template(self):
        template_path = os.path.join(os.path.dirname(__file__), "template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    async def send_email(self, subject, message, html=False, metadata=None):
        if metadata is None:
            metadata = {}

        start_time = time.time()
        log.debug("EmailSender", f"Sending email: {subject}", {"recipients": self.email_to_list, "html": html})

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email_from
            msg["To"] = ", ".join(self.email_to_list)
            msg["Subject"] = subject[:100] if len(subject) > 100 else subject
            msg["Date"] = formatdate(localtime=True)

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

            smtp = aiosmtplib.SMTP(hostname=self.smtp_server, port=self.smtp_port, timeout=30)
            await smtp.connect()
            await smtp.starttls()
            await smtp.login(self.email_from, self.email_password)
            await smtp.send_message(msg)
            await smtp.quit()

            duration_ms = (time.time() - start_time) * 1000
            log.email_sent(subject, self.email_to_list, True, duration_ms)
            return True

        except aiosmtplib.SMTPAuthenticationError:
            duration_ms = (time.time() - start_time) * 1000
            log.email_sent(subject, self.email_to_list, False, duration_ms)
            log.error("EmailSender", "Authentication failed", {"smtp_server": self.smtp_server})
            return False
        except (aiosmtplib.SMTPException, OSError) as e:
            duration_ms = (time.time() - start_time) * 1000
            log.email_sent(subject, self.email_to_list, False, duration_ms)
            log.error("EmailSender", f"SMTP error: {str(e)}")
            return False
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log.email_sent(subject, self.email_to_list, False, duration_ms)
            log.error("EmailSender", f"Unexpected error: {str(e)}")
            return False

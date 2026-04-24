import json


class MessageValidator:
    MAX_SUBJECT_LENGTH = 100
    MAX_SENDER_LENGTH = 50
    MAX_MESSAGE_LENGTH = 100000

    ALLOWED_FIELDS = {"subject", "message", "sender", "html"}

    @classmethod
    def validate(cls, data):
        errors = []

        if not isinstance(data, dict):
            return {"valid": False, "errors": ["Expected JSON object"]}

        for key in data.keys():
            if key not in cls.ALLOWED_FIELDS:
                errors.append(f"Unknown field: {key}")

        subject = data.get("subject", "")
        if subject and len(subject) > cls.MAX_SUBJECT_LENGTH:
            errors.append(f"Subject exceeds {cls.MAX_SUBJECT_LENGTH} chars")

        sender = data.get("sender", "")
        if sender and len(sender) > cls.MAX_SENDER_LENGTH:
            errors.append(f"Sender exceeds {cls.MAX_SENDER_LENGTH} chars")

        message = data.get("message", "")
        if message and len(message) > cls.MAX_MESSAGE_LENGTH:
            errors.append(f"Message exceeds {cls.MAX_MESSAGE_LENGTH} chars")

        html = data.get("html")
        if html is not None and not isinstance(html, bool):
            errors.append("Field 'html' must be boolean")

        return {"valid": len(errors) == 0, "errors": errors}

    @classmethod
    def sanitize(cls, data):
        if not isinstance(data, dict):
            return {}

        sanitized = {}
        for key in cls.ALLOWED_FIELDS & data.keys():
            value = data[key]
            if isinstance(value, str):
                value = value.strip()[:cls.MAX_MESSAGE_LENGTH]
            sanitized[key] = value

        return sanitized
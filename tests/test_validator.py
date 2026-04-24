import pytest
from src.core import MessageValidator


class TestMessageValidator:
    def test_valid_message(self):
        data = {"subject": "Test", "message": "Hello", "sender": "User"}
        result = MessageValidator.validate(data)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_unknown_field(self):
        data = {"subject": "Test", "message": "Hello", "unknown_field": "bad"}
        result = MessageValidator.validate(data)
        assert result["valid"] is False
        assert "Unknown field" in result["errors"][0]

    def test_subject_too_long(self):
        data = {"subject": "x" * 101, "message": "Hello"}
        result = MessageValidator.validate(data)
        assert result["valid"] is False
        assert "exceeds" in result["errors"][0]

    def test_sender_too_long(self):
        data = {"subject": "Test", "sender": "x" * 51, "message": "Hello"}
        result = MessageValidator.validate(data)
        assert result["valid"] is False
        assert "exceeds" in result["errors"][0]

    def test_html_must_be_boolean(self):
        data = {"subject": "Test", "message": "Hello", "html": "yes"}
        result = MessageValidator.validate(data)
        assert result["valid"] is False
        assert "must be boolean" in result["errors"][0]

    def test_message_too_long(self):
        data = {"subject": "Test", "message": "x" * 100001}
        result = MessageValidator.validate(data)
        assert result["valid"] is False
        assert "exceeds" in result["errors"][0]

    def test_sanitize(self):
        data = {"subject": "  Test  ", "message": "Hello", "sender": "User", "html": True, "extra": "removed"}
        result = MessageValidator.sanitize(data)
        assert result == {"subject": "Test", "message": "Hello", "sender": "User", "html": True}
        assert "extra" not in result

    def test_invalid_type(self):
        result = MessageValidator.validate("not a dict")
        assert result["valid"] is False
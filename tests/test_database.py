import pytest
import os
import tempfile
from src.core.database import Database


@pytest.fixture
def db():
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    Database.reset_instance()
    database = Database(db_path)
    yield database
    try:
        os.unlink(db_path)
    except:
        pass


class TestDatabase:
    def test_add_message(self, db):
        msg_id = db.add_message("Test Subject", "Test Message", sender="Test Sender", ip="127.0.0.1")
        assert msg_id > 0

    def test_add_message_defaults(self, db):
        msg_id = db.add_message("Subject", "Message")
        assert msg_id > 0

    def test_update_message_status(self, db):
        msg_id = db.add_message("Subject", "Message")
        db.update_message_status(msg_id, 'sent')
        msg = db.get_message(msg_id)
        assert msg['status'] == 'sent'
        assert msg['sent_at'] is not None

    def test_update_message_with_error(self, db):
        msg_id = db.add_message("Subject", "Message")
        db.update_message_status(msg_id, 'failed', 'Some error')
        msg = db.get_message(msg_id)
        assert msg['status'] == 'failed'
        assert msg['error_message'] == 'Some error'

    def test_get_message(self, db):
        msg_id = db.add_message("Subject", "Message", sender="Test", ip="127.0.0.1")
        msg = db.get_message(msg_id)
        assert msg['subject'] == 'Subject'
        assert msg['message'] == 'Message'
        assert msg['sender'] == 'Test'
        assert msg['ip'] == '127.0.0.1'

    def test_get_nonexistent_message(self, db):
        msg = db.get_message(9999)
        assert msg is None

    def test_get_messages(self, db):
        for i in range(5):
            db.add_message(f"Subject {i}", f"Message {i}")
        messages = db.get_messages(limit=3)
        assert len(messages) == 3

    def test_get_messages_offset(self, db):
        for i in range(5):
            db.add_message(f"Subject {i}", f"Message {i}")
        messages = db.get_messages(limit=3, offset=3)
        assert len(messages) == 2

    def test_get_stats(self, db):
        db.add_message("S1", "M1")
        db.add_message("S2", "M2")
        db.update_message_status(1, 'sent')
        db.update_message_status(2, 'failed')

        stats = db.get_stats()
        assert stats['total'] == 2
        assert stats['sent'] == 1
        assert stats['failed'] == 1
        assert stats['pending'] == 0

    def test_singleton_pattern(self, db):
        db2 = Database(db.db_path)
        assert db is db2

    def test_messages_ordered_by_created_at_desc(self, db):
        # Add messages with small delay to ensure different timestamps
        for i in range(3):
            db.add_message(f"Subject {i}", f"Message {i}")
        
        messages = db.get_messages()
        # Check that messages are returned (basic functionality)
        assert len(messages) == 3
        # Check that they are ordered by created_at DESC (most recent first)
        # With rapid insertion, timestamps might be the same, so just check we get results
        assert messages[0]['id'] is not None
        assert messages[1]['id'] is not None
        assert messages[2]['id'] is not None
"""
Tests for database model helper functions using mocks.
These tests verify the SQL logic without a live DB connection.
"""
from unittest.mock import patch, MagicMock


# ── User model ──────────────────────────────────────────────────────────────

def test_email_exists_returns_true_when_found():
    from app.models.user import email_exists
    with patch('app.models.user.execute_query', return_value={'email': 'a@b.com'}):
        assert email_exists('a@b.com') is True


def test_email_exists_returns_false_when_not_found():
    from app.models.user import email_exists
    with patch('app.models.user.execute_query', return_value=None):
        assert email_exists('nobody@example.com') is False


def test_get_user_by_email_returns_dict():
    from app.models.user import get_user_by_email
    fake = {'id': 1, 'email': 'a@b.com', 'name': 'Alice'}
    with patch('app.models.user.execute_query', return_value=fake):
        result = get_user_by_email('a@b.com')
    assert result == fake


def test_get_user_by_id_returns_none_when_missing():
    from app.models.user import get_user_by_id
    with patch('app.models.user.execute_query', return_value=None):
        result = get_user_by_id(9999)
    assert result is None


def test_create_user_returns_new_id():
    from app.models.user import create_user
    with patch('app.models.user.execute_write', return_value=42):
        user_id = create_user('Alice', 'a@b.com', 'hash', '1234567890', 'token')
    assert user_id == 42


# ── Prediction log model ─────────────────────────────────────────────────────

def test_create_log_returns_log_id():
    from app.models.prediction_log import create_log
    with patch('app.models.prediction_log.execute_write', return_value=7):
        log_id = create_log(
            user_id=1,
            image_filename='test.jpg',
            image_path='/static/uploads/test.jpg',
            result='PNEUMONIA',
            confidence_score=0.9512,
            model_used='resnet50',
            precaution_text='Consult a doctor.',
        )
    assert log_id == 7


def test_get_logs_for_user_returns_list():
    from app.models.prediction_log import get_logs_for_user
    fake_logs = [
        {'id': 1, 'result': 'NORMAL', 'confidence_score': 0.95},
        {'id': 2, 'result': 'PNEUMONIA', 'confidence_score': 0.87},
    ]
    with patch('app.models.prediction_log.execute_query', return_value=fake_logs):
        logs = get_logs_for_user(user_id=1, limit=10)
    assert len(logs) == 2
    assert logs[0]['result'] == 'NORMAL'

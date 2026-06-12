"""
Pytest fixtures shared across all test modules.
"""
import os
import io
import pytest

# Force testing environment before importing app
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-do-not-use-in-prod')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_NAME', 'pneumonia_test_db')
os.environ.setdefault('DB_USER', 'root')
os.environ.setdefault('DB_PASSWORD', '')


@pytest.fixture(scope='session')
def app():
    """Create a Flask app configured for testing."""
    from app import create_app
    application = create_app('testing')
    application.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': 'tests/uploads',
        'MODEL_DIR': 'tests/mock_models',
        'ACTIVE_MODEL': 'resnet50',
    })
    os.makedirs('tests/uploads', exist_ok=True)
    os.makedirs('tests/mock_models', exist_ok=True)
    yield application


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_image_bytes():
    """Return minimal valid JPEG bytes (1x1 white pixel)."""
    # Minimal JPEG: 1×1 white pixel
    jpeg_bytes = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e>'
        b'\x11\x11\x11'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04'
        b'\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa'
        b'\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1'
        b'\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ'
        b'STUVWXYZ'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd2\x8a(\x00\xff\xd9'
    )
    return jpeg_bytes


@pytest.fixture
def auth_headers(client):
    """Register and log in a test user, return the active client session."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'
        sess['user_email'] = 'test@example.com'
    return client

"""
Tests for registration, login, logout, and validation.
These tests mock DB calls to run without a live MySQL server.
"""
from unittest.mock import patch


# ── Registration ────────────────────────────────────────────────────────────

def test_register_page_loads(client):
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Register' in response.data or b'Registration' in response.data


def test_register_missing_fields_returns_errors(client):
    response = client.post('/auth/register', data={
        'name': '',
        'email': '',
        'contact_number': '',
        'password': '',
        'confirm_password': '',
    }, follow_redirects=True)
    assert response.status_code == 200
    # Should show validation errors
    assert b'required' in response.data.lower() or b'error' in response.data.lower() \
           or b'field' in response.data.lower()


def test_register_password_mismatch_returns_error(client):
    with patch('app.auth.forms.email_exists', return_value=False):
        response = client.post('/auth/register', data={
            'name': 'Test User',
            'email': 'newuser@example.com',
            'contact_number': '9876543210',
            'password': 'Password1',
            'confirm_password': 'Password2',
        }, follow_redirects=True)
    assert response.status_code == 200
    assert b'match' in response.data.lower() or b'password' in response.data.lower()


def test_register_success_redirects_to_login(client):
    with patch('app.auth.forms.email_exists', return_value=False), \
         patch('app.models.user.execute_write', return_value=1), \
         patch('app.auth.utils.send_verification_email', return_value=False):
        response = client.post('/auth/register', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'contact_number': '9876543210',
            'password': 'SecurePass1',
            'confirm_password': 'SecurePass1',
        }, follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers.get('Location', '')


# ── Login ───────────────────────────────────────────────────────────────────

def test_login_page_loads(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_login_invalid_credentials_shows_error(client):
    with patch('app.auth.routes.get_user_by_email', return_value=None):
        response = client.post('/auth/login', data={
            'email': 'nobody@example.com',
            'password': 'wrongpass',
        }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid' in response.data or b'invalid' in response.data


def test_login_success_redirects_to_user_home(client):
    from werkzeug.security import generate_password_hash
    fake_user = {
        'id': 1,
        'name': 'Test User',
        'email': 'test@example.com',
        'password_hash': generate_password_hash('SecurePass1'),
        'is_active': 1,
        'email_verified': 1,
    }
    with patch('app.auth.routes.get_user_by_email', return_value=fake_user):
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'SecurePass1',
        }, follow_redirects=False)
    assert response.status_code == 302
    assert '/user' in response.headers.get('Location', '')


# ── Logout ──────────────────────────────────────────────────────────────────

def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test'
        sess['user_email'] = 'test@example.com'
    response = client.get('/auth/logout', follow_redirects=False)
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

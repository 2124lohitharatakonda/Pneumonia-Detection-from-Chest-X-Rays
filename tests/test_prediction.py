"""
Tests for the prediction blueprint — upload, inference, history.
ML model calls are mocked to avoid requiring trained .h5 files.
"""
import io
from unittest.mock import patch, MagicMock


FAKE_PREDICTION = {
    'result': 'NORMAL',
    'confidence': 0.9512,
    'model_used': 'resnet50',
    'precaution_text': 'No pneumonia detected.',
    'raw_scores': {'NORMAL': 0.9512, 'PNEUMONIA': 0.0488},
}


def _login(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'
        sess['user_email'] = 'test@example.com'


# ── User Home ───────────────────────────────────────────────────────────────

def test_user_home_loads_when_logged_in(client):
    _login(client)
    with patch('app.prediction.routes.get_logs_for_user', return_value=[]):
        response = client.get('/user')
    assert response.status_code == 200
    assert b'Upload' in response.data or b'X-Ray' in response.data


# ── Predict ─────────────────────────────────────────────────────────────────

def test_predict_no_file_redirects(client):
    _login(client)
    response = client.post('/predict', data={}, follow_redirects=False)
    assert response.status_code in (302, 200)


def test_predict_invalid_extension_redirects(client):
    _login(client)
    data = {
        'image': (io.BytesIO(b'fake data'), 'test.pdf'),
        'model_choice': 'resnet50',
    }
    with patch('app.prediction.routes.get_logs_for_user', return_value=[]):
        response = client.post(
            '/predict', data=data,
            content_type='multipart/form-data',
            follow_redirects=True,
        )
    assert response.status_code == 200
    # Should show an error or redirect back to upload page
    assert b'JPEG' in response.data or b'invalid' in response.data.lower() \
           or b'Upload' in response.data


def test_predict_valid_image_returns_result(client, sample_image_bytes):
    _login(client)
    data = {
        'image': (io.BytesIO(sample_image_bytes), 'xray.jpg'),
        'model_choice': 'resnet50',
    }
    with patch('app.prediction.routes.predict', return_value=FAKE_PREDICTION), \
         patch('app.prediction.routes.create_log', return_value=1):
        response = client.post(
            '/predict', data=data,
            content_type='multipart/form-data',
            follow_redirects=True,
        )
    assert response.status_code == 200
    assert b'NORMAL' in response.data or b'Result' in response.data


# ── History ─────────────────────────────────────────────────────────────────

def test_history_page_loads_for_logged_in_user(client):
    _login(client)
    with patch('app.prediction.routes.get_logs_for_user', return_value=[]):
        response = client.get('/history')
    assert response.status_code == 200
    assert b'History' in response.data or b'prediction' in response.data.lower()


def test_history_shows_empty_state(client):
    _login(client)
    with patch('app.prediction.routes.get_logs_for_user', return_value=[]):
        response = client.get('/history')
    assert response.status_code == 200
    assert b'No predictions' in response.data or b'yet' in response.data.lower()

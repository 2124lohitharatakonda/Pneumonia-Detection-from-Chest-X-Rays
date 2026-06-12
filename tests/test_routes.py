"""
Tests for public routes (home, about, 404, 405).
"""


def test_home_page_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'PneumoDetect' in response.data or b'Pneumonia' in response.data


def test_about_page_returns_200(client):
    response = client.get('/about')
    assert response.status_code == 200
    assert b'About' in response.data


def test_404_returns_404(client):
    response = client.get('/this-route-does-not-exist-xyz')
    assert response.status_code == 404


def test_user_home_redirects_when_not_logged_in(client):
    response = client.get('/user', follow_redirects=False)
    # Should redirect to login
    assert response.status_code in (301, 302)
    assert b'login' in response.headers['Location'].lower() or \
           '/auth/login' in response.headers['Location']


def test_predict_redirects_when_not_logged_in(client):
    response = client.post('/predict', data={}, follow_redirects=False)
    assert response.status_code in (301, 302)


def test_history_redirects_when_not_logged_in(client):
    response = client.get('/history', follow_redirects=False)
    assert response.status_code in (301, 302)

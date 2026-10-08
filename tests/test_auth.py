from app.models.user import User
from app.models.security_log import SecurityLog, EventType

def test_successful_login(client, auth_helper):
    res = auth_helper.login('homeowner', 'HomeOwner#2026!')
    assert res.status_code == 200
    assert b"Welcome back, homeowner!" in res.data
    assert b"Security Command Center" in res.data

def test_invalid_password(client, auth_helper):
    res = client.post('/login', data={'username': 'homeowner', 'password': 'WrongPassword123'}, follow_redirects=True)
    assert b"Invalid username or password." in res.data

    with client.application.app_context():
        log = SecurityLog.query.filter_by(event_type=EventType.LOGIN_FAILED).first()
        assert log is not None
        assert "Failed authentication attempt" in log.description

def test_missing_credentials(client):
    res = client.post('/login', data={'username': '', 'password': ''}, follow_redirects=True)
    assert b"Username and password are required." in res.data

def test_api_login_success(client):
    res = client.post('/api/login', json={'username': 'admin', 'password': 'Admin#2026!'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['message'] == 'Login successful'
    assert data['user']['username'] == 'admin'
    assert data['user']['role'] == 'ADMIN'

def test_api_login_failure(client):
    res = client.post('/api/login', json={'username': 'admin', 'password': 'BadPassword'})
    assert res.status_code == 401
    assert res.get_json()['error'] == 'Authentication Failed'

def test_logout(client, auth_helper):
    auth_helper.login('homeowner', 'HomeOwner#2026!')
    res = auth_helper.logout()
    assert res.status_code == 200
    assert b"You have been successfully logged out." in res.data

def test_passwords_not_stored_plaintext(app):
    with app.app_context():
        user = User.query.filter_by(username='homeowner').first()
        assert user.password_hash != 'HomeOwner#2026!'
        assert user.password_hash.startswith('$2b$')  # bcrypt signature
        assert user.check_password('HomeOwner#2026!') is True
        assert user.check_password('Wrong') is False

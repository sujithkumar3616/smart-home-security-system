from app.models.device import Device
from app.models.security_log import SecurityLog, EventType

def test_homeowner_lock_and_unlock(client, auth_helper, app):
    # Login as Homeowner
    auth_helper.login('homeowner', 'HomeOwner#2026!')

    # Unlock door
    res = client.post('/lock/operate', data={'device_id': 'DEV-LOCK-001', 'command': 'UNLOCK'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Smart lock unlocked successfully" in res.data

    with app.app_context():
        from app import db
        lock = db.session.get(Device, 'DEV-LOCK-001')
        assert lock.current_state == 'UNLOCKED'
        log = SecurityLog.query.filter_by(event_type=EventType.DOOR_UNLOCKED).first()
        assert log is not None
        assert "UNLOCKED by user_id" in log.description

    # Lock door
    res = client.post('/lock/operate', data={'device_id': 'DEV-LOCK-001', 'command': 'LOCK'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Smart lock locked successfully" in res.data

    with app.app_context():
        from app import db
        lock = db.session.get(Device, 'DEV-LOCK-001')
        assert lock.current_state == 'LOCKED'
        log = SecurityLog.query.filter_by(event_type=EventType.DOOR_LOCKED).first()
        assert log is not None

def test_family_member_unauthorized_unlock_rejected(client, auth_helper, app):
    # Login as Family Member
    auth_helper.login('familymember', 'Family#2026!')

    # Attempt to unlock door
    res = client.post('/lock/operate', data={'device_id': 'DEV-LOCK-001', 'command': 'UNLOCK'})
    # Must be HTTP 403
    assert res.status_code == 403
    assert b"Access Denied: Family members do not have permission to unlock the smart door" in res.data

    with app.app_context():
        from app import db
        lock = db.session.get(Device, 'DEV-LOCK-001')
        # Lock state must remain LOCKED
        assert lock.current_state == 'LOCKED'

        # Security event must be logged
        log = SecurityLog.query.filter_by(event_type=EventType.DOOR_UNLOCK_DENIED).first()
        assert log is not None
        assert log.severity == 'HIGH'
        assert "attempted to UNLOCK" in log.description

def test_direct_api_unlock_bypass_prevented(client, auth_helper, app):
    # Attempting to bypass web UI by directly calling the REST API endpoint as family member
    auth_helper.login('familymember', 'Family#2026!')

    res = client.post('/api/devices/DEV-LOCK-001/unlock')
    assert res.status_code == 403
    data = res.get_json()
    assert data['code'] == 403
    assert "Family members do not have permission to unlock" in data['message']

    with app.app_context():
        from app import db
        lock = db.session.get(Device, 'DEV-LOCK-001')
        assert lock.current_state == 'LOCKED'

def test_invalid_device_lock_operation(client, auth_helper):
    auth_helper.login('homeowner', 'HomeOwner#2026!')
    res = client.post('/api/devices/NON-EXISTENT/lock')
    assert res.status_code == 404

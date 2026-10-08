from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.notification import Notification, NotificationSeverity
from app.models.security_log import SecurityLog, EventType

def test_sensor_event_processing(client, app):
    # Simulate telemetry event via IoT Gateway token
    headers = {'X-Gateway-Token': 'test-gateway-token-12345'}
    res = client.post('/api/sensors/event', json={
        'device_id': 'DEV-MOT-001',
        'sensor_type': 'MOTION',
        'value': 'MOTION_DETECTED'
    }, headers=headers)

    assert res.status_code == 200
    data = res.get_json()
    with app.app_context():
        from app import db
        # Verify stored in sensor_data table
        reading = SensorData.query.filter_by(device_id='DEV-MOT-001').first()
        assert reading is not None
        assert reading.value == 'MOTION_DETECTED'

        # Verify device current_state updated
        dev = db.session.get(Device, 'DEV-MOT-001')
        assert dev.current_state == 'MOTION_DETECTED'

        # Verify rule was triggered (light turned ON)
        light = db.session.get(Device, 'DEV-LIGHT-001')
        assert light.current_state == 'ON'

def test_door_opened_while_locked_security_alert(client, app):
    headers = {'X-Gateway-Token': 'test-gateway-token-12345'}

    # Ensure lock is locked
    with app.app_context():
        from app import db
        lock = db.session.get(Device, 'DEV-LOCK-001')
        lock.current_state = 'LOCKED'
        db.session.commit()

    # Trigger door open
    res = client.post('/api/sensors/event', json={
        'device_id': 'DEV-DOOR-001',
        'sensor_type': 'DOOR',
        'value': 'DOOR_OPEN'
    }, headers=headers)

    assert res.status_code == 200

    with app.app_context():
        # Critical alert must be generated
        alert = Notification.query.filter_by(severity=NotificationSeverity.CRITICAL).first()
        assert alert is not None
        assert "Door was opened while Smart Lock" in alert.message

        # Security log must record potential forced entry
        log = SecurityLog.query.filter_by(event_type=EventType.SECURITY_ALERT).first()
        assert log is not None
        assert "Potential forced entry" in log.description

def test_unknown_device_rejected(client):
    headers = {'X-Gateway-Token': 'test-gateway-token-12345'}
    res = client.post('/api/sensors/event', json={
        'device_id': 'DEV-GHOST-999',
        'sensor_type': 'MOTION',
        'value': 'DETECTED'
    }, headers=headers)

    assert res.status_code == 404
    assert "Unknown device" in res.get_json()['message']

def test_device_auth_failure_invalid_key(client, app):
    # DEV-MOT-001 has key 'motion-secret-key-001'. Supply wrong key without gateway token
    headers = {'X-Device-Key': 'wrong-key-xyz'}
    res = client.post('/api/sensors/event', json={
        'device_id': 'DEV-MOT-001',
        'sensor_type': 'MOTION',
        'value': 'MOTION_DETECTED'
    }, headers=headers)

    assert res.status_code == 401
    assert "Device authentication failed" in res.get_json()['message']

    with app.app_context():
        log = SecurityLog.query.filter_by(event_type=EventType.DEVICE_AUTHENTICATION_FAILURE).first()
        assert log is not None

def test_unauthenticated_sensor_event_rejected(client):
    res = client.post('/api/sensors/event', json={
        'device_id': 'DEV-MOT-001',
        'sensor_type': 'MOTION',
        'value': 'MOTION_DETECTED'
    })
    assert res.status_code == 401

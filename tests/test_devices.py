from app.models.device import Device, DeviceType, DeviceStatus

def test_get_devices_list(client, auth_helper):
    auth_helper.login('homeowner', 'HomeOwner#2026!')
    res = client.get('/api/devices')
    assert res.status_code == 200
    data = res.get_json()
    assert data['count'] >= 6
    device_ids = [d['device_id'] for d in data['devices']]
    assert 'DEV-LOCK-001' in device_ids
    assert 'DEV-MOT-001' in device_ids

def test_admin_device_registration(client, auth_helper, app):
    auth_helper.login('admin', 'Admin#2026!')
    res = client.post('/api/devices', json={
        'device_id': 'DEV-SIREN-001',
        'device_name': 'Exterior Siren Alarm',
        'device_type': DeviceType.SMART_LIGHT,
        'device_key': 'siren-secret-key-123'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['device']['device_id'] == 'DEV-SIREN-001'

    with app.app_context():
        from app import db
        dev = db.session.get(Device, 'DEV-SIREN-001')
        assert dev is not None
        assert dev.verify_device_key('siren-secret-key-123') is True

def test_non_admin_cannot_register_device(client, auth_helper):
    auth_helper.login('homeowner', 'HomeOwner#2026!')
    res = client.post('/api/devices', json={
        'device_id': 'DEV-HACK-001',
        'device_name': 'Rogue Device',
        'device_type': DeviceType.CAMERA
    })
    assert res.status_code == 403

def test_invalid_device_registration_payload(client, auth_helper):
    auth_helper.login('admin', 'Admin#2026!')
    # Invalid device type
    res = client.post('/api/devices', json={
        'device_id': 'DEV-INVALID-001',
        'device_name': 'Bad Type Device',
        'device_type': 'SPY_DRONE'
    })
    assert res.status_code == 400
    assert "Invalid device type" in res.get_json()['message']

def test_device_status_update(client, auth_helper, app):
    auth_helper.login('admin', 'Admin#2026!')
    res = client.put('/api/devices/DEV-CAM-001/status', json={'status': 'OFFLINE'})
    assert res.status_code == 200

    with app.app_context():
        from app import db
        cam = db.session.get(Device, 'DEV-CAM-001')
        assert cam.status == DeviceStatus.OFFLINE

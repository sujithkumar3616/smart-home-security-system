import pytest
from app import create_app, db
from app.models.user import User, UserRole
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.automation import AutomationRule

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        # Seed Users
        admin = User(username='admin', role=UserRole.ADMIN)
        admin.set_password('Admin#2026!')

        homeowner = User(username='homeowner', role=UserRole.HOMEOWNER)
        homeowner.set_password('HomeOwner#2026!')

        family = User(username='familymember', role=UserRole.FAMILY_MEMBER)
        family.set_password('Family#2026!')

        db.session.add_all([admin, homeowner, family])
        db.session.flush()

        # Seed standard devices
        lock = Device(
            device_id='DEV-LOCK-001',
            device_name='Front Door Smart Lock',
            device_type=DeviceType.SMART_LOCK,
            status=DeviceStatus.ONLINE,
            current_state='LOCKED',
            owner_id=homeowner.user_id
        )
        lock.set_device_key('lock-secret-key-001')

        motion = Device(
            device_id='DEV-MOT-001',
            device_name='Living Room Motion Sensor',
            device_type=DeviceType.MOTION_SENSOR,
            status=DeviceStatus.ONLINE,
            current_state='CLEAR',
            owner_id=homeowner.user_id
        )
        motion.set_device_key('motion-secret-key-001')

        door = Device(
            device_id='DEV-DOOR-001',
            device_name='Main Entrance Contact Sensor',
            device_type=DeviceType.DOOR_SENSOR,
            status=DeviceStatus.ONLINE,
            current_state='CLOSED',
            owner_id=homeowner.user_id
        )
        door.set_device_key('door-secret-key-001')

        light = Device(
            device_id='DEV-LIGHT-001',
            device_name='Front Porch Smart Light',
            device_type=DeviceType.SMART_LIGHT,
            status=DeviceStatus.ONLINE,
            current_state='OFF',
            owner_id=homeowner.user_id
        )
        light.set_device_key('light-secret-key-001')

        temp = Device(
            device_id='DEV-TEMP-001',
            device_name='Climate Sensor',
            device_type=DeviceType.TEMP_SENSOR,
            status=DeviceStatus.ONLINE,
            current_state='22.5',
            owner_id=homeowner.user_id
        )

        camera = Device(
            device_id='DEV-CAM-001',
            device_name='Entrance Security Camera',
            device_type=DeviceType.CAMERA,
            status=DeviceStatus.ONLINE,
            current_state='ACTIVE',
            owner_id=homeowner.user_id
        )

        db.session.add_all([lock, motion, door, light, temp, camera])

        # Default automation rule
        rule = AutomationRule(
            user_id=homeowner.user_id,
            name='Motion Porch Light',
            trigger='DEV-MOT-001:MOTION_DETECTED',
            condition='ALWAYS',
            action='DEV-LIGHT-001:ON|NOTIFY:Living room motion triggered porch light',
            status='ENABLED'
        )
        db.session.add(rule)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

class AuthClientHelper:
    def __init__(self, client):
        self.client = client

    def login(self, username, password):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def login_api(self, username, password):
        return self.client.post('/api/login', json={
            'username': username,
            'password': password
        })

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

@pytest.fixture
def auth_helper(client):
    return AuthClientHelper(client)

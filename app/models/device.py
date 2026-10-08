from datetime import datetime
import hashlib
from app import db

class DeviceType:
    SMART_LOCK = 'SMART_LOCK'
    MOTION_SENSOR = 'MOTION_SENSOR'
    DOOR_SENSOR = 'DOOR_SENSOR'
    SMART_LIGHT = 'SMART_LIGHT'
    TEMP_SENSOR = 'TEMP_SENSOR'
    CAMERA = 'CAMERA'

    ALL = [SMART_LOCK, MOTION_SENSOR, DOOR_SENSOR, SMART_LIGHT, TEMP_SENSOR, CAMERA]

class DeviceStatus:
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'
    ERROR = 'ERROR'

    ALL = [ONLINE, OFFLINE, ERROR]

class Device(db.Model):
    __tablename__ = 'devices'

    device_id = db.Column(db.String(64), primary_key=True)
    device_name = db.Column(db.String(128), nullable=False)
    device_type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), default=DeviceStatus.ONLINE, nullable=False)
    current_state = db.Column(db.String(64), default='DEFAULT', nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    device_key_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sensor_readings = db.relationship('SensorData', backref='device', lazy='dynamic', cascade='all, delete-orphan')

    def set_device_key(self, raw_key: str):
        self.device_key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    def verify_device_key(self, raw_key: str) -> bool:
        if not self.device_key_hash:
            return False
        computed = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        return computed == self.device_key_hash

    def to_dict(self):
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'status': self.status,
            'current_state': self.current_state,
            'owner_id': self.owner_id,
            'owner_name': self.owner.username if self.owner else 'System',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

    def __repr__(self):
        return f"<Device {self.device_id} - {self.device_name} ({self.device_type})>"

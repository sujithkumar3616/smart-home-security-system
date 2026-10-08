from datetime import datetime
from app import db

class LogSeverity:
    INFO = 'INFO'
    WARNING = 'WARNING'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

    ALL = [INFO, WARNING, HIGH, CRITICAL]

class EventType:
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILED = 'LOGIN_FAILED'
    LOGOUT = 'LOGOUT'
    DEVICE_REGISTERED = 'DEVICE_REGISTERED'
    DEVICE_UPDATED = 'DEVICE_UPDATED'
    DEVICE_AUTHENTICATION_FAILURE = 'DEVICE_AUTHENTICATION_FAILURE'
    DOOR_LOCKED = 'DOOR_LOCKED'
    DOOR_UNLOCKED = 'DOOR_UNLOCKED'
    DOOR_UNLOCK_DENIED = 'DOOR_UNLOCK_DENIED'
    UNAUTHORIZED_COMMAND = 'UNAUTHORIZED_COMMAND'
    AUTOMATION_CREATED = 'AUTOMATION_CREATED'
    AUTOMATION_MODIFIED = 'AUTOMATION_MODIFIED'
    AUTOMATION_DELETED = 'AUTOMATION_DELETED'
    AUTOMATION_TRIGGERED = 'AUTOMATION_TRIGGERED'
    PRIVILEGE_CHANGE = 'PRIVILEGE_CHANGE'
    SECURITY_ALERT = 'SECURITY_ALERT'
    SENSOR_EVENT = 'SENSOR_EVENT'

class SecurityLog(db.Model):
    __tablename__ = 'security_logs'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    device_id = db.Column(db.String(64), db.ForeignKey('devices.device_id'), nullable=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)
    severity = db.Column(db.String(32), default=LogSeverity.INFO, nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Note: User relationship is defined on User model backref='user'
    device = db.relationship('Device', backref='security_logs', lazy=True)

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'System/Anonymous',
            'device_id': self.device_id,
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<SecurityLog [{self.severity}] {self.event_type}: {self.description[:40]}>"

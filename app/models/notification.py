from datetime import datetime
from app import db

class NotificationSeverity:
    INFO = 'INFO'
    WARNING = 'WARNING'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

    ALL = [INFO, WARNING, HIGH, CRITICAL]

class NotificationStatus:
    UNREAD = 'UNREAD'
    READ = 'READ'
    DISMISSED = 'DISMISSED'

class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True) # Null for broadcast to authorized users
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(32), default=NotificationSeverity.INFO, nullable=False)
    status = db.Column(db.String(32), default=NotificationStatus.UNREAD, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'All Residents',
            'message': self.message,
            'severity': self.severity,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<Notification [{self.severity}] {self.message[:30]}>"

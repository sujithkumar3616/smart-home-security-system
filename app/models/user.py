from datetime import datetime
import bcrypt
from app import db

class UserRole:
    HOMEOWNER = 'HOMEOWNER'
    FAMILY_MEMBER = 'FAMILY_MEMBER'
    ADMIN = 'ADMIN'

    ALL = [HOMEOWNER, FAMILY_MEMBER, ADMIN]

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=UserRole.FAMILY_MEMBER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    devices = db.relationship('Device', backref='owner', lazy='dynamic')
    automation_rules = db.relationship('AutomationRule', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    security_logs = db.relationship('SecurityLog', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password: str):
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

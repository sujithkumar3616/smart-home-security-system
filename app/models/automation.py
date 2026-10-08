from datetime import datetime
import json
from app import db

class AutomationRule(db.Model):
    __tablename__ = 'automation_rules'

    rule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(128), nullable=False, default='Automation Rule')
    trigger = db.Column(db.String(256), nullable=False)    # e.g., "DEV-MOT-001:MOTION_DETECTED" or JSON
    condition = db.Column(db.String(256), nullable=True)  # e.g., "ALWAYS" or "TIME_AFTER:23:00"
    action = db.Column(db.String(256), nullable=False)     # e.g., "DEV-LIGHT-001:ON|NOTIFY:Light turned on due to motion"
    status = db.Column(db.String(32), default='ENABLED', nullable=False) # ENABLED, DISABLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'rule_id': self.rule_id,
            'user_id': self.user_id,
            'name': self.name,
            'trigger': self.trigger,
            'condition': self.condition,
            'action': self.action,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<AutomationRule {self.rule_id}: {self.name} ({self.status})>"

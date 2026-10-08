from datetime import datetime
from app import db

class SensorData(db.Model):
    __tablename__ = 'sensor_data'

    data_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(64), db.ForeignKey('devices.device_id'), nullable=False, index=True)
    sensor_type = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(128), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'data_id': self.data_id,
            'device_id': self.device_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<SensorData {self.device_id}:{self.sensor_type}={self.value}>"

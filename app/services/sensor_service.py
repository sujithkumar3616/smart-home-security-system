from datetime import datetime, timezone
from flask import current_app
from app import db
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.sensor_data import SensorData
from app.models.security_log import EventType, LogSeverity
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.automation_service import AutomationService

class SensorService:
    @staticmethod
    def get_recent_readings(device_id=None, limit=50):
        query = SensorData.query
        if device_id:
            query = query.filter_by(device_id=device_id)
        return query.order_by(SensorData.timestamp.desc()).limit(limit).all()

    @staticmethod
    def process_sensor_event(device_id: str, sensor_type: str, value: str, auth_key: str = None, is_gateway: bool = False):
        """
        Process sensor reading from IoT device simulator or physical gateway.
        Validates device, checks cryptographic authentication, saves telemetry,
        triggers automation rules, and dispatches security alerts.
        """
        if not device_id or not sensor_type or value is None:
            return False, "Device ID, sensor type, and value are required.", 400

        device = db.session.get(Device, device_id.strip())
        if not device:
            AuditService.log_event(
                event_type=EventType.DEVICE_AUTHENTICATION_FAILURE,
                severity=LogSeverity.WARNING,
                description=f"Sensor event rejected: Unknown device '{device_id}'"
            )
            return False, f"Unknown device '{device_id}'", 404

        # Device authentication check
        if device.device_key_hash and not is_gateway:
            if not auth_key or not device.verify_device_key(auth_key):
                AuditService.log_event(
                    event_type=EventType.DEVICE_AUTHENTICATION_FAILURE,
                    severity=LogSeverity.HIGH,
                    description=f"Device authentication failed for '{device_id}'",
                    device_id=device_id
                )
                NotificationService.create_alert(
                    message=f"SECURITY ALERT: Device authentication failure for device {device_id}",
                    severity=LogSeverity.HIGH
                )
                return False, "Device authentication failed: Invalid or missing device key", 401

        # Store reading in database
        reading = SensorData(
            device_id=device.device_id,
            sensor_type=sensor_type.strip().upper(),
            value=str(value).strip(),
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(reading)

        # Update device current state and timestamp
        device.current_state = str(value).strip().upper()
        device.last_activity = datetime.now(timezone.utc)
        device.status = DeviceStatus.ONLINE
        db.session.commit()

        # Audit log for sensor event
        val_upper = str(value).strip().upper()
        AuditService.log_event(
            event_type=EventType.SENSOR_EVENT,
            severity=LogSeverity.INFO,
            description=f"Sensor '{sensor_type}' on '{device.device_name}' reported '{val_upper}'",
            device_id=device.device_id
        )

        # Security breach analysis: Door opened while lock is LOCKED
        if sensor_type.upper() in ['DOOR', 'DOOR_SENSOR'] and val_upper in ['OPEN', 'DOOR_OPEN']:
            # Check lock state
            locks = Device.query.filter_by(device_type=DeviceType.SMART_LOCK).all()
            for l in locks:
                if l.current_state == 'LOCKED':
                    NotificationService.create_alert(
                        message=f"CRITICAL SECURITY ALERT: Door was opened while Smart Lock ({l.device_id}) was LOCKED!",
                        severity=LogSeverity.CRITICAL
                    )
                    AuditService.log_event(
                        event_type=EventType.SECURITY_ALERT,
                        severity=LogSeverity.CRITICAL,
                        description=f"Potential forced entry: Door opened while lock '{l.device_name}' was LOCKED",
                        device_id=l.device_id
                    )

        elif sensor_type.upper() in ['MOTION', 'MOTION_SENSOR'] and val_upper in ['DETECTED', 'MOTION_DETECTED']:
            NotificationService.create_alert(
                message=f"Motion detected by '{device.device_name}'",
                severity=LogSeverity.WARNING
            )

        # Evaluate automation rules
        executed_rules = AutomationService.evaluate_rules(device.device_id, val_upper)

        return True, {
            'reading': reading.to_dict(),
            'current_state': device.current_state,
            'rules_executed': executed_rules
        }, 200

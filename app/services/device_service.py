from datetime import datetime, timezone
import re
from app import db
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.user import UserRole
from app.models.security_log import EventType, LogSeverity
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

class DeviceService:
    @staticmethod
    def get_all_devices():
        return Device.query.order_by(Device.device_name.asc()).all()

    @staticmethod
    def get_device(device_id: str):
        if not device_id:
            return None
        return db.session.get(Device, device_id.strip())

    @staticmethod
    def register_device(device_id: str, device_name: str, device_type: str, owner_id=None, raw_key=None, actor_id=None):
        """
        Register a new device. Only Admin is authorized to register devices.
        """
        if not device_id or not re.match(r'^[a-zA-Z0-9_\-]+$', device_id.strip()):
            return None, "Device ID must contain only alphanumeric characters, dashes, and underscores."
        
        device_id = device_id.strip()
        if len(device_id) < 3 or len(device_id) > 64:
            return None, "Device ID length must be between 3 and 64 characters."

        if not device_name or len(device_name.strip()) < 2:
            return None, "Device name must be at least 2 characters long."

        if device_type not in DeviceType.ALL:
            return None, f"Invalid device type. Allowed types: {', '.join(DeviceType.ALL)}"

        existing = db.session.get(Device, device_id)
        if existing:
            return None, f"Device with ID '{device_id}' already exists."

        # Initial state based on device type
        initial_states = {
            DeviceType.SMART_LOCK: 'LOCKED',
            DeviceType.MOTION_SENSOR: 'CLEAR',
            DeviceType.DOOR_SENSOR: 'CLOSED',
            DeviceType.SMART_LIGHT: 'OFF',
            DeviceType.TEMP_SENSOR: '21.0',
            DeviceType.CAMERA: 'ACTIVE'
        }

        device = Device(
            device_id=device_id,
            device_name=device_name.strip(),
            device_type=device_type,
            status=DeviceStatus.ONLINE,
            current_state=initial_states.get(device_type, 'ONLINE'),
            owner_id=owner_id
        )

        if raw_key:
            device.set_device_key(raw_key)

        try:
            db.session.add(device)
            db.session.commit()

            AuditService.log_event(
                event_type=EventType.DEVICE_REGISTERED,
                severity=LogSeverity.INFO,
                description=f"Device '{device_name}' ({device_id}) registered of type {device_type}",
                user_id=actor_id,
                device_id=device_id
            )
            return device, None
        except Exception as e:
            db.session.rollback()
            return None, f"Database error registering device: {str(e)}"

    @staticmethod
    def execute_command(device_id: str, command: str, user_id: int, user_role: str):
        """
        Execute command on a device with strict backend authorization.
        """
        device = DeviceService.get_device(device_id)
        if not device:
            AuditService.log_event(
                event_type=EventType.UNAUTHORIZED_COMMAND,
                severity=LogSeverity.WARNING,
                description=f"Command '{command}' rejected: Device '{device_id}' not found",
                user_id=user_id
            )
            return False, "Device not found", 404

        cmd = command.strip().upper()

        # Authorization matrix enforcement
        if device.device_type == DeviceType.SMART_LOCK:
            if cmd == 'UNLOCK':
                # FAMILY_MEMBER is explicitly disallowed from unlocking the door
                if user_role == UserRole.FAMILY_MEMBER:
                    desc = f"Access Denied: Family Member (user_id={user_id}) attempted to UNLOCK '{device.device_name}' ({device_id})"
                    AuditService.log_event(
                        event_type=EventType.DOOR_UNLOCK_DENIED,
                        severity=LogSeverity.HIGH,
                        description=desc,
                        user_id=user_id,
                        device_id=device_id
                    )
                    NotificationService.create_alert(
                        message=f"SECURITY ALERT: Unauthorized door unlock attempt by Family Member on {device.device_name}",
                        severity=LogSeverity.HIGH,
                        user_id=user_id
                    )
                    return False, "Access Denied: Family members do not have permission to unlock the smart door.", 403

                if user_role not in [UserRole.HOMEOWNER, UserRole.ADMIN]:
                    return False, "Access Denied: Insufficient permissions to unlock door.", 403

                device.current_state = 'UNLOCKED'
                device.last_activity = datetime.now(timezone.utc)
                db.session.commit()

                AuditService.log_event(
                    event_type=EventType.DOOR_UNLOCKED,
                    severity=LogSeverity.INFO,
                    description=f"Smart lock '{device.device_name}' UNLOCKED by user_id {user_id}",
                    user_id=user_id,
                    device_id=device_id
                )
                return True, "Smart lock unlocked successfully", 200

            elif cmd == 'LOCK':
                # Allowed for Homeowner and Admin
                if user_role not in [UserRole.HOMEOWNER, UserRole.ADMIN]:
                    return False, "Access Denied: Insufficient permissions to lock door.", 403

                device.current_state = 'LOCKED'
                device.last_activity = datetime.now(timezone.utc)
                db.session.commit()

                AuditService.log_event(
                    event_type=EventType.DOOR_LOCKED,
                    severity=LogSeverity.INFO,
                    description=f"Smart lock '{device.device_name}' LOCKED by user_id {user_id}",
                    user_id=user_id,
                    device_id=device_id
                )
                return True, "Smart lock locked successfully", 200
            else:
                return False, f"Invalid command '{cmd}' for Smart Lock. Valid commands: LOCK, UNLOCK", 400

        elif device.device_type == DeviceType.SMART_LIGHT:
            if cmd not in ['ON', 'OFF']:
                return False, f"Invalid command '{cmd}' for Smart Light. Valid commands: ON, OFF", 400

            # Permitted for all authenticated users (Homeowner, Family Member, Admin)
            device.current_state = cmd
            device.last_activity = datetime.now(timezone.utc)
            db.session.commit()

            AuditService.log_event(
                event_type=EventType.DEVICE_UPDATED,
                severity=LogSeverity.INFO,
                description=f"Smart light '{device.device_name}' turned {cmd} by user_id {user_id}",
                user_id=user_id,
                device_id=device_id
            )
            return True, f"Smart light turned {cmd}", 200

        elif device.device_type == DeviceType.CAMERA:
            if cmd not in ['ACTIVE', 'PRIVACY_ON', 'ONLINE', 'OFFLINE']:
                return False, f"Invalid command '{cmd}' for Camera.", 400

            if user_role not in [UserRole.HOMEOWNER, UserRole.ADMIN]:
                return False, "Access Denied: Camera configuration restricted to Homeowner/Admin.", 403

            device.current_state = cmd
            device.last_activity = datetime.now(timezone.utc)
            db.session.commit()

            AuditService.log_event(
                event_type=EventType.DEVICE_UPDATED,
                severity=LogSeverity.INFO,
                description=f"Camera '{device.device_name}' mode changed to {cmd} by user_id {user_id}",
                user_id=user_id,
                device_id=device_id
            )
            return True, f"Camera state updated to {cmd}", 200

        else:
            return False, f"Direct commands not supported for device type '{device.device_type}'", 400

    @staticmethod
    def update_status(device_id: str, new_status: str, actor_id=None):
        device = DeviceService.get_device(device_id)
        if not device:
            return False, "Device not found"
        if new_status not in DeviceStatus.ALL:
            return False, "Invalid status"

        device.status = new_status
        device.last_activity = datetime.now(timezone.utc)
        db.session.commit()

        AuditService.log_event(
            event_type=EventType.DEVICE_UPDATED,
            severity=LogSeverity.INFO,
            description=f"Device '{device_id}' status updated to {new_status}",
            user_id=actor_id,
            device_id=device_id
        )
        return True, "Status updated"

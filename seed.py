import os
from app import create_app, db
from app.models.user import User, UserRole
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.automation import AutomationRule
from app.models.security_log import SecurityLog, EventType, LogSeverity
from app.models.notification import Notification, NotificationSeverity

def seed_database():
    app = create_app('development')
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()

        # Seed Users
        users_data = [
            ("admin", "Admin#2026!", UserRole.ADMIN),
            ("homeowner", "HomeOwner#2026!", UserRole.HOMEOWNER),
            ("familymember", "Family#2026!", UserRole.FAMILY_MEMBER)
        ]

        user_objs = {}
        for username, password, role in users_data:
            existing = User.query.filter_by(username=username).first()
            if not existing:
                u = User(username=username, role=role)
                u.set_password(password)
                db.session.add(u)
                db.session.flush()
                user_objs[username] = u
                print(f"Created user: {username} ({role})")
            else:
                user_objs[username] = existing
                print(f"User already exists: {username} ({role})")

        homeowner_user = user_objs.get("homeowner")
        homeowner_id = homeowner_user.user_id if homeowner_user else None

        # Seed Devices
        devices_data = [
            ("DEV-LOCK-001", "Front Door Smart Lock", DeviceType.SMART_LOCK, "LOCKED", "lock-secret-key-001"),
            ("DEV-MOT-001", "Living Room Motion Sensor", DeviceType.MOTION_SENSOR, "CLEAR", "motion-secret-key-001"),
            ("DEV-DOOR-001", "Main Entrance Door Sensor", DeviceType.DOOR_SENSOR, "CLOSED", "door-secret-key-001"),
            ("DEV-LIGHT-001", "Front Porch Smart Light", DeviceType.SMART_LIGHT, "OFF", "light-secret-key-001"),
            ("DEV-TEMP-001", "Thermostat Climate Sensor", DeviceType.TEMP_SENSOR, "22.5", "temp-secret-key-001"),
            ("DEV-CAM-001", "Front Porch Security Camera", DeviceType.CAMERA, "ACTIVE", "cam-secret-key-001")
        ]

        for dev_id, name, dtype, initial_state, raw_key in devices_data:
            existing = Device.query.filter_by(device_id=dev_id).first()
            if not existing:
                d = Device(
                    device_id=dev_id,
                    device_name=name,
                    device_type=dtype,
                    status=DeviceStatus.ONLINE,
                    current_state=initial_state,
                    owner_id=homeowner_id
                )
                d.set_device_key(raw_key)
                db.session.add(d)
                print(f"Created device: {dev_id} - {name}")
            else:
                print(f"Device already exists: {dev_id}")

        # Seed Automation Rule
        if homeowner_id:
            existing_rule = AutomationRule.query.filter_by(name="Porch Motion Illuminator").first()
            if not existing_rule:
                rule = AutomationRule(
                    user_id=homeowner_id,
                    name="Porch Motion Illuminator",
                    trigger="DEV-MOT-001:MOTION_DETECTED",
                    condition="ALWAYS",
                    action="DEV-LIGHT-001:ON|NOTIFY:Living room motion detected, porch light automatically turned ON.",
                    status="ENABLED"
                )
                db.session.add(rule)
                print("Created default automation rule: Porch Motion Illuminator")

        # Seed Initial Security Log & Alert
        if not SecurityLog.query.first():
            db.session.add(SecurityLog(
                event_type=EventType.SECURITY_ALERT,
                severity=LogSeverity.INFO,
                description="Smart Home Security System initialized and online.",
                user_id=homeowner_id
            ))

        if not Notification.query.first():
            db.session.add(Notification(
                message="System initialized: All security sensors and locks operational.",
                severity=NotificationSeverity.INFO,
                user_id=homeowner_id
            ))

        db.session.commit()
        print("Database seed completed successfully.")

if __name__ == '__main__':
    seed_database()

from flask import Blueprint, render_template, session, redirect, url_for
from app.services.auth_service import login_required
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.notification import Notification, NotificationStatus
from app.models.security_log import SecurityLog

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/dashboard')
@login_required
def index():
    devices = Device.query.all()
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if d.status == DeviceStatus.ONLINE)
    offline_devices = sum(1 for d in devices if d.status == DeviceStatus.OFFLINE)

    # Key Device States
    lock = Device.query.filter_by(device_type=DeviceType.SMART_LOCK).first()
    door = Device.query.filter_by(device_type=DeviceType.DOOR_SENSOR).first()
    motion = Device.query.filter_by(device_type=DeviceType.MOTION_SENSOR).first()
    light = Device.query.filter_by(device_type=DeviceType.SMART_LIGHT).first()
    temp = Device.query.filter_by(device_type=DeviceType.TEMP_SENSOR).first()
    camera = Device.query.filter_by(device_type=DeviceType.CAMERA).first()

    # Recent Alerts & Security Logs
    recent_alerts = Notification.query.order_by(Notification.timestamp.desc()).limit(5).all()
    recent_logs = SecurityLog.query.order_by(SecurityLog.timestamp.desc()).limit(6).all()
    unread_alerts_count = Notification.query.filter_by(status=NotificationStatus.UNREAD).count()

    return render_template(
        'dashboard.html',
        total_devices=total_devices,
        online_devices=online_devices,
        offline_devices=offline_devices,
        lock=lock,
        door=door,
        motion=motion,
        light=light,
        temp=temp,
        camera=camera,
        recent_alerts=recent_alerts,
        recent_logs=recent_logs,
        unread_alerts_count=unread_alerts_count
    )

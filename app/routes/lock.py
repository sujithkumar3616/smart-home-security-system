from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required
from app.services.device_service import DeviceService
from app.models.device import Device, DeviceType
from app.models.security_log import SecurityLog, EventType

lock_bp = Blueprint('lock', __name__)

@lock_bp.route('/lock')
@login_required
def index():
    lock_device = Device.query.filter_by(device_type=DeviceType.SMART_LOCK).first()
    recent_lock_logs = []
    if lock_device:
        recent_lock_logs = SecurityLog.query.filter(
            SecurityLog.device_id == lock_device.device_id
        ).order_by(SecurityLog.timestamp.desc()).limit(10).all()

    return render_template(
        'lock.html',
        lock=lock_device,
        logs=recent_lock_logs,
        user_role=session.get('user_role')
    )

@lock_bp.route('/lock/operate', methods=['POST'])
@login_required
def operate():
    device_id = request.form.get('device_id', '').strip()
    command = request.form.get('command', '').strip().upper()

    user_id = session.get('user_id')
    user_role = session.get('user_role')

    success, msg, status_code = DeviceService.execute_command(
        device_id=device_id,
        command=command,
        user_id=user_id,
        user_role=user_role
    )

    if success:
        flash(f"Success: {msg}", 'success')
        return redirect(url_for('lock.index'))
    else:
        flash(f"{msg}", 'danger')
        if status_code == 403:
            # Explicitly return 403 status code while rendering the page with error
            lock_device = Device.query.filter_by(device_type=DeviceType.SMART_LOCK).first()
            recent_lock_logs = SecurityLog.query.filter(
                SecurityLog.device_id == lock_device.device_id
            ).order_by(SecurityLog.timestamp.desc()).limit(10).all() if lock_device else []
            return render_template(
                'lock.html',
                lock=lock_device,
                logs=recent_lock_logs,
                user_role=user_role,
                access_denied_message=msg
            ), 403

        return redirect(url_for('lock.index'))

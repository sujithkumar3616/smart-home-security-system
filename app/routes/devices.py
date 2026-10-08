from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required, admin_required
from app.services.device_service import DeviceService
from app.models.device import Device, DeviceType, DeviceStatus

devices_bp = Blueprint('devices', __name__)

@devices_bp.route('/devices')
@login_required
def index():
    devices = DeviceService.get_all_devices()
    return render_template(
        'devices.html',
        devices=devices,
        device_types=DeviceType.ALL,
        is_admin=(session.get('user_role') == 'ADMIN')
    )

@devices_bp.route('/devices/register', methods=['POST'])
@login_required
@admin_required
def register():
    device_id = request.form.get('device_id', '').strip()
    device_name = request.form.get('device_name', '').strip()
    device_type = request.form.get('device_type', '').strip()
    raw_key = request.form.get('device_key', '').strip() or None

    user_id = session.get('user_id')
    device, err = DeviceService.register_device(
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        owner_id=user_id,
        raw_key=raw_key,
        actor_id=user_id
    )

    if err:
        flash(err, 'danger')
    else:
        flash(f"Device '{device.device_name}' ({device.device_id}) registered successfully.", 'success')

    return redirect(url_for('devices.index'))

@devices_bp.route('/devices/<device_id>/status', methods=['POST'])
@login_required
@admin_required
def update_status(device_id):
    new_status = request.form.get('status', '').strip().upper()
    user_id = session.get('user_id')
    success, msg = DeviceService.update_status(device_id, new_status, actor_id=user_id)
    if success:
        flash(f"Device status updated to {new_status}.", 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('devices.index'))

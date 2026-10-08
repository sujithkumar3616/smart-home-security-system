from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required
from app.services.sensor_service import SensorService
from app.models.device import Device, DeviceType
from app.models.sensor_data import SensorData

sensors_bp = Blueprint('sensors', __name__)

@sensors_bp.route('/sensors')
@login_required
def index():
    motion = Device.query.filter_by(device_type=DeviceType.MOTION_SENSOR).first()
    door = Device.query.filter_by(device_type=DeviceType.DOOR_SENSOR).first()
    temp = Device.query.filter_by(device_type=DeviceType.TEMP_SENSOR).first()

    recent_readings = SensorData.query.order_by(SensorData.timestamp.desc()).limit(20).all()

    return render_template(
        'sensors.html',
        motion=motion,
        door=door,
        temp=temp,
        readings=recent_readings
    )

@sensors_bp.route('/sensors/simulate', methods=['POST'])
@login_required
def simulate():
    device_id = request.form.get('device_id', '').strip()
    sensor_type = request.form.get('sensor_type', '').strip().upper()
    value = request.form.get('value', '').strip()

    success, res, code = SensorService.process_sensor_event(
        device_id=device_id,
        sensor_type=sensor_type,
        value=value,
        is_gateway=True
    )

    if success:
        flash(f"Simulated Event Processed: {device_id} ({sensor_type}) = {value}. Rules evaluated: {res.get('rules_executed', 0)}", 'success')
    else:
        flash(f"Simulation Error: {res}", 'danger')

    return redirect(url_for('sensors.index'))

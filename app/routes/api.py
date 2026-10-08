from flask import Blueprint, request, jsonify, session, current_app
from app.services.auth_service import AuthService, login_required, roles_required
from app.services.device_service import DeviceService
from app.services.sensor_service import SensorService
from app.services.automation_service import AutomationService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.user import UserRole
from app.models.security_log import SecurityLog, EventType, LogSeverity
from app.models.notification import Notification

api_bp = Blueprint('api', __name__)

# ----------------- AUTHENTICATION APIS -----------------

@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    password = data.get('password')

    user, err = AuthService.authenticate(username, password)
    if err:
        return jsonify({'error': 'Authentication Failed', 'message': err, 'code': 401}), 401

    session.clear()
    session['user_id'] = user.user_id
    session['username'] = user.username
    session['user_role'] = user.role

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'session_active': True
    }), 200

@api_bp.route('/logout', methods=['POST'])
def api_logout():
    user_id = session.get('user_id')
    username = session.get('username', 'Anonymous')
    if user_id:
        AuditService.log_event(
            event_type=EventType.LOGOUT,
            severity=LogSeverity.INFO,
            description=f"User '{username}' logged out via API",
            user_id=user_id
        )
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# ----------------- DEVICE MANAGEMENT APIS -----------------

@api_bp.route('/devices', methods=['GET'])
@login_required
def api_get_devices():
    devices = DeviceService.get_all_devices()
    return jsonify({
        'count': len(devices),
        'devices': [d.to_dict() for d in devices]
    }), 200

@api_bp.route('/devices/<device_id>', methods=['GET'])
@login_required
def api_get_device(device_id):
    device = DeviceService.get_device(device_id)
    if not device:
        return jsonify({'error': 'Not Found', 'message': f"Device '{device_id}' does not exist.", 'code': 404}), 404
    return jsonify({'device': device.to_dict()}), 200

@api_bp.route('/devices', methods=['POST'])
@login_required
@roles_required(UserRole.ADMIN)
def api_register_device():
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    device_type = data.get('device_type')
    raw_key = data.get('device_key')

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
        return jsonify({'error': 'Bad Request', 'message': err, 'code': 400}), 400

    return jsonify({
        'message': 'Device registered successfully',
        'device': device.to_dict()
    }), 201

@api_bp.route('/devices/<device_id>/status', methods=['PUT'])
def api_update_device_status(device_id):
    # Allowed via admin session or valid gateway token
    gateway_token = request.headers.get('X-Gateway-Token')
    is_gateway = (gateway_token and gateway_token == current_app.config.get('DEVICE_GATEWAY_TOKEN'))

    user_role = session.get('user_role')
    user_id = session.get('user_id')

    if not is_gateway and user_role != UserRole.ADMIN:
        AuditService.log_event(
            event_type=EventType.UNAUTHORIZED_COMMAND,
            severity=LogSeverity.WARNING,
            description=f"Unauthorized device status change attempt on '{device_id}' by user_id {user_id}",
            user_id=user_id
        )
        return jsonify({'error': 'Forbidden', 'message': 'Admin permission or valid gateway token required.', 'code': 403}), 403

    data = request.get_json(silent=True) or {}
    status = data.get('status', '').upper()
    success, msg = DeviceService.update_status(device_id, status, actor_id=user_id)
    if not success:
        return jsonify({'error': 'Bad Request', 'message': msg, 'code': 400}), 400

    return jsonify({'message': f"Device {device_id} status updated to {status}"}), 200

# ----------------- SMART LOCK APIS -----------------

@api_bp.route('/devices/<device_id>/lock', methods=['POST'])
@login_required
def api_lock_device(device_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    success, msg, code = DeviceService.execute_command(
        device_id=device_id,
        command='LOCK',
        user_id=user_id,
        user_role=user_role
    )
    if not success:
        return jsonify({'error': 'Operation Failed', 'message': msg, 'code': code}), code

    return jsonify({'message': msg, 'device_id': device_id, 'state': 'LOCKED'}), 200

@api_bp.route('/devices/<device_id>/unlock', methods=['POST'])
@login_required
def api_unlock_device(device_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    success, msg, code = DeviceService.execute_command(
        device_id=device_id,
        command='UNLOCK',
        user_id=user_id,
        user_role=user_role
    )
    if not success:
        return jsonify({'error': 'Operation Failed', 'message': msg, 'code': code}), code

    return jsonify({'message': msg, 'device_id': device_id, 'state': 'UNLOCKED'}), 200

@api_bp.route('/devices/<device_id>/command', methods=['POST'])
@login_required
def api_device_command(device_id):
    data = request.get_json(silent=True) or {}
    command = data.get('command')
    if not command:
        return jsonify({'error': 'Bad Request', 'message': 'Command field required.', 'code': 400}), 400

    user_id = session.get('user_id')
    user_role = session.get('user_role')

    success, msg, code = DeviceService.execute_command(
        device_id=device_id,
        command=command,
        user_id=user_id,
        user_role=user_role
    )
    if not success:
        return jsonify({'error': 'Command Failed', 'message': msg, 'code': code}), code

    return jsonify({'message': msg, 'device_id': device_id, 'command': command}), 200

# ----------------- SENSORS & TELEMETRY APIS -----------------

@api_bp.route('/sensors', methods=['GET'])
@login_required
def api_get_sensors():
    device_id = request.args.get('device_id')
    limit = min(int(request.args.get('limit', 50)), 100)
    readings = SensorService.get_recent_readings(device_id=device_id, limit=limit)
    return jsonify({
        'count': len(readings),
        'readings': [r.to_dict() for r in readings]
    }), 200

@api_bp.route('/sensors/event', methods=['POST'])
def api_sensor_event():
    """
    Ingest sensor telemetry from IoT Hardware Simulator or physical device.
    Verifies authentication via X-Device-Key or X-Gateway-Token or active session.
    """
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id')
    sensor_type = data.get('sensor_type')
    value = data.get('value')

    auth_key = request.headers.get('X-Device-Key')
    gateway_token = request.headers.get('X-Gateway-Token')
    is_gateway = (gateway_token and gateway_token == current_app.config.get('DEVICE_GATEWAY_TOKEN'))

    # If neither gateway token nor device key, require logged in user session
    if not is_gateway and not auth_key and 'user_id' not in session:
        AuditService.log_event(
            event_type=EventType.DEVICE_AUTHENTICATION_FAILURE,
            severity=LogSeverity.WARNING,
            description=f"Unauthenticated sensor telemetry attempt from IP {request.remote_addr}"
        )
        return jsonify({'error': 'Unauthorized', 'message': 'Device authentication or user session required', 'code': 401}), 401

    success, result, code = SensorService.process_sensor_event(
        device_id=device_id,
        sensor_type=sensor_type,
        value=value,
        auth_key=auth_key,
        is_gateway=is_gateway
    )

    if not success:
        return jsonify({'error': 'Event Processing Failed', 'message': result, 'code': code}), code

    return jsonify({
        'message': 'Sensor event processed successfully',
        'result': result
    }), 200

# ----------------- AUTOMATION APIS -----------------

@api_bp.route('/automation', methods=['GET'])
@login_required
def api_get_automation():
    rules = AutomationService.get_all_rules()
    return jsonify({
        'count': len(rules),
        'rules': [r.to_dict() for r in rules]
    }), 200

@api_bp.route('/automation', methods=['POST'])
@login_required
@roles_required(UserRole.HOMEOWNER, UserRole.ADMIN)
def api_create_automation():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    trigger = data.get('trigger')
    condition = data.get('condition', 'ALWAYS')
    action = data.get('action')

    user_id = session.get('user_id')
    rule, err = AutomationService.create_rule(
        user_id=user_id,
        name=name,
        trigger=trigger,
        condition=condition,
        action=action
    )

    if err:
        return jsonify({'error': 'Bad Request', 'message': err, 'code': 400}), 400

    return jsonify({
        'message': 'Automation rule created successfully',
        'rule': rule.to_dict()
    }), 201

@api_bp.route('/automation/<int:rule_id>', methods=['PUT'])
@login_required
@roles_required(UserRole.HOMEOWNER, UserRole.ADMIN)
def api_update_automation(rule_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    success, msg = AutomationService.toggle_rule(rule_id, user_id, user_role)
    if not success:
        return jsonify({'error': 'Operation Failed', 'message': msg, 'code': 400}), 400
    return jsonify({'message': msg, 'rule_id': rule_id}), 200

@api_bp.route('/automation/<int:rule_id>', methods=['DELETE'])
@login_required
@roles_required(UserRole.HOMEOWNER, UserRole.ADMIN)
def api_delete_automation(rule_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    success, msg = AutomationService.delete_rule(rule_id, user_id, user_role)
    if not success:
        return jsonify({'error': 'Operation Failed', 'message': msg, 'code': 400}), 400
    return jsonify({'message': msg, 'rule_id': rule_id}), 200

# ----------------- ALERTS & AUDIT LOGS APIS -----------------

@api_bp.route('/alerts', methods=['GET'])
@login_required
def api_get_alerts():
    user_id = session.get('user_id')
    alerts = NotificationService.get_alerts(user_id=user_id, limit=50)
    return jsonify({
        'count': len(alerts),
        'alerts': [a.to_dict() for a in alerts]
    }), 200

@api_bp.route('/alerts/<int:alert_id>/read', methods=['POST'])
@login_required
def api_read_alert(alert_id):
    success = NotificationService.mark_as_read(alert_id)
    if not success:
        return jsonify({'error': 'Not Found', 'message': 'Alert not found', 'code': 404}), 404
    return jsonify({'message': 'Alert marked as read'}), 200

@api_bp.route('/security-logs', methods=['GET'])
@login_required
@roles_required(UserRole.HOMEOWNER, UserRole.ADMIN)
def api_get_security_logs():
    severity = request.args.get('severity')
    limit = min(int(request.args.get('limit', 50)), 200)
    logs = AuditService.get_recent_logs(limit=limit, severity=severity)
    return jsonify({
        'count': len(logs),
        'logs': [l.to_dict() for l in logs]
    }), 200

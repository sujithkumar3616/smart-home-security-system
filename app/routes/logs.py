from flask import Blueprint, render_template, request, session
from app.services.auth_service import login_required, homeowner_or_admin_required
from app.services.audit_service import AuditService
from app.models.security_log import SecurityLog, LogSeverity, EventType

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
@login_required
@homeowner_or_admin_required
def index():
    severity_filter = request.args.get('severity', '').strip() or None
    event_filter = request.args.get('event_type', '').strip() or None

    query = SecurityLog.query
    if severity_filter:
        query = query.filter_by(severity=severity_filter)
    if event_filter:
        query = query.filter_by(event_type=event_filter)

    logs = query.order_by(SecurityLog.timestamp.desc()).limit(150).all()

    return render_template(
        'logs.html',
        logs=logs,
        severities=LogSeverity.ALL,
        selected_severity=severity_filter,
        selected_event=event_filter
    )

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.services.auth_service import login_required
from app.services.audit_service import AuditService
from app.models.user import User
from app.models.security_log import EventType, LogSeverity

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def index():
    user = User.query.get(session.get('user_id'))
    return render_template('settings.html', user=user)

@settings_bp.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    current_pass = request.form.get('current_password', '')
    new_pass = request.form.get('new_password', '')
    confirm_pass = request.form.get('confirm_password', '')

    user = User.query.get(session.get('user_id'))
    if not user.check_password(current_pass):
        flash("Current password is incorrect.", 'danger')
        return redirect(url_for('settings.index'))

    if len(new_pass) < 6:
        flash("New password must be at least 6 characters.", 'danger')
        return redirect(url_for('settings.index'))

    if new_pass != confirm_pass:
        flash("New passwords do not match.", 'danger')
        return redirect(url_for('settings.index'))

    user.set_password(new_pass)
    db.session.commit()

    AuditService.log_event(
        event_type=EventType.PRIVILEGE_CHANGE,
        severity=LogSeverity.INFO,
        description=f"User '{user.username}' changed their password",
        user_id=user.user_id
    )

    flash("Password updated successfully.", 'success')
    return redirect(url_for('settings.index'))

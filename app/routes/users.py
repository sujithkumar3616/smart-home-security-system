from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.services.auth_service import login_required, admin_required, AuthService
from app.services.audit_service import AuditService
from app.models.user import User, UserRole
from app.models.security_log import EventType, LogSeverity

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
@admin_required
def index():
    users = User.query.order_by(User.created_at.asc()).all()
    return render_template(
        'users.html',
        users=users,
        roles=UserRole.ALL,
        current_user_id=session.get('user_id')
    )

@users_bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', '').strip()

    creator_id = session.get('user_id')
    user, err = AuthService.create_user(username, password, role, creator_user_id=creator_id)

    if err:
        flash(err, 'danger')
    else:
        flash(f"User '{user.username}' with role '{user.role}' created successfully.", 'success')

    return redirect(url_for('users.index'))

@users_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    current_admin_id = session.get('user_id')
    if user_id == current_admin_id:
        flash("Action denied: You cannot delete your own administrative account.", 'danger')
        return redirect(url_for('users.index'))

    target_user = User.query.get(user_id)
    if not target_user:
        flash("User not found.", 'danger')
        return redirect(url_for('users.index'))

    username = target_user.username
    db.session.delete(target_user)
    db.session.commit()

    AuditService.log_event(
        event_type=EventType.PRIVILEGE_CHANGE,
        severity=LogSeverity.WARNING,
        description=f"User account '{username}' (id={user_id}) deleted by admin user_id {current_admin_id}",
        user_id=current_admin_id
    )

    flash(f"User '{username}' was successfully deleted.", 'info')
    return redirect(url_for('users.index'))

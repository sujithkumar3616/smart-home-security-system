from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.models.security_log import EventType, LogSeverity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user, err = AuthService.authenticate(username, password)
        if err:
            flash(err, 'danger')
            return render_template('login.html', username=username), 401

        # Secure Session Initialization
        session.clear()
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['user_role'] = user.role

        next_page = request.args.get('next')
        # Prevent open redirect vulnerability
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard.index')

        flash(f"Welcome back, {user.username}!", "success")
        return redirect(next_page)

    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    username = session.get('username', 'Anonymous')

    if user_id:
        AuditService.log_event(
            event_type=EventType.LOGOUT,
            severity=LogSeverity.INFO,
            description=f"User '{username}' logged out",
            user_id=user_id
        )

    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('auth.login'))

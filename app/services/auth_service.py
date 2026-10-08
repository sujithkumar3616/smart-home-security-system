import re
from functools import wraps
from flask import session, request, redirect, url_for, jsonify, abort, render_template
from app import db
from app.models.user import User, UserRole
from app.models.security_log import EventType, LogSeverity
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

class AuthService:
    @staticmethod
    def authenticate(username, password):
        if not username or not password:
            AuditService.log_event(
                event_type=EventType.LOGIN_FAILED,
                severity=LogSeverity.WARNING,
                description=f"Login attempt rejected: missing credentials for input '{username or 'anonymous'}'"
            )
            return None, "Username and password are required."

        username = username.strip()
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            AuditService.log_event(
                event_type=EventType.LOGIN_FAILED,
                severity=LogSeverity.WARNING,
                description=f"Failed authentication attempt for username '{username}' from IP {request.remote_addr or 'unknown'}"
            )
            return None, "Invalid username or password."

        # Successful login
        AuditService.log_event(
            event_type=EventType.LOGIN_SUCCESS,
            severity=LogSeverity.INFO,
            description=f"User '{user.username}' ({user.role}) logged in successfully",
            user_id=user.user_id
        )
        return user, None

    @staticmethod
    def create_user(username, password, role, creator_user_id=None):
        if not username or len(username.strip()) < 3:
            return None, "Username must be at least 3 characters long."
        if not password or len(password) < 6:
            return None, "Password must be at least 6 characters long."
        if role not in UserRole.ALL:
            return None, f"Invalid role. Allowed roles: {', '.join(UserRole.ALL)}"

        username = username.strip()
        if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
            return None, "Username contains invalid characters. Use letters, numbers, hyphens, and underscores."

        existing = User.query.filter_by(username=username).first()
        if existing:
            return None, f"Username '{username}' already exists."

        user = User(username=username, role=role)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()

            AuditService.log_event(
                event_type=EventType.PRIVILEGE_CHANGE,
                severity=LogSeverity.INFO,
                description=f"User '{username}' created with role '{role}' by user_id {creator_user_id or 'System'}",
                user_id=creator_user_id
            )
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, f"Database error creating user: {str(e)}"

    @staticmethod
    def get_current_user():
        user_id = session.get('user_id')
        if not user_id:
            return None
        return User.query.get(user_id)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'code': 401}), 401
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required', 'code': 401}), 401
                return redirect(url_for('auth.login', next=request.path))

            user_role = session.get('user_role')
            user_id = session.get('user_id')
            username = session.get('username', 'Unknown')

            if user_role not in allowed_roles:
                # Log unauthorized access attempt
                description = (
                    f"Access Denied: User '{username}' ({user_role}) attempted unauthorized access to "
                    f"'{request.method} {request.path}' requiring {list(allowed_roles)}"
                )
                AuditService.log_event(
                    event_type=EventType.UNAUTHORIZED_COMMAND,
                    severity=LogSeverity.WARNING,
                    description=description,
                    user_id=user_id
                )
                NotificationService.create_alert(
                    message=f"Security Notice: Unauthorized access attempt to {request.path} by user '{username}'",
                    severity=LogSeverity.WARNING,
                    user_id=user_id
                )

                if request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Forbidden',
                        'message': 'You do not have permission to perform this action.',
                        'code': 403
                    }), 403

                # For HTML requests, render 403 page
                return render_template('errors/403.html', message='You do not have permission to access this page.'), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def homeowner_or_admin_required(f):
    return roles_required(UserRole.HOMEOWNER, UserRole.ADMIN)(f)


def admin_required(f):
    return roles_required(UserRole.ADMIN)(f)

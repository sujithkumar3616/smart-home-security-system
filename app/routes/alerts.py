from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required
from app.services.notification_service import NotificationService
from app.models.notification import Notification

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts')
@login_required
def index():
    user_id = session.get('user_id')
    alerts = NotificationService.get_alerts(user_id=user_id, limit=100)
    return render_template('alerts.html', alerts=alerts)

@alerts_bp.route('/alerts/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_read(alert_id):
    NotificationService.mark_as_read(alert_id)
    return redirect(url_for('alerts.index'))

@alerts_bp.route('/alerts/read-all', methods=['POST'])
@login_required
def read_all():
    user_id = session.get('user_id')
    count = NotificationService.mark_all_as_read(user_id=user_id)
    flash(f"Marked {count} alerts as read.", 'info')
    return redirect(url_for('alerts.index'))

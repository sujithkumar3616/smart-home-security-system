from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required, homeowner_or_admin_required
from app.services.automation_service import AutomationService
from app.models.device import Device

automation_bp = Blueprint('automation', __name__)

@automation_bp.route('/automation')
@login_required
def index():
    rules = AutomationService.get_all_rules()
    devices = Device.query.all()
    user_role = session.get('user_role')
    user_id = session.get('user_id')

    return render_template(
        'automation.html',
        rules=rules,
        devices=devices,
        user_role=user_role,
        current_user_id=user_id
    )

@automation_bp.route('/automation/create', methods=['POST'])
@login_required
@homeowner_or_admin_required
def create():
    name = request.form.get('name', '').strip()
    trigger = request.form.get('trigger', '').strip()
    condition = request.form.get('condition', 'ALWAYS').strip()
    action = request.form.get('action', '').strip()

    user_id = session.get('user_id')
    rule, err = AutomationService.create_rule(
        user_id=user_id,
        name=name,
        trigger=trigger,
        condition=condition,
        action=action
    )

    if err:
        flash(err, 'danger')
    else:
        flash(f"Automation rule '{rule.name}' created successfully.", 'success')

    return redirect(url_for('automation.index'))

@automation_bp.route('/automation/<int:rule_id>/toggle', methods=['POST'])
@login_required
@homeowner_or_admin_required
def toggle(rule_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    success, msg = AutomationService.toggle_rule(rule_id, user_id, user_role)
    if success:
        flash(f"Rule status updated: {msg}", 'success')
    else:
        flash(msg, 'danger')

    return redirect(url_for('automation.index'))

@automation_bp.route('/automation/<int:rule_id>/delete', methods=['POST'])
@login_required
@homeowner_or_admin_required
def delete(rule_id):
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    success, msg = AutomationService.delete_rule(rule_id, user_id, user_role)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(url_for('automation.index'))

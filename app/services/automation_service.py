from datetime import datetime, time
import logging
from app import db
from app.models.automation import AutomationRule
from app.models.device import Device, DeviceType
from app.models.security_log import EventType, LogSeverity
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class AutomationService:
    @staticmethod
    def get_all_rules():
        return AutomationRule.query.order_by(AutomationRule.created_at.desc()).all()

    @staticmethod
    def get_rule(rule_id: int):
        return db.session.get(AutomationRule, rule_id)

    @staticmethod
    def create_rule(user_id: int, name: str, trigger: str, condition: str, action: str):
        if not name or len(name.strip()) < 3:
            return None, "Rule name must be at least 3 characters long."
        if not trigger or not trigger.strip():
            return None, "Trigger is required (e.g., 'DEV-MOT-001:MOTION_DETECTED')."
        if not action or not action.strip():
            return None, "Action is required (e.g., 'DEV-LIGHT-001:ON|NOTIFY:Motion detected')."

        rule = AutomationRule(
            user_id=user_id,
            name=name.strip(),
            trigger=trigger.strip(),
            condition=(condition or 'ALWAYS').strip(),
            action=action.strip(),
            status='ENABLED'
        )

        try:
            db.session.add(rule)
            db.session.commit()

            AuditService.log_event(
                event_type=EventType.AUTOMATION_CREATED,
                severity=LogSeverity.INFO,
                description=f"Automation rule '{name}' (rule_id={rule.rule_id}) created by user_id {user_id}",
                user_id=user_id
            )
            return rule, None
        except Exception as e:
            db.session.rollback()
            return None, f"Database error creating rule: {str(e)}"

    @staticmethod
    def toggle_rule(rule_id: int, user_id: int, user_role: str):
        rule = AutomationService.get_rule(rule_id)
        if not rule:
            return False, "Automation rule not found"

        # Check ownership unless Admin
        if user_role != 'ADMIN' and rule.user_id != user_id:
            return False, "You do not have permission to modify this rule"

        rule.status = 'DISABLED' if rule.status == 'ENABLED' else 'ENABLED'
        db.session.commit()

        AuditService.log_event(
            event_type=EventType.AUTOMATION_MODIFIED,
            severity=LogSeverity.INFO,
            description=f"Automation rule '{rule.name}' status toggled to {rule.status} by user_id {user_id}",
            user_id=user_id
        )
        return True, f"Rule {rule.status.lower()}"

    @staticmethod
    def delete_rule(rule_id: int, user_id: int, user_role: str):
        rule = AutomationService.get_rule(rule_id)
        if not rule:
            return False, "Automation rule not found"

        if user_role != 'ADMIN' and rule.user_id != user_id:
            return False, "You do not have permission to delete this rule"

        rule_name = rule.name
        db.session.delete(rule)
        db.session.commit()

        AuditService.log_event(
            event_type=EventType.AUTOMATION_DELETED,
            severity=LogSeverity.INFO,
            description=f"Automation rule '{rule_name}' deleted by user_id {user_id}",
            user_id=user_id
        )
        return True, "Rule deleted successfully"

    @staticmethod
    def evaluate_rules(trigger_device_id: str, event_value: str):
        """
        Evaluate all active automation rules when a sensor event occurs.
        Matches triggers, tests conditions, executes actions, dispatches alerts and audit logs.
        """
        active_rules = AutomationRule.query.filter_by(status='ENABLED').all()
        executed_count = 0

        for rule in active_rules:
            try:
                # Trigger pattern matching: e.g., "DEV-MOT-001:MOTION_DETECTED" or "DEV-MOT-001:DETECTED"
                trigger_parts = rule.trigger.split(':')
                if len(trigger_parts) == 2:
                    t_device, t_event = trigger_parts[0].strip(), trigger_parts[1].strip()
                    if t_device != trigger_device_id:
                        continue
                    # Match event value (allow flexible synonyms like DETECTED vs MOTION_DETECTED)
                    if t_event not in event_value.upper() and event_value.upper() not in t_event:
                        continue
                else:
                    # Single value match on device ID
                    if rule.trigger.strip() != trigger_device_id:
                        continue

                # Condition evaluation
                if not AutomationService._check_condition(rule.condition):
                    continue

                # Condition met -> execute action
                AutomationService._execute_action(rule)
                executed_count += 1

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {str(e)}")

        return executed_count

    @staticmethod
    def _check_condition(condition_str: str) -> bool:
        if not condition_str or condition_str.upper() == 'ALWAYS':
            return True

        cond = condition_str.strip()

        # Check time condition e.g. "TIME_AFTER:22:00"
        if cond.startswith('TIME_AFTER:'):
            time_str = cond.split(':', 1)[1].strip()
            try:
                target_hour, target_min = map(int, time_str.split(':'))
                now = datetime.now().time()
                target_time = time(target_hour, target_min)
                return now >= target_time
            except Exception:
                return True

        # Check lock state condition e.g. "LOCK_STATUS:LOCKED"
        if cond.startswith('LOCK_STATUS:'):
            expected_state = cond.split(':', 1)[1].strip().upper()
            locks = Device.query.filter_by(device_type=DeviceType.SMART_LOCK).all()
            for l in locks:
                if l.current_state == expected_state:
                    return True
            return False

        # Check temperature condition e.g. "TEMP_ABOVE:28"
        if cond.startswith('TEMP_ABOVE:'):
            threshold = float(cond.split(':', 1)[1].strip())
            temps = Device.query.filter_by(device_type=DeviceType.TEMP_SENSOR).all()
            for t in temps:
                try:
                    if float(t.current_state) > threshold:
                        return True
                except ValueError:
                    continue
            return False

        return True

    @staticmethod
    def _execute_action(rule: AutomationRule):
        """
        Executes action payload: e.g. "DEV-LIGHT-001:ON|NOTIFY:Motion detected, light turned ON"
        """
        parts = rule.action.split('|')
        for part in parts:
            part = part.strip()
            if part.startswith('NOTIFY:'):
                message = part[len('NOTIFY:'):].strip()
                NotificationService.create_alert(
                    message=f"[Rule: {rule.name}] {message}",
                    severity=LogSeverity.WARNING
                )
            elif ':' in part:
                target_device_id, target_cmd = part.split(':', 1)
                target_device_id = target_device_id.strip()
                target_cmd = target_cmd.strip().upper()

                dev = db.session.get(Device, target_device_id)
                if dev:
                    dev.current_state = target_cmd
                    from datetime import timezone
                    dev.last_activity = datetime.now(timezone.utc)
                    db.session.commit()

        # Record audit log
        AuditService.log_event(
            event_type=EventType.AUTOMATION_TRIGGERED,
            severity=LogSeverity.INFO,
            description=f"Automation rule '{rule.name}' (rule_id={rule.rule_id}) executed successfully: {rule.action}",
            user_id=rule.user_id,
            device_id=rule.trigger.split(':')[0] if ':' in rule.trigger else None
        )

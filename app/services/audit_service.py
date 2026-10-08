import logging
from app import db
from app.models.security_log import SecurityLog, LogSeverity, EventType

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    def log_event(event_type: str, severity: str, description: str, user_id=None, device_id=None):
        """
        Record a security/audit log entry.
        Guarantees that sensitive credentials or secrets are never logged.
        """
        try:
            # Defensive check: ensure no passwords or secrets are accidentally captured in description
            sanitized_description = AuditService._sanitize(description)

            log_entry = SecurityLog(
                event_type=event_type,
                severity=severity,
                description=sanitized_description,
                user_id=user_id,
                device_id=device_id
            )
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record audit log: {str(e)}")
            return None

    @staticmethod
    def _sanitize(text: str) -> str:
        # Strip potential token/password values if present
        sensitive_keywords = ['password', 'passwd', 'secret', 'token', 'key']
        clean_text = text
        for kw in sensitive_keywords:
            if f"{kw}=" in clean_text.lower():
                import re
                clean_text = re.sub(rf"({kw}\s*=\s*)[^\s,;&]+", r"\1[REDACTED]", clean_text, flags=re.IGNORECASE)
        return clean_text

    @staticmethod
    def get_recent_logs(limit=50, severity=None, user_id=None):
        query = SecurityLog.query
        if severity:
            query = query.filter_by(severity=severity)
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(SecurityLog.timestamp.desc()).limit(limit).all()

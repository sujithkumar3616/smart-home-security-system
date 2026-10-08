import logging
from app import db
from app.models.notification import Notification, NotificationSeverity, NotificationStatus

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def create_alert(message: str, severity: str = NotificationSeverity.INFO, user_id=None):
        """
        Create a new alert / notification for system users or a specific user.
        """
        try:
            alert = Notification(
                message=message,
                severity=severity,
                user_id=user_id,
                status=NotificationStatus.UNREAD
            )
            db.session.add(alert)
            db.session.commit()
            return alert
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create alert: {str(e)}")
            return None

    @staticmethod
    def get_alerts(user_id=None, status=None, limit=50):
        query = Notification.query
        if user_id:
            query = query.filter((Notification.user_id == user_id) | (Notification.user_id == None))
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Notification.timestamp.desc()).limit(limit).all()

    @staticmethod
    def mark_as_read(notification_id: int):
        alert = Notification.query.get(notification_id)
        if alert:
            alert.status = NotificationStatus.READ
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_as_read(user_id=None):
        query = Notification.query.filter_by(status=NotificationStatus.UNREAD)
        if user_id:
            query = query.filter((Notification.user_id == user_id) | (Notification.user_id == None))
        count = query.update({Notification.status: NotificationStatus.READ})
        db.session.commit()
        return count

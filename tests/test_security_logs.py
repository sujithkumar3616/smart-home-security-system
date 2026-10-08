from app.models.security_log import SecurityLog, EventType, LogSeverity
from app.services.audit_service import AuditService

def test_security_logging_on_unauthorized_access(client, auth_helper, app):
    auth_helper.login('familymember', 'Family#2026!')
    # Access restricted admin route
    res = client.get('/users')
    assert res.status_code == 403

    with app.app_context():
        log = SecurityLog.query.filter_by(event_type=EventType.UNAUTHORIZED_COMMAND).first()
        assert log is not None
        assert "Access Denied" in log.description
        assert "familymember" in log.description

def test_sensitive_credentials_never_logged(app):
    with app.app_context():
        # Attempt to log a description containing simulated password/token fields
        leak_attempt = "User login attempt with password=SuperSecretPassword123 and token=my-secret-jwt"
        log = AuditService.log_event(
            event_type=EventType.LOGIN_FAILED,
            severity=LogSeverity.WARNING,
            description=leak_attempt
        )

        assert log is not None
        assert "SuperSecretPassword123" not in log.description
        assert "my-secret-jwt" not in log.description
        assert "[REDACTED]" in log.description

def test_security_logs_access_restricted_to_homeowner_and_admin(client, auth_helper):
    # Family Member cannot view logs
    auth_helper.login('familymember', 'Family#2026!')
    res = client.get('/logs')
    assert res.status_code == 403

    # Homeowner can view logs
    auth_helper.login('homeowner', 'HomeOwner#2026!')
    res = client.get('/logs')
    assert res.status_code == 200
    assert b"Audit Records" in res.data

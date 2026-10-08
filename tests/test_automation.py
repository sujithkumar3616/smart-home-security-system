from app.models.automation import AutomationRule
from app.models.device import Device
from app.services.automation_service import AutomationService

def test_create_automation_rule(client, auth_helper, app):
    auth_helper.login('homeowner', 'HomeOwner#2026!')
    res = client.post('/api/automation', json={
        'name': 'Door Open Porch Alert',
        'trigger': 'DEV-DOOR-001:DOOR_OPEN',
        'condition': 'ALWAYS',
        'action': 'DEV-LIGHT-001:ON|NOTIFY:Front door opened'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['rule']['name'] == 'Door Open Porch Alert'

    with app.app_context():
        rule = AutomationRule.query.filter_by(name='Door Open Porch Alert').first()
        assert rule is not None
        assert rule.status == 'ENABLED'

def test_automation_execution_on_trigger(app):
    with app.app_context():
        from app import db
        light = db.session.get(Device, 'DEV-LIGHT-001')
        light.current_state = 'OFF'
        db.session.commit()

        # Trigger event for default seeded rule "DEV-MOT-001:MOTION_DETECTED"
        executed = AutomationService.evaluate_rules('DEV-MOT-001', 'MOTION_DETECTED')
        assert executed >= 1

        # Check light is turned ON
        light = db.session.get(Device, 'DEV-LIGHT-001')
        assert light.current_state == 'ON'

def test_toggle_and_delete_rule(client, auth_helper, app):
    auth_helper.login('homeowner', 'HomeOwner#2026!')

    with app.app_context():
        from app import db
        rule = AutomationRule.query.first()
        rule_id = rule.rule_id

    # Toggle to DISABLED
    res = client.put(f'/api/automation/{rule_id}')
    assert res.status_code == 200

    with app.app_context():
        from app import db
        r = db.session.get(AutomationRule, rule_id)
        assert r.status == 'DISABLED'

    # Delete rule
    res = client.delete(f'/api/automation/{rule_id}')
    assert res.status_code == 200

    with app.app_context():
        from app import db
        r = db.session.get(AutomationRule, rule_id)
        assert r is None

def test_invalid_automation_rejected(client, auth_helper):
    auth_helper.login('homeowner', 'HomeOwner#2026!')
    res = client.post('/api/automation', json={
        'name': 'X',  # Too short
        'trigger': '',
        'action': ''
    })
    assert res.status_code == 400

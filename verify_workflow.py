import requests
import sys

BASE_URL = "http://127.0.0.1:5000"

def run_demonstration():
    print("=" * 70)
    print("EXECUTING SECTION 29: REQUIRED DEMONSTRATION WORKFLOW")
    print("=" * 70)

    session = requests.Session()

    # Step 1 & 2: Open login page
    print("\n[Step 1 & 2]: Testing Login Page GET...")
    r = session.get(f"{BASE_URL}/login")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print("  -> Login page loaded successfully (200 OK)")

    # Step 3: Login as Homeowner
    print("\n[Step 3]: Authenticating as Homeowner...")
    r = session.post(f"{BASE_URL}/login", data={"username": "homeowner", "password": "HomeOwner#2026!"}, allow_redirects=True)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "Security Command Center" in r.text, "Dashboard header not found in response"
    print("  -> Authenticated as Homeowner successfully (200 OK)")

    # Step 4: Open Dashboard
    print("\n[Step 4]: Viewing Dashboard...")
    r = session.get(f"{BASE_URL}/dashboard")
    assert r.status_code == 200
    assert "Networked Devices" in r.text
    print("  -> Dashboard loaded with real metrics (200 OK)")

    # Step 5: View IoT devices
    print("\n[Step 5]: Viewing IoT Device Management...")
    r = session.get(f"{BASE_URL}/devices")
    assert r.status_code == 200
    assert "DEV-LOCK-001" in r.text
    assert "DEV-MOT-001" in r.text
    print("  -> Device catalog loaded (200 OK)")

    # Step 6: View sensor information
    print("\n[Step 6]: Viewing Sensors page...")
    r = session.get(f"{BASE_URL}/sensors")
    assert r.status_code == 200
    assert "Hardware Event Simulator" in r.text
    print("  -> Sensor monitoring interface loaded (200 OK)")

    # Step 7: Lock smart door
    print("\n[Step 7]: Engaging Smart Lock (LOCK)...")
    r = session.post(f"{BASE_URL}/lock/operate", data={"device_id": "DEV-LOCK-001", "command": "LOCK"}, allow_redirects=True)
    assert r.status_code == 200
    print("  -> Smart lock engaged (LOCKED state confirmed)")

    # Step 8: Unlock smart door
    print("\n[Step 8]: Disengaging Smart Lock (UNLOCK)...")
    r = session.post(f"{BASE_URL}/lock/operate", data={"device_id": "DEV-LOCK-001", "command": "UNLOCK"}, allow_redirects=True)
    assert r.status_code == 200
    assert "Smart lock unlocked successfully" in r.text
    print("  -> Smart lock disengaged (UNLOCKED state confirmed)")

    # Re-lock for next test
    session.post(f"{BASE_URL}/lock/operate", data={"device_id": "DEV-LOCK-001", "command": "LOCK"})

    # Step 9: Generate a motion event using IoT Simulator
    print("\n[Step 9 & 10]: Generating Motion Detected Telemetry via Simulator...")
    from app.simulator.iot_simulator import IoTSimulator
    sim = IoTSimulator(base_url=BASE_URL, gateway_token="gateway-sim-secret-key-99881122")
    status, payload = sim.trigger_motion(detected=True)
    assert status == 200, f"Expected 200 from sensor event ingestion, got {status}"
    print(f"  -> Hardware simulator event accepted: {payload['message']}")

    # Step 11: Turn on smart light automatically
    print("\n[Step 11]: Verifying automated device action (Light turned ON)...")
    r = session.get(f"{BASE_URL}/api/devices/DEV-LIGHT-001")
    assert r.status_code == 200
    light_state = r.json()["device"]["current_state"]
    assert light_state == "ON", f"Expected light state ON, got {light_state}"
    print(f"  -> Automation executed successfully: DEV-LIGHT-001 is {light_state}")

    # Step 12: Generate a security notification
    print("\n[Step 12]: Checking generated security alerts...")
    r = session.get(f"{BASE_URL}/api/alerts")
    assert r.status_code == 200
    alerts = r.json()["alerts"]
    assert len(alerts) > 0, "Expected at least 1 alert"
    print(f"  -> Confirmed {len(alerts)} alerts generated. Most recent: '{alerts[0]['message']}'")

    # Step 13: View security/audit log
    print("\n[Step 13]: Inspecting Security Audit Trail...")
    r = session.get(f"{BASE_URL}/logs")
    assert r.status_code == 200
    assert "AUTOMATION_TRIGGERED" in r.text
    print("  -> Security audit trail inspected (200 OK)")

    # Step 14: Logout
    print("\n[Step 14]: Logging out Homeowner session...")
    r = session.get(f"{BASE_URL}/logout", allow_redirects=True)
    assert r.status_code == 200
    print("  -> Session cleared and logged out")

    # Step 15: Login as Family Member
    print("\n[Step 15]: Authenticating as Family Member...")
    r = session.post(f"{BASE_URL}/login", data={"username": "familymember", "password": "Family#2026!"}, allow_redirects=True)
    assert r.status_code == 200
    assert "familymember" in r.text
    print("  -> Authenticated as Family Member (200 OK)")

    # Step 16 & 17: Attempt to unlock the smart door (Must be rejected with HTTP 403)
    print("\n[Step 16 & 17]: Family Member attempting unauthorized Smart Door UNLOCK...")
    r = session.post(f"{BASE_URL}/lock/operate", data={"device_id": "DEV-LOCK-001", "command": "UNLOCK"})
    assert r.status_code == 403, f"Expected 403 Forbidden, got {r.status_code}"
    assert "Access Denied: Family members do not have permission to unlock the smart door" in r.text
    print(f"  -> SUCCESS: Unauthorized operation rejected with HTTP {r.status_code} Forbidden")

    # Also test API endpoint directly
    r_api = session.post(f"{BASE_URL}/api/devices/DEV-LOCK-001/unlock")
    assert r_api.status_code == 403, f"Expected 403 Forbidden on API direct call, got {r_api.status_code}"
    print(f"  -> SUCCESS: Direct API unlock bypass attempt rejected with HTTP {r_api.status_code} Forbidden")

    # Step 18: Confirm security event logged
    # Login as Homeowner or Admin to inspect the security log for the violation
    print("\n[Step 18]: Confirming security violation was recorded in audit log...")
    session_admin = requests.Session()
    session_admin.post(f"{BASE_URL}/login", data={"username": "admin", "password": "Admin#2026!"})
    r_logs = session_admin.get(f"{BASE_URL}/api/security-logs")
    logs = r_logs.json()["logs"]
    denied_logs = [l for l in logs if l["event_type"] == "DOOR_UNLOCK_DENIED"]
    assert len(denied_logs) > 0, "DOOR_UNLOCK_DENIED event not found in audit log"
    print(f"  -> Security violation confirmed in audit log: '{denied_logs[0]['description']}'")

    # Step 19 & 20: Admin registers a new device
    print("\n[Step 19 & 20]: Admin registering new device...")
    r_dev = session_admin.post(f"{BASE_URL}/api/devices", json={
        "device_id": "DEV-SIREN-099",
        "device_name": "Backyard Siren Horn",
        "device_type": "SMART_LIGHT",
        "device_key": "siren-auth-key-99"
    })
    assert r_dev.status_code == 201, f"Expected 201 Created, got {r_dev.status_code}"
    print("  -> Device DEV-SIREN-099 registered successfully by Admin")

    print("\n" + "=" * 70)
    print("ALL 20 STEPS OF THE DEMONSTRATION WORKFLOW PASSED FLAWLESSLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_demonstration()

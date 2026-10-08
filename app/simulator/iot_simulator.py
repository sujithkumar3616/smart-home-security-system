import os
import time
import secrets
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("IoTSimulator")

class IoTSimulator:
    def __init__(self, base_url="http://127.0.0.1:5000", gateway_token=None):
        self.base_url = base_url.rstrip('/')
        self.gateway_token = gateway_token or os.environ.get('DEVICE_GATEWAY_TOKEN', 'gateway-sim-secret-key-99881122')
        self.headers = {
            "Content-Type": "application/json",
            "X-Gateway-Token": self.gateway_token
        }

    def send_event(self, device_id: str, sensor_type: str, value: str, device_key: str = None):
        """
        Sends an HTTP REST telemetry event to the Smart Home Security Backend.
        Simulates hardware networking layer (Wi-Fi/MQTT-to-HTTP Gateway).
        """
        url = f"{self.base_url}/api/sensors/event"
        payload = {
            "device_id": device_id,
            "sensor_type": sensor_type,
            "value": value
        }
        headers = self.headers.copy()
        if device_key:
            headers["X-Device-Key"] = device_key

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            logger.info(f"Event Sent: {device_id} ({sensor_type}) = {value} -> Status: {response.status_code}")
            return response.status_code, response.json() if response.content else {}
        except Exception as e:
            logger.error(f"Failed to transmit event to backend: {str(e)}")
            return 500, {"error": str(e)}

    # Convenience simulation methods
    def trigger_motion(self, detected=True):
        val = "MOTION_DETECTED" if detected else "MOTION_CLEAR"
        return self.send_event("DEV-MOT-001", "MOTION", val)

    def trigger_door(self, open_door=True):
        val = "DOOR_OPEN" if open_door else "DOOR_CLOSED"
        return self.send_event("DEV-DOOR-001", "DOOR", val)

    def report_temperature(self, temp_celsius=None):
        if temp_celsius is None:
            # Generate realistic room temperature fluctuation
            temp_celsius = round(20.0 + (secrets.randbelow(130) / 10.0), 1)
        return self.send_event("DEV-TEMP-001", "TEMPERATURE", str(temp_celsius))

    def set_device_status(self, device_id: str, status: str):
        url = f"{self.base_url}/api/devices/{device_id}/status"
        payload = {"status": status}
        try:
            response = requests.put(url, json=payload, headers=self.headers, timeout=5)
            logger.info(f"Status update: {device_id} -> {status} -> {response.status_code}")
            return response.status_code, response.json()
        except Exception as e:
            logger.error(f"Failed to update device status: {str(e)}")
            return 500, {"error": str(e)}

    def run_continuous_simulation(self, interval=10):
        """
        Runs autonomous background simulation generating realistic home sensor fluctuations.
        """
        logger.info(f"Starting autonomous IoT hardware simulation loop (Interval: {interval}s)...")
        actions = ["temp", "motion", "door"]
        while True:
            choice = secrets.choice(actions)
            if choice == "temp":
                self.report_temperature()
            elif choice == "motion":
                is_detected = secrets.choice([True, False])
                self.trigger_motion(detected=is_detected)
            elif choice == "door":
                is_open = secrets.choice([True, False])
                self.trigger_door(open_door=is_open)
            time.sleep(interval)

#!/usr/bin/env python3
import sys
import argparse
from app.simulator.iot_simulator import IoTSimulator

def main():
    parser = argparse.ArgumentParser(description="IoT Hardware Simulator for Smart Home Security")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Backend base URL")
    parser.add_argument("--token", default="gateway-sim-secret-key-99881122", help="Device Gateway Token")
    parser.add_argument("--motion", action="store_true", help="Simulate motion detected")
    parser.add_argument("--clear-motion", action="store_true", help="Simulate motion cleared")
    parser.add_argument("--open-door", action="store_true", help="Simulate door opened")
    parser.add_argument("--close-door", action="store_true", help="Simulate door closed")
    parser.add_argument("--temp", type=float, help="Simulate temperature reading in °C")
    parser.add_argument("--loop", type=int, help="Run continuous simulation with interval seconds")
    parser.add_argument("--custom", nargs=3, metavar=('DEVICE_ID', 'SENSOR_TYPE', 'VALUE'), help="Send custom telemetry")

    args = parser.parse_args()
    sim = IoTSimulator(base_url=args.url, gateway_token=args.token)

    if args.motion:
        code, resp = sim.trigger_motion(detected=True)
        print(f"[Result {code}]: {resp}")
    elif args.clear_motion:
        code, resp = sim.trigger_motion(detected=False)
        print(f"[Result {code}]: {resp}")
    elif args.open_door:
        code, resp = sim.trigger_door(open_door=True)
        print(f"[Result {code}]: {resp}")
    elif args.close_door:
        code, resp = sim.trigger_door(open_door=False)
        print(f"[Result {code}]: {resp}")
    elif args.temp is not None:
        code, resp = sim.report_temperature(temp_celsius=args.temp)
        print(f"[Result {code}]: {resp}")
    elif args.custom:
        code, resp = sim.send_event(args.custom[0], args.custom[1], args.custom[2])
        print(f"[Result {code}]: {resp}")
    elif args.loop:
        sim.run_continuous_simulation(interval=args.loop)
    else:
        # Interactive mode
        print("=" * 60)
        print("   Smart Home IoT Hardware Event Simulator Console")
        print("=" * 60)
        print("1. Trigger Motion (Living Room DETECTED)")
        print("2. Clear Motion (Living Room CLEAR)")
        print("3. Open Front Door (DOOR_OPEN)")
        print("4. Close Front Door (DOOR_CLOSED)")
        print("5. Report High Temperature (31.5 °C)")
        print("6. Run Autonomous Simulation Loop (5s interval)")
        print("q. Quit")
        print("=" * 60)

        choice = input("Select an option (1-6, q): ").strip()
        if choice == '1':
            code, resp = sim.trigger_motion(detected=True)
            print(f"[Status {code}]: {resp}")
        elif choice == '2':
            code, resp = sim.trigger_motion(detected=False)
            print(f"[Status {code}]: {resp}")
        elif choice == '3':
            code, resp = sim.trigger_door(open_door=True)
            print(f"[Status {code}]: {resp}")
        elif choice == '4':
            code, resp = sim.trigger_door(open_door=False)
            print(f"[Status {code}]: {resp}")
        elif choice == '5':
            code, resp = sim.report_temperature(temp_celsius=31.5)
            print(f"[Status {code}]: {resp}")
        elif choice == '6':
            sim.run_continuous_simulation(interval=5)
        else:
            print("Exiting.")

if __name__ == '__main__':
    main()

"""
Robo Raksha — Mock Robot Telemetry Sender (Person 1 Simulator Tool)
Sends simulated sensor data streams to Person 1's Server to test severity calculation and threshold crossing.
"""

import argparse
import requests
import time

SERVER_URL = "http://localhost:5000/api/telemetry"


def send_telemetry(flame: int, sound: float, vibration: int, distance_cm: int):
    payload = {
        "flame": flame,
        "sound": sound,
        "vibration": vibration,
        "distance_cm": distance_cm
    }
    print(f"🤖 Sending Mock Telemetry to {SERVER_URL}: {payload}")
    try:
        res = requests.post(SERVER_URL, json=payload, timeout=2.0)
        print(f"   Server Response [{res.status_code}]: {res.json()}")
    except Exception as e:
        print(f"❌ Failed to send telemetry: {e}")


def main():
    parser = argparse.ArgumentParser(description="Robo Raksha Mock Robot Simulator")
    parser.add_argument("--mode", choices=["normal", "fire", "sound", "stream"], default="normal",
                        help="Pre-configured simulation scenario mode")
    parser.add_argument("--flame", type=int, default=0, help="1=Flame, 0=No flame")
    parser.add_argument("--sound", type=float, default=40.0, help="Sound level in dB")
    parser.add_argument("--vibration", type=int, default=1, help="1=Moving, 0=Stationary")
    parser.add_argument("--distance", type=int, default=100, help="Distance in cm")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval in seconds for streaming mode")

    args = parser.parse_args()

    if args.mode == "normal":
        print("▶️ Running Normal Sensor Mode (Flame=0, Sound=40dB, Vibration=1)")
        send_telemetry(0, 40.0, 1, 120)

    elif args.mode == "fire":
        print("▶️ Running FIRE EMERGENCY Mode (Flame=1, Sound=87dB, Vibration=0 -> Score = 12)")
        send_telemetry(1, 87.0, 0, 45)

    elif args.mode == "sound":
        print("▶️ Running LOUD SOUND & NO MOVEMENT Mode (Flame=0, Sound=95dB, Vibration=0 -> Score = 7)")
        send_telemetry(0, 95.0, 0, 90)

    elif args.mode == "stream":
        print(f"▶️ Streaming simulated sensor readings every {args.interval} seconds... (Press Ctrl+C to stop)")
        try:
            step = 0
            while True:
                step += 1
                if step < 3:
                    # Normal walking around
                    send_telemetry(0, 42.0, 1, 100)
                elif step < 7:
                    # Sudden fire outbreak & robot stops
                    send_telemetry(1, 88.5, 0, 30)
                else:
                    # Fire continues
                    send_telemetry(1, 92.0, 0, 25)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped streaming.")
    else:
        send_telemetry(args.flame, args.sound, args.vibration, args.distance)


if __name__ == "__main__":
    main()

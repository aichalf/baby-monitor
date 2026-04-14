import json
import random
import re
import threading
import time
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    import serial
except ImportError:
    serial = None

SERIAL_PORT = "COM7"
BAUD_RATE = 115200
USE_SIMULATION_IF_NO_SERIAL = True
MOVEMENT_TIMEOUT_SEC = 5  # After 5s with no movement signal → "No Movement"

movement_last_detected: float = 0.0

latest_data: Dict[str, Any] = {
    "babyTemp": 0.0,
    "heartRate": 0,
    "spo2": 0,
    "movement": "No Movement",
    "movementLevel": 0,
    "state": "NORMAL",
    "message": "Waiting for STM32 data.",
    "connected": False,
    "source": "default",
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://baby-monitor-ashy.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def update_state() -> None:
    global latest_data, movement_last_detected

    temp = float(latest_data.get("babyTemp", 0) or 0)
    bpm = int(latest_data.get("heartRate", 0) or 0)
    spo2 = int(latest_data.get("spo2", 0) or 0)

    movement = str(latest_data.get("movement", "No Movement"))

    # Simulate SpO2 if not provided by STM32
    if spo2 == 0 and latest_data.get("connected"):
        latest_data["spo2"] = random.randint(96, 100)
        spo2 = latest_data["spo2"]

    emergency = False
    reasons = []

    if bpm == 0:
        emergency = True
        reasons.append("no cardiac contact")
    elif bpm < 80 or bpm > 160:
        emergency = True
        reasons.append("abnormal heart rate")

    if spo2 != 0 and spo2 < 95:
        emergency = True
        reasons.append("low blood oxygen")

    if movement in {"Alert", "No Movement"}:
        emergency = True
        reasons.append("movement alert")

    if temp != 0 and (temp > 37.5 or temp < 36.0):
        emergency = True
        reasons.append("abnormal temperature")

    if emergency:
        latest_data["state"] = "EMERGENCY"
        if reasons:
            latest_data["message"] = "Emergency detected: " + ", ".join(reasons) + "."
        else:
            latest_data["message"] = "Emergency detected: check infant immediately."
    else:
        latest_data["state"] = "NORMAL"
        latest_data["message"] = "All parameters are normal."


def _apply_packet(packet: Dict[str, Any]) -> None:
    global latest_data, movement_last_detected

    if "babyTemp" in packet:
        latest_data["babyTemp"] = float(packet.get("babyTemp") or 0)
    if "heartRate" in packet:
        latest_data["heartRate"] = int(packet.get("heartRate") or 0)
    if "spo2" in packet:
        latest_data["spo2"] = int(packet.get("spo2") or 0)
    if "movement" in packet:
        mv = str(packet.get("movement") or "No Movement")
        latest_data["movement"] = mv
        if mv == "Normal":
            movement_last_detected = time.time()
    if "movementLevel" in packet:
        latest_data["movementLevel"] = int(packet.get("movementLevel") or 0)
    if "state" in packet and packet.get("state") in {"NORMAL", "EMERGENCY"}:
        latest_data["state"] = packet["state"]
    if "message" in packet and packet.get("message"):
        latest_data["message"] = str(packet["message"])

    latest_data["connected"] = True
    latest_data["source"] = "stm32"
    update_state()


def parse_stm32_line(raw: str) -> None:
    global latest_data

    line = raw.strip()
    lower = line.lower()

    if not line:
        return

    if line.startswith("{") and line.endswith("}"):
        try:
            packet = json.loads(line)
            if isinstance(packet, dict):
                _apply_packet(packet)
                return
        except json.JSONDecodeError:
            pass

    if "temp" in lower:
        match = re.search(r"(-?\d+(\.\d+)?)", line)
        if match:
            latest_data["babyTemp"] = float(match.group(1))
            latest_data["connected"] = True
            latest_data["source"] = "stm32"
            update_state()
        return

    if "spo2" in lower or "oxygen" in lower:
        match = re.search(r"(\d+)", line)
        if match:
            latest_data["spo2"] = int(match.group(1))
            latest_data["connected"] = True
            latest_data["source"] = "stm32"
            update_state()
        return

    if "bpm" in lower:
        if "no contact" in lower or "no finger" in lower:
            latest_data["heartRate"] = 0
            latest_data["spo2"] = 0
        else:
            match = re.search(r"(\d+)", line)
            if match:
                latest_data["heartRate"] = int(match.group(1))

        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return

    if "movement detected" in lower:
        movement_last_detected = time.time()
        latest_data["movement"] = "Normal"
        latest_data["movementLevel"] = 100
        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return

    if "movement alert" in lower or "no movement" in lower:
        latest_data["movement"] = "No Movement"
        latest_data["movementLevel"] = 0
        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return

    if "no contact" in lower or "no finger" in lower:
        latest_data["heartRate"] = 0
        latest_data["spo2"] = 0
        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return


def simulate_data() -> None:
    global latest_data

    scenarios = [
        {
            "babyTemp": 36.8,
            "heartRate": 132,
            "spo2": 98,
            "movement": "Normal",
            "movementLevel": 100,
            "state": "NORMAL",
            "message": "All parameters are normal.",
            "connected": False,
            "source": "simulation",
        },
        {
            "babyTemp": 38.1,
            "heartRate": 92,
            "spo2": 91,
            "movement": "No Movement",
            "movementLevel": 0,
            "state": "EMERGENCY",
            "message": "Emergency detected: check infant immediately.",
            "connected": False,
            "source": "simulation",
        },
    ]

    while True:
        for item in scenarios:
            latest_data = item.copy()
            print("Simulation:", latest_data)
            time.sleep(5)


def serial_reader() -> None:
    global latest_data

    if serial is None:
        print("pyserial not installed.")
        if USE_SIMULATION_IF_NO_SERIAL:
            simulate_data()
        return

    while True:
        try:
            print(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud...")
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
                print("Connected to serial port.")
                latest_data["connected"] = True

                while True:
                    raw = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not raw:
                        continue

                    print("STM32:", raw)
                    parse_stm32_line(raw)

        except Exception as e:
            print("Serial error:", e)
            latest_data["connected"] = False
            latest_data["source"] = "simulation" if USE_SIMULATION_IF_NO_SERIAL else "default"

            if USE_SIMULATION_IF_NO_SERIAL:
                simulate_data()
            else:
                time.sleep(2)


def movement_watchdog() -> None:
    """Checks every second if movement has timed out."""
    global latest_data, movement_last_detected
    while True:
        time.sleep(1)
        if latest_data.get("connected") and movement_last_detected > 0:
            elapsed = time.time() - movement_last_detected
            if elapsed > MOVEMENT_TIMEOUT_SEC:
                if latest_data.get("movement") == "Normal":
                    latest_data["movement"] = "No Movement"
                    latest_data["movementLevel"] = 0
                    update_state()
                    print(f"Movement timeout ({elapsed:.1f}s) → No Movement")


@app.on_event("startup")
def startup_event():
    threading.Thread(target=serial_reader, daemon=True).start()
    threading.Thread(target=movement_watchdog, daemon=True).start()


@app.get("/api/data")
def get_data():
    return latest_data


@app.get("/api/health")
def health():
    return {"status": "ok"}
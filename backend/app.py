import json
import threading
import time
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    import serial
except ImportError:
    serial = None

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
USE_SIMULATION_IF_NO_SERIAL = True

latest_data: Dict[str, Any] = {
    "babyTemp": 36.8,
    "heartRate": 142,
    "movement": "Normal",
    "movementLevel": 82,
    "state": "NORMAL",
    "message": "Tous les paramètres sont normaux.",
    "connected": False,
    "source": "default"
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = {
        "babyTemp": float(payload.get("babyTemp", 0)),
        "heartRate": int(payload.get("heartRate", 0)),
        "spo2": int(payload.get("spo2", 0)),
        "movement": str(payload.get("movement", "Inconnu")),
        "movementLevel": int(payload.get("movementLevel", 0)),
        "roomTemp": float(payload.get("roomTemp", 0)),
        "humidity": int(payload.get("humidity", 0)),
        "smoke": bool(payload.get("smoke", False)),
        "state": str(payload.get("state", "NORMAL")).upper(),
        "message": str(payload.get("message", "")),
        "connected": True,
        "source": "stm32"
    }
    return data

def simulate_data():
    global latest_data

    scenarios = [
        {
            "babyTemp": 36.8,
            "heartRate": 142,
            "movement": "Normal",
            "movementLevel": 82,
            "state": "NORMAL",
            "message": "Tous les paramètres sont normaux.",
            "connected": False,
            "source": "simulation"
        },
        {
            "babyTemp": 38.3,
            "heartRate": 178,
            "movement": "Aucun mouvement",
            "movementLevel": 5,
            "state": "EMERGENCY",
            "message": "Urgence détectée : vérifier le bébé immédiatement.",
            "connected": False,
            "source": "simulation"
        }
    ]

    while True:
        for item in scenarios:
            latest_data = item
            print("Simulation:", latest_data)
            time.sleep(5)

def serial_reader():
    global latest_data

    if serial is None:
        print("pyserial non installé.")
        if USE_SIMULATION_IF_NO_SERIAL:
            simulate_data()
        return

    while True:
        try:
            print(f"Tentative de connexion sur {SERIAL_PORT} à {BAUD_RATE} bauds...")
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
                print("Connecté au port série.")
                latest_data["connected"] = True

                while True:
                    raw = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not raw:
                        continue

                    try:
                        payload = json.loads(raw)
                        latest_data = normalize_payload(payload)
                        print("Données reçues:", latest_data)
                    except json.JSONDecodeError:
                        print("JSON invalide reçu:", raw)

        except Exception as e:
            print("Erreur série:", e)
            latest_data["connected"] = False
            latest_data["source"] = "simulation" if USE_SIMULATION_IF_NO_SERIAL else "default"

            if USE_SIMULATION_IF_NO_SERIAL:
                simulate_data()
            else:
                time.sleep(2)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=serial_reader, daemon=True)
    thread.start()

@app.get("/api/data")
def get_data():
    return latest_data

@app.get("/api/health")
def health():
    return {"status": "ok"}
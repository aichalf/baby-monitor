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

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
USE_SIMULATION_IF_NO_SERIAL = True

latest_data: Dict[str, Any] = {
    "babyTemp": 0,
    "heartRate": 0,
    "movement": "En attente",
    "movementLevel": 0,
    "state": "NORMAL",
    "message": "En attente de données STM32.",
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

def update_state() -> None:
    global latest_data

    temp = latest_data.get("babyTemp", 0)
    bpm = latest_data.get("heartRate", 0)
    movement = latest_data.get("movement", "En attente")

    emergency = False
    reasons = []

    if bpm == 0:
        emergency = True
        reasons.append("aucun contact cardiaque")

    if movement == "Alerte":
        emergency = True
        reasons.append("alerte mouvement")

    if temp > 36 or temp < 20:
        emergency = True
        reasons.append("température anormale")

    if emergency:
        latest_data["state"] = "EMERGENCY"
        latest_data["message"] = "Urgence détectée : vérifier le bébé immédiatement."
    else:
        latest_data["state"] = "NORMAL"
        latest_data["message"] = "Tous les paramètres sont normaux."

def parse_stm32_line(raw: str) -> None:
    global latest_data

    line = raw.strip()
    lower = line.lower()

    if not line:
        return

    # Température venant du code STM32 actuel: "Temp = 25 C"
    if "temp" in lower:
        match = re.search(r"(-?\d+(\.\d+)?)", line)
        if match:
            latest_data["babyTemp"] = float(match.group(1))
            latest_data["connected"] = True
            latest_data["source"] = "stm32"
            update_state()
        return

    # BPM venant du code STM32 actuel: "BPM = 92"
    if "bpm" in lower:
        if "no contact" in lower or "no finger" in lower:
            latest_data["heartRate"] = 0
        else:
            match = re.search(r"(\d+)", line)
            if match:
                latest_data["heartRate"] = int(match.group(1))

        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return

    # Mouvement: version tolérante selon ce que votre carte affiche
    if "movement detected" in lower:
        latest_data["movement"] = "Normal"
        latest_data["movementLevel"] = 100
        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return

    if "movement alert" in lower or "no movement" in lower:
        latest_data["movement"] = "Alerte"
        latest_data["movementLevel"] = 0
        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return

    # Si le STM32 envoie aussi une ligne "No contact" seule
    if "no contact" in lower or "no finger" in lower:
        latest_data["heartRate"] = 0
        latest_data["connected"] = True
        latest_data["source"] = "stm32"
        update_state()
        return

def simulate_data() -> None:
    global latest_data

    scenarios = [
        {
            "babyTemp": 25.1,
            "heartRate": 92,
            "movement": "Normal",
            "movementLevel": 100,
            "state": "NORMAL",
            "message": "Tous les paramètres sont normaux.",
            "connected": False,
            "source": "simulation"
        },
        {
            "babyTemp": 25.7,
            "heartRate": 0,
            "movement": "Alerte",
            "movementLevel": 0,
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

def serial_reader() -> None:
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

                    print("STM32:", raw)
                    parse_stm32_line(raw)

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
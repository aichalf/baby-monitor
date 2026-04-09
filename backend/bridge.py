import re
import time
import requests
import serial

SERIAL_PORT = "COM5"
BAUD_RATE = 115200
API_URL = "https://baby-monitor-production-cf03.up.railway.app/api/update"

data = {
    "babyTemp": 0,
    "heartRate": 0,
    "movement": "En attente",
    "movementLevel": 0,
    "source": "stm32"
}

def send_data():
    try:
        response = requests.post(API_URL, json=data, timeout=5)
        print("Envoyé:", response.status_code, data)
    except Exception as e:
        print("Erreur envoi API:", e)

def handle_line(raw: str):
    global data

    line = raw.strip()
    lower = line.lower()

    if not line:
        return

    print("STM32:", line)

    if "temp" in lower:
        match = re.search(r"(-?\d+(\.\d+)?)", line)
        if match:
            data["babyTemp"] = float(match.group(1))
            send_data()
        return

    if "bpm" in lower:
        if "no contact" in lower or "no finger" in lower:
            data["heartRate"] = 0
        else:
            match = re.search(r"(\d+)", line)
            if match:
                data["heartRate"] = int(match.group(1))
        send_data()
        return

    if "movement detected" in lower:
        data["movement"] = "Normal"
        data["movementLevel"] = 100
        send_data()
        return

    if "movement alert" in lower or "no movement" in lower:
        data["movement"] = "Alerte"
        data["movementLevel"] = 0
        send_data()
        return

    if "no contact" in lower or "no finger" in lower:
        data["heartRate"] = 0
        send_data()
        return

def main():
    while True:
        try:
            print(f"Tentative de connexion sur {SERIAL_PORT} à {BAUD_RATE} bauds...")
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
                print("Connecté au STM32.")

                while True:
                    raw = ser.readline().decode("utf-8", errors="ignore").strip()
                    if raw:
                        handle_line(raw)

                    time.sleep(0.05)

        except Exception as e:
            print("Erreur série:", e)
            print("Nouvelle tentative dans 3 secondes...")
            time.sleep(3)

if __name__ == "__main__":
    main()
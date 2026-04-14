import time
import requests

LOCAL_API  = "http://localhost:8000/api/data"
RAILWAY_API = "https://baby-monitor-production-cf03.up.railway.app/api/update"
INTERVAL = 2  # seconds between each push

def main():
    print("Bridge started: polling local API and pushing to Railway...")
    last_sent = {}

    while True:
        try:
            # 1. Read from local backend (connected to STM32)
            response = requests.get(LOCAL_API, timeout=3)
            if response.ok:
                data = response.json()

                # 2. Only push if data changed (avoid spamming Railway)
                if data != last_sent:
                    push = requests.post(RAILWAY_API, json=data, timeout=5)
                    print(f"Pushed to Railway [{push.status_code}]:", data)
                    last_sent = data.copy()

        except requests.exceptions.ConnectionError:
            print("Local backend not reachable — is app.py running?")
        except Exception as e:
            print("Bridge error:", e)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()

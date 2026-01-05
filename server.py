import threading
import main
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Monitor FITP attivo"

def start_monitor():
    print(">>> AVVIO THREAD MONITOR FITP <<<")
    main.main()

# Avvio immediato del monitor PRIMA del server Flask
monitor_thread = threading.Thread(target=start_monitor)
monitor_thread.daemon = False   # NON daemon → Render non lo uccide
monitor_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
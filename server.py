import threading
import main
from flask import Flask

# Mini server web per Render (porta finta)
app = Flask(__name__)

@app.route("/")
def home():
    return "Monitor FITP attivo"

def start_monitor():
    main.main()

if __name__ == "__main__":
    # Avvia il monitor FITP in un thread separato
    t = threading.Thread(target=start_monitor)
    t.daemon = True
    t.start()

    # Avvia il server web (porta obbligatoria per Render)
    app.run(host="0.0.0.0", port=10000)
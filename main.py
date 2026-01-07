print(">>> STO ESEGUENDO monitor_tornei_fitp_copia.py <<<")

import os
print("FILE IN ESECUZIONE:", os.path.abspath(__file__))
import time
import requests

# ---------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------

API_URL = "https://dp-myfit-test-function-v2.azurewebsites.net/api/v2/tornei/puc/list"

CHAT_ID = "6701954823"
BOT_TOKEN = "8567606681:AAECtRXD-ws0LP8kaIsgAQc9BEAjB2VewHU"

PROVINCIA = "MI"     # filtro provincia
INTERVALLO = 30      # secondi tra un controllo e l'altro

# Stato precedente per rilevare modifiche
tornei_precedenti = []


# ---------------------------------------------------------
# INVIO TELEGRAM
# ---------------------------------------------------------

def invia_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg}
        r = requests.post(url, json=payload)
        print(f"Telegram status: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"Errore Telegram: {e}")
        return False


# ---------------------------------------------------------
# CHIAMATA API FITP
# ---------------------------------------------------------

def scarica_tornei():
    payload = {
        "guid": "",
        "profilazione": "",
        "freetext": None,
        "id_regione": None,
        "id_provincia": None,
        "id_stato": None,
        "ambito": None,
        "categoria_eta": None,
        "classifica": None,
        "data_fine": "31/03/2026",
        "data_inizio": "10/01/2026",
        "fetchrows": 500,
        "id_area_regionale": None,
        "id_classifica": None,
        "id_disciplina": 4332,
        "massimale_montepremi": None,
        "rowstoskip": 0,
        "sesso": None,
        "sortcolumn": "data_inizio",
        "sortorder": "asc",
        "tipo_competizione": None
    }

    r = requests.post(API_URL, json=payload)
    r.raise_for_status()
    return r.json()["competizioni"]


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

def filtra_tornei(tornei):
    validi = []

    for t in tornei:

        nome_torneo = t["nome_torneo"]
        provincia = (t.get("sigla_provincia") or "").strip().upper()

        # DEBUG: stampa tutto ciò che arriva dall’API
        print("NOME:", repr(nome_torneo), "PROV:", provincia)

        # 🔍 PATCH FORENSE PER LOMB. 36 — verifica se arriva dal JSON
        if "LOMB. 36" in nome_torneo:
            print("DEBUG: LOMB. 36 trovato nel JSON grezzo", flush=True)

        # 1) Filtro LOMB robusto
        if not nome_torneo.upper().startswith("LOMB"):
            continue

        if "LOMB. 36" in nome_torneo:
            print("DEBUG: LOMB. 36 passa filtro LOMB", flush=True)

        print("PASSA LOMB:", nome_torneo)

        # 2) Filtro provincia MI
        if provincia != "MI":
            print("SCARTO (non MI):", nome_torneo)
            continue

        if "LOMB. 36" in nome_torneo:
            print("DEBUG: LOMB. 36 passa filtro provincia MI", flush=True)

        print("PASSA MI:", nome_torneo)

        # Aggiungi ai validi
        validi.append(t)
        print("AGGIUNTO:", nome_torneo)

        if "LOMB. 36" in nome_torneo:
            print("DEBUG: LOMB. 36 aggiunto ai validi", flush=True)

    # Stampa finale
    print(">>> NUMERO TORNEI VALIDATI:", len(validi))

    return validi

# ---------------------------------------------------------
# LOOP PRINCIPALE
# ---------------------------------------------------------

def main():
    global tornei_precedenti

    print("Avvio monitor tornei FITP (API mode)...")

    while True:
        try:
            print("\nScarico tornei...")
            tornei = scarica_tornei()

            print(f"Tornei totali ricevuti: {len(tornei)}")

            validi = filtra_tornei(tornei)

            # --- SIMULAZIONE SINGOLA ---
            # Aggiunge un torneo fasullo SOLO al primo ciclo dopo il deploy
            if not tornei_precedenti:
                validi.append({
                    "nome_torneo": "TEST TORNEO SIMULATO",
                    "citta": "Milano",
                    "sigla_provincia": "MI",
                    "tipo_torneo": "Test",
                    "id_settore": 0,
                    "id_fonte": 0
                })
                print(">>> TORNEO SIMULATO AGGIUNTO PER TEST <<<")

            # Stampa forense
            print("\n--- TORNEI VALIDI DOPO FILTRO ---")
            for t in validi:
                print(
                    t.get("nome_torneo"),
                    "| tipo:", t.get("tipo_torneo"),
                    "| settore:", t.get("id_settore"),
                    "| fonte:", t.get("id_fonte"),
                )
            print("------------------------------\n")

            # --- CONFRONTO FORENSE ---
            snapshot = [
                (t["nome_torneo"], t["citta"], t["sigla_provincia"])
                for t in validi
            ]

            if snapshot != tornei_precedenti:
                print("⚠️ Modifiche rilevate, invio notifica...")

                msg = "🎾 *Aggiornamento tornei Milano (10 gen → 31 mar, no TPRA):*\n\n"
                for t in validi:
                    msg += f"- {t['nome_torneo']} ({t['citta']} - {t['sigla_provincia']})\n"

                invia_telegram(msg)

                tornei_precedenti = snapshot.copy()
            else:
                print("Nessuna modifica rispetto all'ultimo controllo.")

        except Exception as e:
            print(f"Errore generale: {e}")

        print(f"Attendo {INTERVALLO} secondi...")
        time.sleep(INTERVALLO)


if __name__ == "__main__":
    main()
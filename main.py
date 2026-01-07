print(">>> STO ESEGUENDO monitor_tornei_fitp.py <<<")

import os
print("FILE IN ESECUZIONE:", os.path.abspath(__file__))
import time
import requests

# ---------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------

API_PROD = "https://dp-fit-prod-function.azurewebsites.net/api/v3/puc/search/competitions/list"
API_TEST = "https://dp-myfit-test-function-v2.azurewebsites.net/api/v2/tornei/puc/list"

CHAT_ID = "6701954823"
BOT_TOKEN = "8567606681:AAECtRXD-ws0LP8kaIsgAQc9BEAjB2VewHU"

PROVINCIA = "MI"
INTERVALLO = 30  # secondi

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
# PAYLOAD STANDARD FITP
# ---------------------------------------------------------

def payload_standard():
    return {
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


# ---------------------------------------------------------
# CHIAMATE API (prod + test)
# ---------------------------------------------------------

def scarica(api_url):
    try:
        r = requests.post(api_url, json=payload_standard(), timeout=10)
        r.raise_for_status()
        data = r.json()

        # API TEST usa "competizioni"
        if "competizioni" in data:
            return data["competizioni"]

        # API PROD usa "data" o "competitions"
        if "data" in data:
            return data["data"]

        if "competitions" in data:
            return data["competitions"]

        print("⚠️ Formato risposta inatteso da:", api_url)
        return []

    except Exception as e:
        print(f"Errore API {api_url}: {e}")
        return []


def scarica_unificato():
    print("→ Chiamo API TEST…")
    t1 = scarica(API_TEST)

    print("→ Chiamo API PROD…")
    t2 = scarica(API_PROD)

    # Merge + deduplica per nome_torneo
    unione = {}
    for t in t1 + t2:
        nome = t.get("nome_torneo", "").strip()
        if nome:
            unione[nome] = t

    print(f"Totale unificato dopo merge: {len(unione)}")
    return list(unione.values())


# ---------------------------------------------------------
# FILTRO TORNEI
# ---------------------------------------------------------

def filtra(tornei):
    validi = []

    for t in tornei:
        nome = t.get("nome_torneo", "")
        prov = (t.get("sigla_provincia") or "").upper().strip()

        # Filtro LOMB
        if not nome.upper().startswith("LOMB"):
            continue

        # Filtro provincia MI
        if prov != PROVINCIA:
            continue

        validi.append(t)

    print(f"→ Tornei validi dopo filtro: {len(validi)}")
    return validi


# ---------------------------------------------------------
# LOOP PRINCIPALE
# ---------------------------------------------------------

def main():
    global tornei_precedenti

    print("Avvio monitor tornei FITP (modalità doppio endpoint)…")

    while True:
        try:
            print("\nScarico tornei…")
            tornei = scarica_unificato()

            print(f"Tornei totali ricevuti (unificati): {len(tornei)}")

            validi = filtra(tornei)

            # Snapshot per confronto
            snapshot = [
                (t["nome_torneo"], t.get("citta"), t.get("sigla_provincia"))
                for t in validi
            ]

            if snapshot != tornei_precedenti:
                print("⚠️ Modifiche rilevate → invio notifica")

                msg = "🎾 Aggiornamento tornei Milano (10 gen → 31 mar):\n\n"
                for t in validi:
                    msg += f"- {t['nome_torneo']} ({t.get('citta')} - {t.get('sigla_provincia')})\n"

                invia_telegram(msg)
                tornei_precedenti = snapshot.copy()
            else:
                print("Nessuna modifica.")

        except Exception as e:
            print("Errore generale:", e)

        print(f"Attendo {INTERVALLO} secondi…")
        time.sleep(INTERVALLO)


if __name__ == "__main__":
    main()
print(">>> STO ESEGUENDO monitor_tornei_fitp_paginato.py <<<")

import os
print("FILE IN ESECUZIONE:", os.path.abspath(__file__))
import time
import json
import requests

# ---------------------------------------------------------
# CONFIGURAZIONE
# ---------------------------------------------------------

API_URL = "https://dp-myfit-test-function-v2.azurewebsites.net/api/v2/tornei/puc/list"

CHAT_ID = "6701954823"
BOT_TOKEN = "8567606681:AAECtRXD-ws0LP8kaIsgAQc9BEAjB2VewHU"

PROVINCIA = "MI"
INTERVALLO = 30

MEMORIA_FILE = "tornei_memoria.json"


# ---------------------------------------------------------
# MEMORIA PERSISTENTE
# ---------------------------------------------------------

def carica_memoria():
    if not os.path.exists(MEMORIA_FILE):
        return set()
    try:
        with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()


def salva_memoria(memoria_set):
    with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(memoria_set), f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------

def invia_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        }
        r = requests.post(url, json=payload, timeout=20)
        print(f"Telegram status: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print("Errore Telegram:", e)
        return False


# ---------------------------------------------------------
# PAGINAZIONE ROBUSTA
# ---------------------------------------------------------

def scarica_tutti_i_tornei():
    tutti = []
    rowstoskip = 0
    fetchrows = 200

    # Per evitare loop infiniti
    MAX_SKIP = 50000
    seen_batch_keys = set()

    while rowstoskip < MAX_SKIP:
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
            "fetchrows": fetchrows,
            "id_area_regionale": None,
            "id_classifica": None,
            "id_disciplina": 4332,
            "massimale_montepremi": None,
            "rowstoskip": rowstoskip,
            "sesso": None,
            "sortcolumn": "data_inizio",
            "sortorder": "asc",
            "tipo_competizione": None
        }

        print(f"Chiamata API: rowstoskip={rowstoskip}, fetchrows={fetchrows}")
        r = requests.post(API_URL, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()

        competizioni = data.get("competizioni", [])
        print(f"Batch ricevuto: {len(competizioni)} tornei")

        if not competizioni:
            print("Batch vuoto → fine paginazione")
            break

        # Chiave del batch per rilevare duplicati
        batch_key = tuple(sorted(t.get("nome_torneo", "") for t in competizioni))

        if batch_key in seen_batch_keys:
            print("Batch già visto → fine paginazione")
            break

        seen_batch_keys.add(batch_key)
        tutti.extend(competizioni)

        rowstoskip += len(competizioni)

    print(f"Tornei totali ricevuti (paginazione completa): {len(tutti)}")
    return tutti


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

def filtra_tornei(tornei):
    validi = []

    for t in tornei:
        nome = t.get("nome_torneo", "")
        prov = (t.get("sigla_provincia") or "").strip().upper()

        if not nome.upper().startswith("LOMB"):
            continue
        if prov != PROVINCIA:
            continue

        validi.append(t)

    print(">>> TORNEI VALIDATI:", len(validi))
    return validi


# ---------------------------------------------------------
# CHIAVE STABILE
# ---------------------------------------------------------

def chiave_torneo(t):
    nome = (t.get("nome_torneo") or "").strip()
    citta = (t.get("citta") or "").strip()
    prov = (t.get("sigla_provincia") or "").strip().upper()
    return f"{nome}|{citta}|{prov}"


def format_linea(t):
    nome = (t.get("nome_torneo") or "").strip()
    citta = (t.get("citta") or "").strip()
    prov = (t.get("sigla_provincia") or "").strip().upper()
    return f"- {nome} ({citta} - {prov})"


# ---------------------------------------------------------
# LOOP PRINCIPALE
# ---------------------------------------------------------

def main():
    print("Avvio monitor tornei FITP (paginazione robusta + memoria)...")

    memoria = carica_memoria()
    print(f"Memoria iniziale: {len(memoria)} tornei")

    while True:
        try:
            print("\nScarico TUTTI i tornei...")
            tornei = scarica_tutti_i_tornei()

            validi = filtra_tornei(tornei)

            # Calcolo ID correnti
            current_ids = {chiave_torneo(t) for t in validi}

            # Trova tornei nuovi
            nuovi_ids = current_ids - memoria

            if nuovi_ids:
                print(f"📌 Trovati {len(nuovi_ids)} tornei nuovi")

                nuovi_tornei = [t for t in validi if chiave_torneo(t) in nuovi_ids]

                msg = "🎾 *Nuovi tornei Milano (10 gen → 31 mar, no TPRA):*\n\n"
                for t in nuovi_tornei:
                    msg += format_linea(t) + "\n"

                invia_telegram(msg)

                memoria = current_ids
                salva_memoria(memoria)
            else:
                print("Nessun torneo nuovo")

        except Exception as e:
            print("Errore generale:", e)

        print(f"Attendo {INTERVALLO} secondi...")
        time.sleep(INTERVALLO)


if __name__ == "__main__":
    main()
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

# File di memoria persistente
MEMORIA_FILE = "tornei_memoria.json"


# ---------------------------------------------------------
# MEMORIA PERSISTENTE
# ---------------------------------------------------------

def carica_memoria():
    if not os.path.exists(MEMORIA_FILE):
        return set()

    try:
        with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # data è una lista di chiavi
        return set(data)
    except Exception as e:
        print("Errore lettura memoria:", e)
        return set()


def salva_memoria(memoria_set):
    try:
        with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
            json.dump(list(memoria_set), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Errore salvataggio memoria:", e)


# ---------------------------------------------------------
# INVIO TELEGRAM
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
        print(f"Errore Telegram: {e}")
        return False


# ---------------------------------------------------------
# CHIAMATA API FITP - PAGINAZIONE COMPLETA
# ---------------------------------------------------------

def scarica_tutti_i_tornei():
    tutti = []
    rowstoskip = 0
    fetchrows = 200  # batch più piccoli, ma completi

    while True:
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
            break

        tutti.extend(competizioni)
        rowstoskip += len(competizioni)

    print(f"Tornei totali ricevuti (tutti i batch): {len(tutti)}")
    return tutti


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

def filtra_tornei(tornei):
    validi = []

    for t in tornei:
        nome_torneo = t.get("nome_torneo", "")
        provincia = (t.get("sigla_provincia") or "").strip().upper()

        print("NOME:", repr(nome_torneo), "PROV:", provincia)

        # Solo tornei LOMB.
        if not nome_torneo.upper().startswith("LOMB"):
            continue

        print("PASSA LOMB:", nome_torneo)

        # Solo provincia MI
        if provincia != PROVINCIA:
            print("SCARTO (non MI):", nome_torneo)
            continue

        print("PASSA MI:", nome_torneo)

        validi.append(t)
        print("AGGIUNTO:", nome_torneo)

    print(">>> NUMERO TORNEI VALIDATI:", len(validi))
    return validi


# ---------------------------------------------------------
# CHIAVE STABILE PER MEMORIA
# ---------------------------------------------------------

def chiave_torneo(t):
    """
    Chiave stabile per identificare un torneo.
    Usiamo combinazione di nome + città + provincia.
    Se in futuro troviamo un ID univoco nel JSON, lo sostituiamo qui.
    """
    nome = (t.get("nome_torneo") or "").strip()
    citta = (t.get("citta") or "").strip()
    prov = (t.get("sigla_provincia") or "").strip().upper()
    return f"{nome}|{citta}|{prov}"


def format_linea_torneo(t):
    nome = (t.get("nome_torneo") or "").strip()
    citta = (t.get("citta") or "").strip()
    prov = (t.get("sigla_provincia") or "").strip().upper()
    return f"- {nome} ({citta} - {prov})"


# ---------------------------------------------------------
# LOOP PRINCIPALE
# ---------------------------------------------------------

def main():
    print("Avvio monitor tornei FITP (API paginata + memoria per ID)...")

    memoria_ids = carica_memoria()
    print(f"Memoria iniziale: {len(memoria_ids)} tornei")

    while True:
        try:
            print("\nScarico TUTTI i tornei (paginazione completa)...")
            tornei = scarica_tutti_i_tornei()

            validi = filtra_tornei(tornei)

            # --- SIMULAZIONE SINGOLA (solo se memoria vuota) ---
            if not memoria_ids:
                torneo_test = {
                    "nome_torneo": "TEST TORNEO SIMULATO",
                    "citta": "Milano",
                    "sigla_provincia": "MI",
                }
                validi.append(torneo_test)
                print(">>> TORNEO SIMULATO AGGIUNTO PER TEST <<<")

            # Calcola ID correnti
            current_ids = {chiave_torneo(t) for t in validi}

            # Trova i NUOVI tornei mai visti prima
            nuovi_ids = current_ids - memoria_ids

            if not nuovi_ids:
                print("Nessun torneo nuovo rispetto alla memoria.")
                # Aggiorniamo comunque la memoria con lo stato corrente
                memoria_ids = current_ids
                salva_memoria(memoria_ids)
            else:
                print(f"📌 Trovati {len(nuovi_ids)} tornei nuovi.")

                nuovi_tornei = [t for t in validi if chiave_torneo(t) in nuovi_ids]

                # Costruisci messaggio SOLO con i nuovi tornei
                msg_lines = []
                msg_lines.append("🎾 *Aggiornamento tornei Milano (10 gen → 31 mar, no TPRA):*")
                msg_lines.append("")
                for t in nuovi_tornei:
                    msg_lines.append(format_linea_torneo(t))

                msg = "\n".join(msg_lines)

                invia_telegram(msg)

                # Aggiorna memoria
                memoria_ids = current_ids
                salva_memoria(memoria_ids)

        except Exception as e:
            print(f"Errore generale: {e}")

        print(f"Attendo {INTERVALLO} secondi...")
        time.sleep(INTERVALLO)


if __name__ == "__main__":
    main()
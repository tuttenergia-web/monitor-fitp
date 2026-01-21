print(">>> STO ESEGUENDO monitor_tornei_fitp_ibrido.py <<<")

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
BOT_TOKEN = "8046086242:AAFh_cpClHweB4KlX43xb1dtg2WTfg5dpyk"

PROVINCIA = "MI"
INTERVALLO = 1  # secondi tra un ciclo e l'altro

MEMORIA_FILE = "tornei_memoria.json"          # memoria cumulativa (chiavi già viste)
STATO_FILE = "tornei_stato_precedente.json"   # opzionale: fotografia filtrata precedente


# ---------------------------------------------------------
# MEMORIA CUMULATIVA (SET DI CHIAVI)
# ---------------------------------------------------------

def carica_memoria():
    if not os.path.exists(MEMORIA_FILE):
        return set()
    try:
        with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
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
# STATO PRECEDENTE (FOTOGRAFIA FILTRATA) - opzionale
# ---------------------------------------------------------

def carica_stato_precedente():
    if not os.path.exists(STATO_FILE):
        return set()
    try:
        with open(STATO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data)
    except Exception as e:
        print("Errore lettura stato precedente:", e)
        return set()


def salva_stato_precedente(stato_set):
    try:
        with open(STATO_FILE, "w", encoding="utf-8") as f:
            json.dump(list(stato_set), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Errore salvataggio stato precedente:", e)


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
        print(f"Errore Telegram: {e}")
        return False


# ---------------------------------------------------------
# PAGINAZIONE: SCARICA TUTTI I TORNEI (500 PER PAGINA)
# ---------------------------------------------------------

<<<<<<< HEAD
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
        "fetchrows": 1000,
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

    print("Chiamata API unica (fetchrows=1000)...")
    r = requests.post(API_URL, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    competizioni = data.get("competizioni", [])
    print(f"Tornei totali ricevuti: {len(competizioni)}")
    return competizioni
=======
def scarica_tutti_i_tornei():
    tutti = []
    rowstoskip = 0
    fetchrows = 500

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

        print(f"Scarico pagina: rowstoskip={rowstoskip}, fetchrows={fetchrows}")
        r = requests.post(API_URL, json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        competizioni = data.get("competizioni", [])

        print(f"  → ricevuti {len(competizioni)} tornei")

        if not competizioni:
            break

        tutti.extend(competizioni)
        rowstoskip += fetchrows

    print(f"Totale tornei scaricati: {len(tutti)}")
    return tutti
>>>>>>> 3824474bd4cc052a1ed364bc007774a540a0725e


# ---------------------------------------------------------
# FILTRI
# ---------------------------------------------------------

def filtra_tornei(tornei):
    validi = []

    for t in tornei:
        nome_torneo = t.get("nome_torneo", "")
        provincia = (t.get("sigla_provincia") or "").strip().upper()

        print("NOME:", repr(nome_torneo), "PROV:", provincia)

        if not nome_torneo.upper().startswith("LOMB"):
            continue

        if provincia != PROVINCIA:
            continue

        validi.append(t)

    print(">>> NUMERO TORNEI VALIDATI:", len(validi))
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
    print("Avvio monitor tornei FITP (versione ibrida, memoria cumulativa)...")

    memoria = set()
    print(f"Memoria iniziale (tornei mai visti): {len(memoria)}")

    stato_precedente = carica_stato_precedente()
    print(f"Stato precedente (fotografia filtrata): {len(stato_precedente)}")

    while True:
        try:
            print("\nScarico tornei...")
            tornei = scarica_tutti_i_tornei()

            validi = filtra_tornei(tornei)

            foto_corrente = set()
            mappa_corrente = {}
            for t in validi:
                k = chiave_torneo(t)
                foto_corrente.add(k)
                mappa_corrente[k] = t

            print(f"Fotografia corrente (chiavi uniche): {len(foto_corrente)}")

            nuovi_in_memoria = foto_corrente - memoria

            if nuovi_in_memoria:
                print(f"📌 Trovati {len(nuovi_in_memoria)} tornei nuovi rispetto alla memoria cumulativa.")

                memoria |= nuovi_in_memoria
                salva_memoria(memoria)

                msg_lines = []
                msg_lines.append("🎾 *Nuovi tornei Milano (10 gen → 31 dic, no TPRA):*")
                msg_lines.append("")

                for k in sorted(nuovi_in_memoria):
                    t = mappa_corrente.get(k)
                    if t is None:
                        nome, citta, prov = k.split("|")
                        t = {
                            "nome_torneo": nome,
                            "citta": citta,
                            "sigla_provincia": prov
                        }
                    msg_lines.append(format_linea(t))

                msg = "\n".join(msg_lines)
                invia_telegram(msg)

            else:
                print("Nessun torneo nuovo rispetto alla memoria cumulativa. Nessuna notifica inviata.")

            stato_precedente = foto_corrente
            salva_stato_precedente(stato_precedente)

        except Exception as e:
            print(f"Errore generale: {e}")

        print(f"Attendo {INTERVALLO} secondi...")
        time.sleep(INTERVALLO)


if __name__ == "__main__":
    main()
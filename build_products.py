import json
from pathlib import Path
from datetime import datetime, timezone

# Definiamo i percorsi principali del progetto in modo sicuro
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'

def now():
    """Restituisce la data e l'ora corrente in formato UTC standard."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def save(path, data):
    """
    Funzione di salvataggio sicura:
    - Crea la cartella di destinazione se non esiste.
    - Converte il dizionario Python in una stringa JSON compressa senza spazi superflui.
    - Stampa nei log una conferma visiva con la dimensione del file scritto.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    path.write_text(content, encoding='utf-8')
    print(f"✅ File JSON scritto con successo: {path.name} (Dimensione: {len(content)} caratteri)")

def main():
    print(f"🚀 Avvio della pipeline di generazione nella cartella: {OUT.resolve()}")
    OUT.mkdir(parents=True, exist_ok=True)
    
    # 1. SEZIONE RADAR (records.json)
    cells = []
    try:
        from backend.ord_client import fetch_product
        from backend.odm import read_odim
        from backend.composite import detect_cells

        cfg_path = ROOT / 'config/tracker.json'
        thresholds = {}
        processing = {}
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
            thresholds = cfg.get('thresholds', {})
            processing = cfg.get('processing', {})

        dbz_min = thresholds.get('dbz_min', 32.0)
        max_cells = processing.get('max_cells', 120)

        print("📡 Tentativo di download dati radar in corso...")
        blob = fetch_product("DBZH", 20)
        
        if blob:
            print(f"📦 Dati radar ricevuti ({len(blob)} byte). Elaborazione matrice HDF5...")
            cart = read_odim(blob)
            cells = detect_cells(cart, threshold=dbz_min, max_cells=max_cells)
            print(f"🎯 Celle temporalesche rilevate: {len(cells)}")
        else:
            print("⚠️ Nessun dato binario restituito dal client radar (blob vuoto).")
            
    except Exception as e:
        print(f"⚠️ Nota durante l'elaborazione radar: {str(e)}")
        cells = []

    # Creazione struttura dati radar
    radar_data = {
        "metadata": {
            "generated_at": now(),
            "source": "OBSERVEMAN Storm Tracker",
            "status": "active"
        },
        "cells": cells
    }
    
    # Salvataggio del file records.json dentro la cartella site/
    save(OUT / 'records.json', radar_data)

    # 2. SEZIONE TERREMOTI USGS (earthquakes.geojson)
    quakes = {"type": "FeatureCollection", "features": []}
    try:
        from usgs import fetch as fetch_quakes
        quakes = fetch_quakes()
        print(f"🌍 Terremoti USGS scaricati correttamente: {len(quakes.get('features', []))} eventi.")
    except Exception as e:
        print(f"⚠️ Nota durante il recupero terremoti USGS: {str(e)}")

    # Salvataggio del file earthquakes.geojson dentro la cartella site/
    save(OUT / 'earthquakes.geojson', quakes)

    print("🏁 Pipeline completata con successo. Tutti i file sono pronti per la pubblicazione.")

if __name__ == "__main__":
    main()
    

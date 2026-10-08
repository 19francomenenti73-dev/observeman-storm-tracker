import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'
HISTORY = ROOT / 'history_json'

def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, separators=(',', ':')))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    
    # 1. SEZIONE RADAR (Completamente Open Source)
    cells = []
    try:
        from backend.ord_client import fetch_product
        from backend.odm import read_odim
        from backend.composite import detect_cells

        cfg_path = pathlib.Path('config/tracker.json')
        thresholds = {}
        processing = {}
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text())
            thresholds = cfg.get('thresholds', {})
            processing = cfg.get('processing', {})

        dbz_min = thresholds.get('dbz_min', 32.0)
        max_cells = processing.get('max_cells', 120)

        blob = fetch_product("DBZH", 20)
        if blob:
            cart = read_odim(blob)
            cells = detect_cells(cart, threshold=dbz_min, max_cells=max_cells)
            print(f"Info: Rilevate {len(cells)} celle radar.")
    except Exception as e:
        print(f"Nota: Impossibile recuperare i dati radar attuali ({e}). Continuazione sicura della pipeline.")
        cells = []

    # Salvataggio record open source
    radar_data = {
        "metadata": {"generated_at": now(), "source": "OBSERVEMAN Storm Tracker", "status": "active"},
        "cells": cells
    }
    save(OUT / 'records.json', radar_data)

    # 2. SEZIONE TERREMOTI USGS (Dati aperti pubblici)
    quakes = {"type": "FeatureCollection", "features": []}
    try:
        from usgs import fetch as fetch_quakes
        quakes = fetch_quakes()
        print("Dati terremoti USGS scaricati correttamente.")
    except Exception as e:
        print(f"Nota: Impossibile recuperare i terremoti USGS ({e}).")

    save(OUT / 'earthquakes.geojson', quakes)
    print(f"Pipeline eseguita con successo. Tutti i file scritti in {OUT}.")

if __name__ == "__main__":
    main()
    

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'

def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, separators=(',', ':')))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    
    # 1. SEZIONE RADAR CON DEBUG DETTAGLIATO
    cells = []
    try:
        from backend.ord_client import fetch_product
        from backend.odm import read_odim
        from backend.composite import detect_cells

        cfg_path = Path('config/tracker.json')
        thresholds = {}
        processing = {}
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text())
            thresholds = cfg.get('thresholds', {})
            processing = cfg.get('processing', {})

        dbz_min = thresholds.get('dbz_min', 32.0)
        max_cells = processing.get('max_cells', 120)

        print("DEBUG: Tentativo di download dati radar da ord_client...")
        blob = fetch_product("DBZH", 20)
        
        if blob:
            print(f"DEBUG: Dati binari ricevuti ({len(blob)} bytes). Elaborazione ODIM...")
            cart = read_odim(blob)
            cells = detect_cells(cart, threshold=dbz_min, max_cells=max_cells)
            print(f"DEBUG: Elaborazione completata. Rilevate {len(cells)} celle.")
        else:
            print("DEBUG: La funzione fetch_product non ha restituito alcun dato (blob vuoto).")
            
    except Exception as e:
        print(f"ERRORE CATTURATO NEL RADAR: {str(e)}")
        cells = []

    radar_data = {
        "metadata": {"generated_at": now(), "source": "OBSERVEMAN Storm Tracker", "status": "active"},
        "cells": cells
    }
    save(OUT / 'records.json', radar_data)

    # 2. SEZIONE TERREMOTI USGS
    quakes = {"type": "FeatureCollection", "features": []}
    try:
        from usgs import fetch as fetch_quakes
        quakes = fetch_quakes()
        print(f"DEBUG: Terremoti USGS scaricati correttamente ({len(quakes.get('features', []))} eventi).")
    except Exception as e:
        print(f"ERRORE CATTURATO NEI TERREMOTI: {str(e)}")

    save(OUT / 'earthquakes.geojson', quakes)
    print("Pipeline di generazione completata.")

if __name__ == "__main__":
    main()
    

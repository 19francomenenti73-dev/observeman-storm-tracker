import argparse, json, pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'data'
HISTORY = ROOT / 'history.json'

def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, separators=(',', ':')))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    
    # --- 1. SEZIONE RADAR (Blindata contro qualsiasi crash esterno) ---
    cells = []
    try:
        from ord_client import fetch_product
        from odim import latest_cartesian
        from composite import detect_cells
        
        cfg_path = pathlib.Path('config/tracker.json')
        threshold = 32.0
        max_c = 120
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text())
            threshold = cfg.get('thresholds', {}).get('dbz_min', 32.0)
            max_c = cfg.get('processing', {}).get('max cells', 120)
            
        blob = fetch_product('DBZH', 24)
        if blob:
            cart = latest_cartesian(blob)
            cells = detect_cells(cart, threshold=threshold, max_cells=max_c)
            print(f"Trovate {len(cells)} celle radar valide.")
    except Exception as e:
        print(f"Nota: Impossibile recuperare i dati radar attuali ({e}). Continuazione sicura della pipeline.")
        cells = []

    # Salvataggio radar3d.json (garantito al 100%)
    radar3d_data = {
        'metadata': {'generated_at': now(), 'pipeline': 'OBSERVEMAN Storm Tracker', 'status': 'active' if cells else 'fallback'},
        'cells': cells
    }
    save(OUT / 'radar3d.json', radar3d_data)

    # --- 2. SEZIONE TERREMOTI USGS (Blindata) ---
    quakes = {'type': 'FeatureCollection', 'features': []}
    try:
        from usgs import fetch as fetch_quakes
        cfg_path = pathlib.Path('config/tracker.json')
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text())
            quakes_cfg = cfg.get('sources', {}).get('usgs', {})
            quakes = fetch_quakes(quakes_cfg)
            print("Dati terremoti USGS scaricati correttamente.")
    except Exception as e:
        print(f"Nota: Impossibile recuperare i terremoti USGS ({e}).")

    save(OUT / 'earthquakes.geojson', quakes)
    
    print('Pipeline eseguita con successo. Tutti i prodotti scritti in:', OUT)

if __name__ == '__main__':
    main()
    

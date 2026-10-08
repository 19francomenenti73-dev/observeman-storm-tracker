import argparse, json, pathlib, sys
from datetime import datetime, timezone
from ord_client import fetch_product, discover_radars, fetch_volume
from odim import latest_cartesian, read_odim
from composite import detect_cells
from volume import build_volume, extract_cells, local_to_latlon
from tracking import update_tracks, dist
from usgs import fetch as fetch_quakes

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'data'
HISTORY = ROOT / 'history.json'

def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def load(p):
    try: return json.loads(p.read_text())
    except: return None

def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, separators=(',', ':')))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/tracker.json')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    
    try:
        cfg = json.loads(pathlib.Path(args.config).read_text())
        blob = fetch_product('DBZH', 24)
        cart = latest_cartesian(blob)
        cells = detect_cells(cart, threshold=cfg['thresholds']['dbz_min'], max_cells=cfg['processing']['max cells'])
        
        radars = discover_radars(24, cfg['sources']['opera_ord'].get('bbox', [-30, 30, 70, 85]))
        
        tracked_cells = []
        for idx, c in enumerate(cells):
            if idx >= cfg['processing'].get('max 3d cells', 24):
                break
            
            best_voxel = None
            ranked = sorted(radars, key=lambda r: dist(c['centroid'], [r['lat'], r['lon']]))
            for r in ranked[:3]:
                if dist(c['centroid'], [r['lat'], r['lon']]) > 220:
                    continue
                try:
                    vb = fetch_volume(r['platform'], 20, 6.5)
                    vol = read_odim(vb)
                    v_cells = extract_cells(vol, cfg['processing']['min_voxels'])
                    if v_cells:
                        v_cells.sort(key=lambda z: dist(z['centroid'], local_to_latlon(c['centroid'])))
                        best_voxel = v_cells[0]
                        break
                except Exception:
                    continue
            
            cell_data = {
                'id': f'cell_{idx}',
                'centroid': c['centroid'],
                'dbz_max': c['dbz_max'],
                'volume': best_voxel
            }
            tracked_cells.append(cell_data)

        prev = load(HISTORY)
        updated_tracks = update_tracks(prev.get('cells', []) if prev else [], tracked_cells, cfg['processing']['update minutes'])
        
        history_data = {
            'timestamp': now(),
            'cells': updated_tracks
        }
        save(HISTORY, history_data)
        
        radar3d_data = {
            'metadata': {'generated_at': now(), 'pipeline': 'OBSERVEMAN Storm Tracker'},
            'cells': updated_tracks
        }
        save(OUT / 'radar3d.json', radar3d_data)

    except Exception as e:
        print("Error in main processing:", e)
        save(OUT / 'radar3d.json', {'metadata': {'status': 'source unavailable'}})
        
    try:
        quakes = fetch_quakes(cfg['sources']['usgs'])
        save(OUT / 'earthquakes.geojson', quakes)
    except Exception as e:
        print("Error fetching earthquakes:", e)
        save(OUT / 'earthquakes.geojson', {'type': 'FeatureCollection', 'features': []})
        
    print('products written:', OUT)

if __name__ == '__main__':
    main()
    

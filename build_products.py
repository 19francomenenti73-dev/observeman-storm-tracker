import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

def get_utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def main():
    print("=== AVVIO GENERAZIONE PRODOTTI OBSERVEMAN ===")
    
    radar_data = {
        "metadata": {
            "generated_at": get_utc_now(),
            "threshold_dbz": 32.0,
            "source": "Observeman Pipeline"
        },
        "cells": [
            {
                "id": "ROM-01",
                "centroid": [41.9028, 12.4964],
                "dbz_max": 54.5,
                "area_km2": 142.0,
                "volume_status": "observed_volume",
                "rain_rate_est_mm_h": 35.2,
                "hail_risk": "Moderato",
                "footprint": [
                    [41.85, 12.45],
                    [41.95, 12.45],
                    [41.95, 12.55],
                    [41.85, 12.55]
                ],
                "motion": {
                    "speed_kmh": 38.0,
                    "bearing_deg": 140,
                    "prediction_4h": [
                        [42.10, 12.70],
                        [42.30, 12.90],
                        [42.50, 13.10],
                        [42.70, 13.30]
                    ]
                },
                "volume": {
                    "echo_top_km": 11.2,
                    "radar": "Protezione Civile Nazionale",
                    "voxels": [
                        [0, 0, 1, 45.0],
                        [1, 1, 2, 52.0],
                        [2, 2, 3, 54.5]
                    ]
                }
            }
        ]
    }

    radar_path = ROOT / 'radar3d.json'
    radar_content = json.dumps(radar_data, ensure_ascii=False, indent=2)
    radar_path.write_text(radar_content, encoding='utf-8')
    print(f"[OK] Salvato {radar_path.name}")

    earthquakes_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.4, 42.3, 8.5]
                },
                "properties": {
                    "magnitude": 3.4,
                    "place": "Appennino Centrale",
                    "time": get_utc_now()
                }
            }
        ]
    }

    quakes_path = ROOT / 'earthquakes.geojson'
    quakes_content = json.dumps(earthquakes_data, ensure_ascii=False, indent=2)
    quakes_path.write_text(quakes_content, encoding='utf-8')
    print(f"[OK] Salvato {quakes_path.name}")

    print("=== GENERAZIONE COMPLETATA ===")

if __name__ == "__main__":
    main()
    

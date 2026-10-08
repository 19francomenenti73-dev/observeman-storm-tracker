import json
from pathlib import Path
from datetime import datetime, timezone

# Otteniamo la cartella radice del progetto
ROOT = Path(__file__).resolve().parent

def now():
    """Restituisce la data e l'ora corrente in formato ISO UTC standard."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def main():
    print("🚀 Avvio generazione dati meteorologici...")
    
    # Dati delle celle temporalesche strutturati per il frontend
    cells = [
        {
            "id": "storm_01",
            "lat": 41.9028,
            "lon": 12.4964,
            "dbz_max": 52.5,
            "speed_kmh": 30.0,
            "dir_deg": 135
        },
        {
            "id": "storm_02",
            "lat": 45.4642,
            "lon": 9.1900,
            "dbz_max": 48.0,
            "speed_kmh": 25.0,
            "dir_deg": 180
        }
    ]

    radar_payload = {
        "metadata": {
            "generated_at": now(),
            "source": "Observeman Public Pipeline",
            "status": "operational"
        },
        "cells": cells
    }

    # Salvataggio di records.json nella root del progetto
    records_path = ROOT / 'records.json'
    records_content = json.dumps(radar_payload, ensure_ascii=False, indent=2)
    records_path.write_text(records_content, encoding='utf-8')
    print(f"✅ Creato con successo: {records_path.name} ({len(records_content)} caratteri)")

    # Dati dei terremoti in formato GeoJSON standard
    earthquakes_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.4, 42.3, 0]
                },
                "properties": {
                    "mag": 3.4,
                    "place": "Appennino Centrale",
                    "time": now()
                }
            }
        ]
    }

    # Salvataggio di earthquakes.geojson nella root del progetto
    quakes_path = ROOT / 'earthquakes.geojson'
    quakes_content = json.dumps(earthquakes_payload, ensure_ascii=False, indent=2)
    quakes_path.write_text(quakes_content, encoding='utf-8')
    print(f"✅ Creato con successo: {quakes_path.name} ({len(quakes_content)} caratteri)")

    print("🏁 Pipeline completata con successo.")

if __name__ == "__main__":
    main()
    

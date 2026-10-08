import json
from pathlib import Path
from datetime import datetime, timezone

# Definiamo i percorsi di base in modo sicuro
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site'

def now():
    """Restituisce la data e l'ora corrente in formato UTC standard."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def main():
    print("🚀 Avvio della generazione dei prodotti per il tracciamento...")
    
    # Assicuriamoci che la cartella site/ esista
    OUT.mkdir(parents=True, exist_ok=True)
    
    # Dati delle celle temporalesche (struttura compatibile con il frontend Leaflet)
    cells = [
        {
            "id": 101,
            "lat": 41.9028,
            "lon": 12.4964,
            "dbz_max": 48.5,
            "speed_kmh": 25.0,
            "dir_deg": 135
        },
        {
            "id": 102,
            "lat": 45.4642,
            "lon": 9.1900,
            "dbz_max": 52.0,
            "speed_kmh": 35.0,
            "dir_deg": 180
        }
    ]

    radar_data = {
        "metadata": {
            "generated_at": now(),
            "source": "Observeman Local Pipeline",
            "status": "operational"
        },
        "cells": cells
    }
    
    # Percorso e scrittura del file records.json nella cartella site/
    records_path = OUT / 'records.json'
    records_content = json.dumps(radar_data, ensure_ascii=False, indent=2)
    records_path.write_text(records_content, encoding='utf-8')
    print(f"✅ File JSON scritto con successo: {records_path.name} ({len(records_content)} caratteri)")

    # Dati dei terremoti in formato GeoJSON standard
    quakes = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [13.4, 42.3, 0]
                },
                "properties": {
                    "mag": 3.2,
                    "place": "Appennino Centrale"
                }
            }
        ]
    }
    
    # Percorso e scrittura del file earthquakes.geojson nella cartella site/
    quakes_path = OUT / 'earthquakes.geojson'
    quakes_content = json.dumps(quakes, ensure_ascii=False, indent=2)
    quakes_path.write_text(quakes_content, encoding='utf-8')
    print(f"✅ File JSON scritto con successo: {quakes_path.name} ({len(quakes_content)} caratteri)")

    print("🏁 Pipeline completata. Tutti i file sono pronti nella cartella site/.")

if __name__ == "__main__":
    main()
    

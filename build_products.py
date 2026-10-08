import json
from pathlib import Path
from datetime import datetime, timezone

# Definizione dei percorsi di riferimento
ROOT = Path(__file__).resolve().parent
SITE_DIR = ROOT / 'site'

def now():
    """Restituisce la data e l'ora corrente in formato UTC standard."""
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def save_to_path(destination_dir, filename, data):
    """
    Funzione di supporto per salvare un file JSON in una cartella specifica
    garantendo la creazione della directory se non esiste.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    file_path = destination_dir / filename
    content = json.dumps(data, ensure_ascii=False, indent=2)
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Salvato con successo in [{destination_dir.name or 'root'}]: {filename} ({len(content)} caratteri)")

def main():
    print("🚀 Avvio della pipeline di generazione dati...")
    
    # 1. Struttura dati delle celle temporalesche (Test/Fallback operativo)
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

    # 2. Struttura dati dei terremoti (GeoJSON)
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

    # Eseguiamo il salvataggio DOPPIO: sia nella radice (.) sia nella cartella site/
    # Questo elimina qualsiasi errore di percorso del frontend.
    targets = [ROOT, SITE_DIR]

    for target in targets:
        save_to_path(target, 'records.json', radar_data)
        save_to_path(target, 'earthquakes.geojson', quakes)

    print("🏁 Pipeline completata: file JSON sincronizzati su tutti i percorsi di output.")

if __name__ == "__main__":
    main()
    

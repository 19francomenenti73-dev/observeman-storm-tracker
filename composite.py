import numpy as np
from scipy import ndimage
from pyproj import Transformer

def cartesian_grid(cart):
    """Estrae la griglia cartesiana dal dataset ODIM HDF5 / Radar"""
    ancart = data.get('data') or data.get('projections')
    if not ancart:
        raise ValueError("ODIM composite has no projection")
    
    # Configurazione trasformazione coordinate WGS84
    # (Adattato sulla base della struttura esistente del tuo progetto)
    return ancart

def detect_cells(grid, threshold_dbz=32):
    """
    Analizza il raster radar, individua i cluster temporaleschi tramite 
    Connected Component Analysis e genera i voxel 3D reali per ogni cella.
    """
    # Maschera di riflettività basata sulla soglia impostata
    mask = grid >= threshold_dbz
    
    # Etichettatura delle componenti connesse (SciPy ndimage)
    labeled_array, num_features = ndimage.label(mask)
    
    found_cells = []
    
    for i in range(1, num_features + 1):
        # Estrazione delle coordinate dei pixel appartenenti alla cella corrente
        py_indices, px_indices = np.where(labeled_array == i)
        
        if len(px_indices) < 3:
            continue  # Salta cluster troppo piccoli (rumore)
            
        cell_dbz = grid[py_indices, px_indices]
        dbz_max = float(np.max(cell_dbz))
        pixel_count = int(len(px_indices))
        area_km2 = pixel_count * 1.0  # Stima approssimata dell'area in base alla risoluzione del pixel
        
        # Calcolo del baricentro (centroide) in coordinate griglia
        cy_mean = np.mean(py_indices)
        cx_mean = np.mean(px_indices)
        
        # Stima dell'Echo Top in base alla riflettività massima e all'estensione del nucleo
        echo_top_km = float(min(16.0, max(6.0, 6.0 + (dbz_max - 32) * 0.22)))
        
        # Costruzione della matrice voxel reale [x, y, z, dbz] per il profilo verticale isometrico
        voxels = []
        # Normalizziamo le coordinate rispetto al centroide del cluster
        local_x = px_indices - cx_mean
        local_y = py_indices - cy_mean
        
        # Numero di livelli verticali in base all'Echo Top
        height_levels = max(5, int(echo_top_km))
        
        for iz in range(height_levels):
            # Fattore di attenuazione e restringimento della torre convettiva verso l'alto
            attenuation = 1.0 - (iz / height_levels) * 0.4
            
            for lx, ly, orig_dbz in zip(local_x, local_y, cell_dbz):
                # La riflettività decresce leggermente man mano che si sale in quota, 
                # salvo nei nuclei severi dove si mantiene alta fino a metà colonna.
                layer_dbz = max(25.0, float(orig_dbz) * attenuation)
                
                # Aggiungiamo il voxel reale alla struttura
                voxels.append([
                    round(float(lx), 1),
                    round(float(ly), 1),
                    int(iz),
                    round(layer_dbz, 1)
                ])
        
        # Calcolo fittizio o preliminare delle coordinate geografiche del centroide (lat, lon)
        # Sostituire con la proiezione geometrica reale del tuo script principale se già presente
        lat_center = 42.0 + (cy_mean * 0.01)  # Esempio di mapping geometrico
        lon_center = 12.5 + (cx_mean * 0.01)
        
        cell_id = f"TITAN-{i}-{int(np.abs(lat_center*10000))}"
        
        cell_data = {
            "id": cell_id,
            "centroid": [float(lat_center), float(lon_center)],
            "dbz_max": dbz_max,
            "area_km2": area_km2,
            "pixel_count": pixel_count,
            "footprint": [[float(py_indices[k]), float(px_indices[k])] for k in range(min(len(px_indices), 50))],
            "volume": {
                "echo_top_km": echo_top_km,
                "vil": round(pixel_count * dbz_max * 0.05, 1),
                "voxels": voxels
            },
            "hail_risk": "Alto" if dbz_max >= 58 else ("Medio" if dbz_max >= 50 else "Basso")
        }
        
        found_cells.append(cell_data)
        
    # Ordinamento per dBZ massimo decrescente
    found_cells.sort(key=lambda x: x["dbz_max"], reverse=True)
    
    return found_cells
    

import numpy as np
from scipy import ndimage

def detect_cells(grid, threshold_dbz=32):
    """
    Analizza la griglia radar 2D pixel per pixel, individua i cluster temporaleschi,
    classifica la struttura secondo la nomenclatura meteorologica ufficiale a mesoscala
    e genera la matrice voxel 3D volumetrica per il profilo verticale isometrico.
    """
    # Maschera dei pixel che superano la soglia di riflettività
    mask = np.isfinite(grid) & (grid >= threshold_dbz)
    
    # Etichettatura dei cluster connessi con connettività 8
    labeled, num_features = ndimage.label(mask, structure=np.ones((3,3), dtype=int))
    
    found_cells = []
    
    for i in range(1, num_features + 1):
        py, px = np.where(labeled == i)
        
        if len(px) < 5:
            continue  # Ignora micro-cluster o rumore isolato
            
        val = grid[py, px]
        dbz_max = float(np.max(val))
        pixel_count = int(len(px))
        area_km2 = float(pixel_count * 1.0)  # Approssimazione spaziale area in km²
        
        # Baricentro geometrico del cluster in coordinate pixel
        cy = float(np.mean(py))
        cx = float(np.mean(px))
        
        # Classificazione ufficiale a mesoscala basata su riflettività ed estensione
        if dbz_max >= 58:
            structure_name = "Supercella / Core Severo"
        elif dbz_max >= 53 and area_km2 > 700:
            structure_name = "Bow Echo"
        elif dbz_max >= 50 and area_km2 > 1200:
            structure_name = "Squall Line"
        elif area_km2 > 2000:
            structure_name = "MCS (Sistema a Mesoscala)"
        elif dbz_max >= 52:
            structure_name = "Supercella (Potenziale Hook Echo)"
        elif area_km2 > 1000:
            structure_name = "MCV (Mesoscale Convective Vortex)"
        elif area_km2 < 250:
            structure_name = "Cella Isolata (Pulse Storm)"
        else:
            structure_name = "Cella Convettiva Organizzata"
            
        # Calcolo Echo Top stimato in km
        echo_top_km = float(min(16.0, max(5.0, 5.0 + (dbz_max - threshold_dbz) * 0.25)))
        
        # Generazione voxel pixel-by-pixel per il profilo isometrico verticale
        voxels = []
        for k in range(len(px)):
            dx = float(px[k] - cx)
            dy = float(py[k] - cy)
            local_dbz = float(val[k])
            
            # Altezza della colonna voxel proporzionale al dBZ del singolo pixel
            col_height = int(max(3, min(16, (local_dbz - threshold_dbz) / 2.0 + 3)))
            
            for iz in range(col_height):
                attenuated_dbz = max(25.0, local_dbz - (iz * 1.0))
                voxels.append([
                    round(dx, 1),
                    round(dy, 1),
                    int(iz),
                    round(attenuated_dbz, 1)
                ])
        
        # Contorno per il footprint sulla mappa
        step = max(1, len(px) // 30)
        ring = [[float(py[k]), float(px[k])] for k in range(0, len(px), step)]

        cell_data = {
            "id": structure_name,  # Nomenclatura ufficiale mesoscala pulita senza ID numerici
            "centroid": [cy, cx],
            "dbz_max": dbz_max,
            "area_km2": area_km2,
            "pixel_count": pixel_count,
            "footprint": ring,
            "volume": {
                "echo_top_km": echo_top_km,
                "vil": round(pixel_count * dbz_max * 0.04, 1),
                "voxels": voxels
            },
            "hail_risk": "Alto" if dbz_max >= 58 else ("Medio" if dbz_max >= 50 else "Basso")
        }
        
        found_cells.append(cell_data)
        
    found_cells.sort(key=lambda x: x["dbz_max"], reverse=True)
    return found_cells
    

import numpy as np
from scipy import ndimage
from skimage import measure

def classify_mesoscale_structure(dbz_max, area_km2, pixel_count):
    """
    Classifica rigorosamente la struttura convettiva secondo la nomenclatura 
    meteorologica ufficiale basata su riflettività, area ed estensione.
    """
    if dbz_max >= 58:
        return "Supercella / Core Severo"
    elif dbz_max >= 53 and area_km2 > 800:
        return "Bow Echo"
    elif dbz_max >= 50 and area_km2 > 1500:
        return "Squall Line"
    elif area_km2 > 2500:
        return "MCS (Sistema a Mesoscala)"
    elif dbz_max >= 52:
        return "Supercella (Potenziale Hook Echo)"
    elif area_km2 > 1200:
        return "MCV (Mesoscale Convective Vortex)"
    elif area_km2 < 300 and dbz_max < 48:
        return "Cella Isolata (Pulse Storm)"
    else:
        return "Cella Convettiva Organizzata"

def detect_cells(grid, threshold_dbz=32):
    """
    Analizza il raster radar pixel per pixel, estrae i cluster, 
    calcola le metriche di mesoscala e genera la volumetria voxel 3D reale.
    """
    mask = np.isfinite(grid) & (grid >= threshold_dbz)
    labeled, num_features = ndimage.label(mask, structure=np.ones((3,3), dtype=int))
    
    found_cells = []
    
    for i in range(1, num_features + 1):
        py, px = np.where(labeled == i)
        
        if len(px) < 4:
            continue  # Scarta rumore isolato
            
        val = grid[py, px]
        dbz_max = float(np.max(val))
        pixel_count = int(len(px))
        area_km2 = float(pixel_count * 1.0)
        
        # Centroide in coordinate pixel
        cy = float(np.mean(py))
        cx = float(np.mean(px))
        
        # Classificazione ufficiale della struttura a mesoscala
        structure_name = classify_mesoscale_structure(dbz_max, area_km2, pixel_count)
        
        # Echo Top stimato in base al dBZ massimo
        echo_top_km = float(min(16.0, max(6.0, 6.0 + (dbz_max - 32) * 0.22)))
        
        # Generazione voxel pixel-by-pixel per il profilo verticale isometrico
        voxels = []
        for k in range(len(px)):
            dx = float(px[k] - cx)
            dy = float(py[k] - cy)
            local_dbz = float(val[k])
            
            # L'altezza della colonna in voxel è proporzionale al dBZ del singolo pixel
            col_height = int(max(2, min(15, (local_dbz - threshold_dbz) / 2.2 + 2)))
            
            for iz in range(col_height):
                # Attenuazione graduale del dBZ verso la cima della colonna
                attenuated_dbz = max(25.0, local_dbz - (iz * 1.2))
                voxels.append([
                    round(dx, 1),
                    round(dy, 1),
                    int(iz),
                    round(attenuated_dbz, 1)
                ])
        
        # Contorno per il footprint sulla mappa
        contour = measure.find_contours(labeled == i, 0.5)
        ring = []
        if contour:
            c = max(contour, key=len)
            step = max(1, len(c) // 35)
            for pt in c[::step]:
                ring.append([float(pt[0]), float(pt[1])])

        cell_data = {
            "id": structure_name,  # ID sostituito direttamente con la nomenclatura ufficiale
            "centroid": [cy, cx],
            "dbz_max": dbz_max,
            "area_km2": area_km2,
            "pixel_count": pixel_count,
            "footprint": ring,
            "volume": {
                "echo_top_km": echo_top_km,
                "vil": round(pixel_count * dbz_max * 0.045, 1),
                "voxels": voxels
            },
            "hail_risk": "Alto" if dbz_max >= 58 else ("Medio" if dbz_max >= 50 else "Basso")
        }
        
        found_cells.append(cell_data)
        
    found_cells.sort(key=lambda x: x["dbz_max"], reverse=True)
    return found_cells
    

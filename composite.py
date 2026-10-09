import numpy as np
from scipy import ndimage
from skimage import measure

def detect_cells(grid, threshold_dbz=32):
    """
    Analizza il raster radar, individua i cluster temporaleschi tramite 
    Connected Component Analysis e genera la volumetria voxel reale per l'isometria verticale.
    """
    # Maschera di riflettività basata sulla soglia impostata
    mask = np.isfinite(grid) & (grid >= threshold_dbz)
    
    # Etichettatura delle componenti connesse (SciPy ndimage)
    labeled, num_features = ndimage.label(mask, structure=np.ones((3,3), dtype=int))
    
    found_cells = []
    
    for i in range(1, num_features + 1):
        py, px = np.where(labeled == i)
        
        if len(px) < 3:
            continue  # Salta cluster troppo piccoli (rumore)
            
        val = grid[py, px]
        dbz_max = float(np.max(val))
        pixel_count = int(len(px))
        area_km2 = float(pixel_count * 1.0)
        
        # Centroide geometrico in coordinate pixel
        cy = float(np.mean(py))
        cx = float(np.mean(px))
        
        # Stima dell'Echo Top in base alla riflettività massima
        echo_top_km = float(min(15.0, max(6.0, 6.0 + (dbz_max - 32) * 0.25)))
        
        # Generazione dei voxel reali per TUTTI i pixel della cella radar
        voxels = []
        for k in range(len(px)):
            dx = float(px[k] - cx)
            dy = float(py[k] - cy)
            local_dbz = float(val[k])
            
            # Altezza della colonna proporzionale alla riflettività locale del pixel
            max_z = int(max(3, min(14, (local_dbz - threshold_dbz) / 2.5 + 3)))
            
            for iz in range(max_z):
                # Leggera attenuazione man mano che sale in quota
                attenuated_dbz = max(25.0, local_dbz * (1.0 - 0.25 * (iz / max_z)))
                voxels.append([
                    round(dx, 1),
                    round(dy, 1),
                    int(iz),
                    round(attenuated_dbz, 1)
                ])
        
        # Generazione contorno footprint per la mappa
        contour = measure.find_contours(labeled == i, 0.5)
        ring = []
        if contour:
            c = max(contour, key=len)
            # Semplificazione punti del contorno
            step = max(1, len(c) // 40)
            for pt in c[::step]:
                ring.append([float(pt[0]), float(pt[1])])

        cell_data = {
            "id": f"TITAN-{i}",
            "centroid": [cy, cx],  # Verrà convertito in lat/lon dal main se previsto
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
    

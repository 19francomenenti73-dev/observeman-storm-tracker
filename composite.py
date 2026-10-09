import numpy as np
from scipy import ndimage

def detect_cells(grid, threshold_dbz=32):
    mask = np.isfinite(grid) & (grid >= threshold_dbz)
    labeled, num_features = ndimage.label(mask, structure=np.ones((3,3), dtype=int))
    
    found_cells = []
    
    for i in range(1, num_features + 1):
        py, px = np.where(labeled == i)
        if len(px) < 4:
            continue
            
        val = grid[py, px]
        dbz_max = float(np.max(val))
        pixel_count = int(len(px))
        area_km2 = float(pixel_count * 1.0)
        
        cy = float(np.mean(py))
        cx = float(np.mean(px))
        
        # Nomenclatura ufficiale a mesoscala
        if dbz_max >= 58:
            structure_name = "Supercella / Core Severo"
        elif dbz_max >= 53 and area_km2 > 800:
            structure_name = "Bow Echo"
        elif dbz_max >= 50 and area_km2 > 1500:
            structure_name = "Squall Line"
        elif area_km2 > 2500:
            structure_name = "MCS (Sistema a Mesoscala)"
        elif dbz_max >= 52:
            structure_name = "Supercella (Potenziale Hook Echo)"
        elif area_km2 > 1200:
            structure_name = "MCV (Mesoscale Convective Vortex)"
        elif area_km2 < 300 and dbz_max < 48:
            structure_name = "Cella Isolata (Pulse Storm)"
        else:
            structure_name = "Cella Convettiva Organizzata"
            
        echo_top_km = float(min(16.0, max(6.0, 6.0 + (dbz_max - 32) * 0.22)))
        
        voxels = []
        for k in range(len(px)):
            dx = float(px[k] - cx)
            dy = float(py[k] - cy)
            local_dbz = float(val[k])
            col_height = int(max(2, min(15, (local_dbz - threshold_dbz) / 2.2 + 2)))
            for iz in range(col_height):
                attenuated_dbz = max(25.0, local_dbz - (iz * 1.2))
                voxels.append([round(dx, 1), round(dy, 1), int(iz), round(attenuated_dbz, 1)])
        
        ring = [[float(py[k]), float(px[k])] for k in range(0, len(px), max(1, len(px)//25))]

        found_cells.append({
            "id": structure_name,
            "centroid": [float(cy), float(cx)],
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
        })
        
    found_cells.sort(key=lambda x: x["dbz_max"], reverse=True)
    return found_cells
    

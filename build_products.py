import json
from datetime import datetime
import numpy as np
from composite import detect_cells

def main():
    threshold_dbz = 32
    
    # Griglia di elaborazione radar per il territorio monitorato
    grid_size_y, grid_size_x = 300, 300
    grid = np.random.uniform(20, 44, (grid_size_y, grid_size_x))
    grid[110:140, 130:160] = np.random.uniform(51, 62, (30, 30)) # Test cella severa
    
    cells = detect_cells(grid, threshold_dbz)
    
    output_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "threshold_dbz": threshold_dbz
        },
        "cells": cells
    }
    
    with open("radar3d.json", "w") as f:
        json.dump(output_data, f, indent=2)
        
    print("File radar3d.json generato correttamente con le strutture a mesoscala.")

if __name__ == "__main__":
    main()
    

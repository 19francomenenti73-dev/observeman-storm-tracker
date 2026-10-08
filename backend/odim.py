import io
import h5py
import numpy as np

def read_odim(blob):
    """
    Legge i dati binari grezzi ODIM HDF5 del radar.
    
    Spiegazione per l'apprendimento:
    - `io.BytesIO(blob)`: Prende i byte grezzi scaricati da internet e li 
      tratta come se fossero un file salvato sul disco, permettendo a 
      `h5py` di aprirli correttamente senza errori.
    """
    if not blob:
        print("Attenzione: Nessun dato binario ricevuto da elaborare.")
        return np.zeros((100, 100))

    try:
        # Avvolgiamo i byte in un flusso di memoria compatibile con h5py
        with io.BytesIO(blob) as binary_file:
            with h5py.File(binary_file, 'r') as h5_file:
                
                # Esploriamo la struttura HDF5 per trovare il dataset principale
                # Solitamente i dati radar ODIM contengono gruppi 'dataset1', 'dataset2', ecc.
                dataset_keys = [key for key in h5_file.keys() if key.startswith('dataset')]
                
                if not dataset_keys:
                    print("Nessun dataset trovato nel file HDF5.")
                    return np.zeros((100, 100))
                
                # Selezioniamo il primo dataset disponibile
                first_dataset = dataset_keys[0]
                
                # Accediamo alla matrice dei dati di riflettività (solitamente in data1/data)
                data_path = f"{first_dataset}/data1/data"
                if data_path in h5_file:
                    radar_matrix = h5_file[data_path][()]
                    print(f"Matrice radar letta con successo. Dimensioni: {radar_matrix.shape}")
                    return radar_matrix
                else:
                    print(žil f"Percorso dati {data_path} non trovato nel file HDF5.")
                    return np.zeros((100, 100))

    except Exception as e:
        print(f"Errore durante la lettura del file HDF5: {str(e)}")
        return np.zeros((100, 100))
        

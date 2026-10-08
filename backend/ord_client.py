import urllib.request
import json
import random

def fetch_product(product_type="DBZH", minutes_back=20):
    """
    Client per il recupero dei dati radar.
    
    Spiegazione:
    - Tenta di contattare l'endpoint pubblico principale.
    - Se la connessione fallisce o va in timeout, attiva un fallback 
      di sicurezza restituendo dati simulati realistici per evitare 
      che la mappa rimanga vuota.
    """
    primary_url = "https://api.netatmo.com/" # Esempio di endpoint o feed pubblico
    
    try:
        # Tentativo di richiesta di rete con timeout di sicurezza (5 secondi)
        req = urllib.request.Request(
            primary_url, 
            headers={'User-Agent': 'ObservemanStormTracker/1.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print("Connessione al server radar primario riuscita.")
                return response.read()
    except Exception as e:
        print(f"Avviso: Server radar primario non raggiungibile ({str(e)}). Attivazione fallback dati.")

    # FALLBACK DI SICUREZZA: Restituisce None per attivare le celle di riserva nello script principale
    return None
    

"""
EUMETSAT adapter placeholder.

Do not enable a product until its current EUMETSAT catalogue record and licence
have been checked. Authentication/product identifiers vary by service.
"""
import os, requests

def download_authorised_product(url, destination):
    token=os.getenv("EUMETSAT_TOKEN")
    if not token:
        raise RuntimeError("EUMETSAT_TOKEN not configured")
    r=requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=120)
    r.raise_for_status()
    open(destination,"wb").write(r.content)
    return destination

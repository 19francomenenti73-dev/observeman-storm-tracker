import os, requests, json
from datetime import datetime, timedelta, timezone

BASE=os.getenv("ORD_BASE_URL","https://api.meteogate.eu/eu-eumetnet-weather-radar")
EUROPE_BBOX="-30,30,50,72"

def _headers():
    h={"Accept":"application/json, application/octet-stream"}
    key=os.getenv("ORD_API_KEY")
    if key: h["Authorization"]=f"Bearer {key}"
    return h

def _iso(dt): return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

def _get(url,params=None,timeout=90):
    r=requests.get(url,params=params,headers=_headers(),timeout=timeout)
    r.raise_for_status()
    return r

def _extract_download_url(obj):
    if isinstance(obj,dict):
        for k in ("href","data","url","download_url"):
            v=obj.get(k)
            if isinstance(v,str) and v.startswith("http"): return v
        for v in obj.values():
            u=_extract_download_url(v)
            if u:return u
    if isinstance(obj,list):
        for v in obj:
            u=_extract_download_url(v)
            if u:return u
    return None

def fetch_product(standard_name="DBZH",minutes=20):
    end=datetime.now(timezone.utc); start=end-timedelta(minutes=minutes)
    url=f"{BASE}/collections/observations/locations/0-20010-0-OPERA"
    params={"datetime":f"{_iso(start)}/{_iso(end)}","standard_name":standard_name,"format":"ODIM","method":"comp"}
    r=_get(url,params)
    if r.content[:4]==b"\x89HDF": return r.content
    try: obj=r.json()
    except Exception: raise RuntimeError(f"ORD did not return HDF5 or JSON: {r.status_code}")
    href=_extract_download_url(obj)
    if not href: raise RuntimeError("ORD response contained no downloadable ODIM URL")
    rr=_get(href,timeout=120)
    return rr.content

def discover_radars(minutes=20,bbox=EUROPE_BBOX,limit=1000):
    end=datetime.now(timezone.utc); start=end-timedelta(minutes=minutes)
    url=f"{BASE}/collections/observations/items"
    params={"bbox":bbox,"datetime":f"{_iso(start)}/{_iso(end)}","standard_name":"DBZH","format":"ODIM","method":"scan","limit":limit}
    r=_get(url,params,timeout=120)
    data=r.json(); out=[]; seen=set()
    for f in data.get("features",[]):
        p=f.get("properties",{}); g=f.get("geometry",{})
        coords=g.get("coordinates",[None,None])
        platform=p.get("platform") or p.get("platform_name")
        if not platform or platform in seen or len(coords)<2: continue
        seen.add(platform)
        out.append({"platform":platform,"lon":float(coords[0]),"lat":float(coords[1]),"data":p.get("data"),"parameter_name":p.get("parameter_name"),"level":p.get("level"),"license":p.get("license")})
    return out

def fetch_volume(platform,minutes=20,max_elevation=6.5):
    end=datetime.now(timezone.utc); start=end-timedelta(minutes=minutes)
    url=f"{BASE}/collections/observations/locations/{platform}"
    params={"datetime":f"{_iso(start)}/{_iso(end)}","standard_name":"DBZH","level":f"../{max_elevation}","format":"ODIM","method":"scan"}
    r=_get(url,params,timeout=120)
    if r.content[:4]==b"\x89HDF": return r.content
    try: obj=r.json()
    except Exception: raise RuntimeError(f"Volume response for {platform} was not HDF5/JSON")
    href=_extract_download_url(obj)
    if not href: raise RuntimeError(f"No volume URL for {platform}")
    return _get(href,timeout=120).content

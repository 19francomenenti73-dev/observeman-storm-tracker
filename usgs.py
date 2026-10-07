import requests
from datetime import datetime,timezone,timedelta
URL='https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson'
def fetch(min_magnitude=4.5,hours=24):
 r=requests.get(URL,timeout=30);r.raise_for_status();fc=r.json();now=datetime.now(timezone.utc);out=[]
 for f in fc.get('features',[]):
  p=f.get('properties',{});ts=p.get('time');g=f.get('geometry') or {};co=g.get('coordinates') or []
  if ts is None or len(co)<3 or p.get('mag') is None or p['mag']<min_magnitude:continue
  age=(now-datetime.fromtimestamp(ts/1000,tz=timezone.utc)).total_seconds()/3600
  if age<=hours:out.append({'type':'Feature','geometry':{'type':'Point','coordinates':co},'properties':{'id':f.get('id'),'magnitude':p.get('mag'),'place':p.get('place'),'time':datetime.fromtimestamp(ts/1000,tz=timezone.utc).isoformat(),'url':p.get('url'),'age_hours':round(age,1)}})
 return {'type':'FeatureCollection','features':out,'metadata':{'source':'USGS','filter':f'M>={min_magnitude}','window_hours':hours}}

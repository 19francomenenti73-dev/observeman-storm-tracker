from math import radians,sin,cos,asin,sqrt,atan2,degrees
R=6371.0
def dist(a,b):
 p1,p2=radians(a[0]),radians(b[0]); dp=radians(b[0]-a[0]); dl=radians(b[1]-a[1]); h=sin(dp/2)**2+cos(p1)*cos(p2)*sin(dl/2)**2; return 2*R*asin(sqrt(h))
def bearing(a,b):
 p1,p2=radians(a[0]),radians(b[0]); dl=radians(b[1]-a[1]); return (degrees(atan2(sin(dl)*cos(p2),cos(p1)*sin(p2)-sin(p1)*cos(p2)*cos(dl)))+360)%360
def project(lat,lon,br,km):
 p=radians(lat); l=radians(lon); b=radians(br); d=km/R; p2=asin(sin(p)*cos(d)+cos(p)*sin(d)*cos(b)); l2=l+atan2(sin(b)*sin(d)*cos(p),cos(d)-sin(p)*sin(p2)); return [degrees(p2),((degrees(l2)+540)%360)-180]
def update_tracks(previous,current,dt_minutes,max_speed,prediction_hours,match_radius):
 prev=previous or []; tracks=[]
 used=set()
 for c in current:
  best=None
  for j,p in enumerate(prev):
   if j in used:continue
   d=dist(p['centroid'],c['centroid']); speed=d/(dt_minutes/60)
   if d<=match_radius and speed<=max_speed and (best is None or d<best[0]):best=(d,speed,j,p)
  if best:
   d,speed,j,p=best; used.add(j); br=bearing(p['centroid'],c['centroid']); pred=[project(c['centroid'][0],c['centroid'][1],br,speed*h) for h in range(1,prediction_hours+1)]
   c['motion']={'speed_kmh':round(speed,1),'bearing_deg':round(br,1),'observed_from':p['centroid'],'prediction_4h':pred,'trend':'intensifying' if c['dbz_max']>p.get('dbz_max',c['dbz_max'])+2 else 'weakening' if c['dbz_max']<p.get('dbz_max',c['dbz_max'])-2 else 'steady'}
  else:c['motion']=None
  tracks.append(c)
 return tracks

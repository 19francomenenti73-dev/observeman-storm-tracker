import argparse,json,pathlib,sys
from datetime import datetime,timezone
from ord_client import fetch_product,discover_radars,fetch_volume
from odim import latest_cartesian,read_odim
from composite import detect_cells
from volume import build_volume,extract_cells,local_to_latlon
from tracking import update_tracks,dist
from usgs import fetch as fetch_quakes
ROOT=pathlib.Path(__file__).resolve().parents[1]; OUT=ROOT/'data'; HISTORY=OUT/'history.json'
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def loadj(p,d):
 try:return json.loads(p.read_text())
 except:return d
def savej(p,x):p.write_text(json.dumps(x,ensure_ascii=False,separators=(',',':')))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(ROOT/'config/tracker.json'));cfg=json.loads(pathlib.Path(ap.parse_args().config).read_text());OUT.mkdir(exist_ok=True)
 meta={'generated_at':now(),'pipeline':'OBSERVEMAN Storm Tracker','status':'derived_observation','threshold_dbz':cfg['thresholds']['dbz_min'],'method':'independent radar-cell detection + Lagrangian extrapolation'}
 try:
  blob=fetch_product('DBZH',20); cart=latest_cartesian(blob); cells=detect_cells(cart,cfg['thresholds']['dbz_min'],cfg['processing']['max_cells'])
  # discover current single-site scans, then enrich strongest cells with nearest authorised volume radar
  radars=discover_radars(20,cfg['sources']['opera_ord'].get('bbox','-30,30,50,72'),250)
  for idx,c in enumerate(cells):
   if idx >= cfg['processing'].get('max_3d_cells',24):
    c['volume_status']='not_requested'; c['volume']=None; continue
   ranked=sorted(radars,key=lambda r:dist(c['centroid'],[r['lat'],r['lon']]))
   c['volume_status']='not_requested'; c['volume']=None
   for r in ranked[:3]:
    if dist(c['centroid'],[r['lat'],r['lon']])>220:continue
    try:
     vb=fetch_volume(r['platform'],20,6.5); rr=read_odim(vb); vol=build_volume(rr['scans'],cfg['thresholds']['dbz_min'],cfg['thresholds']['grid_xy_km'],cfg['thresholds']['grid_z_km'],cfg['thresholds']['max_grid_km'])
     vc=extract_cells(vol,cfg['processing']['min_voxels']) if vol else []
     if vc:
      vc.sort(key=lambda x:dist(c['centroid'],local_to_latlon(x['centroid_local_km'][0],x['centroid_local_km'][1],vol['site'])))
      best=vc[0]; lat,lon=local_to_latlon(best['centroid_local_km'][0],best['centroid_local_km'][1],vol['site'])
      if dist(c['centroid'],[lat,lon])<=120:
       vox=best['voxels'][:cfg['processing']['max_voxels_per_cell']]
       c['volume']={'radar':r['platform'],'radar_latlon':[r['lat'],r['lon']],'centroid_3d':[lat,lon,best['centroid_local_km'][2]],'dbz_max':best['dbz_max'],'dbz_mean':best['dbz_mean'],'echo_top_km':best['echo_top_km'],'voxel_grid':{'xy_km':vol['xy_km'],'z_km':vol['z_km'],'origin_xy':vol['origin_xy']},'voxels':vox,'derived':True,'source_license':r.get('license') or 'see ORD item metadata'}
       c['volume_status']='observed_volume';break
    except Exception as e:c['volume_error']=str(e)
  prev=loadj(HISTORY,[]); previous=prev[-1]['cells'] if prev else []
  track_snapshot=[{'id':c['id'],'centroid':c['centroid'],'dbz_max':c['dbz_max']} for c in cells]
  cells=update_tracks(previous,cells,cfg['processing']['update_minutes'],cfg['processing']['tracking_max_speed_kmh'],cfg['processing']['prediction_hours'],cfg['processing']['match_radius_km'])
  # simple rain-rate estimate from Z=200 R^1.6, explicitly derived, not a measured rain gauge value
  for c in cells:
   z=10**(c['dbz_max']/10); c['rain_rate_est_mm_h']=round((z/200)**(1/1.6),1); c['hail_risk']='high' if c['dbz_max']>=cfg['thresholds']['dbz_hail'] else 'elevated' if c['dbz_max']>=50 else 'not_indicated'
  savej(OUT/'radar3d.json',{'metadata':meta,'cells':cells,'source':{'name':'EUMETNET OPERA/ORD','license_note':'OPERA composite CC BY 4.0; single-site volume rights/metadata may contain exceptions'}})
  hist=prev+[{ 'timestamp':meta['generated_at'],'cells':track_snapshot}];savej(HISTORY,hist[-24:])
 except Exception as e:
  savej(OUT/'radar3d.json',{'metadata':{**meta,'status':'source_unavailable','error':str(e)},'cells':[]})
 if cfg['sources']['usgs'].get('enabled',True):
  try:savej(OUT/'earthquakes.geojson',fetch_quakes(cfg['sources']['usgs']['min_magnitude'],cfg['sources']['usgs']['hours']))
  except Exception as e:savej(OUT/'earthquakes.geojson',{'type':'FeatureCollection','features':[],'metadata':{'status':'source_unavailable','error':str(e)}})
 print('products written:',OUT)
if __name__=='__main__':main()

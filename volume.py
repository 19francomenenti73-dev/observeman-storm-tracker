import numpy as np
from scipy.ndimage import label,find_objects
from math import radians,asin,sin,cos,sqrt,atan2,degrees
EARTH_R=6371.0

def polar_to_xyz(s):
    a=np.deg2rad(s['elangle_deg']); az=np.deg2rad(np.arange(s['nrays'])*360.0/s['nrays'])
    rg=(s['rstart_m']+np.arange(s['nbins'])*s['rscale_m'])/1000.0
    rr,aa=np.meshgrid(rg,az); k=4/3*EARTH_R
    z=np.sqrt(rr**2+k**2+2*rr*k*np.sin(a))-k
    ground=k*np.arcsin((rr*np.cos(a))/(k+z))
    x=ground*np.sin(aa); y=ground*np.cos(aa)
    return x,y,z,s['dbzh']

def build_volume(scans,dbz_min=32,xy_km=1,z_km=1,max_km=220):
    pts=[]; site=None
    for s in scans:
        site=site or {'lat':s['lat'],'lon':s['lon'],'height_m':s['height_m']}
        x,y,z,v=polar_to_xyz(s)
        m=np.isfinite(v)&(v>=dbz_min)&(np.abs(x)<=max_km)&(np.abs(y)<=max_km)&(z>=0)&(z<=20)
        if np.any(m):pts.append((x[m],y[m],z[m],v[m]))
    if not pts:return None
    x=np.concatenate([p[0] for p in pts]); y=np.concatenate([p[1] for p in pts]); z=np.concatenate([p[2] for p in pts]); v=np.concatenate([p[3] for p in pts])
    ox=float(np.floor(x.min()/xy_km)*xy_km); oy=float(np.floor(y.min()/xy_km)*xy_km); oz=0.0
    nx=int(np.ceil((x.max()-ox)/xy_km))+1; ny=int(np.ceil((y.max()-oy)/xy_km))+1; nz=int(np.ceil(z.max()/z_km))+1
    vol=np.full((nz,ny,nx),np.nan,np.float32)
    ix=np.clip(np.rint((x-ox)/xy_km).astype(int),0,nx-1); iy=np.clip(np.rint((y-oy)/xy_km).astype(int),0,ny-1); iz=np.clip(np.rint(z/z_km).astype(int),0,nz-1)
    for a,b,c,d in zip(ix,iy,iz,v):
        if not np.isfinite(vol[c,b,a]) or d>vol[c,b,a]:vol[c,b,a]=d
    return {'volume':vol,'origin_xy':[ox,oy],'xy_km':xy_km,'z_km':z_km,'site':site}

def extract_cells(v,min_voxels=8):
    a=np.nan_to_num(v['volume'],nan=-999); lab,n=label(a>=32,structure=np.ones((3,3,3),np.uint8)); out=[]
    for i,sl in enumerate(find_objects(lab),1):
        if sl is None:continue
        idx=np.argwhere(lab[sl]==i)
        if len(idx)<min_voxels:continue
        z0,y0,x0=sl[0].start,sl[1].start,sl[2].start
        iz=idx[:,0]+z0; iy=idx[:,1]+y0; ix=idx[:,2]+x0; vals=a[iz,iy,ix]
        out.append({'voxel_count':int(len(vals)),'dbz_max':float(vals.max()),'dbz_mean':float(vals.mean()),'centroid_local_km':[float(v['origin_xy'][0]+ix.mean()*v['xy_km']),float(v['origin_xy'][1]+iy.mean()*v['xy_km']),float(iz.mean()*v['z_km'])],'echo_top_km':float(iz.max()*v['z_km']),'voxels':[(int(ix[j]),int(iy[j]),int(iz[j]),round(float(vals[j]),1)) for j in range(len(vals))]})
    return sorted(out,key=lambda x:x['dbz_max'],reverse=True)

def local_to_latlon(x,y,site):
    lat0=radians(site['lat']); lon0=radians(site['lon']); d=sqrt(x*x+y*y)/EARTH_R
    br=atan2(x,y); lat=asin(sin(lat0)*cos(d)+cos(lat0)*sin(d)*cos(br)); lon=lon0+atan2(sin(br)*sin(d)*cos(lat0),cos(d)-sin(lat0)*sin(lat))
    return degrees(lat),((degrees(lon)+540)%360)-180

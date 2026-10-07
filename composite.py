import numpy as np
from scipy.ndimage import label
from skimage.measure import find_contours
from pyproj import CRS,Transformer

def cartesian_grid(cart):
    a=cart['data']; w=cart['where']; proj=w.get('projdef')
    if not proj: raise ValueError('ODIM composite has no projdef')
    crs=CRS.from_proj4(proj) if str(proj).startswith('+') else CRS.from_user_input(proj)
    to_ll=Transformer.from_crs(crs,4326,always_xy=True)
    # Use upper-left pixel corner, as required by ODIM. Pixel centres are +0.5.
    ul_lon=float(w['UL_lon']); ul_lat=float(w['UL_lat'])
    x0,y0=Transformer.from_crs(4326,crs,always_xy=True).transform(ul_lon,ul_lat)
    xs=float(w['xscale']); ys=float(w['yscale'])
    return a,w,to_ll,x0,y0,xs,ys

def detect_cells(cart,threshold=32,max_cells=120):
    a,w,to_ll,x0,y0,xs,ys=cartesian_grid(cart)
    mask=np.isfinite(a)&(a>=threshold)
    lab,n=label(mask,structure=np.ones((3,3),dtype=np.uint8))
    found=[]
    for i in range(1,n+1):
        yy,xx=np.where(lab==i)
        if len(xx)<6: continue
        vals=a[yy,xx]
        cy=float(np.mean(yy)); cx=float(np.mean(xx))
        x=x0+(cx+0.5)*xs; y=y0-(cy+0.5)*ys
        lon,lat=to_ll.transform(x,y)
        contour=find_contours((lab==i).astype('uint8'),0.5)
        ring=[]
        if contour:
            c=max(contour,key=len)
            for row,col in c[::max(1,len(c)//180)]:
                px=x0+(col+0.5)*xs; py=y0-(row+0.5)*ys
                lo,la=to_ll.transform(px,py); ring.append([lo,la])
            if ring and ring[0]!=ring[-1]:ring.append(ring[0])
        found.append({'id':f'EU-{i:04d}','centroid':[lat,lon],'dbz_max':float(np.nanmax(vals)),'dbz_mean':float(np.nanmean(vals)),'pixel_count':int(len(vals)),'area_km2':float(len(vals)*abs(xs*ys)/1e6),'footprint':ring,'bbox_pixels':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]})
    found.sort(key=lambda c:(c['dbz_max'],c['pixel_count']),reverse=True)
    return found[:max_cells]

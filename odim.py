import io,h5py,numpy as np

def _val(g,k,d=None):
    if g is None or k not in g.attrs:return d
    v=g.attrs[k]
    if isinstance(v,bytes):return v.decode("utf-8","ignore")
    if isinstance(v,np.ndarray) and v.size==1:return v.reshape(-1)[0].item()
    return v

def read_odim(blob,quantity="DBZH"):
    scans=[]; cart=[]
    with h5py.File(io.BytesIO(blob),'r') as f:
        rootwhat=f.get('what'); rootwhere=f.get('where')
        root_source=_val(rootwhat,'source','')
        for name in sorted(k for k in f.keys() if k.startswith('dataset')):
            g=f[name]; w=g.get('where'); what=g.get('what')
            if 'data1' not in g: continue
            dg=g['data1']; q=str(_val(dg.get('what'),'quantity',''))
            if quantity and q and q.upper()!=quantity.upper(): continue
            arr=dg['data'][()].astype('float32')
            gain=float(_val(dg.get('what'),'gain',1.0)); off=float(_val(dg.get('what'),'offset',0.0))
            arr=arr*gain+off
            nodata=_val(dg.get('what'),'nodata'); undetect=_val(dg.get('what'),'undetect')
            if nodata is not None: arr[raw:=dg['data'][()]==nodata]=np.nan
            if undetect is not None: arr[dg['data'][()]==undetect]=np.nan
            obj=str(_val(what,'object',''))
            if obj in ('COMP','IMAGE','') and w is not None and 'xscale' in w.attrs:
                cart.append({'name':name,'data':arr,'where':{k:_val(w,k) for k in w.attrs.keys()},'what':{k:_val(what,k) for k in what.attrs.keys()} if what else {}})
            elif w is not None:
                scans.append({'name':name,'dbzh':arr,'elangle_deg':float(_val(w,'elangle',0.5)),'nrays':int(_val(w,'nrays',arr.shape[0])),'nbins':int(_val(w,'nbins',arr.shape[1])),'rstart_m':float(_val(w,'rstart',0.0)),'rscale_m':float(_val(w,'rscale',1000.0)),'lon':float(_val(w,'lon',_val(rootwhere,'lon',0.0))),'lat':float(_val(w,'lat',_val(rootwhere,'lat',0.0))),'height_m':float(_val(w,'height',_val(rootwhere,'height',0.0))),'what':{k:_val(what,k) for k in what.attrs.keys()} if what else {},'source':root_source})
        return {'scans':scans,'cartesian':cart,'root':{'source':root_source}}

def latest_cartesian(blob,quantity='DBZH'):
    r=read_odim(blob,quantity)
    if not r['cartesian']: raise ValueError('No Cartesian/composite ODIM dataset found')
    return r['cartesian'][0]

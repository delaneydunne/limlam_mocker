import numpy as np

def _ra_dec_nu_to_hitmap(ra,dec,nu,mapinst,weights=None):
    hitmaps, hitedges = np.histogramdd( np.c_[ra, dec, nu],
        bins = (mapinst.pix_binedges_x, mapinst.pix_binedges_y, 
                    mapinst.nu_binedges[::-1]), weights=weights )
    return hitmaps[:,:,::-1]

def _def_kspace_params(mapinst,redshift_to_chi,dk_scale=1,logscale=False):
    x,y,z = mapinst.pix_binedges_x, mapinst.pix_binedges_y, mapinst.nu_binedges
    zco = redshift_to_chi(mapinst.nu_rest/z-1).value
    # assume comoving transverse distance = comoving distance
    #     (i.e. no curvature)
    avg_ctd = np.mean(zco)
    xco = x/(180)*np.pi*avg_ctd
    yco = y/(180)*np.pi*avg_ctd
    dxco, dyco, dzco = [np.abs(np.mean(np.diff(d))) for d in (xco, yco, zco)]
    mapinst.voxcovol = dxco*dyco*dzco
    mapinst.totalcovol = np.ptp(xco)*np.ptp(yco)*np.ptp(zco)
    kx = 2*np.pi*np.fft.fftfreq(xco.size-1,d=dxco)
    ky = 2*np.pi*np.fft.fftfreq(yco.size-1,d=dyco)
    kz = 2*np.pi*np.fft.rfftfreq(zco.size-1,d=dzco)
    mapinst.kvec = np.meshgrid(kx,ky,kz,indexing='ij')
    kgrid = np.sqrt(sum(ki**2 for ki in mapinst.kvec))
    dk = max(np.diff(kx)[0],np.diff(ky)[0],np.diff(kz)[0])*dk_scale
    kmax_dk = int(np.ceil(max(np.amax(kx),np.amax(ky),np.amax(kz))/dk))
    # bin EDGES
    if not logscale:
        kbins = np.linspace(0,kmax_dk*dk,kmax_dk+1)
    else:
        kbins = np.logspace(-1.39, np.log10(kmax_dk*dk),kmax_dk+1)
    Nmodes = np.histogram(kgrid[kgrid>0],bins=kbins)[0]
    
    # bin CENTERS
    k = (kbins[1:]+kbins[:-1])/2
    fftsq_to_Pk=(dxco*dyco*dzco)**2/np.abs(np.ptp(xco)*np.ptp(yco)*np.ptp(zco))
    mapinst.k = k
    mapinst.kbins = kbins
    mapinst.kgrid = kgrid
    mapinst.Nmodes = Nmodes
    mapinst.fftsq_to_Pk = fftsq_to_Pk
    
def halos_to_hitmap(halos,mapinst,weights=None):
    return _ra_dec_nu_to_hitmap(halos.ra, halos.dec, halos.nucat, mapinst,
                                    weights=weights)

def co_cat_xspec(mapinst):
    tco = mapinst.map
    tcat = mapinst.catmap
    Pk_3D = mapinst.fftsq_to_Pk*np.real(
                np.fft.rfftn(tco)*np.conj(np.fft.rfftn(tcat)))
    k = mapinst.k
    kgrid = mapinst.kgrid
    kbins = mapinst.kbins
    Pk_nmodes = np.histogram(kgrid[kgrid>0],bins=kbins,weights=Pk_3D[kgrid>0])[0]
    if hasattr(mapinst,'Nmodes'):
        nmodes = mapinst.Nmodes
    else:
        nmodes = np.histogram(kgrid[kgrid>0],bins=kbins)[0]
    Pk = Pk_nmodes/nmodes
    #***
    # Pkvolcorr = Pk / mapinst.totalcovol
    
    return k,Pk,nmodes

def map_to_xspec(mapinst,Pkvec=False):
    t = mapinst.map
    hit = mapinst.hit
    Pk_3D = mapinst.fftsq_to_Pk*np.real(
                np.fft.rfftn(t)*np.conj(np.fft.rfftn(hit)))
    k = mapinst.k
    kgrid = mapinst.kgrid
    kbins = mapinst.kbins
    Pk_nmodes = np.histogram(kgrid[kgrid>0],bins=kbins,weights=Pk_3D[kgrid>0])[0]
    if hasattr(mapinst,'Nmodes'):
        nmodes = mapinst.Nmodes
    else:
        nmodes = np.histogram(kgrid[kgrid>0],bins=kbins)[0]
    Pk = Pk_nmodes/nmodes
    if Pkvec:
        return k,Pk,nmodes,Pk_3D
    else:
        return k,Pk,nmodes

def map_to_linespec(mapinst,Pkvec=False,attribute='map'):
    t = getattr(mapinst, attribute)
    Pk_3D = mapinst.fftsq_to_Pk*np.abs(np.fft.rfftn(t))**2
    k = mapinst.k
    kgrid = mapinst.kgrid
    kbins = mapinst.kbins
    Pk_nmodes = np.histogram(kgrid[kgrid>0],bins=kbins,weights=Pk_3D[kgrid>0])[0]
    if hasattr(mapinst,'Nmodes'):
        nmodes = mapinst.Nmodes
    else:
        nmodes = np.histogram(kgrid[kgrid>0],bins=kbins)[0]
    Pk = Pk_nmodes/nmodes
    
    if Pkvec:
        return k,Pk,nmodes,Pk_3D
    else:
        return k,Pk,nmodes

def map_to_galspec(mapinst,Pkvec=False,attribute='hit'):
    hit = getattr(mapinst, attribute)
    Pk_3D = mapinst.fftsq_to_Pk*np.abs(np.fft.rfftn(hit))**2
    k = mapinst.k
    kgrid = mapinst.kgrid
    kbins = mapinst.kbins
    Pk_nmodes = np.histogram(kgrid[kgrid>0],bins=kbins,weights=Pk_3D[kgrid>0])[0]
    if hasattr(mapinst,'Nmodes'):
        nmodes = mapinst.Nmodes
    else:
        nmodes = np.histogram(kgrid[kgrid>0],bins=kbins)[0]
    Pk = Pk_nmodes/nmodes
    if Pkvec:
        return k,Pk,nmodes,Pk_3D
    else:
        return k,Pk,nmodes

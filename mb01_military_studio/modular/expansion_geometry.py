# SPDX-License-Identifier: MIT
"""Six additive visual hangar panels. Pure geometry; no protection/structural rating.
All source geometry is X across / Y inward / Z up. Caller performs canonicalization.
The original AS07 primitives are reused; no hidden wall is placed behind an opening.
"""
from math import radians, ceil
from ..vendor import as07_reference as A

BUILDERS = frozenset({'hg_cassette', 'hg_vision', 'hg_shaded', 'hg_dual_vent',
                       'hg_double_service', 'hg_canopy_service'})


def _cassette(m):
    w,h,t=m.cfg.width,m.cfg.height,m.cfg.thickness
    m.wall(metal=True)
    # Cassette bands follow the common bay width and finish inside the cell bounds.
    for i in range(1,4):
        z=.50+(h-.65)*i/4
        m.box('CassetteReveals',(0.,-.038,z),(w-.06,.020,.024),'Joint','DETAIL',.001)
        m.box('CassetteFold',(0.,-.052,z+.025),(w-.06,.027,.025),'RoofOliveLight','DETAIL',.001)
    for s in (-1,1):
        m.box('CassetteJambs',(s*(w/2-.045),-.041,h/2),(.050,.035,h-.04),
              m.cfg.style.frame_material,'FACADE',.002)
    m.notes.append('Cassette folds are decorative; no panel-system engineering rating.')


def _vision(m):
    w,h=m.cfg.width,m.cfg.height
    ow=w-.62;bottom=1.02;oh=min(2.12,h-1.62)
    m.wall((ow,bottom,oh),metal=True)
    m.frame(ow,bottom,oh,transom=True,mullion=True)
    # A top flashing + shallow shadow seam, both below the main hangar clerestory level.
    m.box('VisionHeadFlashing',(0.,-.045,bottom+oh+.080),(ow+.20,.23,.040),
          m.cfg.style.frame_material,'FACADE',.002)
    m.box('VisionHeadShadow',(0.,-.038,bottom+oh+.034),(ow+.12,.018,.012),
          'Joint','DETAIL',.001)


def _shaded(m):
    w,h=m.cfg.width,m.cfg.height
    m.window(clerestory=True)
    ow=w-.48;head=h-.45;shade_z=head+.14
    # Horizontal fins project OUTWARD (-Y), never through the glazing aperture.
    for k in range(4):
        m.box('ShadeFins',(0.,-.15-.16*k,shade_z),(ow+.22,.10,.045),
              'RoofOlive','DETAIL',.002)
    for x in (-ow*.36,ow*.36):
        m.box('ShadeArms',(x,-.345,shade_z-.054),(.042,.77,.063),
              m.cfg.style.frame_material,'DETAIL',.002)
        m.box('ShadeWallPlate',(x,-.025,shade_z-.13),(.12,.04,.26),
              m.cfg.style.frame_material,'DETAIL',.002)
    m.notes.append('Brise-soleil is scenery geometry; daylight/thermal performance is not computed.')


def _wall_holes(m, holes):
    """Build a tiled solid wall minus nonoverlapping rectangular apertures.
    holes: x0,z0,x1,z1. No full backing box and no overlapping coplanar tiles.
    """
    w,h,t=m.cfg.width,m.cfg.height,m.cfg.thickness
    for i,(x0,z0,x1,z1) in enumerate(holes):
        if not (-w/2+.12<=x0<x1<=w/2-.12 and .50<=z0<z1<=h-.14):
            raise ValueError('Dual-vent aperture does not fit the module.')
        for other in holes[:i]:
            if min(x1,other[2])>max(x0,other[0]) and min(z1,other[3])>max(z0,other[1]):
                raise ValueError('Overlapping wall apertures.')
        m.openings.append(dict(width=x1-x0,bottom=z0,height=z1-z0,
          center_output=(t/2,-(x0+x1)/2,(z0+z1)/2)))
    xs=sorted({-w/2,w/2}|{v for q in holes for v in (q[0],q[2])})
    zs=sorted({0.,h}|{v for q in holes for v in (q[1],q[3])})
    for a,b in zip(xs,xs[1:]):
        for lo,hi in zip(zs,zs[1:]):
            x,z=(a+b)/2,(lo+hi)/2
            if any(q[0]<x<q[2] and q[1]<z<q[3] for q in holes):continue
            m.box('Wall',(x,t/2,z),(b-a,t,hi-lo),'RoofOlive','BODY',.004)
    m.box('Plinth',(0.,-.023,.24),(w,.046,.48),m.cfg.style.plinth_material,'FACADE',.004)
    m.box('HeadReveal',(0.,-.009,h-.105),(w,.018,.014),'Joint','DETAIL',.001)
    # Metal seams stop at every opening rather than running across them.
    for k in range(1,max(3,int(w/.58))):
        x=-w/2+w*k/max(3,int(w/.58));intervals=[(.52,h-.14)]
        for x0,z0,x1,z1 in holes:
            if x0-.025<x<x1+.025:
                new=[]
                for lo,hi in intervals:
                    if z0-.025>lo:new.append((lo,min(hi,z0-.025)))
                    if z1+.025<hi:new.append((max(lo,z1+.025),hi))
                intervals=new
        for lo,hi in intervals:
            if hi-lo>.06:m.box('PanelSeams',(x,-.018,(lo+hi)/2),(.024,.036,hi-lo),
                               'RoofOliveLight','DETAIL',.0015)


def _dual_vent(m):
    w,h,t=m.cfg.width,m.cfg.height,m.cfg.thickness
    outer=.34;middle=.24;vw=(w-2*outer-middle)/2
    bottom=h*.47;vh=min(1.70,h-bottom-.48)
    centres=(-middle/2-vw/2,middle/2+vw/2)
    holes=[(x-vw/2,bottom,x+vw/2,bottom+vh) for x in centres]
    _wall_holes(m,holes)
    for index,x in enumerate(centres):
        f=.070;mat=m.cfg.style.frame_material
        for xx in (x-vw/2+f/2,x+vw/2-f/2):
            m.box('VentFrame',(xx,.085,bottom+vh/2),(f,.18,vh),mat,'FACADE',.003)
        for zz in (bottom+f/2,bottom+vh-f/2):
            m.box('VentFrame',(x,.085,zz),(vw-2*f,.18,f),mat,'FACADE',.003)
        n=max(4,int((vh-.17)/.13))
        for k in range(n):
            zz=bottom+.13+(vh-.26)*k/max(1,n-1)
            m.box('VentBlades',(x,.085,zz),(vw-.18,.20,.025),'RoofOliveLight',
                  'DETAIL',.0015,axes=A.euler_axes(radians(27),0,0))
        m.box('VentScreen',(x,t+.017,bottom+vh/2),(vw-.15,.016,vh-.14),
              'Interior','DETAIL',0.)
        m.box('VentHood',(x,-.030,bottom+vh+.050),(vw+.12,.30,.050),mat,'FACADE',.003)
    m.notes.append('Dark vent screens are intentional. No airflow or protection rating.')


def _canopy(m, double=False):
    m.entry(double=double,canopy=True,metal=True)
    # Base entry supplies pivot-correct leaf, real wall opening and supported canopy.
    ow=min(2.3,m.cfg.width-.7) if double else min(1.18,m.cfg.width-.7)
    top=2.62 if double else 2.30
    m.box('EntryShadowReveal',(0.,-.045,top+.104),(ow+.20,.020,.018),'Joint','DETAIL',.001)
    for sign in (-1,1):
        m.box('EntryJambFold',(sign*(ow/2+.085),-.024,top/2),(.04,.05,top),
              m.cfg.style.frame_material,'FACADE',.002)


def generate(m, builder):
    if builder=='hg_cassette':_cassette(m)
    elif builder=='hg_vision':_vision(m)
    elif builder=='hg_shaded':_shaded(m)
    elif builder=='hg_dual_vent':_dual_vent(m)
    elif builder=='hg_double_service':_canopy(m,double=True)
    elif builder=='hg_canopy_service':_canopy(m,double=False)
    else:raise ValueError('Unknown expansion builder: '+str(builder))
    return m

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
    # Accent bay of flat folded cassette trays on the same core, plinth and flashings.
    m.clad((),sheet=False);m.cassettes()
    m.notes.append('Cassette trays are scenery geometry; no panel-system engineering rating.')


def _vision(m):
    w,h=m.cfg.width,m.cfg.height
    ow=w-.62;bottom=1.02;oh=min(2.12,h-1.62)
    # Low vision band: aluminium glazing with pressure caps; head/sill/jamb flashings come
    # from the shared opening trims instead of a flat plank.
    m.wall((ow,bottom,oh),metal=True)
    m.frame(ow,bottom,oh,transom=True,mullion=True,hangar=True)


def _shaded(m):
    w,h=m.cfg.width,m.cfg.height
    m.window(clerestory=True)
    ow=w-.48;top=h-.45;shade_z=top+.14
    # Horizontal fins project OUTWARD (-Y), never through the glazing aperture. The wall
    # plates sit above the head flashing ledge, clear of the glass; fins top out at h-.2875.
    for k in range(4):
        m.box('ShadeFins',(0.,-.15-.16*k,shade_z),(ow+.22,.10,.045),
              'RoofOlive','DETAIL',.002)
    for x in (-ow*.36,ow*.36):
        m.box('ShadeArms',(x,-.382,shade_z-.054),(.042,.696,.063),
              m.cfg.style.frame_material,'DETAIL',.002)
        m.box('ShadeWallPlate',(x,-.02225,top+.108),(.12,.0435,.184),
              m.cfg.style.frame_material,'DETAIL',.002)
    m.notes.append('Brise-soleil is scenery geometry; daylight/thermal performance is not computed.')


def _wall_holes(m, holes):
    """Profiled steel wall minus nonoverlapping rectangular apertures (x0,z0,x1,z1).
    The core is tiled per aperture column; no full backing box behind any opening.
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
    m.clad(holes)


def _dual_vent(m):
    w,h=m.cfg.width,m.cfg.height
    outer=.34;middle=.24;vw=(w-2*outer-middle)/2
    bottom=h*.47;vh=min(1.70,h-bottom-.48)
    holes=[(x-vw/2,bottom,x+vw/2,bottom+vh) for x in (-middle/2-vw/2,middle/2+vw/2)]
    _wall_holes(m,holes)
    # Twin weather louvres, each with its own head flashing and sloped sill.
    for x0,z0,x1,z1 in holes:m.louvre(x0,z0,x1,z1)
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

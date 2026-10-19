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
    # Clerestory 150 mm lower than the plain band, so the fins (top h-.4375) stand clear of
    # the gutter and roof fascia instead of merging with them into one mass.
    m.window(clerestory=True,drop=.15)
    ow=w-.48;top=h-.60;shade_z=top+.14
    # Horizontal fins project OUTWARD (-Y), never through the glazing aperture. The wall
    # plates bear on the head flashing face leg (4 mm packer implied above it), clear of the glass.
    for k in range(4):
        m.box('ShadeFins',(0.,-.15-.16*k,shade_z),(ow+.22,.10,.045),
              'RoofOlive','DETAIL',.002)
    for x in (-ow*.36,ow*.36):
        m.box('ShadeArms',(x,-.382,shade_z-.054),(.042,.696,.063),
              m.cfg.style.frame_material,'DETAIL',.002)
        m.box('ShadeWallPlate',(x,-.02525,top+.108),(.12,.0425,.184),
              m.cfg.style.frame_material,'DETAIL',.002)
    m.notes.append('Brise-soleil is scenery geometry; daylight/thermal performance is not computed.')


def _wall_holes(m, holes, skin=None):
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
    m.clad(holes,skin=skin)


def _dual_vent(m):
    w,h=m.cfg.width,m.cfg.height
    outer=.34;middle=.24;vw=(w-2*outer-middle)/2
    bottom=h*.47;vh=min(1.70,h-bottom-.48)
    holes=[(x-vw/2,bottom,x+vw/2,bottom+vh) for x in (-middle/2-vw/2,middle/2+vw/2)]
    # Twin weather louvres trimmed as one ganged opening: one head flashing, one sill with stop
    # ends, outer jamb angles and a cover plate over the 240 mm pier (no sheet or screw under it).
    span=(holes[0][0],bottom,holes[1][2],bottom+vh)
    _wall_holes(m,holes,[span])
    for x0,z0,x1,z1 in holes:m.louvre(x0,z0,x1,z1,trims=False)
    m.opening_trims(*span,.0245,.0995,piers=[(holes[0][2],holes[1][0])])
    m.notes.append('Dark vent screens are intentional. No airflow or protection rating.')


def _canopy(m, double=False):
    # Door set (frame, leaves, opening trims) comes from entry(); a single entry gets a vision leaf.
    m.entry(double=double,glazed=not double,metal=True)
    w=m.cfg.width;draft=m.cfg.detail=='DRAFT'
    ow=min(2.3,w-.7) if double else min(1.18,w-.7)
    dh=2.62 if double else 2.30
    # Cantilevered steel entrance canopy sized to the door (not the bay): wall channel, two tapered
    # arms, fascia, deck tray (front edge trim = drip below + kerb above, side upstands, abutment
    # flashing, scupper spout beside the door), two ~35 deg tie rods with clevises, lugs and a
    # turnbuckle, galvanized soffit and a housed downlight (no separate wall light here). The
    # channel sits 120 mm over the head flashing's face leg; arms, lugs and tie-rod wall plates
    # stand on the cladding crest nearest ow/2+.47, so the plates bear on a rib; nothing reaches
    # past |x| = w/2-.15 (a bay too narrow for a crest past the jamb trims keeps the edge line).
    pc=m.clad_pitch(w);k=round((ow/2+.47+w/2)/pc-.5)
    while k>0 and -w/2+(k+.5)*pc>w/2-.18:k-=1
    xr=-w/2+(k+.5)*pc
    if xr<ow/2+.12:xr=w/2-.18
    xe=xr+.03;P=1.25 if double else 1.10;zu=dh+.22
    YZX=((0,1,0),(0,0,1),(1,0,0));S='SteelDark'
    c=m.part('EntryCanopy','FACADE',.003)
    c.box((0.,-.0265,zu+.07),(2*xe,.057,.14),S)                                   # wall channel
    arm=[(-.055,zu),(-(P-.085),zu+.05),(-(P-.085),zu+.14),(-.055,zu+.14)]
    for x0 in (-xe,xe-.06):
        c.prism(arm,(x0,0.,0.),YZX,.06,S)                                          # tapered arms
    c.box((0.,-(P-.055),zu+.095),(2*xe,.060,.090),S)                               # fascia
    c.box((0.,-(P-.010)/2,zu+.1525),(2*xe,P-.006,.025),S)                          # deck
    c.box((0.,-P+.004,zu+.155),(2*xe,.008,.080),S)              # edge trim: 17 mm drip groove + kerb
    for s in (-1,1):
        c.box((s*(xe-.004),-(P+.037)/2,zu+.180),(.008,P-.053,.030),S)              # side upstands
    c.box((xe-.12,-P-.030,zu+.1775),(.040,.100,.025),S)                            # scupper spout
    c.prism([(.002,zu+.165),(-.045,zu+.165),(-.045,zu+.195),(.002,zu+.255)],(-xe,0.,0.),YZX,2*xe,S)
    zr=zu+.200+(P-.185)*.70
    rods=m.part('CanopyTieRods','DETAIL',0.)
    for s in (-1,1):
        x=s*xr
        c.box((x,-(P-.10),zu+.19475),(.012,.080,.0605),S)                          # deck lug
        c.box((x,-.024,zr),(.10,.052,.16),S)                                       # wall plate + packer
        c.box((x,-.07725,zr),(.012,.0555,.070),S)                                  # wall lug
        a=(x,-(P-.10),zu+.200);b=(x,-.085,zr);u=A.unit(A.sub(b,a))
        rods.beam(a,A.add(a,A.mul(u,.045)),.028,.028,'Galvanized')                 # clevises
        rods.beam(A.sub(b,A.mul(u,.045)),b,.028,.028,'Galvanized')
        rods.cylinder(A.add(a,A.mul(u,.040)),A.sub(b,A.mul(u,.040)),.010,'Galvanized',6 if draft else 10)
        mid=A.mul(A.add(a,b),.5)
        rods.cylinder(A.sub(mid,A.mul(u,.065)),A.add(mid,A.mul(u,.065)),.016,'Galvanized',6 if draft else 8)  # turnbuckle
    m.box('CanopySoffit',(0.,-(P-.03)/2,zu+.1325),(2*(xe-.06),P-.140,.015),'Galvanized','DETAIL',.001)
    lx=min(.35,xe-.20)
    m.box('CanopyLight',(0.,-P*.45,zu+.120),(2*lx,.140,.011),S,'DETAIL',.001)         # housing
    m.box('CanopyLight',(0.,-P*.45,zu+.1125),(2*lx-.03,.100,.005),'LightWarm','DETAIL',.001)


def generate(m, builder):
    if builder=='hg_cassette':_cassette(m)
    elif builder=='hg_vision':_vision(m)
    elif builder=='hg_shaded':_shaded(m)
    elif builder=='hg_dual_vent':_dual_vent(m)
    elif builder=='hg_double_service':_canopy(m,double=True)
    elif builder=='hg_canopy_service':_canopy(m,double=False)
    else:raise ValueError('Unknown expansion builder: '+str(builder))
    return m

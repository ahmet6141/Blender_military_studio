# SPDX-License-Identifier: MIT
"""Parametric closed hangar with reusable facade modules and explicit component roles.
Not structural engineering. Real apertures, recessed drain, roof openings and door
motion are geometry contracts; life-safety/performance certification is not implied.
"""
from math import ceil, sqrt, pi, radians, hypot
from dataclasses import asdict
from copy import deepcopy
from .. import core
from ..modular.contracts import ModuleInput, Style
from ..modular import geometry as MG
from .contracts import HangarConfig, PANEL_MODULES, ENTRY_TYPES, stable_variant, gate_motion, gate_clear_width
from . import VERSION
from ..assembly.contracts import envelope
import re
A = core.A


def rectangle_difference(rect, cut):
    """Nonoverlapping pieces of rect minus an axis-aligned cut, XY, not a Boolean op."""
    x0,y0,x1,y1 = rect
    a,b,c,d = max(x0,cut[0]),max(y0,cut[1]),min(x1,cut[2]),min(y1,cut[3])
    if a >= c or b >= d:
        return [rect]
    pieces = [(x0,y0,a,y1),(c,y0,x1,y1),(a,y0,c,b),(a,d,c,y1)]
    return [p for p in pieces if p[2]-p[0] > 1e-8 and p[3]-p[1] > 1e-8]


def roof_level(c, x):
    return envelope(c).roof(x)


def _roof_uv(p, slope):
    # A continuous source-space chart: U along the building, V true sloping length.
    # End-cap UVs use the source's planar mapping; skin faces get the roof chart.
    scale=sqrt(1.+slope*slope)
    for index, face in enumerate(p.faces):
        v=[p.vertices[j] for j in face]
        normal=A.cross(A.sub(v[1],v[0]),A.sub(v[2],v[0]))
        # Only sloped skin faces: vertical edges need their original nondegenerate charts.
        if abs(normal[2]) > 1e-10 and max(q[1] for q in v)-min(q[1] for q in v) > 1e-7:
            p.uvs[index]=[(q[1],q[0]*scale) for q in v]


def _ibeam(p, a, b, mat='SteelDark', width=.24, height=.46):
    direction=A.unit(A.sub(b,a));u=(0.,1.,0.);v=A.unit(A.cross(direction,u))
    p.prism(A.i_profile(width,height,.026,.035),a,(u,v,direction),sqrt(A.dot(A.sub(b,a),A.sub(b,a))),mat)


def _copy_module(m, config, token, width, face_id, translate, axes):
    """Module output is canonical; rotate/translate it into design coordinates once."""
    settings=ModuleInput(PANEL_MODULES[token],'HANGAR',width,config.eave_height,
        config.wall_thickness,config.detail,config.personnel_open,
        Style(config.palette,'ConcreteLight','SteelDark','Concrete',0.))
    src=MG.build(settings)
    report=MG.validation(src)
    if report['errors']:
        raise ValueError(face_id+': '+'; '.join(report['errors']))
    def vector(p):
        return tuple(sum(p[j]*axes[j][i] for j in range(3)) for i in range(3))
    def tr(p):
        return A.add(vector(p),translate)
    C=MG.ModuleModel;env=envelope(config);X,by=env.outside_x,env.back_y;rear=face_id.startswith('REAR')
    def side(v):return 1. if v[0]>0 else -1.
    # The wall coatings are separate from the roof coating: profiled sheet, pressed trims,
    # cassette tone and the liner. Louvre blades keep the frame's powder coat (one product).
    remap={'Cladding':'HG_Wall','CassetteTrays':'HG_WallCassette','EaveTrim':'HG_WallTrim',
           'BaseFlashing':'HG_WallTrim','HeadFlashing':'HG_WallTrim','JambTrims':'HG_WallTrim',
           'SillFlashing':'HG_WallTrim','CladFixings':'HG_WallTrim','ShadeFins':'HG_Alu'}
    mapping={}
    # Rear cells: one continuous HG_RearCladding sheet (and its fixings) runs from the plinth to
    # the verges over the whole rear (_facades cuts each cell's skin_holes), so there is no eave
    # seam, bay joint or UV break. Fixings follow config.fasteners.
    tiled={'Cladding','CassetteTrays','EaveTrim','BaseFlashing','HeadFlashing','JambTrims','SillFlashing','Wall','Plinth'}
    for source in src.parts:
        role=source.name.split('__')[-1]
        if (rear and role in ('EaveTrim','Cladding','CladFixings')) or (role=='CladFixings' and not config.fasteners):
            continue
        part=deepcopy(source)
        part.name='SM_MB01_HG_'+face_id+'__'+role
        mapping[source.name]=part.name
        part.vertices=[tr(v) for v in source.vertices];part.pivot=tr(source.pivot)
        if role in tiled:
            # UV0 in design metres, like the hangar-built sheets: the coated-steel tile runs on
            # across bay lines instead of restarting (and mirroring) in every cell.
            C.plan_uvs(part)
        if role=='Wall':
            # Core: exterior coat on its outward face (what an open crest void shows), light
            # liner inside. Building-end rear cores stop behind the side cladding return.
            C.tone_faces(part,[vector((-1.,0.,0.))],'HG_Wall','HG_WallLiner')
            if rear:
                C.shift(part,lambda v:abs(v[0])>X-C.CLAD_CORE+1e-9,lambda v:(side(v)*(X-C.CLAD_CORE),v[1],v[2]))
        elif role in remap:
            part.material_names=[remap[role] if n in ('RoofOlive','RoofOliveLight') else n for n in part.material_names]
        if rear and role=='BaseFlashing':
            # Building-end drip mitres on the plan diagonal into the side return (x-y = X-by).
            C.shift(part,lambda v:abs(v[0])>X-1e-6,lambda v:(side(v)*(X+v[1]-by),v[1],v[2]))
        m.parts.append(part)
    for d in src.doors:
        d=deepcopy(d);d['part']=mapping[d['part']];d['closed']=tr(d['closed']);d['opened']=tr(d['opened'])
        d['open_fraction']=config.personnel_open;d['channel']='PERSONNEL'
        m.doors.append(d)
    m.hangar_meta['facade_cells'].append(dict(id=face_id,kind=token,module_id=settings.module_id,
        width_m=width,height_m=config.eave_height,wall_thickness_m=config.wall_thickness,
        transform_design=dict(origin=translate,axes=axes)))
    if token in ENTRY_TYPES:
        center=tr((0.,0.,0.));out=vector((-1.,0.,0.))
        m.hangar_meta['personnel_openings_design'].append(dict(id=face_id,center=center,normal=out,clear_width_m=src.ports[0].get('clear_width_m',1.03),leaf_count=len(src.doors)))
    return src


def _frame_y(c,i):
    """Frame line of portal i. The two end frames sit inside the girt zone so the column's
    outer flange (.20 from the frame line) stays 5 mm behind the cladding core face; every
    part that bears on a frame (cleats, splices) uses this, not i*bay_pitch."""
    from ..modular.geometry import ModuleModel
    bp=c.depth/c.bays;e=max(0.,.205-(c.wall_thickness-ModuleModel.CLAD_CORE))
    return i*bp+(e if i==0 else (-e if i==c.bays else 0.))


def _structure(m,c):
    a,d,z=c.width/2,c.depth,c.base_height
    bp=d/c.bays
    from ..modular.geometry import ModuleModel
    lim=c.wall_thickness-ModuleModel.CLAD_CORE-.005    # wall-side stop for end-frame plates
    for i in range(c.bays+1):
        y=_frame_y(c,i);end=-1 if i==0 else (1 if i==c.bays else 0)

        def span(half):   # plates stop 3 mm inside the flange's outer face (no shared plane)
            lo,hi=y-half,y+half
            if end<0:lo=max(lo,-lim+.003)
            if end>0:hi=min(hi,d+lim-.003)
            return (lo+hi)/2,hi-lo
        frame=m.p(f'HG_Portal_{i:02d}','STRUCTURE',.004)
        for side in (-1,1):
            x=side*(a-.22)
            frame.prism(A.i_profile(.34,.40,.035,.040),(x,y,z+.105),A.IDENTITY,c.eave_height-.54-.105,'SteelDark')
            _ibeam(frame,(x,y,roof_level(c,x)-.52),(0,y,roof_level(c,0)-.52))
            yc,dy=span(.34)
            m.box('HG_BaseShoes',(x,yc,z+.055),(.62,dy,.11),'SteelDark','STRUCTURE',.004)
            # Thickening plate is a visible mechanical joint, not a load calculation.
            yc,dy=span(.23)
            m.box('HG_EaveConnection',(x,yc,roof_level(c,x)-.64),(.48,dy,.26),'Galvanized','DETAIL',.004)
            if c.fasteners and c.detail!='DRAFT':
                p=m.p('HG_Fasteners','DETAIL',.001)
                for dx in (-.23,.23):
                    for dy in (-.25,.25):
                        yy=y+dy
                        if end<0:yy=max(yy,-lim+.05)
                        if end>0:yy=min(yy,d+lim-.05)
                        p.cylinder((x+dx,yy,z+.111),(x+dx,yy,z+.155),.028,'Galvanized',6)
                        p.cylinder((x+dx,yy,z+.108),(x+dx,yy,z+.121),.044,'Galvanized',12)
        m.box('HG_RidgeSplice',(0,y,roof_level(c,0)-.52),(.70,.045,.32),'Galvanized','DETAIL',.003)
    # Purlins remain under the roof. No main purlins across the monitor opening.
    xs=[-a+(j+.5)*(2*a/12) for j in range(12)]
    mh=c.monitor_width/2
    for j,x in enumerate(xs):
        if c.roof_type=='MONITOR' and abs(x)<mh+.10:
            continue
        p=m.p(f'HG_Purlin_{j:02d}','STRUCTURE',.002)
        p.box((x,d/2,roof_level(c,x)-.16),(.10,d+.22,.13),'Galvanized')
        m.hangar_meta['roof_supports_design'].append(dict(x=x,top=roof_level(c,x)-.095,skin_lower=roof_level(c,x)))
    for side,sequence in ((-1,c.panel_sequence('LEFT')),(1,c.panel_sequence('RIGHT'))):
        for i,token in enumerate(sequence):
            if token!='METAL':continue
            y0=i*bp+.30;y1=(i+1)*bp-.30;x=side*(a-.34)
            p=m.p('HG_SelectiveBraces','STRUCTURE',.002)
            # The two diagonals of the X sit in separate planes (one bolted in front of the
            # other, as real flat-bar bracing is) instead of intersecting with coplanar faces.
            p.beam((x,y0,z+.65),(x,y1,z+c.eave_height-.80),.045,.055,'Galvanized')
            p.beam((x-side*.05,y1,z+.65),(x-side*.05,y0,z+c.eave_height-.80),.045,.055,'Galvanized')


# ------------------------------------------------------------------ roof system helpers
# Section datums (design coords): roof_level(x) is the underside of the 85 mm build-up
# (HG_RoofSkin prism); the pan surface is roof_level+ROOF_SKIN. Pressed flashings are
# modelled 6 mm thick (0.7 mm sheet exaggerated so it reads without a bevel); every lap
# is offset >=2 mm (sloped or long faces) or bedded into the part below, never coplanar.
ROOF_SKIN=.085
SEAM=((-.016,-.005),(.016,-.005),(.009,.058),(-.009,.058))   # tapered double-lock rib, 5 mm bedded
OVER=.072            # flashing underside above the pan: clears the seam head (.058*sqrt(1+s*s))
VERGE=((-.150,-.005),(-.150,.070),(.010,.070),(.010,-.180),(.030,-.200),(.026,-.204),
       (.004,-.182),(.004,.064),(-.144,.064),(-.144,-.005))   # u out from sheet edge, v up from pan
# Notch return (monitor roofs): same section, cover 4 mm higher so it laps over the verge.
VERGE_RETURN=tuple((u,v+.004 if v>.06 else (-.002 if v==-.005 else v)) for u,v in VERGE)
# Stop end that closes the verge channel at the eave (fills the U, recessed 2 mm).
VERGE_STOP=((-.144,-.005),(.004,-.005),(.004,.064),(-.144,.064))
GUTTER=((0.,0.),(0.,-.150),(.176,-.150),(.206,-.016),(.218,-.016),(.218,-.008),
        (.198,-.008),(.1715,-.146),(.004,-.146),(.004,0.))   # u out from back leg, v from back top
GUTTER_END=((-.002,.002),(-.002,-.152),(.1775,-.152),(.2075,-.0175),(.2200,-.0175),(.2200,-.0065))
FLASH='HG_RoofFlashing'
XZ=((1,0,0),(0,0,1),(0,1,0))   # prism axes: profile in the XZ plane, extruded along +Y


def _run(p,y,a,b,profile,mat,crimp=0.):
    """Prism along the sloped XZ segment a->b at depth y; profile u=+Y, v=upward normal.
    crimp: the head (v>.03) of the b end is set back along the run, the ~55 degree folded
    dog-ear end of a real seam at the eave. Every face stays planar, no extra triangles."""
    dx,dz=b[0]-a[0],b[1]-a[1];L=hypot(dx,dz);t=(dx/L,0.,dz/L)
    n=(-t[2],0.,t[0]) if t[0]>0 else (t[2],0.,-t[0])
    def place(k,u,v):
        s=k*L-(crimp if k and v>.03 else 0.)
        return (a[0]+n[0]*v+t[0]*s,y+u,a[1]+n[2]*v+t[2]*s)
    _sweep(p,profile,place,(0,1),mat)


def _sweep(p,profile,place,stations,mat):
    """Closed extrusion of a 2D profile through several stations: exact mitres at the ridge,
    no internal caps. place(station,u,v)->xyz. Same face layout as MeshPart.prism."""
    pr=list(profile)
    if A.polygon_area(pr)<0:pr.reverse()
    n=len(pr);K=len(stations);tri=A.triangulate_polygon(pr)
    verts=[place(st,u,v) for st in stations for u,v in pr]
    faces=[tuple(reversed(t)) for t in tri]+[tuple(j+n*(K-1) for j in t) for t in tri]
    for k in range(K-1):
        faces+=[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for i in range(n)]
    p.primitive(verts,faces,mat)


def _sheet(p,rows,mat,up,skip=()):
    """Open single-sided sheet from a grid rows[k][j]; faces turned so their normal z has the
    sign of up (+1 roof top, -1 ceiling). skip: (k,j) quads left open (rooflight holes)."""
    K,J=len(rows),len(rows[0]);verts=[q for r in rows for q in r]
    faces=[(k*J+j,k*J+j+1,(k+1)*J+j+1,(k+1)*J+j) for k in range(K-1) for j in range(J-1) if (k,j) not in skip]
    if not faces:return
    a,b,c=(verts[i] for i in faces[0][:3])
    if A.cross(A.sub(b,a),A.sub(c,a))[2]*up<0:faces=[tuple(reversed(f)) for f in faces]
    p.primitive(verts,faces,mat,closed=False)


def _frustum(p,a,b,r0,r1,mat,n=12):
    from math import cos,sin
    z=A.unit(A.sub(b,a));ref=(0,0,1) if abs(z[2])<.95 else (0,1,0)
    x=A.unit(A.cross(ref,z));y=A.cross(z,x)
    v=[A.add(o,A.add(A.mul(x,r*cos(i*2*pi/n)),A.mul(y,r*sin(i*2*pi/n)))) for o,r in ((a,r0),(b,r1)) for i in range(n)]
    p.primitive(v,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)


def _roof_grid(c):
    """Pan pitch that divides the bay, so a seam sits on every bay joint and the per-bay
    skin sheets never show a butt line: 6-12 pans of 467-542 mm (WORKING/HERO) per bay."""
    bp=c.depth/c.bays;n=max(4,int(bp/(.70 if c.detail=='DRAFT' else .50)+.5))
    return [i*bp/n for i in range(c.bays*n+1)],bp/n,n


def _ridge(p,y0,y1,zs,slope,W,crown,mat):
    """Ridge flashing: two wings clearing the seam heads, drip hems down to 4 mm above the
    pans, a rolled crown. zs = pan surface at x=0. y0/y1 end inside the verge face legs; the
    crown void is closed by 6 mm end plates set 2 mm back, resting on the verge covers."""
    S=lambda X:zs-slope*X;U=lambda X:S(X)+OVER;O=lambda X:U(X)+.006;w=W-.006
    pr=[(W,S(W)+.004),(W,O(W)),(.05,O(.05)),(0.,O(0.)+crown),(-.05,O(.05)),(-W,O(W)),(-W,S(W)+.004),
        (-w,S(w)+.004),(-w,U(w)),(-.044,U(.044)),(0.,O(0.)+crown-.007),(.044,U(.044)),(w,U(w)),(w,S(w)+.004)]
    p.prism(pr,(0,y0,0),XZ,y1-y0,mat)
    cap=[(-.05,S(.05)+.070),(0.,S(0.)+.070),(.05,S(.05)+.070),(.05,U(.05)),(0.,O(0.)+crown-.007),(-.05,U(.05))]
    for ya in (y0+.002,y1-.008):
        p.prism(cap,(0,ya,0),XZ,.006,mat)


def _eave_trim(p,side,edge,under,slope,y0,y1,mat):
    """Eave drip flashing: 45 mm flange slid under the pan ends (top 3 mm below the pan, so
    the sheets lap onto the drip), face leg over the build-up edge stopping 3 mm below the
    pan line, 45-degree kick into the gutter. under = skin underside z at |x|=edge."""
    S=lambda X:under+ROOF_SKIN+slope*(edge-X)
    pr=[(edge-.045,S(edge-.045)-.009),(edge-.045,S(edge-.045)-.003),(edge+.010,S(edge+.010)-.003),
        (edge+.010,under-.050),(edge+.038,under-.078),(edge+.034,under-.082),(edge+.004,under-.054),
        (edge+.004,S(edge+.004)-.009)]
    p.prism([(side*x,z) for x,z in pr],(0,y0,0),XZ,y1-y0,mat)


def _verge(p,surface,stations,y_edge,out,mat,stops=()):
    """Verge/barge flashing along a gable edge; surface(x) = pan z. out=-1 front, +1 rear.
    stops: eave-end stations whose open U-channel gets a stop end, recessed 2 mm."""
    place=lambda x,u,v:(x,y_edge+out*u,surface(x)+v)
    _sweep(p,VERGE,place,stations,mat)
    for xe in stops:
        o=1. if xe>0 else -1.
        _sweep(p,VERGE_STOP,place,(xe-o*.008,xe-o*.002),mat)


def _facade_boxes(m,side):
    """Face AABBs (|x| mirrored to +) of the facade modules on one side; _facades has
    already placed them when _gutters runs, so wall-domain changes are respected."""
    tag='_LEFT_' if side<0 else '_RIGHT_';out=[]
    for p in m.parts:
        if tag in p.name and '__' in p.name:
            for f in p.faces:
                q=[p.vertices[j] for j in f];xs=[side*v[0] for v in q]
                out.append((min(xs),max(xs),min(v[1] for v in q),max(v[1] for v in q),min(v[2] for v in q),max(v[2] for v in q)))
    return out


def _pipe_hits(boxes,env,y,z0,z1):
    """Facade faces entering the downpipe corridor (pipe, clamps, shoe): 70-400 mm off the
    wall face, +-75 mm along the wall, z0..z1. 0 = clear."""
    x0,x1=env.outside_x+.07,env.outside_x+.40
    return sum(1 for b in boxes if b[1]>x0 and b[0]<x1 and b[3]>y-.075 and b[2]<y+.075 and b[5]>z0 and b[4]<z1)


def _downpipe_lines(m,c,env,side,z0,z1,conflicts):
    """Rainwater outlets: one near each end (nudged inward if a module feature is in the
    way; always placed, at the least obstructed try if none is clear, and logged), frame
    lines nearest to ~14 m spacing whose corridor is clear, then gaps over 18 m are split."""
    d=c.depth;bp=d/c.bays;ys=[];boxes=_facade_boxes(m,side)
    clear=lambda y:_pipe_hits(boxes,env,y,z0,z1)==0
    for y,step in ((.22,.30),(d-.22,-.30)):
        best=None
        for k in range(6):
            hits=_pipe_hits(boxes,env,y+k*step,z0,z1)
            if best is None or hits<best[0]:best=(hits,y+k*step)
            if not hits:break
        ys.append(best[1])
        if best[0]:conflicts.append(dict(side=side,y=best[1],faces=best[0]))
    n=max(1,int(d/14.+.5))
    for k in range(1,n):
        free=[i*bp for i in range(1,c.bays) if min([abs(i*bp-y) for y in ys]+[9.])>=4. and clear(i*bp)]
        if free:
            y=min(free,key=lambda v:abs(v-d*k/n))
            if abs(y-d*k/n)<=1.5*bp:ys.append(y)
    ys=sorted(ys)
    while True:   # split the widest remaining run over 18 m at the clear line nearest its middle
        for g,ya,yb in sorted(((b-a,a,b) for a,b in zip(ys,ys[1:])),reverse=True):
            if g<=18.:return ys
            free=[i*bp for i in range(1,c.bays) if ya+4.<=i*bp<=yb-4. and clear(i*bp)]
            if free:
                ys=sorted(ys+[min(free,key=lambda v:abs(v-(ya+yb)/2))]);break
        else:return ys


def _roof_underside(m,c,env,lights):
    """Interior: trapezoidal liner (ribs downslope, resting on the purlins) between the
    walls/monitor kerb, cut for rooflights; cleats tie each purlin to the rafter below."""
    a,d=c.width/2,c.depth;bp=d/c.bays;s=env.slope;R=lambda X:roof_level(c,X)
    _,q,n=_roof_grid(c)          # one liner rib per roof pan: rooflight cuts land on rib starts
    xin=c.monitor_width/2 if c.roof_type=='MONITOR' else 0.;xout=a-.002
    for side in (-1,1):
        p=m.p(f'HG_RoofLiner_{side:+d}','ROOF',0.)
        for i in range(c.bays):
            prof=[]
            for r in range(int(bp/q+.5)):
                y=i*bp+r*q;prof+=[(y,0.),(y+q-.060,0.),(y+q-.045,-.025),(y+q-.015,-.025)]
            prof.append(((i+1)*bp,0.))
            hole=[l for l in lights if l['side']==side and l['bay']==i]
            xs=[xin]+([hole[0]['x0'],hole[0]['x1']] if hole else [])+[xout]
            skip={(1,j) for j in range(len(prof)-1) if hole and prof[j][0]>=hole[0]['y0']-1e-9
                  and prof[j+1][0]<=hole[0]['y1']+1e-9}
            rows=[[(side*X,y,R(X)-.070+dz) for y,dz in prof] for X in xs]
            _sheet(p,rows,'HG_RoofLiner',-1,skip)
    if c.detail=='DRAFT':return
    k=sqrt(1.+s*s);cl=m.p('HG_PurlinCleats','STRUCTURE',.001)
    for sup in m.hangar_meta['roof_supports_design']:
        x=sup['x'];o=1. if x>0 else -1.;xc=x+o*.054
        bottom=R(xc)-.52+.23*k-.005;top=R(x)-.12          # rafter top flange (_structure, .46 I-beam)
        for i in range(c.bays+1):
            cl.box((xc,_frame_y(c,i),(bottom+top)/2),(.010,.14,top-bottom),'Galvanized')


def _rooflight_plan(c,env):
    """GRP strips in a checkerboard of interior bays: 2-3 pans wide, half the slope long,
    kept off the light-hanger zone (bay centre +-0.70 m), the ridge and the eaves."""
    if c.roof_type!='GABLE':return []
    bp=c.depth/c.bays;rx=env.roof_x;_,pitch,n=_roof_grid(c)
    L=min(7.2,max(3.,.5*rx));xc=.55*rx;room=bp/2-.70
    k0=1 if 2*pitch<=room else 0;k=max(1,min(3,int(room/pitch)-k0));out=[]
    for i in range(1,c.bays-1):
        for side in (-1,1):
            if (i+(side>0))%2:continue
            y0=i*bp+k0*pitch
            out.append(dict(side=side,bay=i,x0=xc-L/2,x1=xc+L/2,y0=y0,y1=y0+k*pitch,pans=k))
    return out


def _monitor(m,c,env,ys):
    """Lantern on the ridge: kerb upstand + apron flashing, continuous sill/head rails with
    bay and intermediate mullions, glass captured 20 mm in the rails, end walls on the
    gable planes, standing-seam monitor roof with its own ridge, eave drips and verges."""
    d=c.depth;bp=d/c.bays;s=env.slope;mh=c.monitor_width/2;t=c.wall_thickness
    R=lambda X:roof_level(c,abs(X));S=lambda X:R(X)+ROOF_SKIN
    mx=mh+.15;meave=roof_level(c,0)+c.monitor_height;peak=meave+.32;ms=.32/mx
    Mz=lambda X:meave+(peak-meave)*(1-abs(X)/mx)                 # monitor roof underside
    kh=min(.22,max(.12,.2*(Mz(mh)-S(mh))));sill=S(mh)+kh;head=Mz(mh-.06)+.002
    ndiv=max(2,int(bp/1.4+.5))
    # 1 mm bevel (none): ~100 mullion boxes with a 2-segment bevel cost ~6k tris post-bevel,
    # and a 2 mm round on 50-120 mm sections is invisible at roof distance.
    frames=m.p('HG_MonitorFrames','FACADE',.001);kerb=m.p('HG_MonitorKerb','ROOF',.001)
    # Lantern eave drip: not named '*Drip' so LOD1 (small-token filter) keeps it like LOD0/LOD2.
    drip=m.p('HG_MonitorEaveTrim','ROOF',.001);vg=m.p('HG_Bargeboards','ROOF',.001)
    for side in (-1,1):
        x=side*mh
        kerb.box((side*(mh-.05),d/2,(R(mh)-.095+sill)/2),(.10,d,sill-(R(mh)-.095)),'HG_RoofLiner')
        # Apron: vertical leg tucked into the sill rail, cover over the seam ends, drip hem.
        pr=[(mh+.004,sill+.020),(mh+.010,sill+.020),(mh+.010,S(mh+.010)+OVER+.006),(mh+.200,S(mh+.200)+OVER+.006),
            (mh+.200,S(mh+.200)+.004),(mh+.194,S(mh+.194)+.004),(mh+.194,S(mh+.194)+OVER),(mh+.004,S(mh+.004)+OVER)]
        kerb.prism([(side*u,z) for u,z in pr],(0,env.front_y-.003,0),XZ,env.back_y-env.front_y+.006,FLASH)
        # Stop ends close the apron void where it oversails the notch returns (set back 2 mm).
        se=[(mh+.010,S(mh+.010)-.005),(mh+.194,S(mh+.194)-.005),(mh+.194,S(mh+.194)+OVER),(mh+.010,S(mh+.010)+OVER)]
        for ya in (env.front_y-.001,env.back_y-.005):
            kerb.prism([(side*u,z) for u,z in se],(0,ya,0),XZ,.006,FLASH)
        for zc,hz in ((sill+.04,.08),(head-.04,.08)):
            frames.box((x,d/2,zc),(.12,d,hz),'SteelDark')
        lines=[(i*bp+k*bp/ndiv,.07 if k==0 else .05) for i in range(c.bays) for k in range(ndiv) if i or k]
        for y,w in [(.025,.05),(d-.025,.05)]+lines:
            frames.box((x,y,(sill+head)/2),(.11,w,head-sill-.16),'SteelDark')
        for i in range(c.bays):
            m.box(f'HG_MonitorGlass_{i}_{side}',(x,(i+.5)*bp,(sill+head)/2),(.024,bp-.06,head-sill-.12),'Glass','GLASS',0.)
        for i in range(c.bays+1):
            z0=R(mh)-.51;z1=Mz(mh-.204)+.003
            m.box('HG_MonitorPosts',(side*(mh-.129),i*bp,(z0+z1)/2),(.15,.095,z1-z0),'SteelDark','STRUCTURE',.003)
        _eave_trim(drip,side,mx,meave,ms,env.roof_y0-.007,env.roof_y1+.007,FLASH)
        # End-wall corner trims (L), bedded into the apron cover and the monitor roof. The
        # return leg covers the whole end-wall return and stops 3 mm inside the end jamb.
        for yf,o in ((env.front_y,-1),(env.back_y,1)):
            z0=S(mh)+.074;z1=Mz(mh-.09)+.003
            vg.box((side*(mh-.041),yf+o*.0065,(z0+z1)/2),(.098,.013,z1-z0),FLASH)
            ya,yb=(yf-.010,.003) if o<0 else (d-.003,yf+.010)
            vg.box((side*(mh+.0065),(ya+yb)/2,(z0+z1)/2),(.013,yb-ya,z1-z0-.004),FLASH)
    for i in range(c.bays):
        y0=env.roof_y0 if i==0 else i*bp;y1=env.roof_y1 if i==c.bays-1 else (i+1)*bp
        for lo,hi,za,zb in ((-mx,0,meave,peak),(0,mx,peak,meave)):
            p=m.p(f'HG_MonitorRoof_{i}_{int(lo==0)}','ROOF',.002);f0=len(p.faces)
            p.prism([(lo,za),(hi,zb),(hi,zb+ROOF_SKIN),(lo,za+ROOF_SKIN)],(0,y0,0),XZ,y1-y0,'HG_Roof')
            _roof_uv(p,ms)
            # Soffit seen from the hangar floor through the lantern: flat liner finish.
            if 'HG_RoofLiner' not in p.material_names:p.material_names.append('HG_RoofLiner')
            for k in range(f0,len(p.faces)):
                q=[p.vertices[j] for j in p.faces[k][:3]]
                if A.cross(A.sub(q[1],q[0]),A.sub(q[2],q[0]))[2]<0:p.material_ids[k]=p.material_names.index('HG_RoofLiner')
    # Lantern frame: one-piece cranked RHS 100x180 rafter on every frame line (top bedded 2 mm
    # into the soffit, ends framed into the posts) and a ridge purlin running between the
    # end rafters; the end rafters butt the end walls.
    raf=m.p('HG_MonitorRafters','STRUCTURE',.001);xr=mh-.13
    for i in range(c.bays+1):
        raf.prism([(-xr,Mz(xr)+.002),(0.,Mz(0.)+.002),(xr,Mz(xr)+.002),(xr,Mz(xr)-.178),(0.,Mz(0.)-.178),(-xr,Mz(xr)-.178)],
                  (0,min(max(i*bp-.05,0.),d-.10),0),XZ,.10,'SteelDark')
    raf.box((0.,d/2,Mz(0.)-.058),(.10,d-.10,.12),'SteelDark')
    _ridge(m.p('HG_MonitorCap','ROOF',.001),env.roof_y0-.008,env.roof_y1+.008,peak+ROOF_SKIN,ms,.17,.030,FLASH)
    Sm=lambda X:peak+ROOF_SKIN-ms*abs(X)
    for y_edge,out in ((env.roof_y0,-1),(env.roof_y1,1)):
        _verge(vg,Sm,(-(mx-.001),0.,mx-.001),y_edge,out,FLASH,(-(mx-.001),mx-.001))
    # End walls stand on the gable planes, top follows the monitor roof underside exactly.
    prof=[(-mh,R(mh)),(0,R(0)),(mh,R(mh)),(mh,Mz(mh)),(0,Mz(0)),(-mh,Mz(mh))]
    for y in (env.front_y,d):
        m.p('HG_MonitorEndCaps','BODY',.003).prism(prof,(0,y,0),XZ,t,'HG_Wall')


def _roof_hardware(m,c,env,ys,pitch,npan,lights):
    """Fall-arrest line on seam clamps (posts <=10 m apart) and two vent stacks with EPDM
    boots; placed clear of rooflights, ridge vents and the monitor apron."""
    d=c.depth;bp=d/c.bays;s=env.slope;rx=env.roof_x;mon=c.roof_type=='MONITOR';mh=c.monitor_width/2 if mon else 0.
    R=lambda X:roof_level(c,abs(X));S=lambda X:R(X)+ROOF_SKIN
    T=lambda sd:A.unit((sd,0.,-s));N=lambda sd:A.unit((sd*s,0.,1.))
    line=m.p('HG_RoofSafetyLine','ROOF',.001)     # ROOF: hidden with the roof in section view
    for X in ((-(mh+1.25),mh+1.25) if mon else (1.0,)):
        sd=1. if X>0 else -1.;n=max(1,ceil((d-1.)/10.))
        posts=sorted({min(ys,key=lambda y:abs(y-(.5+j*(d-1.)/n))) for j in range(n+1)})
        top=S(X)+.50
        for y in posts:
            base=(X,y,S(X));line.box(A.add(base,A.mul(N(sd),.0355)),(.12,.06,.075),'Galvanized',(T(sd),(0,1,0),N(sd)))
            line.cylinder((X,y,S(X)+.065),(X,y,top),.022,'Galvanized',8)
            line.box((X,y,top),(.05,.04,.03),'Galvanized')
        line.pipe([(X,posts[0],top-.002),(X,posts[-1],top-.002)],.005,'Galvanized',6)
        for y in (posts[0]+.15,posts[-1]-.15):
            line.cylinder((X,y-.11,top-.002),(X,y+.11,top-.002),.028,'Yellow',8)
    from math import cos,sin
    stacks=m.p('HG_RoofPenetrations','ROOF',.001)
    for sd in (-1,1):
        free=[i for i in range(1,c.bays-1) if not any(l['side']==sd and l['bay']==i for l in lights)] or [1]
        i=max(free) if sd>0 else min(free)
        X=.62*rx if not mon else mh+.15+.55*(rx-mh-.15);x=sd*X;y=i*bp+(npan//2+.5)*pitch
        stacks.box(A.add((x,y,S(X)),A.mul(N(sd),.002)),(.44,.36,.006),'Galvanized',(T(sd),(0,1,0),N(sd)))
        zb=S(X)+.005-.12*s-.002;top=S(X)+.95
        _frustum(stacks,(x,y,zb),(x,y,zb+.14+.12*s),.12,.065,'Rubber')
        stacks.cylinder((x,y,zb+.01),(x,y,top),.055,'Galvanized',12)
        _frustum(stacks,(x,y,top+.07),(x,y,top+.13),.11,.015,'Galvanized')
        for k in range(3):
            ang=k*2*pi/3
            stacks.box((x+.045*cos(ang),y+.045*sin(ang),top+.031),(.012,.012,.082),'Galvanized')


def _roof(m,c):
    a,d=c.width/2,c.depth;bp=d/c.bays;env=envelope(c);s=env.slope;rx=env.roof_x
    mon=c.roof_type=='MONITOR';mh=c.monitor_width/2 if mon else 0.
    R=lambda X:roof_level(c,abs(X));S=lambda X:R(X)+ROOF_SKIN
    ys,pitch,npan=_roof_grid(c);lights=_rooflight_plan(c,env);hero=c.detail!='DRAFT'
    # ---- skin: per-bay sheets (texture-kit tiling surface), cut for GRP rooflights
    for i in range(c.bays):
        ya,yb=env.roof_y0 if i==0 else i*bp,env.roof_y1 if i==c.bays-1 else (i+1)*bp
        for side in (-1,1):
            lo,hi=(-rx,-mh) if side<0 else (mh,rx)
            p=m.p(f'HG_RoofSkin_{i:02d}_{side:+d}','ROOF',.002)
            cut=[l for l in lights if l['side']==side and l['bay']==i]
            pieces=rectangle_difference((lo,ya,hi,yb),(min(side*cut[0]['x0'],side*cut[0]['x1']),cut[0]['y0'],
                   max(side*cut[0]['x0'],side*cut[0]['x1']),cut[0]['y1'])) if cut else [(lo,ya,hi,yb)]
            for x0,y0,x1,y1 in pieces:
                p.prism([(x0,R(x0)),(x1,R(x1)),(x1,S(x1)),(x0,S(x0))],(0,y0,0),XZ,y1-y0,'HG_Roof')
                m.hangar_meta['roof_cells'].append(dict(id=p.name,x0=x0,x1=x1,y0=y0,y1=y1))
            _roof_uv(p,s)
    # ---- standing seams on the grid + one 5 mm pencil rib in every pan
    seams=m.p('HG_StandingSeams','DETAIL',.001)
    runs=[(mh+.17 if mon else .27,rx-.012,S)]
    if mon:
        mx=mh+.15;meave=roof_level(c,0)+c.monitor_height;peak=meave+.32;ms=.32/mx
        Sm=lambda X:peak+ROOF_SKIN-ms*abs(X)
        runs.append((.14,mx-.012,Sm))
    for x_in,x_out,surf in runs:
        main=surf is S
        for side in (-1,1):
            for y in ys:
                # Seams inside a rooflight run belong to the GRP sheet (split at its laps); the
                # boundary seams stay metal. The downslope end is crimped (dog-ear) at the eave.
                lit=[l for l in lights if main and l['side']==side and l['y0']+1e-6<y<l['y1']-1e-6]
                cuts=[(x_in,x_out,'HG_RoofSeam')] if not lit else [(x_in,lit[0]['x0'],'HG_RoofSeam'),
                      (lit[0]['x0'],lit[0]['x1'],'HG_RoofLight'),(lit[0]['x1'],x_out,'HG_RoofSeam')]
                for u0,u1,mat in cuts:
                    _run(seams,y,(side*u0,surf(u0)),(side*u1,surf(u1)),SEAM,mat,.045 if u1==x_out else 0.)
            # Pencil ribs on the main roof only: on the lantern they sit 1-1.6 m higher, read as
            # nothing and cost ~1k tris on wide monitors.
            if not hero or not main:continue
            for j in range(len(ys)-1):
                y=(ys[j]+ys[j+1])/2
                lit=[l for l in lights if l['side']==side and l['y0']-1e-9<=y<=l['y1']+1e-9]
                spans=[(x_in,x_out)] if not lit else [(x_in,lit[0]['x0']-.03),(lit[0]['x1']+.03,x_out)]
                for u0,u1 in spans:
                    _sheet(seams,[[(side*X,y-.015,surf(X)-.001),(side*X,y,surf(X)+.005),(side*X,y+.015,surf(X)-.001)]
                                  for X in (u0,u1)],'HG_Roof',1)
                if lit:
                    l=lit[0]
                    _sheet(seams,[[(side*X,y-.015,surf(X)-.002),(side*X,y,surf(X)+.006),(side*X,y+.015,surf(X)-.002)]
                                  for X in (l['x0']+.03,l['x1']-.03)],'HG_RoofLight',1)
    # ---- GRP rooflights: translucent body through the build-up, end-lap strips
    if lights:
        rl=m.p('HG_RoofLights','ROOF',.001)
        for l in lights:
            sd=l['side'];x0,x1=l['x0']+.001,l['x1']-.001
            rl.prism([(sd*x0,S(x0)-.001),(sd*x1,S(x1)-.001),(sd*x1,R(x1)-.073),(sd*x0,R(x0)-.073)],
                     (0,l['y0']+.001,0),XZ,l['y1']-l['y0']-.002,'HG_RoofLight')
            # End laps shed water downslope: the metal sheet above laps over the GRP at the
            # head, the GRP laps over the metal sheet below at the foot.
            for X,mat in ((l['x0'],'HG_Roof'),(l['x1'],'HG_RoofLight')):
                rl.prism([(sd*(X-.025),S(X-.025)-.001),(sd*(X+.025),S(X+.025)-.001),(sd*(X+.025),S(X+.025)+.004),
                          (sd*(X-.025),S(X-.025)+.004)],(0,l['y0']-.010,0),XZ,l['y1']-l['y0']+.020,mat)
    # ---- eaves: drip flashing over the build-up edge, fascia board for the gutter brackets
    trim=m.p('HG_RoofEaveTrim','ROOF',.001);fascia=m.p('HG_RoofFascia','ROOF',.001)
    for side in (-1,1):
        _eave_trim(trim,side,rx,R(rx),s,env.roof_y0-.007,env.roof_y1+.007,FLASH)
        top=R(rx-.009)+.002;bot=R(rx)-.24
        fascia.box((side*(rx-.006),(env.roof_y0+env.roof_y1)/2,(top+bot)/2),(.006,env.roof_y1-env.roof_y0+.012,top-bot),FLASH)
    # ---- verges: one mitred sweep per gable (GABLE), or eave->monitor runs plus notch returns
    vg=m.p('HG_Bargeboards','ROOF',.001)
    for y_edge,out in ((env.roof_y0,-1),(env.roof_y1,1)):
        if not mon:
            _verge(vg,S,(-(rx-.006),0.,rx-.006),y_edge,out,FLASH,(-(rx-.006),rx-.006))
        else:
            for side in (-1,1):
                _verge(vg,S,(side*(mh-.012),side*(rx-.006)),y_edge,out,FLASH,(side*(rx-.006),))
                # Notch return: caps the sheet edge at x=+-mh in the overhang in front of the
                # monitor end wall (the monitor sits back on the gable plane).
                ya,yb=(env.roof_y0-.007,env.front_y+.002) if out<0 else (env.back_y-.002,env.roof_y1+.007)
                _sweep(vg,VERGE_RETURN,lambda y,u,v,sd=side:(sd*(mh-u),y,S(mh-u)+v),(ya,yb),FLASH)
    if not mon:
        # ---- ridge: flashing over the seam ends + louvred ridge ventilators, placed in mirrored
        # bay pairs (plus the middle bay on odd counts) so the ridge reads symmetric
        _ridge(m.p('HG_RidgeCap','ROOF',.001),env.roof_y0-.008,env.roof_y1+.008,S(0.),s,.30,.040,FLASH)
        vents=m.p('HG_RoofRidgeVents','ROOF',.001);O=lambda X:S(X)+OVER+.006
        Lv=min(2.4,bp-1.0);h0=S(0.)+.50;Hu=lambda X:h0-.060*X/.414
        lo,hi=O(.26)+.04,Hu(.26)-.04;nb=max(4,int((hi-lo-.03)/.055))
        for i in sorted({j for i in range(1,c.bays//2,3) for j in (i,c.bays-1-i)}|({c.bays//2} if c.bays%2 else set())):
            yc=(i+.5)*bp
            vents.prism([(-.26,O(.26)-.003),(0.,O(0.)-.003),(.26,O(.26)-.003),(.26,Hu(.26)+.002),(0.,Hu(0.)+.002),
                         (-.26,Hu(.26)+.002)],(0,yc-Lv/2,0),XZ,Lv,FLASH)
            vents.prism([(-.420,Hu(.42)-.064),(-.420,Hu(.42)+.006),(0.,Hu(0.)+.006),(.420,Hu(.42)+.006),(.420,Hu(.42)-.064),
                         (.414,Hu(.414)-.064),(.414,Hu(.414)),(0.,Hu(0.)),(-.414,Hu(.414)),(-.414,Hu(.414)-.064)],
                        (0,yc-Lv/2-.05,0),XZ,Lv+.10,FLASH)
            for side in (-1,1):
                # Dark louvre throat with 40-degree weather blades (60 mm deep, 6-7 per side at
                # ~65 mm pitch) bedded 3 mm into it; blades end 10 mm short of the opening.
                vents.box((side*.258,yc,(lo+hi)/2),(.010,Lv-.10,hi-lo),'Interior')
                for k in range(nb):
                    zz=lo+.03+(hi-lo-.06)*k/(nb-1)
                    vents.box((side*.2856,yc,zz),(.06,Lv-.12,.008),'Galvanized',A.euler_axes(0,side*radians(40),0))
    else:
        _monitor(m,c,env,ys)
    if hero:_roof_hardware(m,c,env,ys,pitch,npan,lights)
    _roof_underside(m,c,env,lights)
    m.hangar_meta['roof_design']=dict(pan_pitch_m=pitch,pans_per_bay=npan,seam_height_m=.058,
        rooflights=lights,build_up_m=ROOF_SKIN,downpipes_design=[],downpipe_conflicts=[])


def _facades(m,c):
    a,d,z=c.width/2,c.depth,c.base_height;bp=d/c.bays;env=envelope(c);seqs={}
    for side,label in ((-1,'LEFT'),(1,'RIGHT')):
        seqs[side]=c.panel_sequence(label)
        for i,token in enumerate(seqs[side]):
            axes=((-side,0,0),(0,-side,0),(0,0,1))
            _copy_module(m,c,token,bp,f'{label}_{i:02d}',(side*env.outside_x,(i+.5)*bp,z),axes)
    # Rear wall uses the same validated module family; deliberate single personnel bay. The cells
    # bring core, trims and openings; their skin holes are collected in the rear sheet's u (= -x).
    rear_width=2*env.outside_x
    n=max(4,ceil(rear_width/5.4));bw=rear_width/n;rear=[]
    for i in range(n):
        token='PERSONNEL' if c.rear_service_door and i==n//2 else ('LOUVER' if i in (1,n-2) else 'METAL')
        cx=-env.outside_x+(i+.5)*bw
        src=_copy_module(m,c,token,bw,f'REAR_{i:02d}',(cx,env.back_y,z),((0,-1,0),(1,0,0),(0,0,1)))
        rear+=[(q[0]-cx,q[1],q[2]-cx,q[3]) for q in getattr(src,'skin_holes',())]
    # Front, gables and corners use the module wall build-up: core (liner inside) 47 mm behind
    # the crest plane, one continuous trapezoidal sheet whose crest plane stays the old outer
    # face (front_y/back_y), pressed flashings in layers L1/L2 outside it.
    C=MG.ModuleModel;t=c.wall_thickness;X,fy,by=env.outside_x,env.front_y,env.back_y
    ey=z+c.eave_height;ridge=roof_level(c,0);core=t-C.CLAD_CORE;Xc=X-C.CLAD_CORE
    ow,oh=c.opening_width,c.opening_height;top=z+oh;topbase=top+.36
    zc=top+.745          # rail canopy deck top (_gates.head: HG_RailCanopy)
    # Pocket, plinth and drip ends stop 20 mm inside the 200 mm portal jamb (deep enough not to
    # depth-fight its inner face); 2 mm only on walls so thick that the core stands proud of it.
    oj=ow/2+(.02 if fy+C.CLAD_CORE>-.29 else .002)
    def roof(x):return roof_level(c,x)-C.CLAD_TOP
    for sign in (-1,1):
        lo,hi=sorted((sign*oj,sign*Xc))
        m.box('HG_FrontPockets',((lo+hi)/2,fy+C.CLAD_CORE+core/2,z+c.eave_height/2),(hi-lo,core,c.eave_height),'HG_Wall','BODY',0.)
        for xx in (sign*(a-.04),sign*(ow/2+.10)):
            m.box('HG_PortalJambs',(xx,-.14,z+oh/2),(.20,.31,oh+.10),'SteelDark','STRUCTURE',.005)
        lo,hi=sorted((sign*oj,sign*X))
        m.box('HG_FrontPlinth',((lo+hi)/2,fy+(C.CLAD_CORE-.046)/2,z+.24),(hi-lo,C.CLAD_CORE+.046,.48),'Concrete','FACADE',.004)
        x0,x1=sorted((sign*oj,sign*(X+.07)))
        m.p('HG_FrontBaseFlashing','DETAIL',0.).prism(C.BASE_FLASH,(x0,fy,z),C.YZX,x1-x0,'HG_WallTrim')
        if fy-.004<-.295:
            # Thick walls only: the pocket sheet's raw edge shows beside the portal jamb.
            e0,e1=sorted((sign*(ow/2+.002),sign*(ow/2+.10)))
            m.box('HG_PocketEdgeTrims',((e0+e1)/2,fy-.00275,z+.30+oh/2),(e1-e0,.0025,oh-.40),'HG_WallTrim','DETAIL',0.)
    # Corner ends of the pocket drips mitre on the plan diagonal x+y = X+front_y.
    C.shift(m.p('HG_FrontBaseFlashing'),lambda v:abs(v[0])>X+.065,lambda v:((X+fy-v[1])*(1 if v[0]>0 else -1),v[1],v[2]))
    m.box('HG_FrontHeaderInfill',(0,fy+C.CLAD_CORE+core/2,(topbase+ey)/2),(2*oj,core,ey-topbase),'HG_Wall','BODY',0.)
    # Gable cores close the volume below the main roof; the raised monitor has its own end caps.
    profile=[(-Xc,ey),(Xc,ey),(Xc,roof_level(c,Xc)),(0,ridge),(-Xc,roof_level(c,Xc))]
    for label,y,out in (('FRONT',fy+C.CLAD_CORE,-1.),('REAR',d,1.)):
        m.p('HG_Gable_'+label,'BODY',0.).prism(profile,(0,y,0),((1,0,0),(0,0,1),(0,1,0)),core,'HG_Wall')
        C.tone_faces(m.p('HG_Gable_'+label),[(0.,out,0.)],'HG_Wall','HG_WallLiner')
    for name in ('HG_FrontPockets','HG_FrontHeaderInfill'):
        C.tone_faces(m.p(name),[(0.,-1.,0.)],'HG_Wall','HG_WallLiner')
    # Sheets, one per elevation from the plinth to the verges. Front: below the gate canopy the
    # wall is enclosed by the door houses, header and pelmet, so between the door-house end plates
    # (_gates: a+.091) the sheet starts 50 mm over the deck behind an abutment flashing; outside
    # them (seen only on walls thicker than the corner angle) it stays full height. Rear: the
    # cells' apertures cut with the module rule, so eave, bay joints and UVs are continuous.
    front=((0.,fy,0.),(1.,0.,0.),(0.,1.,0.));back=((0.,by,0.),(-1.,0.,0.),(0.,-1.,0.))
    pf,pr=C.clad_pitch(2*X),C.clad_pitch(bw);xh=a+.091
    C.profile_sheet(m.p('HG_FrontCladding','BODY',0.),-X,X,pf,-X,z+C.CLAD_BASE,roof,[(-xh,z,xh,zc+.05)],(0.,),front,'HG_Wall')
    C.profile_sheet(m.p('HG_RearCladding','BODY',0.),-X,X,pr,-X,z+C.CLAD_BASE,lambda u:roof(-u),C.sheet_cuts(rear,z),(0.,),back,'HG_Wall')
    # Abutment flashing: L1 upstand lapping 100 mm over the sheet foot, 2.5 mm cover leg on the
    # deck with a hemmed front edge; it stops against the corner angles' hems.
    xa=X-.1505
    m.p('HG_CanopyAbutment','DETAIL',0.).prism([(fy-.0015,zc),(fy-.0015,zc+.15),(fy-.004,zc+.15),(fy-.004,zc+.0025),
        (fy-.094,zc+.0025),(fy-.094,zc+.005),(fy-.104,zc+.005),(fy-.104,zc)],(-xa,0.,0.),C.YZX,2*xa,'HG_WallTrim')
    if c.fasteners and c.detail=='HERO':
        # Same girt lines as the side bays, continued up the gables at the same spacing.
        rows=C.girt_rows(z+.58,ey-.166,top=ridge-.2)
        fx=m.p('HG_CladFixings','DETAIL',0.)
        C.fixings(fx,-X+.15,X-.15,pf,-X,rows,[(-xh,z,xh,zc+.15)],roof,front,'HG_WallTrim')
        C.fixings(fx,-X+.15,X-.15,pr,-X,rows,[(q[0],z+q[1],q[2],z+q[3]) for q in rear],lambda u:roof(-u),back,'HG_WallTrim')
    # Verge trims: 100 mm plates under the roof edge in layer L2 (over the corner angles), plumb
    # ends meeting at the apex (the halves abut, never cross); they run out over the eave-trim
    # face legs at the corners, whose returns stop against their back face.
    for y in (fy-.0065,by+.0045):
        for s in (-1,1):
            xa=s*(X+.0065)
            m.p('HG_VergeTrims','DETAIL',0.).prism([(xa,roof_level(c,xa)-.106),(0.,ridge-.106),(0.,ridge-.006),(xa,roof_level(c,xa)-.006)],
                (0.,y,0.),((1,0,0),(0,0,1),(0,1,0)),.002,'HG_WallTrim')
    # Corners (front/rear walls own the corner square): side-elevation cladding return in the
    # side bays' rib rhythm (bay lines on crest centres), plinth return, mitred base flashing,
    # eave-trim return and a hemmed 150/150 angle flashing (plain under the eave trim), bedded
    # ~1 mm into the base flashing. Next to a cassette bay the side leg runs on to the bay line
    # instead of a ribbed strip: its edge and the trays' 10 mm inset read as one cassette joint.
    Lf=.15;ps=C.clad_pitch(bp);eave=C.eave_profile(ey)
    for sx in (-1,1):
        inward=((-sx,0,0),(0,0,1),(0,1,0));sideframe=((sx*X,0.,0.),(0.,sx,0.),(-sx,0.,0.));seq=seqs[sx]
        for Y,sy,(u0,u1),(f0,f1),(t0,t1),yj,cas in ((fy,-1,(fy,0.),(fy-.07,0.),(fy-.0045,0.),0.,seq[0]=='CASSETTE'),
                                                   (by,1,(d,by),(d,by+.07),(d,by+.0045),d,seq[-1]=='CASSETTE')):
            Ls=t if cas else .15
            full=[(-Lf,.0015),(-Lf,.008),(-Lf+.008,.008),(-Lf+.008,.004),(.004,.004),(.004,-Ls+.008),(.008,-Ls+.008),(.008,-Ls),(.0015,-Ls),(.0015,.0015)]
            plain=[(-Lf,.0015),(-Lf,.004),(.004,.004),(.004,-Ls),(.0015,-Ls),(.0015,.0015)]
            if not cas:
                ua,ub=sorted((sx*u0,sx*u1))
                C.profile_sheet(m.p('HG_CornerCladding','BODY',0.),ua,ub,ps,sx*yj+ps/2,z+C.CLAD_BASE,ey-C.CLAD_TOP,frame=sideframe,mat='HG_Wall')
            # Precast corner unit with 5 mm sealant joints, recessed 5 mm, to the end-wall plinth
            # (at x=X) and to the side-bay plinth (at the bay line yj): no abutting bevel seams.
            xa,xb=sorted((sx*(X+.005),sx*(X+.046)));ya,yb=sorted((Y+sy*.046,yj+sy*.005))
            m.box('HG_CornerPlinths',((xa+xb)/2,(ya+yb)/2,z+.24),(xb-xa,yb-ya,.48),'Concrete','FACADE',.004)
            jt=m.p('HG_PlinthJoints','DETAIL',0.);xa,xb=sorted((sx*X,sx*(X+.041)))
            jt.box(((xa+xb)/2,yj+sy*.0025,z+.23875),(xb-xa,.005,.4775),'Joint')
            xa,xb=sorted((sx*X,sx*(X+.005)));ya,yb=sorted((Y+sy*.041,Y-sy*C.CLAD_CORE))
            jt.box(((xa+xb)/2,(ya+yb)/2,z+.23875),(xb-xa,yb-ya,.4775),'Joint')
            m.p('HG_CornerBaseFlashing','DETAIL',0.).prism(C.BASE_FLASH,(sx*X,f0,z),inward,f1-f0,'HG_WallTrim')
            m.p('HG_CornerEaveTrims','DETAIL',0.).prism(eave,(sx*X,t0,0.),inward,t1-t0,'HG_WallTrim')
            caps=m.p('HG_CornerCaps','FACADE',0.)
            for prof,z0,z1 in ((full,z+.4925,ey-.101),(plain,ey-.101,ey-C.CLAD_TOP)):
                caps.prism([(sx*(X+u),Y+sy*v) for u,v in prof],(0.,0.,z0),A.IDENTITY,z1-z0,'HG_WallTrim')
        # Cassette <-> profiled bay lines: 120 mm L1 cover plate from the base flashing up behind
        # the eave-trim face leg, and a 2.5 mm return 60 mm into the profiled bay that closes its
        # open pan; on the cassette side the plate laps the tray inset.
        for i,(p0,p1) in enumerate(zip(seq,seq[1:])):
            if (p0=='CASSETTE')!=(p1=='CASSETTE'):
                yb=(i+1)*bp;s=1. if p0=='CASSETTE' else -1.;zm=(z+.4925+ey-C.CLAD_TOP)/2;hz=ey-C.CLAD_TOP-z-.4925
                bt=m.p('HG_BayTransitionTrims','DETAIL',0.)
                bt.box((sx*(X+.00275),yb,zm),(.0025,.12,hz),'HG_WallTrim')
                bt.box((sx*(X-.017),yb+s*.05875,zm),(.037,.0025,hz),'HG_WallTrim')
        # Fill the sloped wall/roof return without protruding through the roof skin.
        lo,hi=(a,X) if sx>0 else (-X,-a)
        prof=[(lo,ey),(hi,ey)]
        if sx>0: prof.append((lo,roof_level(c,lo)))
        else: prof.append((hi,roof_level(c,hi)))
        m.p('HG_WallRoofClosure_'+str(sx),'BODY',.001).prism(prof,(0,0,0),
            ((1,0,0),(0,0,1),(0,1,0)),d,'HG_Wall')
    # Side-return drips mitre into the pocket / rear drips: y = front_y-(|x|-X), back_y+(|x|-X).
    C.shift(m.p('HG_CornerBaseFlashing'),lambda v:v[1]<fy-.065,lambda v:(v[0],fy-(abs(v[0])-X),v[2]))
    C.shift(m.p('HG_CornerBaseFlashing'),lambda v:v[1]>by+.065,lambda v:(v[0],by+(abs(v[0])-X),v[2]))

TRACK_PITCH=.24
TRACK_INNER_BOTTOM=.13   # above opening head: top of the inner running flanges
TRACK_INNER_TOP=.25      # cavity ceiling
WHEEL_R=.05


def _track_system(m,c):
    """Top-hung telescopic door hardware, one track per leaf row.

    Box-section rail with a bottom slot (hanger stems pass through, twin rollers run on the
    inner flanges), a continuous support girder bolted to the canopy soffit through hanger
    plates, cross spacers between adjacent girders, rubber-buffered end stops and a floor
    guide channel. All quads; still visual hardware, not a rated door design.
    Seen from below the head reads as one dark soffit: painted rails, 6 mm closer strips under
    the 60 mm gaps between adjacent rails (5 mm under each web, 2 mm below the web bottoms,
    16 mm clear of the leaf tops) and an inner closer in front of the portal jambs.
    """
    oh=c.opening_height;z=c.base_height;w=c.width;top=z+oh
    L=w-.18;n=c.gate_leaves//2
    pitch=1.5;count=max(2,round(L/pitch));xs=[-L/2+.10+(L-.20)*i/(count-1) for i in range(count)]
    for j in range(n):
        y=-.43-j*TRACK_PITCH
        rail=m.p(f'HG_GateRail_{j}','STRUCTURE',.002)
        rail.box((0,y,top+.265),(L,.18,.03),'HG_GateTrack')                     # top plate .25..28
        for s in (-1,1):
            rail.box((0,y+s*.08,top+.095),(L,.02,.31),'HG_GateTrack')          # webs -.06..25
            rail.box((0,y+s*.0475,top+.11),(L,.045,.04),'HG_GateTrack')        # running flanges .09..13
        closer=m.p('HG_TrackClosers','DETAIL',.001)
        if j==0:closer.box((0,-.321,top-.065),(L,.048,.006),'HG_GateTrack')     # inner closer, 2 mm off the jambs
        if j<n-1:closer.box((0,y-.12,top-.065),(L,.070,.006),'HG_GateTrack')    # gap to the next track out
        # Support girder sits on the rail, hanger plates tie it to the canopy soffit.
        m.box(f'HG_TrackGirder_{j}',(0,y,top+.33),(L,.18,.10),'SteelDark','STRUCTURE',.003)
        hang=m.p('HG_TrackHangers','DETAIL',.001)
        for xx in xs:
            hang.box((xx,y,top+.386),(.16,.22,.012),'Galvanized')
            hang.box((xx,y,top+.509),(.10,.14,.234),'Galvanized')               # stem up to the soffit (+.626)
            if j<n-1:
                hang.box((xx,y-TRACK_PITCH/2,top+.33),(.08,.06,.06),'SteelDark')   # cross spacer, girder to girder
        stops=m.p('HG_TrackEndStops','DETAIL',.001)
        for s in (-1,1):
            stops.box((s*(L/2+.006),y,top+.185),(.012,.20,.21),'SteelDark')
            stops.box((s*(L/2-.04),y,top+.22),(.06,.10,.10),'Rubber')
        # Floor guide channel: shallow U, the leaf guide pins run inside the slot.
        guide=m.p('HG_GroundGuides','DETAIL',.001)
        guide.box((0,y,z+.004),(w-.20,.10,.008),'Galvanized')
        for s in (-1,1):
            guide.box((0,y+s*.0425,z+.019),(w-.20,.015,.022),'Galvanized')


def _trolley(m,c,p,xx,y,z1,top):
    """Twin-roller hanger: bracket on the leaf top rail, stem through the rail slot, axle
    carrier and four wheels on the inner flanges; plus the bottom guide pin in the channel."""
    seg=10 if c.detail=='DRAFT' else 16
    p.box((xx,y,z1+.03),(.26,.13,.06),'Galvanized')
    stem_top=top+.17
    p.box((xx,y,(z1+.06+stem_top)/2),(.06,.04,stem_top-(z1+.06)),'Galvanized')
    p.box((xx,y,top+.185),(.26,.05,.05),'Galvanized')
    zc=top+TRACK_INNER_BOTTOM+WHEEL_R+.001
    first=len(p.vertices)
    for dx in (-.09,.09):
        for s in (-1,1):
            p.cylinder((xx+dx,y+s*.031,zc),(xx+dx,y+s*.059,zc),WHEEL_R,'Galvanized',seg)
    rv=p.vertices[first:]
    m.hangar_meta.setdefault('roller_checks_design',[]).append(dict(part=p.name,
        actual_z_min=min(v[2] for v in rv),actual_z_max=max(v[2] for v in rv),
        track_inner_bottom=top+TRACK_INNER_BOTTOM,track_inner_top=top+TRACK_INNER_TOP))
    # Bottom guide shoe rides inside the floor channel slot, 2 mm above the channel base.
    z0=c.base_height+.025
    p.box((xx,y,z0-.0075),(.10,.06,.015),'Galvanized')


def sign_text(c):
    """'HG_VEHICLE_DEPOT_01' -> ('VEHICLE DEPOT', '01'); prefix dropped, underscores spaced."""
    body=c.name
    for prefix in ('HG_','HGR_','HANGAR_'):
        if body.upper().startswith(prefix):body=body[len(prefix):];break
    found=re.match(r'^(.*?)[_-]?(\d+)$',body)
    title,number=(found.group(1),found.group(2)) if found and found.group(1) else (body,'')
    return re.sub(r'[_-]+',' ',title).strip().upper() or 'HANGAR',number


def _identity_sign(m,c):
    """Gable identity sign on one proportional grid (unit = panel height H).

    Amber number block (H x H) + anthracite name field; title, aluminium rule and
    tracked subtitle share one left edge; equal margins; aluminium edge frame;
    concealed mounting on a recessed carrier so the panel floats with a shadow gap.
    Letters are raised, bevelled geometry in one bundled OFL family (Big Shoulders).
    """
    z=c.base_height;oh=c.opening_height;env=envelope(c);face=env.front_y
    title,number=sign_text(c)
    W=min(7.6,max(4.4,c.width*.17));H=round(W/4.8,3)
    zc=z+oh+.745+.32+H/2
    zc=min(zc,roof_level(c,W/2+.3)-.35-H/2)          # stays inside the gable field
    x0,x1=-W/2,W/2;xb=x0+H if number else x0
    yc0,yc1=face,face-.06                             # recessed carrier (shadow gap)
    yp0,yp1=yc1,yc1-.04                               # panel
    inset=.10*H
    m.box('HG_SignCarrier',(0,(yc0+yc1)/2,zc),(W-2*inset,yc0-yc1,H-2*inset),'SteelDark','DETAIL',.002)
    if number:
        m.box('HG_SignNumberBlock',((x0+xb)/2,(yp0+yp1)/2,zc),(xb-x0,yp0-yp1,H),'Yellow','DETAIL',.002)
    m.box('HG_SignField',((xb+x1)/2,(yp0+yp1)/2,zc),(x1-xb,yp0-yp1,H),'HG_SignFace','DETAIL',.002)
    f=.024;fy=(yp0+yp1-.006)/2;fd=yp0-yp1+.006           # frame 3 mm proud of the face
    fr=m.p('HG_SignFrame','DETAIL',.002)
    for zz in (zc-H/2-f/2,zc+H/2+f/2):fr.box((0,fy,zz),(W+2*f,fd,f),'HG_Alu')
    for xx in (x0-f/2,x1+f/2):fr.box((xx,fy,zc),(f,fd,H),'HG_Alu')
    face_y=yp1
    pad=.20*H;xt=xb+pad;xr=x1-.16*H
    if number:
        e=.010
        m.label(number,((x0+xb)/2,face_y-e,zc),H*.6,'HG_SignInk',name='HangarNumber',extrude=e,bevel=.002,
                font='BigShoulders-Bold.ttf',anchor='CENTER',cap_height=.58*H,max_width=.74*H)
    e=.008
    m.label(title,(xt,face_y-e,zc+.13*H),H*.4,'White',name='HangarIdentity',extrude=e,bevel=.0015,
            font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.32*H,max_width=xr-xt,tracking=1.04)
    m.box('HG_SignRule',((xt+xr)/2,face_y-.002,zc-.095*H),(xr-xt,.004,max(.006,.011*H)),'HG_Alu','DETAIL',.001)
    if c.subtitle.strip():
        e=.004
        m.label(c.subtitle.strip().upper(),(xt,face_y-e,zc-.255*H),H*.15,'HG_SignSub',name='HangarSubtitle',extrude=e,
                font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.10*H,max_width=xr-xt,tracking=1.45)
    m.hangar_meta['identity_sign_design']=dict(title=title,number=number,subtitle=c.subtitle.strip().upper(),
        width_m=W,height_m=H,center=(0.,face_y,zc),grid_unit_m=H)

def _gates(m,c):
    """Top-hung telescopic main gate: steel leaves, door head (pelmet, canopy, fascia), door houses.

    Leaf section, local to each leaf (metres; whole-mm planes, so no two same-facing faces share a plane):
      q  across the leaf from its LEADING (inner) edge 0 to its trailing edge lw; L and R leaves mirror
      v  depth from the track centreline, EXTERIOR NEGATIVE; the whole leaf stays in [-.100,+.100]
         (neighbouring tracks are .24 apart; track 0 also clears a .36 m pocket wall at v=+.07);
         above h=lh-.025 it keeps |v|<=.069 (rail webs), below h=.006 it avoids |v| .030-.054 (guide lips)
      h  height above the leaf bottom z0 (= base+.025); the floor is h=-.025
    """
    oh=c.opening_height;z=c.base_height;w=c.width;a=w/2;top=z+oh;n=c.gate_leaves//2;env=envelope(c)
    lh=oh-.06;ht=lh-.125                      # leaf height; seat of the leaf head flashing
    LEAD,TRAIL=.23,.12                        # flat stile zones: lock stile with pocket handle / trailing stile
    GIRT,CELL=1.70,2.40                       # max sheet span between frame rails / max cell before a stud
    RIB=.40 if c.detail=='DRAFT' else .25     # target rib pitch; the sheet keeps a whole number of ribs
    # Rib cap: leaves over ~6.3 m (4 leaves on a 25+ m opening) widen the pitch instead of adding ribs.
    # Budget exception: glazed leaves wider than ~5.2 m on tall openings (no preset) pass ~2.5k tris
    # pre-bevel, up to ~2.8k at 7.9 m; the 12 presets peak at 2.34k (MRO leading leaf).
    RIBS=24
    glz=None
    if c.gate_glazing:                        # vision band (bottom, top) above the leaf bottom
        gt=lh-.55;glz=(gt-min(1.20,max(.80,.17*lh)),gt)
    yo=-.43-(n-1)*.24                         # outermost track: pelmet and door houses sit in front of it

    def stencil_digit(d,W=.12,H=.30,t=.026,g=.007):
        # Seven-segment stencil numeral as (x0, z0, x1, z1) strokes in a W x H cell: t-wide strokes,
        # g-wide stencil breaks where the bars meet the stems; '1' is one centred stem.
        if d==1:return [((W-t)/2,H/2+g/2,(W+t)/2,H),((W-t)/2,0.,(W+t)/2,H/2-g/2)]
        bars=dict(a=(t+g,H-t,W-t-g,H),g=(t+g,(H-t)/2,W-t-g,(H+t)/2),d=(t+g,0.,W-t-g,t),
                  f=(0.,H/2+g/2,t,H),b=(W-t,H/2+g/2,W,H),e=(0.,0.,t,H/2-g/2),c=(W-t,0.,W,H/2-g/2))
        return [bars[k] for k in ('abcdef','bc','abged','abgcd','fgbc','afgcd','afgecd','abc','abcdefg','abcdfg')[d]]

    def ribbed(p,origin,axes,u0,u1,crest,pan,back,pitch,length,mat,most=999,liner=None):
        # Trapezoidal profiled skin, 40 mm crests on 100 mm rib bases at an even pitch, flat back;
        # one closed shell extruded along axes[2], its ear-clipped caps end inside flashings/trims.
        k=min(most,max(3,round((u1-u0)/pitch)));P=(u1-u0)/k;prof=[(u0,pan)]
        for i in range(k):
            mc=u0+(i+.5)*P;prof+=[(mc-.050,pan),(mc-.020,crest),(mc+.020,crest),(mc+.050,pan)]
        prof+=[(u1,pan),(u1,back),(u0,back)]
        f0=len(p.faces);p.prism(prof,origin,axes,length,mat)
        if liner:
            # Insulated panel: the shell's flat back face IS the liner (own material on the same
            # closed shell), so no liner box hides behind it and no buried faces take texture or
            # lightmap space. prism() emits 2*(n-2) cap triangles, then one side face per profile
            # edge of the (counter-clockwise) profile.
            if A.polygon_area(prof)<0:prof.reverse()
            nn=len(prof);b=next(i for i in range(nn) if prof[i][1]==back==prof[(i+1)%nn][1])
            if liner not in p.material_names:p.material_names.append(liner)
            p.material_ids[f0+2*(nn-2)+b]=p.material_names.index(liner)

    def cap(p,X,y,z0,q0,q1,hb,vb,mat,drip=.040):
        # Weathering flashing: drip leg in front of the ribs, solid wedge sloping back up to vb.
        # Sheet ends finish inside the wedge, so ribs rise out of the slope with no open ends.
        rise=.003+(vb+.100)*.52
        prof=[(-.100,hb-drip),(-.094,hb-drip),(-.094,hb-.005),(vb,hb-.005),(vb,hb+rise),(-.100,hb+.003)]
        p.prism(prof,(X(q0),y,z0),((0,1,0),(0,0,1),(1. if X(1.)>X(0.) else -1.,0,0)),q1-q0,mat)

    def leaf(p,motion):
        """One telescopic leaf; everything that moves with it is in part p (pivot = closed pose)."""
        xc,y,z0=motion['closed'];lw=motion['width'];j=motion['track']
        s=-1. if motion['side']=='L' else 1.;xin=xc-s*lw/2
        X=lambda q:xin+s*q
        def bx(q0,q1,v0,v1,h0,h1,mat):
            x0,x1=X(q0),X(q1)
            p.box(((x0+x1)/2,y+(v0+v1)/2,z0+(h0+h1)/2),(abs(x1-x0),v1-v0,h1-h0),mat)
        def cyl(qa,va,ha,qb,vb,hb,r,mat,seg=8):
            p.cylinder((X(qa),y+va,z0+ha),(X(qb),y+vb,z0+hb),r,mat,seg)
        wl,wt=LEAD,TRAIL
        # ---- welded frame, exposed on the inside face: painted RHS stiles, girts, studs and K-bracing,
        #      galvanised bottom rail and top hanger rail
        bx(0,lw,-.093,.061,.008,.128,'Galvanized')                       # bottom rail
        bx(.001,lw-.001,-.064,.061,lh-.140,lh,'Galvanized')             # top hanger rail (trolleys sit on it)
        for q0 in (0.,lw-.12):bx(q0,q0+.12,-.018,.062,.128,lh-.140,'SteelDark')   # stiles 120x80 RHS
        fixed=[(.008,.128),(1.57,1.67)]+([(glz[0]-.05,glz[0]+.05),(glz[1]-.05,glz[1]+.05)] if glz else [])+[(lh-.14,lh)]
        rails=[];rows=[]
        for (a0,a1),(b0,b1) in zip(fixed,fixed[1:]):
            if glz and abs(a0-(glz[0]-.05))<1e-9:continue                # vision band: glazing bars, no girts
            gap=b0-a1;k=max(0,ceil(gap/GIRT)-1);lo=a1
            for i in range(k):
                cz=a1+gap*(i+1)/(k+1);rails.append((cz-.05,cz+.05));rows.append((lo,cz-.05));lo=cz+.05
            rows.append((lo,b0))
        for g0,g1 in rails+fixed[1:-1]:bx(.119,lw-.119,-.017,.055,g0,g1,'SteelDark')   # girts, handle girt, transoms
        cells=max(1,ceil((lw-.24)/CELL));qs=[.12+(lw-.24)*i/cells for i in range(cells+1)]
        zones=[(.128,glz[0]-.05),(glz[1]+.05,lh-.14)] if glz else [(.128,lh-.14)]
        for qk in qs[1:-1]:
            for za,zb in zones:bx(qk-.04,qk+.04,-.016,.050,za,zb,'SteelDark')         # studs behind the girts
        for r,(ha,hb) in enumerate(rows):
            if hb-ha<.5:continue
            for i in range(cells):                                       # zig-zag bracing, row 0 rises away from the pull bar
                qa=qs[i]+(0. if i==0 else .04);qb=qs[i+1]-(0. if i==cells-1 else .04)
                e0,e1=((qa,ha),(qb,hb)) if (r+i)%2==0 else ((qa,hb),(qb,ha))
                p.beam((X(e0[0]),y+.024,z0+e0[1]),(X(e1[0]),y+.024,z0+e1[1]),.040,.060,'SteelDark')
        # ---- exterior: insulated panels between flat stile covers, flashings with drips
        sheet=[(.124,glz[0]-.002),(glz[1]-.002,ht-.002)] if glz else [(.124,ht-.002)]
        for h0,h1 in sheet:          # 35 mm trapezoid (crest -.092, pan -.057), liner face at -.016 bearing on the frame
            ribbed(p,(xin,y,z0+h0),((s,0,0),(0,1,0),(0,0,1)),wl-.021,lw-wt+.021,-.092,-.057,-.016,RIB,h1-h0,'HG_Gate',RIBS,'HG_GateLiner')
        hp0,hp1=.95,1.35                                                  # recessed pull-handle pocket
        for q0,q1,h0,h1 in ((.002,wl,.120,hp0),(.002,wl,hp1,ht),(.002,.130,hp0,hp1),(.212,wl,hp0,hp1),(lw-wt-.002,lw-.002,.120,ht)):
            bx(q0,q1,-.094,-.015,h0,h1,'HG_GateTrim')                    # folded stile covers
        bx(.130,.212,-.060,-.015,hp0,hp1,'SteelDark')                    # pocket back
        cyl(.170,-.078,hp0-.010,.170,-.078,hp1+.010,.011,'Galvanized')   # grip bar, ends buried in the cover
        cap(p,X,y,z0,0.,lw,.320,-.056,'Galvanized',drip=.308)            # galvanised kick plate
        cap(p,X,y,z0,0.,lw+.040,ht,-.063,'HG_GateTrim')                  # leaf head flashing, over the astragal
        if glz:
            gb,gt=glz;g0,g1=wl-.005,lw-wt+.005
            cap(p,X,y,z0,g0,g1,gb,-.056,'HG_GateTrim')                   # sill with drip
            cap(p,X,y,z0,g0,g1,gt,-.056,'HG_GateTrim')                   # head over the glazing
            bx(g0+.001,g1-.001,-.070,-.030,gb+.020,gb+.060,'HG_GateAlu') # glazing channels
            bx(g0+.001,g1-.001,-.070,-.030,gt-.045,gt-.005,'HG_GateAlu')
            bx(wl-.010,lw-wt+.010,-.058,-.042,gb+.040,gt-.025,'HG_GatePolycarb')   # 16 mm opal multiwall polycarbonate
            wg=lw-wl-wt;npn=max(1,ceil(wg/1.20))
            for i in range(1,npn):
                qb=wl+wg*i/npn
                bx(qb-.025,qb+.025,-.080,-.057,gb+.060,gt-.045,'HG_GateAlu')   # pressure caps outside
                bx(qb-.020,qb+.020,-.043,.030,gb+.050,gt-.050,'HG_GateAlu')    # glazing bars inside
        # ---- seals: brushes either side of the floor guide (exterior one 3 mm off the floor, clear of the
        #      2.5 mm apron paint), top brushes 1-2 mm inside the rail webs
        bx(.001,lw-.001,-.098,-.056,-.006,.012,'Galvanized');bx(.003,lw-.003,-.090,-.062,-.022,-.006,'Rubber')
        bx(.001,lw-.001,.054,.064,-.006,.008,'Galvanized');bx(.003,lw-.003,.055,.063,-.021,-.006,'Rubber')
        bx(.003,lw-.003,-.069,-.063,lh-.035,lh-.006,'Rubber');bx(.003,lw-.003,.060,.068,lh-.035,lh-.006,'Rubber')
        if j==0:
            bx(-.005,.010,-.050,.040,.014,lh-.150,'Rubber')                # meeting seal, 2 mm gap at the centre
        else:
            bx(-.040,.080,.060,.100,.014,lh-.141,'HG_GateTrim')            # rebate behind the inner neighbour's astragal
        # Trailing astragal on the exterior face: laps the outer neighbour's rebate; on the outermost leaf it
        # runs behind the door-house jamb trim and rubber blade. Labyrinths, no sightline into the hangar.
        # Its top tucks 1 mm under the head flashing's drip; the rebate stops 1 mm under the hanger rail.
        bx(lw-.030,lw+.040,-.099,-.070,.014,ht-.041,'HG_GateTrim')
        # ---- handles and locks
        cyl(.180,.042,.90,.180,.042,1.50,.014,'Galvanized')               # inside pull bar, 44 mm knuckle space
        for hh in (.93,1.47):bx(.118,.180,.034,.050,hh-.02,hh+.02,'Galvanized')   # stand-off brackets
        if j==0:
            cyl(.135,.062,.006,.135,.062,1.20,.006,'Galvanized')          # drop bolt (retracted) ...
            cyl(.135,.060,.80,.235,.060,.80,.007,'Galvanized')            # ... its lever below the pull bar
            for hh in (.25,.65,1.15):bx(.118,.143,.050,.066,hh-.02,hh+.02,'Galvanized')
            # hazard chevrons on the leading stile: 45 deg, 100 mm, butt-joined black/yellow pieces;
            # q mirrors, so the two leading leaves form a V at the meeting line
            qa,qb,b,st=.012,.112,.100,.1414;N=13;h0=.36
            pieces=[[(qa,h0),(qb,h0),(qb,h0+b)]]
            for k in range(N):pieces.append([(qa,h0+k*st),(qb,h0+k*st+b),(qb,h0+(k+1)*st+b),(qa,h0+(k+1)*st)])
            pieces.append([(qa,h0+N*st),(qb,h0+N*st+b),(qa,h0+N*st+b)])
            for k,pc in enumerate(pieces):
                p.prism(pc,(xin,y-.094,z0),((s,0,0),(0,0,1),(0,-1,0)),.006,'HG_GateHazardInk' if k%2==0 else 'HG_GateHazard')
        if c.detail!='DRAFT':
            # Leaf number for maintenance, 1..2n left to right seen from outside: condensed 120 x 300 mm
            # stencil strokes raised 5 mm on the leading-stile cover above the chevrons, kept to its far side
            # so the two meeting-leaf numbers stand 17 cm apart; laid out in world x (never mirrored).
            xl=min(X(.085),X(.205))
            for sa,ha,sb,hb in stencil_digit(n-j if s<0 else n+1+j):
                p.box((xl+(sa+sb)/2,y-.0965,z0+2.70+(ha+hb)/2),(sb-sa,.005,hb-ha),'White')
        if c.detail!='DRAFT' and c.fasteners:                            # cover screws at every rail line
            lv=[(g0+g1)/2 for g0,g1 in rails+fixed[1:-1]]+[ht-.06]
            for qq in (.221,lw-.060):
                for hh in lv:cyl(qq,-.093,hh,qq,-.099,hh,.008,'Galvanized',6)
        return X

    def head():
        """Door head: header, canopy with folded fascia, pelmet over the leaf tops, door houses."""
        C=MG.ModuleModel;X,fy=env.outside_x,env.front_y
        u0,u1=c.opening_width/2+.005,a+.091;ue=u1+.083     # door house: jamb line, end plate, end plinth face
        cd=.44+(n-1)*.24;Le=X+.068                         # canopy ends 68 mm past the corner caps' outer planes
        # Header ends 2 mm inside the door-house end plates (no step proud of them at the corners).
        m.box('HG_GateHeader',(0,-.12,top+.3225),(2*(a+.089),.32,.645),'SteelDark','STRUCTURE',.004)
        yf,zt=-.505-cd,top+.745                            # 330 mm folded fascia, 50 mm upstand, drip lip
        # Slab from the fascia's back leg to 9 mm in front of the wall crests (it no longer runs through
        # the cladding, corner caps and end frame); a galvanised soffit liner 1 mm under it spans the
        # pelmet zone between the door-house end plates, 1 mm in front of the header face.
        m.box('HG_RailCanopy',(0,(yf+.040+fy-.009)/2,top+.695),(2*Le,fy-.049-yf,.10),'SteelDark','FACADE',.005)
        m.box('HG_CanopySoffit',(0,(yo-.681)/2,top+.635),(2*u1,.119-yo,.018),'Galvanized','DETAIL',.001)
        m.p('HG_CanopyFascia','FACADE',.003).prism([(yf-.022,zt-.280),(yf+.040,zt-.280),(yf+.040,zt+.050),
            (yf-.010,zt+.050),(yf-.010,zt-.262),(yf-.022,zt-.262)],(-Le,0,0),C.YZX,2*Le,'SteelDark')
        m.box('HG_PortalAccent',(0,yf-.013,zt-.115),(2*Le,.006,.050),'Yellow','DETAIL',.001)
        # 2 mm end caps over the fascia profile and the slab end; abutment flashing where the slab meets
        # the facade: 100 mm leg on the slab, 150 mm upstand 1 mm in front of the corner-cap legs that
        # covers the open rib ends (kept under the verge trims at the corners).
        cap_end=[(yf-.022,zt-.280),(yf+.040,zt-.280),(yf+.040,zt-.100),(fy-.009,zt-.100),(fy-.009,zt),(yf+.040,zt),
                 (yf+.040,zt+.050),(yf-.010,zt+.050),(yf-.010,zt-.262),(yf-.022,zt-.262)]
        for sx in (-1.,1.):
            m.p('HG_CanopyEndCaps','FACADE',.001).prism(cap_end,(sx*Le,0,0),((0,1,0),(0,0,1),(sx,0,0)),.002,'SteelDark')
        hu=min(zt+.152,z+c.eave_height-.12)
        m.p('HG_CanopyFlashing','DETAIL',0.).prism([(fy-.109,zt),(fy-.009,zt),(fy-.009,hu),(fy-.011,hu),
            (fy-.011,zt+.002),(fy-.109,zt+.002)],(-(X+.008),0,0),C.YZX,2*(X+.008),'HG_WallTrim')
        # Pelmet (track cover) in front of the outermost track: hides girders, hangers and the outer rail
        # web; its return laps over the leaf tops at the rail-web bottom line (top-.060), 3 mm short of the
        # outer web and 24 mm clear of the leaf, so it takes no opening height the rails do not already take.
        h1=top-.060
        m.p('HG_GateTrackCover','FACADE',.002).prism([(yo-.150,h1),(yo-.093,h1),(yo-.093,h1+.008),
            (yo-.144,h1+.008),(yo-.144,top+.625),(yo-.150,top+.625)],(-u1,0,0),C.YZX,2*u1,'SteelDark')
        # Amber warning beacons on the pelmet above each jamb (wall bracket, base, lens, cap) and a
        # push-button station (open / close / stop) with a rain hood on the left door-house front.
        bc=m.p('HG_GateBeacons','DETAIL',.001);zb=top+.20;yb=yo-.235
        for sx in (-1.,1.):
            xb=sx*(c.opening_width/2+.30)
            bc.box((xb,yo-.153,zb),(.10,.006,.12),'SteelDark')
            bc.box((xb,yo-.223,zb-.045),(.05,.134,.03),'SteelDark')
            bc.cylinder((xb,yb,zb-.030),(xb,yb,zb-.005),.050,'SteelDark',12)
            bc.cylinder((xb,yb,zb-.005),(xb,yb,zb+.115),.044,'HG_GateBeacon',12)
            bc.cylinder((xb,yb,zb+.115),(xb,yb,zb+.130),.047,'SteelDark',12)
        cs=m.p('HG_GateControls','DETAIL',.002);xc,zc,yc=-(c.opening_width/2+.45),z+1.40,yo-.145
        cs.box((xc,yc-.060,zc),(.25,.12,.35),'SteelDark')
        cs.box((xc,yc-.075,zc+.181),(.27,.15,.012),'SteelDark')
        for dz,mat in ((.08,'Yellow'),(0.,'Rubber'),(-.08,'Red')):
            cs.cylinder((xc,yc-.120,zc+dz),(xc,yc-.135,zc+dz),.018,mat,8)
        # Door houses: clad pocket fronts flush with the pelmet face, enclosing the parked leaves. They
        # start 5 mm outside the opening line (no loss of clear width); at the jamb the outermost leaf's
        # astragal runs behind the jamb trim and a rubber blade, closing the slot into the hangar.
        # Base as on the building: an L-shaped .48 m concrete plinth under the front and the end, 46 mm
        # proud of the crests, the building's drip flashing mitred round it, sheets from CLAD_BASE; a
        # sealed movement joint where the end plinth meets the facade plinth, under the facade drip.
        # Ends: vertical-rib sheet on a backing plate between the corner angle and a rear end trim
        # 1 mm in front of the corner cap. Trims are colour-matched; the jamb trim stays dark with the pelmet.
        # Trim feet start at z+.495 and lap 1-4 mm into the drip flashing, as the building's corner caps do.
        hs=m.p('HG_GateHouses','FACADE',.002);pl=m.p('HG_GateHousePlinths','FACADE',.004)
        fl=m.p('HG_GateHouseFlashings','DETAIL',0.);ce=yo-.144             # crest plane of the house fronts
        for sx in (-1.,1.):
            def hbx(ua,ub,v0,v1,za,zb,mat):
                hs.box((sx*(ua+ub)/2,yo+(v0+v1)/2,(za+zb)/2),(ub-ua,v1-v0,zb-za),mat)
            hbx(u0,u0+.10,-.150,-.110,z,h1,'SteelDark')                  # jamb trim: steel post beside the plinth end
            hbx(u0,u0+.030,-.110,-.103,z+.003,h1-.004,'Rubber')          # jamb blade, 3 mm off the leaf band
            hbx(u1-.10,u1,-.150,-.110,z+.495,h1,'HG_WallTrim')           # corner angle, front leg
            hbx(u1,u1+.006,-.150,fy-.009-yo,z+.495,top+.644,'HG_WallTrim')            # end plate (sheet backing)
            hbx(u1+.006,u1+.043,-.150,-.050,z+.495,top+.644,'HG_WallTrim')            # corner angle, side leg
            hbx(u1+.006,u1+.043,fy-.050-yo,fy-.009-yo,z+.495,top+.644,'HG_WallTrim')  # rear end trim
            # 25 mm trapezoid sheets at the wall's .25 pitch, ends buried in the trims: front (crest -.144,
            # pan -.119, back -.113) and end (crest u1+.037, back 1 mm off the plate), 1-2 mm under the tops
            ribbed(hs,(0,yo,z+.50),((sx,0,0),(0,1,0),(0,0,1)),u0+.05,u1-.05,-.144,-.119,-.113,.25,h1-.001-(z+.50),'HG_Wall')
            ribbed(hs,(sx*(u1+.006),0,z+.50),((0,1,0),(-sx,0,0),(0,0,1)),yo-.06,fy-.012,-.031,-.006,-.001,.25,top+.643-(z+.50),'HG_Wall')
            # (1 mm over the apron: on 4-track gates the plinth bridges the trench drain's rim)
            pl.prism([(sx*u,v) for u,v in ((u0+.10,yo-.190),(ue,yo-.190),(ue,fy-.0615),(u1-.030,fy-.0615),(u1-.030,yo-.106),
                (u0+.10,yo-.106))],(0,0,z+.001),A.IDENTITY,.479,'Concrete')
            pl.box((sx*(u1-.030+ue-.006)/2,fy-.05375,z+.225),(ue-.006-u1+.030,.0155,.448),'Rubber')
            # Drip flashing: front run and end return (its back edge 1 mm into the end plate), built to sentinel
            # ends, then mitred on the plan diagonal.
            fl.prism(C.BASE_FLASH,(sx*(u0+.10),ce,z),((0,1,0),(0,0,1),(sx,0,0)),u1+.20-u0-.10,'HG_WallTrim')
            fl.prism(C.BASE_FLASH,(sx*(u1+.038),yo-.40,z),((-sx,0,0),(0,0,1),(0,1,0)),fy-.061-yo+.40,'HG_WallTrim')
            C.shift(fl,lambda v:abs(v[0]-sx*(u1+.20))<1e-6,lambda v:(sx*(u1+.038-(v[1]-ce)),v[1],v[2]))
            C.shift(fl,lambda v:abs(v[1]-(yo-.40))<1e-6,lambda v:(v[0],ce+u1+.038-sx*v[0],v[2]))
        if c.fasteners and c.detail=='HERO':
            # Screws in alternate pans on the facade's girt lines (the house pans sit 25 mm behind the crests).
            fx=m.p('HG_GateHouseFixings','DETAIL',0.);rows=C.girt_rows(z+.58,h1-.166)
            k=max(3,round((u1-u0-.10)/.25));ke=max(3,round((fy+.048-yo)/.25))   # ribbed() rib counts
            for sx in (-1.,1.):
                C.fixings(fx,*sorted((sx*(u0+.05),sx*(u1-.05))),(u1-u0-.10)/k,sx*(u0+.05),rows,
                          frame=((0,yo-.154,0),(1,0,0),(0,1,0)),mat='HG_WallTrim')
                C.fixings(fx,*sorted((sx*(yo-.050),sx*(fy-.050))),(fy+.048-yo)/ke,sx*(yo-.06),rows,
                          frame=((sx*(u1+.047),0,0),(0,sx,0),(-sx,0,0)),mat='HG_WallTrim')

    _track_system(m,c)
    head()
    for motion in gate_motion(c):
        p=m.p('HG_'+motion['id'],'DOOR',.002);p.pivot=motion['closed']
        X=leaf(p,motion)
        x,y,bottom=motion['closed'];lw=motion['width']
        for xx in (x-lw*.32,x+lw*.32):
            _trolley(m,c,p,xx,y,bottom+lh,top)
            p.box((xx,y,bottom+.004),(.08,.04,.012),'Galvanized')     # guide shoe stem into the bottom rail
        if motion['track']==0:
            # Floor keeper for the drop bolt at the closed pose, 1 mm outside the guide channel lips.
            m.p('HG_GateFloorKeepers','DETAIL',0.).cylinder((X(.135),y+.062,z-.006),(X(.135),y+.062,z+.0015),.011,'Galvanized',12)
        dct=dict(motion);dct['part']=p.name;m.doors.append(dct)
    m.port('AIRCRAFT_FRONT',(0,-.20,z),-pi/2,c.opening_width,'HANGAR')
    m.hangar_meta['gate_clear_width_at_pose_m']=gate_clear_width(c)
    m.hangar_meta['gate_clear_height_m']=c.opening_height-.01
    m.hangar_meta['gate_clearance_scope']='Visual aperture measurement only; not aircraft movement or safety certification.'


def _floor(m,c):
    a,d,z=c.width/2,c.depth,c.base_height
    dr=(-c.opening_width/2-1.,-1.65,c.opening_width/2+1.,-1.23)
    m.hangar_meta['drain_cutout_design']=list(dr) if c.drain else None
    m.hangar_meta['surface_owner']='MB01' if c.local_ground else 'EXTERNAL'
    if not c.local_ground:
        if c.drain:m.notes.append('External floor: drain is a cutout request only; grate/floor/landings are not generated.')
        return
    env=envelope(c)
    xlo,xhi=-env.floor_x,env.floor_x;ylo,yhi=-c.apron_depth,env.floor_back_y
    nx=max(4,ceil((xhi-xlo)/4.2));ny=max(4,ceil(d/4.2))
    xs=[xlo+(xhi-xlo)*i/nx for i in range(nx+1)]
    ys=[ylo,0.]+[d*i/ny for i in range(1,ny+1)]+[yhi]
    for i in range(nx):
        for j in range(len(ys)-1):
            rect=(xs[i]+.007,ys[j]+.007,xs[i+1]-.007,ys[j+1]-.007)
            pieces=rectangle_difference(rect,dr) if c.drain else [rect]
            role='EXPOSED' if (ys[j]+ys[j+1])/2<0 else 'INDOOR'
            variant=stable_variant(c,f'floor-{i}-{j}',4)
            mat=f'HG_Concrete_{role}_{variant}'
            for rr in pieces:
                x0,y0,x1,y1=rr
                m.box('HG_Floor_'+role,((x0+x1)/2,(y0+y1)/2,z-.09),(x1-x0,y1-y0,.18),mat,'GROUND',.002)
                m.hangar_meta['floor_rectangles_design'].append(list(rr))
    for rr in rectangle_difference((xlo,ylo,xhi,yhi),dr) if c.drain else [(xlo,ylo,xhi,yhi)]:
        x0,y0,x1,y1=rr
        m.box('HG_JointBed',((x0+x1)/2,(y0+y1)/2,z-.205),(x1-x0,y1-y0,.05),'Joint','GROUND',0.)
    if c.drain:
        xa,ya,xb,yb=dr
        # Channel bottom is below the surrounding slab. Rim rests at the cut edges.
        m.box('HG_DrainTrough',((xa+xb)/2,(ya+yb)/2,z-.235),(xb-xa,yb-ya,.05),'SteelDark','GROUND',.002)
        for yy in (ya+.014,yb-.014):
            # Rim runs between the two .05 m end blocks rather than through them.
            m.box('HG_DrainRim',((xa+xb)/2,yy,z-.027),(xb-xa-.10,.028,.055),'Galvanized','DETAIL',.002)
        count=ceil((xb-xa)/.105)
        grate=m.p('HG_DrainGrating','DETAIL',.001)
        for i in range(count):
            xx=xa+.06+i*(xb-xa-.12)/max(1,count-1)
            grate.box((xx,(ya+yb)/2,z-.018),(.022,yb-ya-.063,.028),'Galvanized')
        for xx in (xa+.025,xb-.025):
            m.box('HG_DrainEnds',(xx,(ya+yb)/2,z-.10),(.05,yb-ya,.19),'Galvanized','GROUND',.002)
    # Paint on real floor surfaces only. Longitudinal markings do not cover the drain.
    p=m.p('HG_ApronMarkings','MARKINGS',0.)
    segments=[(-c.apron_depth+.25,-1.71),(-1.16,-.12)] if c.drain else [(-c.apron_depth+.25,-.12)]
    for lo,hi in segments:
        if hi>lo:p.floor_polygon([(-.045,lo),(.045,lo),(.045,hi),(-.045,hi)],z+.0025,'Yellow')
    for j in range(max(1,int(d*.75/2.6))):
        yy=.9+j*2.6
        p.floor_polygon([(-.04,yy),(.04,yy),(.04,yy+1.25),(-.04,yy+1.25)],z+.0025,'Yellow')
    # Service boundary is a design graphic, not a regulation-specific marking set.
    for side in (-1,1):
        x=side*(a-2.0)
        p.floor_polygon([(x-.03,.65),(x+.03,.65),(x+.03,d-.60),(x-.03,d-.60)],z+.0025,'White')


def _loading_dock(m,c):
    """Rear loading dock: the floor level continues as a platform past the rear wall and
    the service yard sits 1.15 m lower, reached by a 1:8 ramp. Door sills stay at floor
    level, so rear personnel doors open onto the platform."""
    if not c.loading_dock:return
    env=envelope(c);z=c.base_height;h=1.15;depth=3.2;width=2*env.outside_x-4.
    y0=env.floor_back_y if c.local_ground else env.back_y
    m.box('HG_DockPlatform',(0.,y0+depth/2,z-(h+.18)/2),(width,depth,h+.18),'HG_Concrete_INDOOR_0','GROUND',.004)
    m.box('HG_DockNosing',(0.,y0+depth-.04,z-.04),(width,.08,.08),'Galvanized','DETAIL',.002)
    ramp=h*8.;xb=-width/2;xa=xb-ramp
    m.p('HG_DockRamp','GROUND',.004).prism([(xa,z-h-.18),(xb,z-h-.18),(xb,z)],(0,y0,0),((1,0,0),(0,0,1),(0,1,0)),depth,'HG_Concrete_EXPOSED_1')
    m.box('HG_DockRampKerb',(xb-ramp/2,y0+.08,z-h/2-.04),(ramp,.16,h+.08),'HG_Concrete_EXPOSED_0','GROUND',.004)
    yard_x0,yard_x1=xa-1.,width/2+2.
    m.box('HG_DockYard',((yard_x0+yard_x1)/2,y0+depth+3.,z-h-.09),(yard_x1-yard_x0,6.,.18),'HG_Concrete_EXPOSED_2','GROUND',.002)
    n=max(2,int(width//2.6))
    for i in range(n):
        x=-width/2+(i+.5)*width/n
        m.box('HG_DockBumpers',(x,y0+depth+.06,z-.25),(.32,.12,.40),'Rubber','DETAIL',0.)
        if i%2==0:m.box('HG_DockLevellers',(x,y0+depth-.92,z+.012),(1.9,1.6,.024),'SteelDark','DETAIL',.002)
    for x in (-width/2+.35,width/2-.35):
        m.p('HG_DockBollards','DETAIL',0.).cylinder((x,y0+.30,z),(x,y0+.30,z+.9),.06,'Yellow',12)
    m.box('HG_DockGuard',(width/2-.03,y0+depth/2,z+.55),(.06,depth,1.1),'Galvanized','DETAIL',.002)
    m.hangar_meta['loading_dock_design']=dict(width_m=width,depth_m=depth,height_m=h,ramp_m=ramp,y0=y0)
    m.port('DOCK_SERVICE',(0.,y0+depth+3.,z-h),pi/2,width,'SERVICE_ROAD')


def _landings_and_ports(m,c):
    z=c.base_height
    for entry in m.hangar_meta['personnel_openings_design']:
        x,y,_=entry['center'];nx,ny,_=entry['normal'];width=c.walkway_width
        if c.loading_dock and ny>.5:
            continue  # rear doors open onto the dock platform; the dock owns that edge
        # Canonical module outward normal converted into design. The entry sits at exterior plane.
        if c.local_ground and c.landings:
            # Side apron ends at a+.65; rear apron ends at d+.24.
            # Match the correct edge instead of leaving a .41 m rear landing gap.
            start=.43 if abs(nx)>.5 else .02;end=2.03
            cx,cy=x+nx*(start+end)/2,y+ny*(start+end)/2
            dims=(end-start,width,.15) if abs(nx)>.5 else (width,end-start,.15)
            m.box('HG_Landing_'+entry['id'],(cx,cy,z-.075),dims,'HG_Concrete_INDOOR_0','GROUND',.005)
            from math import atan2
            m.port('PERSONNEL_'+entry['id'],(x+nx*end,y+ny*end,0.),atan2(ny,nx),width,'PEDESTRIAN')
        else:
            from math import atan2
            m.port('OPENING_'+entry['id'],(x,y,z),atan2(ny,nx),entry.get('clear_width_m',1.03),'PEDESTRIAN_OPENING')


def _gutters(m,c):
    """Fascia-hung box gutter: drip flashing kicks into it, hidden hangers every ~1.2 m,
    stop ends 50 mm past the verges, running outlets with 45-degree swan necks to downpipes
    on band clamps, shoes over a gully on the apron."""
    if not c.gutters:return
    env=envelope(c);z=c.base_height;rx=env.roof_x;rl=roof_level(c,rx);hero=c.detail!='DRAFT'
    y0,y1=env.roof_y0-.05,env.roof_y1+.05;top=rl-.072
    g=m.p('HG_Gutters','DETAIL',.001);hang=m.p('HG_GutterHangers','DETAIL',.001)
    pipes=m.p('HG_Downpipes','DETAIL',0.);clamps=m.p('HG_PipeClamps','DETAIL',.001)
    for side in (-1,1):
        X=lambda u:side*(rx+.001+u)
        g.prism([(X(u),top+v) for u,v in GUTTER],(0,y0,0),XZ,y1-y0,'Galvanized')
        for ye in (y0,y1):
            g.prism([(X(u),top+v) for u,v in GUTTER_END],(0,ye-.002,0),XZ,.004,'Galvanized')
        if hero:
            nh=max(2,int((y1-y0-.5)/1.2+.5))+1     # fascia brackets at ~1.2 m
            for k in range(nh):
                y=y0+.25+k*(y1-y0-.5)/(nh-1)
                hang.beam((X(-.006),y,top+.001),(X(.214),y,top-.007),.025,.004,'Galvanized')
        px=side*(env.outside_x+.14);xo=X(.088);h45=abs(xo-px);meta=m.hangar_meta['roof_design']
        lines=_downpipe_lines(m,c,env,side,z+.10,top-.20,meta['downpipe_conflicts'])
        meta['downpipes_design']+=[dict(side=side,y=y) for y in lines]
        for y in lines:
            g.cylinder((xo,y,top-.140),(xo,y,top-.250),.046,'Galvanized',8)
            zt=top-.30;pipes.pipe([(xo,y,top-.20),(xo,y,zt),(px,y,zt-h45),(px,y,z+.33),(px+side*.15,y,z+.18)],
                                  .055,'Galvanized',8 if c.detail=='DRAFT' else 12)
            lo,hi=z+.9,zt-h45-.25;nc=max(2,ceil((hi-lo)/2.)+1)
            for k in range(nc):
                zz=lo+(hi-lo)*k/(nc-1)
                # Round band (octagon inscribed radius 57 mm clears the 55 mm pipe) on a stand-off
                # stem bedded 4 mm into the cladding and 2 mm into the band.
                clamps.cylinder((px,y,zz-.0175),(px,y,zz+.0175),.062,'SteelDark',8)
                so=abs(px)-.06-(env.outside_x-.004)
                clamps.box((side*(env.outside_x-.004+so/2),y,zz),(so,.03,.03),'SteelDark')
            if c.local_ground and hero:
                gx=side*(env.outside_x+.285)
                m.box('HG_RainGullies',(gx,y,z+.022),(.28,.28,.05),'HG_Concrete_EXPOSED_0','GROUND',.001)
                m.box('HG_RainGullies',(gx,y,z+.049),(.20,.20,.006),'Galvanized','GROUND',.001)


def _services(m,c):
    a,d,z=c.width/2,c.depth,c.base_height;bp=d/c.bays
    if c.services:
        for side,sequence in ((-1,c.panel_sequence('LEFT')),(1,c.panel_sequence('RIGHT'))):
            x=side*(a-.72);tz=z+3.65
            p=m.p('HG_CableTray','DETAIL',.002)
            for dx in (-.13,.13):p.box((x+dx,d/2,tz),(.025,d-.75,.08),'Galvanized')
            for i in range(ceil(d/.95)):
                y=.4+i*(d-.8)/max(1,ceil(d/.95)-1)
                p.box((x,y,tz-.029),(.27,.025,.025),'Galvanized')
            m.p('HG_Conduits','DETAIL',0.).pipe([(x+.03,.4,tz+.015),(x+.03,d-.4,tz+.015)],.018,'Rubber',8)
            for i,token in enumerate(sequence):
                if token!='METAL':continue
                y=(i+.5)*bp
                m.box('HG_ServiceCabinets',(side*(a-.52),y,z+1.2),(.35,.85,1.15),'SteelDark','DETAIL',.015)
                m.box('HG_ServiceCabinetFaces',(side*(a-.708),y,z+1.2),(.025,.76,1.03),'HG_Wall','DETAIL',.004)
                m.box('HG_CabinetHandles',(side*(a-.742),y+.23,z+1.24),(.028,.035,.20),'Galvanized','DETAIL',.002)
                break
    if c.fixtures:
        for side in (-1,1):
            x=side*a*.52
            for i in range(c.bays):
                y=(i+.5)*bp;bottom=roof_level(c,x)-1.0
                m.box('HG_LinearLightHousings',(x,y,bottom),(.21,1.72,.105),'SteelDark','DETAIL',.003)
                m.box('HG_LinearDiffusers',(x,y,bottom-.061),(.164,1.59,.017),'LightWarm','DETAIL',.001)
                for dy in (-.58,.58):
                    slope=-side*envelope(c).slope
                    tangent=A.unit((1.,0.,slope));normal=A.unit((-slope,0.,1.))
                    contact=(x,y+dy,roof_level(c,x))
                    shoe_center=A.sub(contact,A.mul(normal,.0125))
                    m.p('HG_LightSuspension','DETAIL',.001).cylinder((x,y+dy,bottom+.052),
                        (shoe_center[0],shoe_center[1],shoe_center[2]),.012,'Galvanized',8)
                    m.box('HG_LightShoe',shoe_center,(.10,.14,.025),'Galvanized','DETAIL',.001,
                        axes=(tangent,(0.,1.,0.),normal))
                m.hangar_meta['light_fixtures_design'].append(dict(position=(x,y,bottom-.08),dimensions=(.17,1.6),watts_artist=55.))
    if c.signage:
        _identity_sign(m,c)
        for entry in m.hangar_meta['personnel_openings_design']:
            x,y,_=entry['center'];nx,ny,_=entry['normal']
            # A shallow perimeter luminaire and neutral door label panel.
            dims=(.065,.38,.13) if abs(nx)>.5 else (.38,.065,.13)
            m.box('HG_PersonnelCanopyLights',(x+nx*.08,y+ny*.08,z+2.65),dims,'LightWarm','DETAIL',.002)


def build(config):
    c=config.checked();m=core.Model(c.legacy_settings())
    m.hangar_config=c
    m.hangar_meta=dict(schema='mb01.hangar_geometry/0.3-alpha.1',version=VERSION,
        standards_status='CGI_ONLY_NOT_CERTIFIED',facade_cells=[],roof_cells=[],roof_supports_design=[],
        personnel_openings_design=[],floor_rectangles_design=[],light_fixtures_design=[],
        nominal_width_m=c.width,nominal_depth_m=c.depth,envelope=envelope(c).to_dict())
    for operation in (_structure,_roof,_facades,_gates,_floor,_loading_dock,_landings_and_ports,_gutters,_services):
        operation(m,c)
    m.notes += ['New closed hangar assembly; original AS07 and legacy buildings are not altered.',
        'Profile sizes, apertures and fixtures are artistic geometry, not structural/fire/military compliance.',
        'Main gate uses explicit telescopic pockets; emitted rest/posed geometry is not a runtime Blueprint.',
        'Textures are existing procedural PBR sources, not newly downloaded scans.',
        'Roof monitor has an actual opening; lights/clearances require native application review.']
    # Source functions write design coordinates. Convert all geometric objects once.
    m.finish()
    m.hangar_meta['axes']='output: +X inward, +Y left, +Z up; *_design records use source width X / depth Y'
    return m


def validation(model):
    r=core.validation(model);r['version']=VERSION;r['family']='HANGAR_STUDIO'
    c=model.hangar_config;meta=model.hangar_meta
    for support in meta['roof_supports_design']:
        if support['top']>support['skin_lower']-.04:
            r['errors'].append('Purlin intrudes into roof skin.')
    cut=meta['drain_cutout_design']
    if c.local_ground and cut:
        for rect in meta['floor_rectangles_design']:
            if min(rect[2],cut[2])-max(rect[0],cut[0])>1e-8 and min(rect[3],cut[3])-max(rect[1],cut[1])>1e-8:
                r['errors'].append('Floor slab covers the drain opening.');break
    if c.roof_type=='MONITOR':
        for cell in meta['roof_cells']:
            if cell['x0']<-1e-8 and cell['x1']>1e-8:
                r['errors'].append('Opaque main roof spans monitor opening.')
    for roller in meta.get('roller_checks_design',[]):
        if roller['actual_z_min']<roller['track_inner_bottom'] or roller['actual_z_max']>roller['track_inner_top']:
            r['errors'].append('Gate roller intersects closed rail web.')
    if abs(gate_clear_width(c,1.)-c.opening_width)>1e-8:
        r['errors'].append('Fully open leaves obstruct the nominal opening.')
    from ..assembly.meshqa import inspect_parts
    qa=inspect_parts(model.parts)
    r['assembly_mesh_qa']=qa
    if qa['status']=='FAIL':
        r['errors'].extend(f"{i['code']}: {i['part']}" for i in qa['issues'] if i['severity']=='ERROR')
    r['hangar']=meta;r['status']='PASS' if not r['errors'] else 'FAIL'
    return r


def pose(model,part):
    return core.door_transform(model,part)

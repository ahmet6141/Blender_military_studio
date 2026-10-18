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
    for source in src.parts:
        role=source.name.split('__')[-1]
        # Rear cells run on into the gable sheet (no eave trim); fixings follow config.fasteners.
        if (rear and role=='EaveTrim') or (role=='CladFixings' and not config.fasteners):
            continue
        part=deepcopy(source)
        part.name='SM_MB01_HG_'+face_id+'__'+role
        mapping[source.name]=part.name
        part.vertices=[tr(v) for v in source.vertices];part.pivot=tr(source.pivot)
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


def _structure(m,c):
    a,d,z=c.width/2,c.depth,c.base_height
    bp=d/c.bays
    for i in range(c.bays+1):
        y=i*bp
        frame=m.p(f'HG_Portal_{i:02d}','STRUCTURE',.004)
        for side in (-1,1):
            x=side*(a-.22)
            frame.prism(A.i_profile(.34,.40,.035,.040),(x,y,z+.105),A.IDENTITY,c.eave_height-.54-.105,'SteelDark')
            _ibeam(frame,(x,y,roof_level(c,x)-.52),(0,y,roof_level(c,0)-.52))
            m.box('HG_BaseShoes',(x,y,z+.055),(.62,.68,.11),'SteelDark','STRUCTURE',.004)
            # Thickening plate is a visible mechanical joint, not a load calculation.
            m.box('HG_EaveConnection',(x,y,roof_level(c,x)-.64),(.48,.46,.26),'Galvanized','DETAIL',.004)
            if c.fasteners and c.detail!='DRAFT':
                p=m.p('HG_Fasteners','DETAIL',.001)
                for dx in (-.23,.23):
                    for dy in (-.25,.25):
                        p.cylinder((x+dx,y+dy,z+.111),(x+dx,y+dy,z+.155),.028,'Galvanized',6)
                        p.cylinder((x+dx,y+dy,z+.108),(x+dx,y+dy,z+.121),.044,'Galvanized',12)
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


def _roof(m,c):
    a,d=c.width/2,c.depth;bp=d/c.bays;env=envelope(c)
    mh=c.monitor_width/2 if c.roof_type=='MONITOR' else 0.
    # Per-bay sheets are distinct assets with one continuous metre-scaled chart.
    for i in range(c.bays):
        ya,yb=env.roof_y0 if i==0 else i*bp,env.roof_y1 if i==c.bays-1 else (i+1)*bp
        for side in (-1,1):
            lo,hi=(-env.roof_x,-mh) if side<0 else (mh,env.roof_x)
            pa,pb=roof_level(c,lo),roof_level(c,hi)
            p=m.p(f'HG_RoofSkin_{i:02d}_{side:+d}','ROOF',.002)
            p.prism([(lo,pa),(hi,pb),(hi,pb+.085),(lo,pa+.085)],(0,ya,0),
                    ((1,0,0),(0,0,1),(0,1,0)),yb-ya,'HG_Roof')
            _roof_uv(p,env.slope)
            m.hangar_meta['roof_cells'].append(dict(id=p.name,x0=lo,x1=hi,y0=ya,y1=yb))
    # Standing seams run downslope and terminate at the correct roof edge.
    pitch=.72 if c.detail=='DRAFT' else .60
    count=max(4,ceil(d/pitch))
    seams=m.p('HG_StandingSeams','DETAIL',.001)
    for i in range(count+1):
        y=env.roof_y0+(env.roof_y1-env.roof_y0)*i/count
        # On a gable the two halves stop 16 mm short of the ridge (under the ridge cap)
        # instead of both ending on the ridge line with coplanar side faces.
        gap=.016 if mh==0. else 0.
        for lo,hi in ((-env.roof_x,-mh-gap),(mh+gap,env.roof_x)):
            seams.beam((lo,y,roof_level(c,lo)+.105),(hi,y,roof_level(c,hi)+.105),.029,.036,'HG_RoofTrim')
    if c.roof_type=='GABLE':
        p=m.p('HG_RidgeCap','ROOF',.002)
        p.prism([(-.24,roof_level(c,0)+.06),(0,roof_level(c,0)+.17),(.24,roof_level(c,0)+.06),
                 (.24,roof_level(c,0)+.10),(0,roof_level(c,0)+.21),(-.24,roof_level(c,0)+.10)],
                 (0,env.roof_y0-.04,0),((1,0,0),(0,0,1),(0,1,0)),env.roof_y1-env.roof_y0+.08,'HG_RoofTrim')
    else:
        sill=roof_level(c,mh)+.04
        meave=roof_level(c,0)+c.monitor_height
        peak=meave+.32
        for i in range(c.bays):
            y0=i*bp+.045;y1=(i+1)*bp-.045
            for s in (-1,1):
                x=s*mh
                m.box(f'HG_MonitorGlass_{i}_{s}',(x,(y0+y1)/2,(sill+meave)/2),(.024,y1-y0,meave-sill-.15),
                      'Glass','GLASS',0.)
                for z in (sill,meave):
                    m.box('HG_MonitorFrames',(x,(y0+y1)/2,z),(.13,y1-y0,.085),'SteelDark','FACADE',.002)
                # 1 cm shorter than the frame rails so the drip's end faces never share a plane with them.
                m.box('HG_MonitorDrip',(x+s*.07,(y0+y1)/2,sill-.045),(.23,y1-y0-.02,.045),'Galvanized','DETAIL',.002)
            for y in (i*bp,):
                for s in (-1,1):
                    # Posts sit 1 cm proud of the .13 m frame rails: flush faces z-fight.
                    m.box('HG_MonitorPosts',(s*mh,y,(roof_level(c,mh)-.51+meave)/2),(.15,.095,meave-(roof_level(c,mh)-.51)),
                          'SteelDark','STRUCTURE',.003)
            for lo,hi,za,zb in ((-mh-.15,0,meave,peak),(0,mh+.15,peak,meave)):
                p=m.p(f'HG_MonitorRoof_{i}_{int(lo==0)}','ROOF',.002)
                p.prism([(lo,za),(hi,zb),(hi,zb+.085),(lo,za+.085)],(0,env.roof_y0 if i==0 else i*bp,0),
                    ((1,0,0),(0,0,1),(0,1,0)),bp+(-env.roof_y0 if i==0 else 0)+(env.roof_y1-d if i==c.bays-1 else 0),'HG_Roof')
                _roof_uv(p,.32/(mh+.15))
        for s in (-1,1):
            m.box('HG_MonitorPosts',(s*mh,d,(roof_level(c,mh)-.51+meave)/2),(.15,.095,meave-roof_level(c,mh)+.51),'SteelDark','STRUCTURE',.003)
        m.box('HG_MonitorCap',(0,(env.roof_y0+env.roof_y1)/2,peak+.12),(.20,env.roof_y1-env.roof_y0+.08,.07),'HG_RoofTrim','DETAIL',.002)
        for y in (env.roof_y0,env.roof_y1-.10):
            profile=[(-mh,roof_level(c,mh)),(0,roof_level(c,0)),(mh,roof_level(c,mh)),(mh,meave),(0,peak),(-mh,meave)]
            m.p('HG_MonitorEndCaps','BODY',.003).prism(profile,(0,y,0),((1,0,0),(0,0,1),(0,1,0)),.10,'HG_Wall')
    # Continuous bargeboard follows the gable; no fake vertical rectangle through the roof.
    for y in (env.roof_y0-.035,env.roof_y1+.035):
        for lo,hi in ((-env.roof_x,0),(0,env.roof_x)):
            m.p('HG_Bargeboards','FACADE',.003).beam((lo,y,roof_level(c,lo)+.015),(hi,y,roof_level(c,hi)+.015),.15,.20,'SteelDark')


def _facades(m,c):
    a,d,z=c.width/2,c.depth,c.base_height;bp=d/c.bays;env=envelope(c)
    for side,label in ((-1,'LEFT'),(1,'RIGHT')):
        for i,token in enumerate(c.panel_sequence(label)):
            axes=((-side,0,0),(0,-side,0),(0,0,1))
            _copy_module(m,c,token,bp,f'{label}_{i:02d}',(side*env.outside_x,(i+.5)*bp,z),axes)
    # Rear wall uses the same validated module family; deliberate single personnel bay.
    rear_width=2*env.outside_x
    n=max(4,ceil(rear_width/5.4));bw=rear_width/n
    for i in range(n):
        token='PERSONNEL' if c.rear_service_door and i==n//2 else ('LOUVER' if i in (1,n-2) else 'METAL')
        _copy_module(m,c,token,bw,f'REAR_{i:02d}',(-env.outside_x+(i+.5)*bw,env.back_y,z),((0,-1,0),(1,0,0),(0,0,1)))
    # Front, gables and corners use the module wall build-up: core (liner inside) 37 mm behind
    # the crest plane, one continuous trapezoidal sheet whose crest plane stays the old outer
    # face (front_y/back_y), pressed flashings in layers L1/L2 outside it.
    C=MG.ModuleModel;t=c.wall_thickness;X,fy,by=env.outside_x,env.front_y,env.back_y
    ey=z+c.eave_height;ridge=roof_level(c,0);core=t-C.CLAD_CORE;Xc=X-C.CLAD_CORE
    ow,oh=c.opening_width,c.opening_height;topbase=z+oh+.36
    def roof(x):return roof_level(c,x)-C.CLAD_TOP
    for sign in (-1,1):
        # Door pockets behind the sliding leaves: core 2 mm clear of the portal jamb face.
        lo,hi=sorted((sign*(ow/2+.002),sign*Xc))
        m.box('HG_FrontPockets',((lo+hi)/2,fy+C.CLAD_CORE+core/2,z+c.eave_height/2),(hi-lo,core,c.eave_height),'HG_Wall','BODY',0.)
        for xx in (sign*(a-.04),sign*(ow/2+.10)):
            m.box('HG_PortalJambs',(xx,-.14,z+oh/2),(.20,.31,oh+.10),'SteelDark','STRUCTURE',.005)
        lo,hi=sorted((sign*(ow/2+.002),sign*X))
        m.box('HG_FrontPlinth',((lo+hi)/2,fy-.0045,z+.24),(hi-lo,.083,.48),'Concrete','FACADE',.004)
        x0,x1=sorted((sign*(ow/2+.002),sign*(X+.07)))
        m.p('HG_FrontBaseFlashing','DETAIL',0.).prism(C.BASE_FLASH,(x0,fy,z),C.YZX,x1-x0,'HG_WallTrim')
        if fy-.004<-.295:
            # Thick walls only: the pocket sheet's raw edge shows beside the portal jamb.
            e0,e1=sorted((sign*(ow/2+.002),sign*(ow/2+.10)))
            m.box('HG_PocketEdgeTrims',((e0+e1)/2,fy-.00275,z+.30+oh/2),(e1-e0,.0025,oh-.40),'HG_WallTrim','DETAIL',0.)
    # Corner ends of the pocket drips mitre on the plan diagonal x+y = X+front_y.
    C.shift(m.p('HG_FrontBaseFlashing'),lambda v:abs(v[0])>X+.065,lambda v:((X+fy-v[1])*(1 if v[0]>0 else -1),v[1],v[2]))
    m.box('HG_FrontHeaderInfill',(0,fy+C.CLAD_CORE+core/2,(topbase+ey)/2),(ow+.004,core,ey-topbase),'HG_Wall','BODY',0.)
    # Gable cores close the volume below the main roof; the raised monitor has its own end caps.
    profile=[(-Xc,ey),(Xc,ey),(Xc,roof_level(c,Xc)),(0,ridge),(-Xc,roof_level(c,Xc))]
    for label,y,out in (('FRONT',fy+C.CLAD_CORE,-1.),('REAR',d,1.)):
        m.p('HG_Gable_'+label,'BODY',0.).prism(profile,(0,y,0),((1,0,0),(0,0,1),(0,1,0)),core,'HG_Wall')
        C.tone_faces(m.p('HG_Gable_'+label),[(0.,out,0.)],'HG_Wall','HG_WallLiner')
    for name in ('HG_FrontPockets','HG_FrontHeaderInfill'):
        C.tone_faces(m.p(name),[(0.,-1.,0.)],'HG_Wall','HG_WallLiner')
    # Sheets: front runs from the pocket foot through the eave line to the verge, gate cut out;
    # the rear gable continues the rear bays' rib rhythm above the eave (hairline end lap).
    front=((0.,fy,0.),(1.,0.,0.),(0.,1.,0.));back=((0.,by,0.),(-1.,0.,0.),(0.,-1.,0.))
    pf,pr=C.clad_pitch(2*X),C.clad_pitch(bw);xe=X*(1-.02/c.roof_rise);gate=(-ow/2,z,ow/2,topbase)
    C.profile_sheet(m.p('HG_FrontCladding','BODY',0.),-X,X,pf,-X,z+C.CLAD_BASE,roof,[gate],(0.,),front,'HG_Wall')
    C.profile_sheet(m.p('HG_RearCladding','BODY',0.),-xe,xe,pr,-X,ey-C.CLAD_TOP,lambda u:roof(-u),(),(0.,),back,'HG_Wall')
    if c.fasteners and c.detail=='HERO':
        # Same girt lines as the side bays, continued up the gables at the same spacing.
        rows=C.girt_rows(z+.58,ey-.166,top=ridge-.2)
        fx=m.p('HG_CladFixings','DETAIL',0.)
        C.fixings(fx,-X+.15,X-.15,pf,-X,rows,[gate],roof,front,'HG_WallTrim')
        C.fixings(fx,-xe,xe,pr,-X,[r for r in rows if r[0]>ey],(),lambda u:roof(-u),back,'HG_WallTrim')
    # Verge trims: 100 mm plates under the roof edge in layer L2 (over the corner angles), plumb
    # ends meeting at the apex (the halves abut, never cross); they run out over the eave-trim
    # face legs at the corners, whose returns stop against their back face.
    for y in (fy-.0065,by+.0045):
        for s in (-1,1):
            xa=s*(X+.0065)
            m.p('HG_VergeTrims','DETAIL',0.).prism([(xa,roof_level(c,xa)-.106),(0.,ridge-.106),(0.,ridge-.006),(xa,roof_level(c,xa)-.006)],
                (0.,y,0.),((1,0,0),(0,0,1),(0,1,0)),.002,'HG_WallTrim')
    # Corners (front/rear walls own the corner square): side-elevation cladding return in the
    # side bays' rib rhythm, plinth return, mitred base flashing, eave-trim return and a
    # hemmed 150/150 angle flashing (plain under the eave trim).
    Lf=Ls=.15
    full=[(-Lf,.0015),(-Lf,.008),(-Lf+.008,.008),(-Lf+.008,.004),(.004,.004),(.004,-Ls+.008),(.008,-Ls+.008),(.008,-Ls),(.0015,-Ls),(.0015,.0015)]
    plain=[(-Lf,.0015),(-Lf,.004),(.004,.004),(.004,-Ls),(.0015,-Ls),(.0015,.0015)]
    ps=C.clad_pitch(bp);eave=C.eave_profile(ey)
    for sx in (-1,1):
        inward=((-sx,0,0),(0,0,1),(0,1,0));sideframe=((sx*X,0.,0.),(0.,sx,0.),(-sx,0.,0.))
        for Y,sy,(u0,u1),yp,(f0,f1),(t0,t1) in ((fy,-1,(fy,0.),(fy-.046,0.),(fy-.07,0.),(fy-.0045,0.)),
                                                (by,1,(d,by),(d,by+.046),(d,by+.07),(d,by+.0045))):
            ua,ub=sorted((sx*u0,sx*u1))
            C.profile_sheet(m.p('HG_CornerCladding','BODY',0.),ua,ub,ps,sx*(0. if sy<0 else d),z+C.CLAD_BASE,ey-C.CLAD_TOP,frame=sideframe,mat='HG_Wall')
            xa,xb=sorted((sx*X,sx*(X+.046)))
            m.box('HG_CornerPlinths',((xa+xb)/2,sum(yp)/2,z+.24),(xb-xa,yp[1]-yp[0],.48),'Concrete','FACADE',.004)
            m.p('HG_CornerBaseFlashing','DETAIL',0.).prism(C.BASE_FLASH,(sx*X,f0,z),inward,f1-f0,'HG_WallTrim')
            m.p('HG_CornerEaveTrims','DETAIL',0.).prism(eave,(sx*X,t0,0.),inward,t1-t0,'HG_WallTrim')
            caps=m.p('HG_CornerCaps','FACADE',0.)
            for prof,z0,z1 in ((full,z+.495,ey-.101),(plain,ey-.101,ey-C.CLAD_TOP)):
                caps.prism([(sx*(X+u),Y+sy*v) for u,v in prof],(0.,0.,z0),A.IDENTITY,z1-z0,'HG_WallTrim')
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
    """
    oh=c.opening_height;z=c.base_height;w=c.width;top=z+oh
    L=w-.18;n=c.gate_leaves//2
    pitch=1.5;count=max(2,round(L/pitch));xs=[-L/2+.10+(L-.20)*i/(count-1) for i in range(count)]
    for j in range(n):
        y=-.43-j*TRACK_PITCH
        rail=m.p(f'HG_GateRail_{j}','STRUCTURE',.002)
        rail.box((0,y,top+.265),(L,.18,.03),'Galvanized')                       # top plate .25..28
        for s in (-1,1):
            rail.box((0,y+s*.08,top+.095),(L,.02,.31),'Galvanized')            # webs -.06..25
            rail.box((0,y+s*.0475,top+.11),(L,.045,.04),'Galvanized')          # flanges -.06..-.02
        # Support girder sits on the rail, hanger plates tie it to the canopy soffit.
        m.box(f'HG_TrackGirder_{j}',(0,y,top+.33),(L,.18,.10),'SteelDark','STRUCTURE',.003)
        hang=m.p('HG_TrackHangers','DETAIL',.001)
        for xx in xs:
            hang.box((xx,y,top+.386),(.16,.22,.012),'Galvanized')
            hang.box((xx,y,top+.51),(.10,.14,.236),'Galvanized')
            if j<n-1:
                hang.box((xx,y-TRACK_PITCH/2,top+.33),(.08,.07,.06),'SteelDark')   # cross spacer
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
    oh=c.opening_height;z=c.base_height;w=c.width
    _track_system(m,c)
    coverdepth=.44+(c.gate_leaves//2-1)*.24
    # The header meets the opening head: no open band at the wall plane between the leaf
    # tops and the rails (interior rafters were visible from outside above the gate).
    m.box('HG_GateHeader',(0,-.12,z+oh+.3225),(w+.20,.32,.645),'SteelDark','STRUCTURE',.004)
    m.box('HG_RailCanopy',(0,-.28-coverdepth/2,z+oh+.695),(w+.44,coverdepth+.45,.10),'SteelDark','FACADE',.005)
    m.box('HG_CanopySoffit',(0,-.28-coverdepth/2,z+oh+.637),(w+.21,coverdepth+.22,.018),'Galvanized','DETAIL',.001)
    m.box('HG_PortalAccent',(0,-.51-coverdepth,z+oh+.71),(w+.20,.022,.025),'Yellow','DETAIL',.001)
    for motion in gate_motion(c):
        x,y,bottom=motion['closed'];lw=motion['width'];lh=oh-.06
        p=m.p('HG_'+motion['id'],'DOOR',.003);p.pivot=motion['closed']
        fh=.085;z0=bottom;z1=bottom+lh
        for xx in (x-lw/2+fh/2,x+lw/2-fh/2):
            p.box((xx,y,(z0+z1)/2),(fh,.13,lh),'SteelDark')
        levels=[z0+fh/2,z1-fh/2,z0+lh*.44,z0+lh*.68]
        if c.gate_glazing:levels.append(z0+lh*.88)
        for zz in levels:p.box((x,y,zz),(lw-2*fh,.13,fh),'SteelDark')
        if c.gate_glazing:
            gb,gt=z0+lh*.68+fh/2,z0+lh*.88-fh/2
            for lo,hi in ((z0+fh,gb-fh),(gt+fh,z1-fh)):
                if hi>lo:p.box((x,y+.013,(lo+hi)/2),(lw-.17,.075,hi-lo),'HG_Gate')
            p.box((x,y+.010,(gb+gt)/2),(lw-.17,.018,gt-gb),'Glass')
        else:p.box((x,y+.013,(z0+z1)/2),(lw-.17,.075,lh-.17),'HG_Gate')
        # Rolled seams stop below the glazed strip, no ribs across transparent panels.
        for k in range(1,max(2,ceil(lw/.68))):
            xx=x-lw/2+k*lw/max(2,ceil(lw/.68))
            p.box((xx,y-.034,z0+lh*.34),(.021,.025,lh*.62),'HG_GateTrim')
        p.box((x,y-.065,z0+.22),(lw-.17,.015,.22),'Galvanized')
        p.box((x,y-.073,z0+1.06),(.035,.045,.34),'Galvanized')
        p.box((x,y+.068,z0+.022),(lw-.10,.030,.035),'Rubber')
        p.box((x,y+.068,z1+.012),(lw-.10,.030,.034),'Rubber')  # top weather seal under the header
        for xx in (x-lw*.32,x+lw*.32):
            _trolley(m,c,p,xx,y,z1,z+oh)
        if c.detail!='DRAFT' and c.fasteners:
            for xx in (x-lw/2+.044,x+lw/2-.044):
                for zz in (z0+.14,z0+lh*.44,z1-.14):
                    p.cylinder((xx,y-.071,zz),(xx,y-.084,zz),.015,'Galvanized',6)
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
    if not c.gutters:return
    a,d,z=c.width/2,c.depth,c.base_height
    profile=[(-.15,-.105),(.15,-.105),(.15,.095),(.125,.095),(.125,-.077),(-.125,-.077),(-.125,.095),(-.15,.095)]
    p=m.p('HG_Gutters','DETAIL',.002)
    for side in (-1,1):
        env=envelope(c)
        x=side*(env.outside_x+.33);top=roof_level(c,x)-.025
        p.prism(profile,(x,env.roof_y0,top),((1,0,0),(0,0,1),(0,1,0)),env.roof_y1-env.roof_y0,'Galvanized')
        for y in (.22,d-.22):
            px=side*(env.outside_x+.12)
            # Mitred pipes are not bevelled: even one segment degenerates UVs at the mitres,
            # and a 2 mm bevel on a 55 mm round tube is invisible anyway.
            m.p('HG_Downpipes','DETAIL',0.).pipe([(x,y,top-.08),(px,y,top-.38),(px,y,z+.33),(px+side*.20,y,z+.20)],.055,'Galvanized',10 if c.detail=='DRAFT' else 16)
            for zz in (z+.65,z+2.4,z+4.2,z+5.8):
                if zz<top-.4:m.box('HG_PipeClamps',(px-side*.04,y,zz),(.18,.04,.04),'SteelDark','DETAIL',.001)


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

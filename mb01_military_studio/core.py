# SPDX-License-Identifier: MIT
"""MB01: dependency-free architectural scenery. Not construction or range engineering.
Source design coordinates: X across facade, Y into building. Final public coordinates:
+X into building, +Y left, +Z up. One numeric unit is one metre.
"""
from dataclasses import dataclass, asdict, replace
from math import pi, sin, cos, ceil, radians, isfinite, sqrt
import hashlib, json, random, re
from .vendor import as07_reference as A

VERSION='0.4.0-alpha.1'
KINDS=('HQ','UNIT','HANGAR','SHELTER','RANGE_SET')
PRESETS={
    'HQ':dict(width=35.2,depth=20.4,floors=3,floor_height=3.6,bays=8,roof='FLAT'),
    'UNIT':dict(width=30.8,depth=14.4,floors=2,floor_height=3.4,bays=8,roof='PITCHED'),
    'HANGAR':dict(width=28.,depth=36.,floors=1,floor_height=7.2,bays=8,roof='PITCHED'),
    'SHELTER':dict(width=24.,depth=32.,floors=1,floor_height=4.8,bays=8,roof='ARCH'),
    'RANGE_SET':dict(width=20.,depth=18.,floors=1,floor_height=3.2,bays=6,roof='FLAT'),
}

@dataclass
class Settings:
    kind:str='HQ'
    name:str='KARARGAH_01'
    width:float=35.2
    depth:float=20.4
    floors:int=3
    floor_height:float=3.6
    bays:int=8
    roof:str='FLAT'
    detail:str='WORKING'
    palette:str='COASTAL'
    seed:int=17
    base_height:float=.18
    walkway_width:float=3.2
    plaza_depth:float=4.5
    local_ground:bool=True
    services:bool=True
    signage:bool=True
    sunshades:bool=True
    door_open:float=.64
    roof_rise:float=4.2
    wear:float=.15
    office_style:str='AUTO'
    service_bays:int=3
    stair_tower:bool=True
    roof_screen:bool=True
    corner_glass:bool=False
    command_variant:str='EXECUTIVE'
    facade_relief:float=.55
    vertical_fins:int=6
    atrium_floors:int=3
    base_cladding:bool=True
    night_lighting:bool=True
    micro_details:bool=True

    def checked(self):
        if self.kind not in KINDS:raise ValueError('Unknown building family.')
        for k in ('width','depth','floor_height','base_height','walkway_width','plaza_depth','roof_rise','door_open','wear','facade_relief'):
            v=getattr(self,k)
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v):raise ValueError(k+' must be finite.')
        if not 14<=self.width<=56 or not 10<=self.depth<=64:raise ValueError('Supported visual asset bounds: width 14..56, depth 10..64.')
        if type(self.floors)!=int or not 1<=self.floors<=4:raise ValueError('Floors: integer 1..4.')
        if type(self.bays)!=int or not 4<=self.bays<=12:raise ValueError('Bays: integer 4..12.')
        if self.detail not in ('DRAFT','WORKING','HERO'):raise ValueError('Invalid detail level.')
        if self.palette not in ('COASTAL','WOODLAND','URBAN'):raise ValueError('Invalid palette.')
        if self.roof not in ('FLAT','PITCHED','ARCH'):raise ValueError('Invalid roof option.')
        if self.kind in ('HQ','UNIT') and self.roof=='ARCH':raise ValueError('Arched roof is available only in the AS07 shelter family.')
        required_roof={'HANGAR':'PITCHED','SHELTER':'ARCH','RANGE_SET':'FLAT'}.get(self.kind)
        if required_roof and self.roof!=required_roof:raise ValueError('Load the preset for this family first; required roof: '+required_roof)
        if not .08<=self.base_height<=.35:raise ValueError('Base height: .08.. .35.')
        if not 2.4<=self.walkway_width<=5.0:raise ValueError('Walkway width: 2.4..5.')
        if not 2.5<=self.plaza_depth<=7:raise ValueError('Plaza depth: 2.5..7.')
        if not 0<=self.door_open<=1 or not 0<=self.wear<=1:raise ValueError('Door opening and wear: 0..1.')
        if not isinstance(self.name,str) or not 1<=len(self.name.strip())<=48:raise ValueError('Name: 1..48 characters.')
        if type(self.seed)!=int:raise ValueError('Seed must be an integer.')
        for k in ('local_ground','services','signage','sunshades'):
            if type(getattr(self,k))!=bool:raise ValueError(k+' must be boolean.')
        if self.kind in ('HQ','UNIT') and not 3.0<=self.floor_height<=4.3:raise ValueError('Facade storey height: 3.0..4.3.')
        if self.kind=='HANGAR' and not 6<=self.floor_height<=10:raise ValueError('Hangar eave height: 6..10.')
        if self.kind=='RANGE_SET' and not 2.8<=self.floor_height<=4.5:raise ValueError('Scenery canopy height: 2.8..4.5.')
        if self.office_style not in ('AUTO','COMMAND','BARRACKS','SUPPORT','LOGISTICS'):raise ValueError('Invalid office style.')
        if self.command_variant not in ('EXECUTIVE','TECHNICAL','MONOLITHIC'):raise ValueError('Invalid command variant.')
        if not .18<=self.facade_relief<=1.40:raise ValueError('Facade relief: .18..1.40 m.')
        if type(self.vertical_fins)!=int or not 0<=self.vertical_fins<=12:raise ValueError('Vertical fins: integer 0..12.')
        if type(self.atrium_floors)!=int or not 1<=self.atrium_floors<=4:raise ValueError('Atrium floors: integer 1..4.')
        if type(self.service_bays)!=int or not 0<=self.service_bays<=5:raise ValueError('Service bays: integer 0..5.')
        for k in ('stair_tower','roof_screen','corner_glass','base_cladding','night_lighting','micro_details'):
            if type(getattr(self,k))!=bool:raise ValueError(k+' must be boolean.')
        if self.kind not in ('HQ','UNIT') and any((self.office_style!='AUTO',self.service_bays,self.stair_tower!=True,self.roof_screen!=True,self.corner_glass)):pass
        if self.kind=='SHELTER':
            A.validate_config(dict(span=self.width,depth=self.depth,eave_height=self.floor_height,
                roof_rise=self.roof_rise,bay_count=self.bays))
        return self

def settings_for(kind,**kwargs):
    d=dict(PRESETS[kind]);d.update(kwargs);d['kind']=kind
    return Settings(**d).checked()

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
from .mb_common import canonical

class Model:
    def __init__(self,s):
        self.cfg=s.checked();self.parts=[];self.labels=[];self.ports=[];self.doors=[];self.collisions=[];self.notes=[];self.openings=[]
        self._parts={};self.done=False
    def p(self,name,group='BODY',bevel=.008):
        if name not in self._parts:
            p=A.MeshPart('SM_MB01_'+name,group,0 if self.cfg.detail=='DRAFT' else bevel)
            self._parts[name]=p;self.parts.append(p)
        return self._parts[name]
    def box(self,name,c,d,mat,group='BODY',bevel=.008,collide=False,axes=A.IDENTITY):
        self.p(name,group,bevel).box(c,d,mat,axes)
        if collide:self.collisions.append(dict(part='SM_MB01_'+name,center=tuple(c),dims=tuple(d),axes=axes))
    def label(self,text,loc,size,mat='White',rotation=(pi/2,0,0),name='Label'):
        if self.cfg.signage:self.labels.append(dict(name=f'{name}_{len(self.labels):02d}',body=text,location=loc,size=size,material=mat,rotation=rotation))
    def port(self,name,loc,yaw,width,role='PEDESTRIAN'):
        self.ports.append(dict(name=name,location=loc,yaw=yaw,width=width,height=self.cfg.base_height,role=role,
            location_convention='base_plane' if role=='PEDESTRIAN' else 'surface_plane'))
    def finish(self):
        if self.done:return self
        for p in self.parts:
            p.vertices=[canonical(v) for v in p.vertices];p.pivot=canonical(p.pivot)
        for r in self.labels:
            r['location']=canonical(r['location']);a=list(r['rotation']);a[2]-=pi/2;r['rotation']=tuple(a)
        for r in self.ports:r['location']=canonical(r['location']);r['yaw']-=pi/2
        for r in self.collisions:
            r['center']=canonical(r['center']);r['axes']=tuple(canonical(a) for a in r['axes'])
        for r in self.doors:
            for k in ('closed','opened'):r[k]=canonical(r[k])
        self.parts=[p for p in self.parts if p.faces];self.done=True
        return self

def local_ground(m,front=True):
    s=m.cfg;w,d,z=s.width,s.depth,s.base_height
    if s.local_ground:
        m.box('Foundation',(0,d/2,z-.16),(w+.65,d,.32),'Concrete','GROUND',.009,True)
        if front:
            # Independent thin tiles over a lower continuous foundation; no duplicate coplanar tops.
            m.box('ForecourtBed',(0,-s.plaza_depth/2,z-.10),(w+1.2,s.plaza_depth,.16),'Joint','GROUND',0,True)
            nx=max(2,ceil((w+1.2)/1.8));ny=ceil(s.plaza_depth/1.15);dx=(w+1.2)/nx;dy=s.plaza_depth/ny
            for i in range(nx):
                for j in range(ny):
                    m.box('ForecourtPavers',(-(w+1.2)/2+(i+.5)*dx,-s.plaza_depth+(j+.5)*dy,z-.025),
                          (dx-.008,dy-.008,.05),'ConcreteLight' if (i*7+j*3)%9<2 else 'Concrete','GROUND',.003)
    m.port('PERSONNEL_OUT',(0,-s.plaza_depth,0),-pi/2,s.walkway_width)

def rect_frame(m,name,x,y,z,width,height,depth,mat='SteelDark',side=False):
    # Canonical front-facing window detail in a local plane; side handled by facade transform.
    f=.065
    for xx in (x-width/2,x+width/2):m.box(name,(xx,y,z),(f,depth,height+f),mat,'FACADE',.003)
    for zz in (z-height/2,z+height/2):m.box(name,(x,y,zz),(width+f,depth,f),mat,'FACADE',.003)

def front_window(m,x,y,z,w,h,index,normal=-1):
    # A real wall opening. Glass, reveal and blind live INSIDE; no solid wall behind.
    rect_frame(m,'WindowFrames',x,y,z,w,h,.12)
    m.box('WindowFrames',(x,y,z),(.045,.13,h-.04),'SteelDark','FACADE',.002)
    m.box('WindowTransoms',(x,y,z+h*.16),(w-.04,.13,.038),'SteelDark','FACADE',.002)
    m.box('WindowGlass',(x,y+.021*normal,z),(w-.065,.018,h-.04),'Glass','GLASS',0)
    m.box('WindowSills',(x,y+normal*.11,z-h/2-.062),(w+.20,.38,.10),'ConcreteLight','FACADE',.006)
    # Boxed recess, not a visible open facade shell. Dark return gives glazing depth.
    by=y-normal*.29
    m.box('WindowInteriorBack',(x,by,z),(w-.03,.025,h-.03),'Interior','DETAIL',0)
    for xx in (x-w/2,x+w/2):m.box('WindowReveals',(xx,y-normal*.10,z),(.04,.37,h),'Plaster','DETAIL',.002)
    blindh=h*(.22+((index*13+m.cfg.seed)%7)*.055)
    m.box('InteriorBlinds',(x,y-normal*.12,z+h/2-blindh/2),(w-.13,.018,blindh),'Blind','DETAIL',.001)
    if m.cfg.sunshades:
        shadez=z+h/2+.17
        for k in range(3 if m.cfg.kind=='HQ' else 2):
            m.box('SunshadeBlades',(x,y+normal*(.14+k*.14),shadez),(w+.22,.075,.045),'RoofOlive','DETAIL',.002)
        for xx in (x-w*.40,x+w*.40):m.box('SunshadeBrackets',(xx,y+normal*.25,shadez-.035),(.035,.5,.06),'SteelDark','DETAIL',.002)
    if m.cfg.detail=='HERO':
        m.box('WindowHandles',(x+.11,y+normal*.10,z-.19),(.017,.019,.14),'Galvanized','DETAIL',.001)

def facade_run(m,xlo,xhi,y,z0,height,floors,n,front=True,entry=False):
    """Build wall strips + piers around window apertures. No hidden solid wall."""
    s=m.cfg;normal=-1 if front else 1;bw=(xhi-xlo)/n;wall_t=.28
    for f in range(floors):
        z=z0+f*height;wh=1.65;bottom=z+.93;top=bottom+wh
        for i in range(n):
            x=xlo+(i+.5)*bw;winw=min(1.92,bw-.80)
            door=entry and f==0 and i==n//2
            if door:
                dw=min(2.1,bw-.55);dh=2.65
                for a,b in ((x-bw/2,x-dw/2),(x+dw/2,x+bw/2)):
                    m.box('FacadeWalls',((a+b)/2,y,z+height/2),(b-a,wall_t,height-.025),'Plaster','BODY',.006,True)
                m.box('FacadeWalls',(x,y,z+dh+(height-dh)/2),(dw,wall_t,height-dh),'Plaster','BODY',.006,True)
                rect_frame(m,'DoorFrames',x,y+normal*.03,z+dh/2,dw,dh,.18)
                m.box('EntryGlass',(x,y+normal*.045,z+dh/2),(dw-.1,.024,dh-.1),'Glass','GLASS',0)
                m.box('EntryMullions',(x,y+normal*.085,z+dh/2),(.075,.12,dh),'SteelDark','DETAIL',.004)
                for xx in (x-.17,x+.17):m.box('EntryHandles',(xx,y+normal*.15,z+1.2),(.025,.028,.44),'Galvanized','DETAIL',.002)
                m.openings.append(dict(kind='PEDESTRIAN',center=(x,y,z),width=dw,height=dh))
            else:
                m.box('FacadeWalls',(x,y,(z+bottom)/2),(bw-.012,wall_t,bottom-z),'Plaster','BODY',.006,True)
                m.box('FacadeWalls',(x,y,(top+z+height)/2),(bw-.012,wall_t,z+height-top-.018),'Plaster','BODY',.006,True)
                for a,b in ((x-bw/2,x-winw/2),(x+winw/2,x+bw/2)):
                    m.box('FacadeWalls',((a+b)/2,y,(bottom+top)/2),(b-a,wall_t,wh),'Plaster','BODY',.006,True)
                front_window(m,x,y+normal*.055,(bottom+top)/2,winw,wh,f*n+i,normal)
            m.box('StoreyShadowLines',(x,y+normal*.15,z+height-.12),(bw-.012,.042,.035),'SteelDark','DETAIL',.001)
    # Plinth, top coping, repeated pilaster shadow lines are not duplicate walls.
    for i in range(n+1):
        x=xlo+i*bw
        m.box('FacadePilasters',(x,y+normal*.16,z0+floors*height/2),(.07,.045,floors*height-.06),'Stone','FACADE',.003)


def side_facade(m,x,y0,y1,z0,height,floors,n,side=1):
    """Reuse front facade geometry rotated around local Z; cut actual side openings too."""
    temporary=Model(m.cfg)
    facade_run(temporary,-(y1-y0)/2,(y1-y0)/2,0,z0,height,floors,n,True,False)
    # local outward -Y -> +X for right wall, -X for left.
    angle=side*pi/2;ca,sa=cos(angle),sin(angle)
    def tr(v):return (x+ca*v[0]-sa*v[1],(y0+y1)/2+sa*v[0]+ca*v[1],v[2])
    for p in temporary.parts:
        dest=m.p(p.name[8:],p.group,p.bevel)
        # Append preserving UV and primitive topology rather than recomputing projections.
        off=len(dest.vertices);dest.vertices.extend(tr(v) for v in p.vertices)
        idx=[]
        for name in p.material_names:
            if name not in dest.material_names:dest.material_names.append(name)
            idx.append(dest.material_names.index(name))
        dest.faces.extend(tuple(j+off for j in f) for f in p.faces)
        dest.material_ids.extend(idx[j] for j in p.material_ids);dest.smooth.extend(p.smooth);dest.uvs.extend(p.uvs)
        dest.primitive_count+=p.primitive_count;dest.closed_primitive_count+=p.closed_primitive_count
    for c in temporary.collisions:
        m.collisions.append(dict(part=c['part'],center=tr(c['center']),dims=c['dims'],axes=A.euler_axes(0,0,angle)))


def roof_building(m,w,d,z,pitched=False):
    if not pitched:
        m.box('RoofDeck',(0,d/2,z-.06),(w+.12,d+.12,.16),'RoofMembrane','ROOF',.003,True)
        for x in (-w/2,w/2):
            m.box('ParapetWalls',(x,d/2,z+.26),(.22,d+.30,.58),'Plaster','ROOF',.007,True)
            m.box('ParapetCoping',(x,d/2,z+.575),(.36,d+.43,.07),'Galvanized','ROOF',.006)
        for y in (0,d):
            m.box('ParapetWalls',(0,y,z+.26),(w,.22,.58),'Plaster','ROOF',.007,True)
            m.box('ParapetCoping',(0,y,z+.575),(w+.36,.36,.07),'Galvanized','ROOF',.006)
    else:
        # Ridge parallel to facade; two continuous folded panels with real seam strips.
        rise=max(.75,min(1.8,d*.10));thick=.08
        for side in (-1,1):
            ya=(-.35 if side<0 else d/2);yb=(d/2 if side<0 else d+.35)
            za=(z if side<0 else z+rise);zb=(z+rise if side<0 else z)
            poly=[(ya,za),(yb,zb),(yb,zb+thick),(ya,za+thick)]
            m.p('PitchedRoof','ROOF',.003).prism(poly,(-w/2-.35,0,0),((0,1,0),(0,0,1),(1,0,0)),w+.7,'RoofOlive')
            for i in range(ceil(w/.9)+1):
                x=-w/2+i*w/ceil(w/.9)
                m.p('RoofSeams','DETAIL',.001).beam((x,ya,za+thick),(x,yb,zb+thick),.023,.025,'SteelDark')
        for x in (-w/2,w/2):
            profile=[(0,z-.02),(d,z-.02),(d/2,z+rise)]
            m.p('GableInfill','ROOF',.005).prism(profile,(x-.10,0,0),((0,1,0),(0,0,1),(1,0,0)),.20,'Plaster')
        m.box('RoofRidgeCap',(0,d/2,z+rise+.10),(w+.78,.23,.055),'Galvanized','DETAIL',.005)
    # Rainpipes, scupper plates, brackets. End locations avoid facade window centres.
    for x in (-w/2+.13,w/2-.13):
        p=m.p('RainwaterPipes','DETAIL',.002)
        p.pipe([(x,d+.22,z+.15),(x,d+.35,z-.15),(x,d+.35,.38),(x,d+.54,.25)],.055,'Galvanized',10)
        for zz in (1.1,3.0,5.5,8):
            if zz<z-.3:m.box('PipeClamps',(x,d+.28,zz),(.19,.19,.028),'SteelDark','DETAIL',.001)


def service_details(m,w,d,z):
    s=m.cfg
    if not s.services:return
    # Roof equipment are decorative housings, not a functional HVAC plan.
    for i in range((2 if s.kind=='HQ' else 1) if s.roof!='PITCHED' else 0):
        x=-2.6+i*3.5;y=d*.65
        m.box('RoofPlantFeet',(x,y,z+.19),(2.1,1.4,.3),'SteelDark','DETAIL',.01)
        m.box('RoofPlantHousing',(x,y,z+.78),(2.6,1.85,1.02),'RoofOlive','DETAIL',.035)
        for j in range(10):m.box('RoofPlantLouvres',(x,y-.94,z+.4+j*.073),(2.26,.035,.027),'SteelDark','DETAIL',.001)
        for dx in (-.68,.68):
            p=m.p('RoofPlantFans','DETAIL',.002)
            p.cylinder((x+dx,y,z+1.30),(x+dx,y,z+1.34),.46,'SteelDark',20)
            p.tube((x+dx,y,z+1.34),(x+dx,y,z+1.38),.46,.425,'Galvanized',20)
    for x in (-w*.39,w*.39):
        m.box('ServiceCabinets',(x,d+.25,1.15),(.80,.38,1.32),'RoofOlive','DETAIL',.016)
        m.box('ServiceCabinetHandles',(x+.25,d+.45,1.15),(.023,.031,.19),'Galvanized','DETAIL',.001)
    for x in (-w*.30,w*.30):
        bench(m,x,-m.cfg.plaza_depth*.60,s.base_height)
    # Entry downlights housed in opaque recess; emitters are separate material islands.
    if s.night_lighting:
        for x in (-1.2,1.2):
            m.box('SoffitLights',(x,-1.6,s.base_height+2.93),(.38,.14,.028),'LightWarm','DETAIL',0)


def bench(m,x,y,z):
    for xx in (x-.8,x+.8):m.box('BenchLegs',(xx,y,z+.24),(.09,.46,.48),'SteelDark','PROPS',.007)
    for j in range(4):m.box('BenchSlats',(x,y-.21+j*.14,z+.49),(1.95,.10,.065),'Timber','PROPS',.006)
    for zz in (z+.69,z+.85):m.box('BenchBack',(x,y+.25,zz),(1.95,.055,.10),'Timber','PROPS',.004)
    for xx in (x-.8,x+.8):m.box('BenchBackSupports',(xx,y+.26,z+.66),(.055,.075,.42),'SteelDark','PROPS',.003)



def office_style_for(s):
    if s.office_style!='AUTO':
        return s.office_style
    return 'COMMAND' if s.kind=='HQ' else 'BARRACKS'


def add_office_lobby(m, central, x0=0.0, title='KARARGAH', secondary='KARARGAH 01', compact=False):
    s=m.cfg;w,d,b=s.width,s.depth,s.base_height;h=s.floors*s.floor_height
    lobbyheight=max(s.floor_height+0.6,h if not compact else min(h,s.floor_height*2+.4))
    for x in (x0-central/2,x0+central/2):
        m.box('LobbyPiers',(x,-.33,b+lobbyheight/2),(.38,.9,lobbyheight+.15),'Stone','FACADE',.015,True)
        m.box('LobbyAccent',(x-.075,-.795,b+lobbyheight/2),(.035,.025,lobbyheight-.22),'Yellow','DETAIL',.002)
    panes=4 if central>5 else 3
    for i in range(panes):
        x=x0-central/2+(i+.5)*central/panes
        m.box('LobbyGlass',(x,-.25,b+lobbyheight/2),(central/panes-.045,.024,lobbyheight-.06),'Glass','GLASS',0)
        m.box('LobbyFrames',(x-central/(panes*2),-.31,b+lobbyheight/2),(.052,.11,lobbyheight),'SteelDark','FACADE',.003)
    for f in range(int(max(1,round(lobbyheight/s.floor_height)))+1):
        m.box('LobbyFrames',(x0,-.31,b+min(h,f*s.floor_height)),(central,.12,.06),'SteelDark','FACADE',.003)
    m.box('LobbyInterior',(x0,2.2,b+lobbyheight/2),(central-.45,.12,lobbyheight),'Interior','BODY',0)
    for x in (x0-central/2+.1,x0+central/2-.1):
        m.box('LobbyReturns',(x,.95,b+lobbyheight/2),(.18,2.5,lobbyheight),'Plaster','BODY',.005)
    for x in (x0-.19,x0+.19):
        m.box('LobbyPullHandles',(x,-.41,b+1.26),(.033,.045,.53),'Galvanized','DETAIL',.002)
    canopy_depth=2.2 if compact else 3.0
    m.box('EntryCanopy',(x0,-1.25,b+3.02),(central+1.6,canopy_depth,.18),'SteelDark','DETAIL',.012)
    m.box('EntryCanopyEdge',(x0,-1.25-canopy_depth/2-.01,b+3.055),(central+1.55,.025,.035),'Yellow','DETAIL',.001)
    for x in (x0-central/2-.55,x0+central/2+.55):
        m.p('CanopySupports','DETAIL',.004).beam((x,-1.25-canopy_depth/2+.18,b),(x,-1.25-canopy_depth/2+.42,b+3.0),.09,.09,'SteelDark')
    m.box('IdentityPanel',(x0,-.49,b+min(h,lobbyheight)-.48),(central-.65,.16,.62),'SteelDark','DETAIL',.012)
    m.label(title,(x0,-.579,b+min(h,lobbyheight)-.43),.29,'White',name='BuildingTitle')
    m.label(secondary.replace('_',' ')[:26],(x0,-1.25-canopy_depth/2-.12,b+3.02),.16,'White',name='EntryIdentity')
    if s.night_lighting:
        for x in (x0-1.2,x0+1.2):
            m.box('SoffitLights',(x,-1.25-canopy_depth/2+.7,b+2.93),(.38,.14,.028),'LightWarm','DETAIL',0)


def add_corner_glass(m, side_x, side_y, z0, floors, storey_h, front=True, side=1):
    normal=-1 if front else 1
    for f in range(floors):
        z=z0+f*storey_h+1.75
        m.box('CornerGlass',(side_x+.18*side,side_y+normal*.02,z),(.34,.018,1.38),'Glass','GLASS',0)
        m.box('CornerFrames',(side_x+.14*side,side_y+normal*.11,z),(.09,.18,1.50),'SteelDark','DETAIL',.002)
        m.box('CornerFrames',(side_x+.29*side,side_y+normal*.11,z),(.09,.18,1.50),'SteelDark','DETAIL',.002)


def add_roof_screen(m,cx,cy,z,w,d):
    if not m.cfg.roof_screen:
        return
    for x in (cx-w/2,cx+w/2):
        m.box('RoofScreens',(x,cy,z+.62),(.10,d,1.24),'RoofOlive','DETAIL',.006)
    for y in (cy-d/2,cy+d/2):
        m.box('RoofScreens',(cx,y,z+.62),(w,.10,1.24),'RoofOlive','DETAIL',.006)
    for j in range(7):
        yy=cy-d/2+.18+j*(d-.36)/6
        m.box('RoofScreenLouvres',(cx,yy,z+.62),(w-.24,.028,.050),'SteelDark','DETAIL',.001,axes=A.euler_axes(pi/2,0,0))


def add_service_bays(m,xlo,xhi,y,z0,total_h,count,front=True):
    if count<=0:
        return
    normal=-1 if front else 1
    count=max(1,count)
    bw=(xhi-xlo)/count
    door_h=min(3.65,total_h-1.35)
    wall_t=.28
    can_y=y+normal*1.55
    m.box('ServiceCanopy',((xlo+xhi)/2,can_y,z0+4.15),(xhi-xlo+0.48,2.1,.18),'SteelDark','DETAIL',.010)
    for i in range(count):
        x=xlo+(i+.5)*bw
        dw=min(3.3,bw-.52)
        for a,b in ((x-bw/2,x-dw/2),(x+dw/2,x+bw/2)):
            m.box('ServiceWingWalls',((a+b)/2,y,z0+total_h/2),(b-a,wall_t,total_h),'Plaster','BODY',.006,True)
        m.box('ServiceWingWalls',(x,y,z0+door_h+(total_h-door_h)/2),(dw,wall_t,total_h-door_h),'Plaster','BODY',.006,True)
        rect_frame(m,'ServiceDoorFrames',x,y+normal*.05,z0+door_h/2,dw,door_h,.18)
        m.box('RollupDoors',(x,y+normal*.08,z0+door_h/2),(dw-.08,.06,door_h-.08),'SteelDark','DOOR',.003,True)
        for k in range(5):
            zz=z0+.35+k*(door_h-.70)/4
            m.box('RollupDoorSlats',(x,y+normal*.11,zz),(dw-.18,.016,.035),'RoofOliveLight','DETAIL',.001)
        for off in (-dw/2+.24,dw/2-.24):
            m.box('SafetyBollards',(x+off,y+normal*1.16,z0+.62),(.12,.12,1.24),'Yellow','DETAIL',.004)
        m.openings.append(dict(kind='SERVICE_BAY',center=(x,y,z0),width=dw,height=door_h))
    for xx in (xlo-.02,xhi+.02):
        m.box('ServiceWingJambs',(xx,y,z0+total_h/2),(.12,wall_t,total_h),'Stone','FACADE',.004,True)


def add_stair_tower(m,side=1,front_offset=.72):
    s=m.cfg
    if not (s.stair_tower and s.floors>1):
        return
    w,d,b=s.width,s.depth,s.base_height
    tower_w=3.2;tower_d=2.8;tower_h=s.floors*s.floor_height+.28
    x=side*(w/2+tower_w/2-.18);y=d*.76
    m.box('StairTowerMass',(x,y,b+tower_h/2),(tower_w,tower_d,tower_h),'RoofOlive','BODY',.007,True)
    m.box('StairTowerPlinth',(x,y,b+.18),(tower_w+.14,tower_d+.14,.36),'ConcreteLight','DETAIL',.006)
    rect_frame(m,'TowerDoorFrame',x,y+tower_d/2+.10,b+1.15,1.15,2.3,.16)
    m.box('TowerDoor',(x,y+tower_d/2+.14,b+1.15),(1.06,.07,2.22),'SteelDark','DOOR',.004)
    for f in range(s.floors):
        z=b+.92+f*s.floor_height
        m.box('TowerWindows',(x,y-.72,z),(1.35,.03,1.00),'Glass','GLASS',0)
        for j in range(7):
            m.box('TowerLouvres',(x,y+tower_d/2+.04,b+1.2+f*.55+j*.09),(1.85,.026,.030),'SteelDark','DETAIL',.001)
    yline=y-tower_d/2+.18
    run=min(max(2.4,s.floor_height*0.92),3.1)
    for lvl in range(s.floors-1):
        z0=b+.10+lvl*s.floor_height
        z1=b+.10+(lvl+1)*s.floor_height
        land_y=yline-lvl*0.02
        landing_z=z1-.22
        m.box('StairLandings',(x-side*(tower_w/2+.92),land_y,landing_z),(1.84,1.08,.12),'SteelDark','DETAIL',.004)
        m.p('ExternalStairs','DETAIL',.003).beam((x-side*(tower_w/2+.15),land_y+.38,z0+.42),(x-side*(tower_w/2+1.55),land_y-.18,landing_z),.12,.18,'SteelDark')
        m.p('StairStringers','DETAIL',.003).beam((x-side*(tower_w/2+.32),land_y+.42,z0+.36),(x-side*(tower_w/2+1.38),land_y-.14,landing_z),.06,.13,'SteelDark')
        m.p('StairStringers','DETAIL',.003).beam((x-side*(tower_w/2+1.02),land_y+.42,z0+.36),(x-side*(tower_w/2+2.08),land_y-.14,landing_z),.06,.13,'SteelDark')
        for rr in (-.42,.42):
            m.p('StairRails','DETAIL',.002).beam((x-side*(tower_w/2+.92),land_y+rr,landing_z+.06),(x-side*(tower_w/2+.92),land_y+rr,landing_z+.96),.045,.045,'SteelDark')
    m.p('LadderCage','DETAIL',.002).beam((x+side*(tower_w/2-.28),y+tower_d/2-.08,b+.2),(x+side*(tower_w/2-.28),y+tower_d/2-.08,b+tower_h+.85),.06,.06,'SteelDark')
    for zz in [b+.35+i*.32 for i in range(int((tower_h+.4)/.32))]:
        m.box('LadderRungs',(x+side*(tower_w/2-.28),y+tower_d/2-.12,zz),(.30,.035,.03),'Galvanized','DETAIL',.001)


def add_service_yard(m,service_x,service_y,service_z):
    if not m.cfg.services:
        return
    for i in range(2):
        m.box('YardCondensers',(service_x+1.15*i,service_y,service_z+.95),(.92,.62,1.75),'RoofOlive','DETAIL',.014)
        m.box('YardFans',(service_x+1.15*i,service_y+.33,service_z+1.30),(.66,.028,.66),'SteelDark','DETAIL',.001)
    for i in range(4):
        zz=service_z+.5+i*.55
        m.box('ServiceConduits',(service_x-1.1,service_y,zz),(.07,1.26,.07),'Galvanized','DETAIL',.001)
    m.box('UtilityPad',(service_x,service_y,service_z+.03),(3.2,2.2,.06),'ConcreteLight','GROUND',.003,True)


def _detail_at_least(s, level):
    rank={'DRAFT':0,'WORKING':1,'HERO':2}
    return rank[s.detail]>=rank[level]


def add_command_architecture(m, central):
    """Architectural articulation for a fictional command/HQ asset.
    This is an exterior CGI language system, not a real facility design standard.
    """
    s=m.cfg;w,d,b=s.width,s.depth,s.base_height;h=s.floors*s.floor_height
    relief=s.facade_relief
    variant=s.command_variant
    accent='SteelDark' if variant!='EXECUTIVE' else 'RoofOlive'
    cladding='Stone' if variant!='TECHNICAL' else 'ConcreteDark'

    # A low durable plinth reads correctly at eye level and prevents the facade from feeling weightless.
    if s.base_cladding:
        plinth_h=min(.82,s.floor_height*.24)
        wing=(w-central)/2
        for x in (-central/2-wing/2,central/2+wing/2):
            m.box('HQBaseCladding',(x,-.18,b+plinth_h/2),(wing-.08,.22,plinth_h),cladding,'FACADE',.004)
        for side in (-1,1):
            m.box('HQSideBaseCladding',(side*(w/2+.12),d/2,b+plinth_h/2),(.20,d-.12,plinth_h),cladding,'FACADE',.004)

    # Horizontal shadow bands and slim metal cassettes add real facade depth without dense geometry.
    for f in range(1,s.floors+1):
        z=b+f*s.floor_height-.17
        for x,cw in ((-(w+central)/4,(w-central)/2),((w+central)/4,(w-central)/2)):
            m.box('HQSpandrelBands',(x,-relief*.36,z),(cw-.22,.16,.12),accent,'FACADE',.003)
            if _detail_at_least(s,'WORKING'):
                m.box('HQShadowReveals',(x,-relief*.45,z-.09),(cw-.18,.028,.025),'Joint','DETAIL',.001)

    # Deep vertical blades. Density is parameterized so the AI agent can tune silhouette after screenshots.
    if s.vertical_fins:
        left=-w/2+.75;right=w/2-.75
        candidates=[]
        for i in range(s.vertical_fins):
            t=(i+1)/(s.vertical_fins+1);x=left+(right-left)*t
            if abs(x)>central*.62:candidates.append(x)
        for i,x in enumerate(candidates):
            fin_depth=relief*(1.00 if variant=='TECHNICAL' else .78)
            fin_w=.13 if variant!='MONOLITHIC' else .22
            m.box('HQVerticalFins',(x,-fin_depth/2-.18,b+h*.55),(fin_w,fin_depth,h*.83),accent,'FACADE',.005)
            if _detail_at_least(s,'HERO') and s.micro_details:
                for z in (b+1.05,b+h-.95):
                    m.box('HQFinBrackets',(x,-fin_depth-.16,z),(.24,.08,.11),'Galvanized','DETAIL',.002)

    # Central portal and recessed curtain wall crown produce a stronger institutional silhouette.
    atrium_h=min(h,max(s.floor_height+1.0,s.atrium_floors*s.floor_height-.35))
    portal_w=central+2.15 if variant!='MONOLITHIC' else central+2.75
    for x in (-portal_w/2,portal_w/2):
        m.box('HQPortalBlades',(x,-.26,b+atrium_h/2),(.48,.72,atrium_h+.18),cladding,'FACADE',.012,True)
    m.box('HQPortalCrown',(0,-.28,b+atrium_h-.18),(portal_w+.48,.78,.52),accent,'FACADE',.010)
    if _detail_at_least(s,'WORKING'):
        for x in (-portal_w/2,portal_w/2):
            m.box('HQPortalReveal',(x,-.66,b+atrium_h/2),(.075,.06,atrium_h-.6),'Joint','DETAIL',.001)

    # Architectural site furniture and anti-float contact details (not security engineering).
    if _detail_at_least(s,'WORKING'):
        for side in (-1,1):
            x=side*(central/2+2.15)
            m.box('HQPlanter',(x,-2.25,b+.34),(1.40,.72,.68),'ConcreteDark','PROPS',.018)
            m.box('HQPlanterSoil',(x,-2.25,b+.695),(1.18,.52,.05),'Gravel','PROPS',.002)
        for x in (-central/2-1.05,central/2+1.05):
            m.box('HQWayfindingPylon',(x,-3.05,b+.85),(.30,.30,1.70),accent,'PROPS',.018)

    # Roof screen gets secondary rails / cap to read as a constructed assembly in close-up.
    if s.roof_screen and _detail_at_least(s,'WORKING'):
        rz=b+h+1.22
        for x in (-3.1,3.1):
            m.box('HQRoofScreenPosts',(x,d*.68,rz),(0.10,2.35,1.30),'SteelDark','DETAIL',.003)
        m.box('HQRoofScreenCap',(0,d*.68,rz+.69),(6.35,2.42,.08),'Galvanized','DETAIL',.003)

    if _detail_at_least(s,'HERO') and s.micro_details:
        # Expansion-joint covers, drip edges and panel fasteners are sparse and silhouette-safe.
        for side in (-1,1):
            x=side*(w*.36)
            m.box('HQExpansionJoints',(x,-.315,b+h/2),(.022,.03,h-.65),'Joint','DETAIL',.0008)
        for x in (-w*.34,-w*.22,w*.22,w*.34):
            for f in range(s.floors):
                z=b+.72+f*s.floor_height
                m.p('HQFacadeFasteners','DETAIL',.0008).cylinder((x,-.39,z),(x,-.43,z),.018,'Galvanized',8)

    m.notes.append('0.4 HQ articulation: layered facade, portal blades, spandrel bands, optional fins, close-up micro detail and configurable command variants.')


def build_office(m):
    s=m.cfg;w,d,b=s.width,s.depth,s.base_height;h=s.floors*s.floor_height
    style=office_style_for(s)
    local_ground(m)
    n=max(4,round(w/3.6));n+=n%2
    side_n=max(3,round(d/3.5))
    for f in range(1,s.floors):
        z=b+f*s.floor_height
        m.box('FloorSlabs',(0,d/2,z-.075),(w-.28,d-.28,.15),'Concrete','BODY',.005,True)

    if style=='COMMAND':
        central=6.8
        leftn=max(2,round((w-central)/2/3.5))
        facade_run(m,-w/2,-central/2,0,b,s.floor_height,s.floors,leftn,True)
        facade_run(m,central/2,w/2,0,b,s.floor_height,s.floors,leftn,True)
        facade_run(m,-w/2,w/2,d,b,s.floor_height,s.floors,n+1,False,True)
        side_facade(m,w/2,0,d,b,s.floor_height,s.floors,side_n,1)
        side_facade(m,-w/2,0,d,b,s.floor_height,s.floors,side_n,-1)
        add_office_lobby(m,central,0.0,'KARARGAH',s.name)
        add_command_architecture(m,central)
        for x in (-w/2+.85,w/2-.85):
            m.box('CornerPilasters',(x,d/2,b+h/2),(.70,d-.22,h-.08),'RoofOlive','FACADE',.008)
        if s.corner_glass:
            add_corner_glass(m,w/2-.22,0.0,b,s.floors,s.floor_height,True,1)
            add_corner_glass(m,-w/2+.22,0.0,b,s.floors,s.floor_height,True,-1)
        add_roof_screen(m,0,d*.68,b+h+.02,6.2,2.0)
        title='KARARGAH'
        m.notes.append('COMMAND style: glazed lobby, stronger vertical accents and optional corner glazing. Exterior shell only.')

    elif style=='BARRACKS':
        central=5.0
        leftn=max(2,round((w-central)/2/3.45))
        facade_run(m,-w/2,-central/2,0,b,s.floor_height,s.floors,leftn,True)
        facade_run(m,central/2,w/2,0,b,s.floor_height,s.floors,leftn,True)
        facade_run(m,-w/2,w/2,d,b,s.floor_height,s.floors,n,False,False)
        side_facade(m,w/2,0,d,b,s.floor_height,s.floors,side_n,1)
        side_facade(m,-w/2,0,d,b,s.floor_height,s.floors,side_n,-1)
        add_office_lobby(m,central,0.0,'BIRLIK BINASI',s.name,compact=True)
        add_stair_tower(m,1)
        add_roof_screen(m,0,d*.70,b+h+.02,4.8,1.8)
        title='BIRLIK BINASI'
        m.notes.append('BARRACKS style: repeated room bays with external stair tower and compact entry volume.')

    else:
        service_count=min(5,max(1,s.service_bays or 3))
        service_zone=max(w*.34,min(w*.46,service_count*4.1+.9))
        split=w/2-service_zone
        central=4.8 if style=='SUPPORT' else 5.4
        leftn=max(2,round(((split+w/2)-central)/2/3.55))
        facade_run(m,-w/2,-central/2,0,b,s.floor_height,s.floors,leftn,True)
        facade_run(m,central/2,split,0,b,s.floor_height,s.floors,leftn,True)
        add_service_bays(m,split,w/2,0,b,h,service_count,True)
        # Rear uses office facade + a simpler service strip with personnel access.
        facade_run(m,-w/2,split,d,b,s.floor_height,s.floors,max(4,round((split+w/2)/3.6)),False,False)
        doorx=(split+w/2)/2+.2;dw=1.15;dh=2.35
        m.box('ServiceRearWalls',((split+w/2)/2,d,b+h/2),(w/2-split,.22,h),'Plaster','BODY',.006,True)
        for a,bx in ((split,doorx-dw/2),(doorx+dw/2,w/2)):
            m.box('ServiceRearWalls',((a+bx)/2,d,b+h/2),(bx-a,.24,h),'Plaster','BODY',.006,True)
        m.box('ServiceRearWalls',(doorx,d,b+dh+(h-dh)/2),(dw,.24,h-dh),'Plaster','BODY',.006,True)
        rect_frame(m,'RearDoorFrame',doorx,d+.10,b+dh/2,dw,dh,.16)
        m.box('RearPersonnelDoor',(doorx,d+.14,b+dh/2),(dw-.06,.07,dh-.06),'SteelDark','DOOR',.005,True)
        side_facade(m,-w/2,0,d,b,s.floor_height,s.floors,side_n,-1)
        # Service side is plainer and more utilitarian.
        m.box('ServiceSideWall',(w/2,d/2,b+h/2),(.22,d,h),'Plaster','BODY',.006,True)
        for zc in [b+1.6+i*s.floor_height for i in range(max(1,s.floors-1))]:
            m.box('ServiceSideLouvres',(w/2+.06,d*.32,zc),(.02,1.6,.74),'SteelDark','DETAIL',.001)
        add_office_lobby(m,central,0.0,'DESTEK BINASI' if style=='SUPPORT' else 'LOJISTIK / EGITIM',s.name,compact=True)
        add_roof_screen(m,split+(w/2-split)/2,d*.72,b+h+.02,4.4,1.8)
        add_stair_tower(m,1)
        add_service_yard(m,w/2+1.8,d*.82,b)
        title='DESTEK BINASI' if style=='SUPPORT' else 'LOJISTIK / EGITIM'
        m.notes.append(style+' style: mixed office + service wing with roll-up bays, roof screening and external service yard.')

    roof_building(m,w,d,b+h,s.roof=='PITCHED')
    service_details(m,w,d,b+h+(1.1 if s.roof=='PITCHED' else 0))
    if s.local_ground:
        m.box('RearServiceLanding',(0,d+.70,b-.08),(s.walkway_width,1.4,.16),'Concrete','GROUND',.006,True)
    m.port('REAR_SERVICE_OUT',(0,d+1.4,0),pi/2,s.walkway_width)
    m.openings.append(dict(kind='LOBBY',center=(0,0,b),width=min(6.8,w*.26),height=h))
    m.notes.append('HQ/UNIT families remain visual shell assets only; no complete interior room layout is generated.')


def i_beam(m,name,a,b,width=.24,depth=.42):
    axis=A.unit(A.sub(b,a));ref=(0,0,1) if abs(axis[2])<.95 else (0,1,0)
    x=A.unit(A.cross(ref,axis));y=A.cross(axis,x)
    m.p(name,'STRUCTURE',.004).prism(A.i_profile(width,depth,.028,.028),a,(x,y,axis),sqrt(A.dot(A.sub(b,a),A.sub(b,a))),'SteelDark')


def build_hangar(m):
    s=m.cfg;w,d,z=s.width,s.depth,s.base_height;h=s.floor_height;rise=max(1.25,w*.075);ow=w*.64;oh=h-.72
    local_ground(m)
    # Vertical I columns and two rafters per portal, purlins follow each slope.
    for i in range(s.bays+1):
        y=i*d/s.bays
        for side in (-1,1):
            x=side*(w/2-.21)
            spring=z+h+rise*(1-abs(x)/(w/2+.38))-.36
            i_beam(m,'PortalColumns',(x,y,z+.08),(x,y,spring),.32,.38)
            i_beam(m,'PortalRafters',(x,y,spring),(0,y,z+h+rise-.36),.26,.43)
            m.box('PortalFootplates',(x,y,z+.06),(.64,.65,.12),'SteelDark','DETAIL',.005)
            if s.detail!='DRAFT':
                for dx in (-.21,.21):
                    for dy in (-.22,.22):m.p('Fasteners','DETAIL',.001).cylinder((x+dx,y+dy,z+.12),(x+dx,y+dy,z+.16),.028,'Galvanized',6)
    for side in (-1,1):
        for j in range(6):
            x=side*w/2*(j+.2)/6;zz=z+h+rise*(1-abs(x)/(w/2+.38))-.11
            m.box('Purlins',(x,d/2,zz),(.085,d+.15,.13),'Galvanized','DETAIL',.003)
        # Cladding below and above clerestory; solid piers between real openings.
        x=side*(w/2+.025);low=h*.65;wh=1.10
        m.box('SideCladding',(x,d/2,z+low/2),(.15,d,low),'RoofOlive','BODY',.004,True)
        m.box('UpperCladding',(x,d/2,z+low+wh+(h-low-wh)/2),(.15,d,h-low-wh),'RoofOlive','BODY',.004,True)
        for i in range(s.bays):
            y=(i+.5)*d/s.bays;length=d/s.bays
            m.box('ClerestoryGlass',(x,y,z+low+wh/2),(.025,length-.16,wh-.10),'Glass','GLASS',0)
            for yy in ((y-length/2,y+length/2) if i==s.bays-1 else (y-length/2,)):m.box('ClerestoryFrames',(x,yy,z+low+wh/2),(.20,.10,wh),'SteelDark','DETAIL',.002)
            for zz in (z+low,z+low+wh):m.box('ClerestoryFrames',(x,y,zz),(.20,length,.065),'SteelDark','DETAIL',.002)
        # Vertical cladding profiles stop at the actual window strip.
        for j in range(ceil(d/.72)+1):
            y=j*d/ceil(d/.72)
            m.box('CladdingRibs',(x+side*.10,y,z+low/2),(.030,.032,low-.035),'RoofOliveLight','DETAIL',.001)
        # Concrete skirt and free-flowing exterior drainpipe.
        m.box('ConcretePlinth',(x+side*.10,d/2,z+.22),(.12,d,.44),'ConcreteLight','DETAIL',.006)
        p=m.p('Rainwater','DETAIL',.002)
        p.box((side*(w/2+.2),d/2,z+h+.06),(.20,d+.65,.12),'Galvanized')
        for y in (.5,d-.5):p.pipe([(side*(w/2+.2),y,z+h),(side*(w/2+.36),y,z+h-.3),(side*(w/2+.36),y,z+.2)],.055,'Galvanized',10)
    # Front wall surrounds an actual door aperture, not a cuboid hidden by door faces.
    for a,b in ((-w/2,-ow/2),(ow/2,w/2)):
        m.box('FrontPiers',((a+b)/2,0,z+h/2),(b-a,.22,h),'RoofOlive','BODY',.007,True)
    m.box('FrontLintel',(0,0,z+oh+(h-oh)/2),(ow,.22,h-oh),'RoofOlive','BODY',.006,True)
    # Back cladding with a real offset personnel opening.
    doorx=w*.31;dw=1.2;dh=2.35
    for a,b in ((-w/2,doorx-dw/2),(doorx+dw/2,w/2)):
        m.box('RearWall',((a+b)/2,d,z+h/2),(b-a,.22,h),'RoofOlive','BODY',.008,True)
    m.box('RearWall',(doorx,d,z+dh+(h-dh)/2),(dw,.22,h-dh),'RoofOlive','BODY',.007,True)
    rect_frame(m,'RearDoorFrame',doorx,d+.10,z+dh/2,dw,dh,.16)
    m.box('RearPersonnelDoor',(doorx,d+.14,z+dh/2),(dw-.06,.07,dh-.06),'SteelDark','DOOR',.005,True)
    m.box('RearDoorHandle',(doorx-.38,d+.21,z+1.05),(.17,.045,.028),'Galvanized','DETAIL',.002)
    # Gable panels and thick folded roof with seam geometry.
    profile=[(-w/2,z+h),(w/2,z+h),(0,z+h+rise)]
    for y in (-.10,d-.04):m.p('Gables','ROOF',.004).prism(profile,(0,y,0),((1,0,0),(0,0,1),(0,1,0)),.16,'RoofOlive')
    for side in (-1,1):
        x0,x1=(-w/2-.38,0) if side<0 else (0,w/2+.38)
        za,zb=(z+h,z+h+rise) if side<0 else (z+h+rise,z+h)
        prof=[(x0,za),(x1,zb),(x1,zb+.08),(x0,za+.08)]
        m.p('RoofPanels','ROOF',.003).prism(prof,(0,-.35,0),((1,0,0),(0,0,1),(0,1,0)),d+.7,'RoofOliveLight')
        for i in range(ceil(d/.9)+1):
            y=-.25+i*(d+.5)/ceil(d/.9)
            m.p('RoofSeams','DETAIL',.001).beam((x0,y,za+.10),(x1,y,zb+.10),.025,.030,'SteelDark')
    m.box('RidgeCap',(0,d/2,z+h+rise+.12),(.25,d+.85,.06),'Galvanized','DETAIL',.004)
    # Two leaves per side slide onto parallel tracks. Geometry is closed-rest and pivot local.
    leafw=ow/4+.02
    for side in (-1,1):
        for i in range(2):
            closed=(side*(i+.5)*ow/4,-.24-i*.14,z+.05)
            opened=(side*(ow/2+ow/8+.11),closed[1],closed[2])
            key=f'SlidingDoor_{"L" if side<0 else "R"}{i}'
            p=m.p(key,'DOOR',.006);p.pivot=closed
            p.box((closed[0],closed[1],z+oh/2),(leafw,.10,oh-.07),'RoofOliveLight')
            for zz in (.26,oh-.23):p.box((closed[0],closed[1]-.062,z+zz),(leafw-.08,.03,.045),'SteelDark')
            for k in range(ceil(leafw/.38)):
                x=closed[0]-leafw/2+.15+k*.38
                p.box((x,closed[1]-.061,z+oh/2),(.025,.025,oh-.16),'RoofOlive')
            p.box((closed[0],closed[1]-.071,z+.55),(leafw-.12,.018,.22),'Yellow')
            m.doors.append(dict(part=p.name,kind='SLIDE',closed=closed,opened=opened,open_fraction=s.door_open))
            m.collisions.append(dict(part=p.name,center=(closed[0],closed[1],z+oh/2),dims=(leafw,.12,oh-.07),axes=A.IDENTITY))
    for y in (-.24,-.38):
        m.box('DoorTopRails',(0,y,z+oh+.12),(w-.20,.08,.13),'SteelDark','DETAIL',.003)
        m.box('DoorFloorRails',(0,y,z+.008),(w-.20,.06,.016),'Galvanized','DETAIL',.001)
    # Readable fascia signage and protected practical lights.
    m.box('HangarIdentityPanel',(0,-.29,z+h+rise*.46),(7.8,.14,.8),'SteelDark','DETAIL',.009)
    m.label('BAKIM HANGARI',(0,-.37,z+h+rise*.47),.39,'White',name='HangarTitle')
    m.label(s.name.replace('_',' ')[:22],(-w*.39,-.151,z+2.5),.23,'Yellow',name='HangarID')
    for x in (-w*.37,w*.37):
        m.box('EntryWallLights',(x,-.21,z+3.4),(.60,.16,.15),'SteelDark','DETAIL',.006)
        m.box('EntryWallDiffusers',(x,-.303,z+3.385),(.49,.018,.075),'LightWarm','DETAIL',0)
    if s.services:
        for side in (-1,1):
            for i in range(s.bays):
                y=(i+.5)*d/s.bays;lx=side*w*.25;lz=z+h+rise*.42-.45
                m.box('SuspendedLights',(lx,y,lz),(.20,1.8,.10),'SteelDark','DETAIL',.006)
                m.box('SuspendedDiffusers',(lx,y,lz-.056),(.15,1.68,.016),'LightWarm','DETAIL',0)
                attach=z+h+rise*(1-abs(lx)/(w/2+.38))-.035
                for dy in (-.58,.58):
                    m.p('LuminaireHangers','DETAIL',.001).cylinder((lx,y+dy,lz+.053),(lx,y+dy,attach),.009,'Galvanized',8)
                    m.box('LuminaireAnchorPlates',(lx,y+dy,attach+.012),(.14,.14,.025),'SteelDark','DETAIL',.002)
        for i in range(3):
            m.box('ServiceLockers',(-w/2+1.0,d*.65+i*1.0,z+1.03),(.55,.82,2.06),'RoofOlive','PROPS',.016)
            m.box('LockerHandle',(-w/2+1.295,d*.65+i*1.0,z+1.15),(.035,.11,.023),'Galvanized','DETAIL',.001)
    m.port('AIRCRAFT_IN',(0,-.12,z),-pi/2,ow,'HANGAR')
    m.port('PERSONNEL_REAR_OUT',(doorx,d+1.25,0),pi/2,s.walkway_width)
    if s.local_ground:m.box('RearLanding',(doorx,d+.65,z-.08),(s.walkway_width,1.3,.16),'Concrete','GROUND',.006,True)
    m.openings.append(dict(kind='HANGAR',width=ow,height=oh,center=(0,0,z)))
    m.notes.append('Moving panels are preview/asset transforms, not a tested runtime Unreal door Blueprint.')


def build_shelter(m):
    s=m.cfg
    cfg=dict(A.CONFIG);cfg.update(span=s.width,depth=s.depth,eave_height=s.floor_height,roof_rise=s.roof_rise,
        bay_count=s.bays,detail={'DRAFT':'PREVIEW','WORKING':'HIGH','HERO':'CINEMATIC'}[s.detail],
        add_service_props=s.services,add_signage=s.signage,add_practical_lights=False,
        door_open_degrees=s.door_open*95)
    source=A.ShelterModel(cfg)
    # Do not execute original .build(): local apron and presentation are explicitly omitted.
    for fn in ('build_frame','build_roof','build_walls','build_services'):
        getattr(source,fn)()
    if s.services:source.build_props()
    source.build_signage()
    local_ground(m)
    for p in source.parts:
        p.name=p.name.replace('SM_AS07_','SM_MB01_AS07_')
        p.vertices=[(x,y,z+s.base_height) for x,y,z in p.vertices]
        p.pivot=(p.pivot[0],p.pivot[1],p.pivot[2]+s.base_height)
        p.bevel=0 if s.detail=='DRAFT' else p.bevel
        if p.group=='Door':
            p.group='DOOR';m.doors.append(dict(part=p.name,kind='HINGE',closed=p.pivot,opened=p.pivot,
                angle=-radians(95),open_fraction=s.door_open))
        else:p.group=p.group.upper()
        m.parts.append(p)
    # Original labels belong to source body: retain source layout with a new instance ID.
    for l in source.labels if s.signage else []:
        l=dict(l);loc=l['location'];l['location']=(loc[0],loc[1],loc[2]+s.base_height)
        l['name']='AS07_'+str(len(m.labels));l['body']=l['body'].replace('AS / 07','AS / 07')
        m.labels.append(l)
    for c in source.collisions:
        # AS07 has group-level hulls; do not misassign them to individual assets.
        pass
    m.port('AIRCRAFT_IN',(0,0,s.base_height),-pi/2,max(1,s.width-.8),'HANGAR')
    dx=s.width/2*.55
    if s.local_ground:m.box('AS07RearLanding',(dx,s.depth+.8,s.base_height-.08),(s.walkway_width,1.6,.16),'Concrete','GROUND',.006,True)
    m.port('PERSONNEL_REAR_OUT',(dx,s.depth+1.6,0),pi/2,s.walkway_width)
    m.notes.append('AS07 retained source geometry; new local foundation optional. AS07 structural collision uses static complex geometry, not whole-building boxes.')


def build_range_set(m):
    """Nonfunctional film set: pavilion, tables, abstract display targets and scenic backdrop.
    No ballistic model, protective specification, live-fire layout or safety calculation.
    """
    s=m.cfg;w,d,z=s.width,s.depth,s.base_height;h=s.floor_height
    local_ground(m)
    deckdepth=4.2
    for i in range(s.bays+1):
        x=-w/2+i*w/s.bays
        for y in (0,deckdepth):
            m.box('PavilionPosts',(x,y,z+h/2),(.14,.14,h),'SteelDark','STRUCTURE',.006,True)
            m.box('PostShoes',(x,y,z+.07),(.31,.31,.14),'Galvanized','DETAIL',.008)
        m.p('CanopyRafters','STRUCTURE',.003).beam((x,-.5,z+h),(x,deckdepth+.45,z+h+.3),.09,.15,'SteelDark')
    m.box('PavilionRoof',(0,deckdepth/2,z+h+.22),(w+1.0,deckdepth+1.3,.095),'RoofOlive','ROOF',.006,axes=A.euler_axes(.052,0,0))
    for j in range(ceil(w/.65)+1):
        x=-w/2+j*w/ceil(w/.65)
        m.p('PavilionRoofSeams','DETAIL',.001).beam((x,-.52,z+h+.13),(x,deckdepth+.57,z+h+.4),.025,.025,'SteelDark')
    for i in range(s.bays):
        x=-w/2+(i+.5)*w/s.bays
        # Benches and partition boards only: no weapons, ammunition or containment components.
        tablew=w/s.bays-.7
        m.box('SetTables',(x,2.75,z+.92),(tablew,.75,.065),'Timber','PROPS',.007)
        for xx in (x-tablew*.36,x+tablew*.36):m.box('TableLegs',(xx,2.75,z+.46),(.055,.55,.92),'SteelDark','PROPS',.002)
        m.box('NumberBoards',(x,4.32,z+h-.28),(.48,.055,.34),'SteelDark','DETAIL',.005)
        m.label(f'{i+1:02d}',(x,4.285,z+h-.28),.20,'White',name='SetBay')
        # Abstract concentric circles are printed decorative boards, not training targets.
        ty=d-2.0
        m.box('DisplayStands',(x,ty,z+.65),(.065,.08,1.30),'SteelDark','DETAIL',.004)
        m.box('DisplayBoards',(x,ty,z+1.50),(.80,.06,1.02),'Plaster','DETAIL',.004)
        p=m.p('DisplayGraphics','DETAIL',0)
        for r in (.09,.18,.28):
            points=[(x+r*cos(2*pi*j/48),ty-.036,z+1.5+r*sin(2*pi*j/48)) for j in range(49)]
            p.pipe(points,.006,'SteelDark',5)
        m.box('DisplayFeet',(x,ty,z+.03),(.65,.6,.06),'SteelDark','DETAIL',.004)
    # Thin open landscape/screen modules are decorative boundaries, NOT ballistic protection.
    for side in (-1,1):
        for j in range(5):
            yy=deckdepth+1+(d-deckdepth-2)*(j+.5)/5
            m.box('ScenicEdgePosts',(side*(w/2+.3),yy,z+.55),(.07,.07,1.10),'SteelDark','DETAIL',.003)
        for zz in (.45,.95):m.box('ScenicEdgeRails',(side*(w/2+.3),(deckdepth+d)/2,z+zz),(.05,d-deckdepth,.035),'Galvanized','DETAIL',.002)
    m.box('SetIdentity',(0,-.63,z+h+.04),(5.3,.08,.53),'SteelDark','DETAIL',.008)
    m.label('EGITIM ALANI / SET',(0,-.68,z+h+.04),.25,'White',name='SetTitle')
    m.notes.append('RANGE_SET is fictional CGI scenery only. Dimensions are artistic. No live-fire suitability, ballistic containment, protective material or safe-distance claim.')


def build(settings):
    settings.checked();m=Model(settings)
    if settings.kind in ('HQ','UNIT'):build_office(m)
    elif settings.kind=='HANGAR':build_hangar(m)
    elif settings.kind=='SHELTER':build_shelter(m)
    else:build_range_set(m)
    return m.finish()


def validation(m):
    # Use the unchanged source topology validator; explicit notes avoid its old runtime text.
    r=A.validate_model(m)
    r['version']=VERSION;r['family']=m.cfg.kind;r['notes']=list(m.notes)
    known={p.name for p in m.parts}
    for p in m.parts:
        if len(p.uvs)!=len(p.faces):r['errors'].append('UV face mismatch '+p.name)
        for f,uv in zip(p.faces,p.uvs):
            if len(f)!=len(uv) or any(not isfinite(x) for pair in uv for x in pair):r['errors'].append('UV invalid '+p.name);break
        if len(p.faces)!=len(p.material_ids):r['errors'].append('Material length '+p.name)
    for port in m.ports:
        if port['role']=='PEDESTRIAN' and (port['width']<=0 or port['height']<=0):r['errors'].append('Invalid pedestrian contract.')
    for door in m.doors:
        if door['part'] not in known:r['errors'].append('Unresolved door part '+door['part'])
    r['ports']=m.ports;r['door_parts']=len(m.doors);r['status']='PASS' if not r['errors'] else 'FAIL'
    r['blender_runtime_tested']=False;r['ue_runtime_tested']=False
    return r


def door_transform(m,p):
    """Placement for the separately pivot-local door; returns location + Z rotation."""
    d=next((d for d in m.doors if d['part']==p.name),None)
    if not d:return p.pivot,0.
    t=d['open_fraction']
    loc=tuple(d['closed'][j]*(1-t)+d['opened'][j]*t for j in range(3))
    return loc,d.get('angle',0)*t

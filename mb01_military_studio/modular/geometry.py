# SPDX-License-Identifier: MIT
"""14 bounded visual facade modules; real openings, shared material roles and pivots.
Source assembly coordinates: X across facade, Y inward, Z upward.
Output coordinates match MB01: +X inward, +Y left, +Z upward, metre units.
This is an artistic mesh assembly, not a structural or protection calculation.
"""
from dataclasses import asdict
from math import pi, radians
from ..vendor import as07_reference as A
from .catalog import require
from .contracts import ModuleInput, digest
from ..mb_common import canonical

VERSION = '0.2.0-alpha.1'


class ModuleModel:
    def __init__(self, settings):
        self.cfg = settings.checked()
        self.spec = require(settings.module_id)
        self.parts = []
        self.labels = []
        self.doors = []
        self.ports = []
        self.openings = []
        self.wall_boxes = []
        self.notes = ['One facade module, not a complete building.',
                      'Assembly contacts are intentional; not a Boolean-unioned CAD solid.',
                      'No structural, military-code or ballistic performance is represented.']
        self._parts = {}
        self._finished = False

    def part(self, role, group='DETAIL', bevel=.005, pivot=(0., 0., 0.)):
        if role not in self._parts:
            name = 'SM_MB02_' + self.spec.id.replace('.', '_') + '__' + role
            p = A.MeshPart(name, group, 0. if self.cfg.detail == 'DRAFT' else bevel, pivot)
            self.parts.append(p)
            self._parts[role] = p
        return self._parts[role]

    def box(self, role, center, dims, mat, group='DETAIL', bevel=.005, axes=A.IDENTITY):
        self.part(role, group, bevel).box(center, dims, mat, axes)
        if role == 'Wall':
            self.wall_boxes.append({'center_source': tuple(center), 'dims': tuple(dims)})

    def wall(self, aperture=None, metal=False):
        w, h, t = self.cfg.width, self.cfg.height, self.cfg.thickness
        material = 'RoofOlive' if metal else self.cfg.style.wall_material
        if aperture is None:
            self.box('Wall', (0, t/2, h/2), (w, t, h), material, 'BODY')
        else:
            ow, bottom, oh = aperture
            top = bottom + oh
            if not (0. < ow < w-.18 and 0. <= bottom < top <= h-.12):
                raise ValueError('Aperture does not fit the bounded module.')
            self.openings.append({'width': ow, 'bottom': bottom, 'height': oh,
                                  'center_output': canonical((0, t/2, bottom+oh/2))})
            pier = (w-ow)/2
            for sign in (-1, 1):
                self.box('Wall', (sign*(ow/2+pier/2), t/2, h/2), (pier, t, h), material, 'BODY')
            if bottom > 0:
                self.box('Wall', (0, t/2, bottom/2), (ow, t, bottom), material, 'BODY')
            self.box('Wall', (0, t/2, (top+h)/2), (ow, t, h-top), material, 'BODY')
        # Applied base facing, clipped at all door openings; not a duplicate floor.
        baseh = .38 if not metal else .48
        spans = [(-w/2, w/2)]
        if aperture is not None and aperture[1] < baseh:
            spans = [(-w/2, -aperture[0]/2), (aperture[0]/2, w/2)]
        for lo, hi in spans:
            self.box('Plinth', ((lo+hi)/2, -.023, baseh/2), (hi-lo, .046, baseh),
                     self.cfg.style.plinth_material, 'FACADE', .004)
        # Fine top reveal: visually coherent with a later continuous coping module.
        self.box('HeadReveal', (0, -.009, h-.105), (w, .018, .014), 'Joint', 'DETAIL', .001)
        if metal:
            # Ribs remain on piers or below/above aperture; never cross a clear opening.
            n = max(3, int(w/.58))
            for k in range(1, n):
                x = -w/2 + w*k/n
                intervals = [(.5, h-.14)]
                if aperture and abs(x) < aperture[0]/2 + .025:
                    intervals = [(.5, aperture[1]-.025), (aperture[1]+aperture[2]+.025, h-.14)]
                for z0, z1 in intervals:
                    if z1-z0 > .06:
                        self.box('PanelSeams', (x, -.018, (z0+z1)/2), (.024, .036, z1-z0),
                                 'RoofOliveLight', 'DETAIL', .0015)

    def frame(self, ow, bottom, oh, transom=False, mullion=True):
        t = self.cfg.thickness
        f, y = .06, min(.09, t*.4)
        mat = self.cfg.style.frame_material
        for sign in (-1, 1):
            self.box('WindowFrames', (sign*(ow/2-f/2), y, bottom+oh/2), (f, .11, oh), mat, 'FACADE', .003)
        for z in (bottom+f/2, bottom+oh-f/2):
            self.box('WindowFrames', (0, y, z), (ow-2*f, .11, f), mat, 'FACADE', .003)
        if mullion:
            self.box('WindowFrames', (0, y, bottom+oh/2), (.046, .10, oh-.12), mat, 'FACADE', .002)
        if transom:
            self.box('WindowTransom', (0, y, bottom+oh*.67), (ow-.12, .10, .038), mat, 'FACADE', .002)
        self.box('Glass', (0, y+.025, bottom+oh/2), (ow-.12, .014, oh-.12), 'Glass', 'GLASS', 0.)
        # Reveal edges and projecting sill with a shallow underside drip detail.
        for sign in (-1, 1):
            self.box('RevealReturns', (sign*(ow/2+.012), t*.46, bottom+oh/2),
                     (.024, t*.95, oh), self.cfg.style.wall_material, 'FACADE', .002)
        self.box('Sill', (0, .025, bottom-.036), (ow+.16, .38, .072), 'ConcreteLight', 'FACADE', .005)
        self.box('SillDrip', (0, -.119, bottom-.07), (ow+.10, .014, .008), 'Joint', 'DETAIL', .001)

    def window(self, narrow=False, shade=False, unit=False, clerestory=False, glazed=False):
        w, h = self.cfg.width, self.cfg.height
        if clerestory:
            ow, bottom, oh = w-.48, h-1.6, 1.15
        elif glazed:
            ow, bottom, oh = w-.54, .32, h-.62
        else:
            ow = min(1.20, w*.32) if narrow else min(2.16, w*.55)
            bottom = .88
            oh = min(1.68 if unit else 1.82, h-bottom-.40)
        self.wall((ow, bottom, oh), metal=clerestory)
        self.frame(ow, bottom, oh, transom=glazed or (not narrow and not unit), mullion=not narrow)
        if unit:
            self.box('Blind', (0, self.cfg.thickness+.05, bottom+oh-.20), (ow-.15, .025, .34), 'Blind', 'DETAIL', .002)
        if shade:
            z = bottom+oh+.14
            for k in range(3):
                self.box('SunshadeFins', (0, -.12-k*.15, z), (ow+.24, .09, .046),
                         'RoofOlive', 'DETAIL', .002)
            for x in (-ow*.37, ow*.37):
                self.box('SunshadeBrackets', (x, -.25, z-.044), (.038, .60, .05),
                         self.cfg.style.frame_material, 'DETAIL', .002)

    def ventilation(self, hangar=False):
        w, h = self.cfg.width, self.cfg.height
        ow = min(w-.60, 2.6)
        bottom = h*.48 if hangar else .98
        oh = min(1.75 if hangar else 1.36, h-bottom-.45)
        self.wall((ow, bottom, oh), metal=hangar)
        f=.07; mat=self.cfg.style.frame_material
        for x in (-ow/2+f/2, ow/2-f/2):
            self.box('VentFrame', (x, .09, bottom+oh/2), (f, .19, oh), mat, 'FACADE', .003)
        for z in (bottom+f/2, bottom+oh-f/2):
            self.box('VentFrame', (0, .09, z), (ow-.14, .19, f), mat, 'FACADE', .003)
        n=max(4, int((oh-.17)/.13))
        for i in range(n):
            z=bottom+.13+(oh-.26)*i/max(1,n-1)
            self.box('VentBlades', (0, .09, z), (ow-.18, .20, .025), 'RoofOliveLight',
                     'DETAIL', .0015, axes=A.euler_axes(radians(27),0,0))
        # Intentional dark screen; not a claimed performance-rated ventilation assembly.
        self.box('VentScreen', (0,self.cfg.thickness+.017,bottom+oh/2),
                 (ow-.15,.016,oh-.14),'Interior','DETAIL',0.)

    def entry(self, double=False, glazed=False, canopy=False, metal=False):
        w,h,t=self.cfg.width,self.cfg.height,self.cfg.thickness
        ow=min(2.3,w-.7) if double else min(1.18,w-.7)
        dh=2.62 if double else 2.30
        self.wall((ow,0.,dh),metal=metal)
        if metal:
            # Hangar personnel door set. Real-world model: outward-opening (-Y) 50 mm insulated steel
            # leaf (folded pull-face pan over a core) on lift-off butt hinges whose axis lies 8 mm
            # outside the pull face, in a pressed-steel wrap frame set back in the clad reveal so its
            # 65 mm face stands 4 mm proud of the leaf (as on a real outward door); the cladding
            # returns into the reveal in front of it. Rebate soffit through the wall, stop behind the
            # push face. Everything that swings is in DoorLeaf_<i>; frame-side hardware is in
            # DoorHardware. Leaf pieces are >= 5.5 mm thick so the clamped 2 mm bevel never collapses
            # them. glazed = wired-glass vision panel (single leaf only); the canopy is built by
            # expansion_geometry._canopy, not here.
            YZX=((0,1,0),(0,0,1),(1,0,0));mat=self.cfg.style.frame_material;draft=self.cfg.detail=='DRAFT'
            seams=self._parts.get('PanelSeams')   # rib side faces as built by wall(); none -> no guard
            ribx={round(abs(v[0]),6) for v in seams.vertices} if seams else set()
            def clear_rib(v):
                # Keep an end face (half-width v) >= 3 mm off every cladding-rib side face.
                return v-.006 if any(abs(v-r)<.003 for r in ribx) else v
            def ring(p,outer,hole,ya,yb,m):
                # Slab with a rectangular through-hole: 16 convex quads, no internal bevel seams.
                (x0,x1,z0,z1),(h0,h1,k0,k1)=outer,hole
                o=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)];n=[(h0,k0),(h1,k0),(h1,k1),(h0,k1)]
                v=[(a,yy,b) for yy in (ya,yb) for a,b in o+n];fs=[]
                for i in range(4):
                    j=(i+1)%4;fs+=[(i,j,4+j,4+i),(12+i,12+j,8+j,8+i),(i,8+i,8+j,j),(4+i,4+j,12+j,12+i)]
                p.primitive(v,fs,m)
            y=min(.095,t*.4);yp=y-.018;ye=yp+.008;yi=ye+.050   # pivot plane, pull face, push face
            yf=ye-.004                                           # frame face plane
            zs0,zs1=.045,dh-.083                                 # jamb stops: threshold bar -> head stop
            for s in (-1,1):   # jamb: face + rebate side + soffit through the wall, 4 mm interior lip
                self.box('DoorFrame',(s*(ow/2-.0325),(yf+t+.004)/2,dh/2),(.065,t+.004-yf,dh),mat,'FACADE',.003)
                self.box('DoorFrame',(s*(ow/2-.074),yi+.019,(zs0+zs1)/2),(.018,.030,zs1-zs0),mat,'FACADE',.003)
                self.box('DoorHardware',(s*(ow/2-.074),yi+.00225,(zs0+zs1)/2),(.014,.0035,zs1-zs0),
                         'Joint','DETAIL',.001)                                                      # gasket
            self.box('DoorFrame',(0.,(yf+t+.004)/2,dh-.0325),(ow-.130,t+.004-yf,.065),mat,'FACADE',.003)
            self.box('DoorFrame',(0.,yi+.019,dh-.074),(ow-.130,.030,.018),mat,'FACADE',.003)
            self.box('DoorHardware',(0.,yi+.00225,dh-.074),(ow-.134,.0035,.014),'Joint','DETAIL',.001)
            # Threshold: weathered nose across the whole reveal, then (between the jambs) a stop bar
            # under the jamb stops, a sloped interior face (no trip edge) and a ramp.
            zy=.010+.006*(yf+.044)/(yi+.048)                     # sloped top line at the frame face
            xa=ow/2-.065;th=self.part('Threshold','DETAIL',.002)
            th.prism([(-.050,0.),(yf,0.),(yf,zy),(-.044,.010),(-.050,.006)],(-ow/2,0.,0.),YZX,ow,'Galvanized')
            th.prism([(yf,0.),(t+.030,0.),(t+.030,.006),(yi+.064,.018),(yi+.034,.045),(yi+.004,.045),
                      (yi+.004,.016),(yf,zy)],(-xa,0.,0.),YZX,2*xa,'Galvanized')
            # Rain deflector at the cladding face over the opening: 45 deg nose and a drip lip 45 mm
            # proud of the wall, 3 mm shadow joint above the head reveal; ribs over the opening lap it.
            xf=clear_rib(ow/2+.040)
            head=[(.002,dh+.003),(.002,dh+.034),(-.038,dh+.034),(-.045,dh+.027),(-.045,dh-.014),
                  (-.039,dh-.014),(-.039,dh+.003)]
            self.part('DoorHeadFlashing','FACADE',.002).prism(head,(-xf,0.,0.),YZX,2*xf,mat)
            count=2 if double else 1;clear=ow-.15
            leafw=(clear-(.014 if double else 0))/count
            zb,zt=.035,dh-.069;lh=zt-zb;vision=glazed and not double   # 4 mm head gap
            yc0,yc1=yi+.038,min(yi+.062,t+.002);ym=(yc0+yc1)/2         # closer slide channel
            hw=self.part('DoorHardware','DETAIL',.001)
            if double:   # one channel with close-sequence coordinator: passive leaf closes first
                hw.box((0.,ym,dh-.075),(clear-.20,yc1-yc0,.020),'Galvanized')
            for i in range(count):
                c=-clear/2+leafw/2+i*(leafw+.014)
                left=i==0
                px=c-leafw/2 if left else c+leafw/2
                q=1 if left else -1                               # hinge -> lock direction along X
                X=lambda s,px=px,q=q:px+q*s
                L0,L1=c-leafw/2,c+leafw/2
                pivot=(px,y-.018,.035)
                p=self.part('DoorLeaf_'+str(i),'DOOR',.002,pivot)
                active=not double or i==1                         # right-hand leaf of a pair
                if vision:   # core / folded pull-face pan / beads / glass around a 300x600 aperture
                    gw=min(.30,leafw-.44);gx0,gx1=c-gw/2,c+gw/2;gz0,gz1=1.30,min(1.90,zt-.25)
                    def ap(d):return (gx0-d,gx1+d,gz0-d,gz1+d)
                    ring(p,(L0,L1,zb,zt),ap(0.),ye+.003,yi,'RoofOlive')
                    ring(p,(L0+.004,L1-.004,zb+.004,zt-.004),ap(.004),ye,ye+.008,'RoofOlive')
                    ring(p,ap(.018),ap(-.012),ye-.006,ye+.0045,'SteelDark')
                    ring(p,ap(.018),ap(-.006),yi-.0045,yi+.006,'SteelDark')
                    p.box((c,ye+.0075,(gz0+gz1)/2),(gw+.016,.006,gz1-gz0+.016),'Glass')
                else:        # core + pull-face pan standing 3 mm proud, inset 4 mm (folded edge)
                    p.box((c,(ye+.003+yi)/2,(zb+zt)/2),(leafw,yi-ye-.003,lh),'RoofOlive')
                    p.box((c,ye+.004,(zb+zt)/2),(leafw-.008,.008,lh-.008),'RoofOlive')
                p.box((c,(ye+yi)/2,.02875),(leafw-.040,yi-ye-.020,.0135),'Rubber')          # drop seal
                ka=.038 if double and i==1 else .030                                         # astragal leg
                p.box(((L0+ka+L1-.030)/2,ye-.0005,.175),(L1-.030-L0-ka,.006,.250),'Galvanized')  # kick plates
                p.box((c,yi+.0005,.175),(leafw-.060,.006,.250),'Galvanized')
                if active:
                    p.box((c,ye-.0005,2.02 if vision else 1.55),(.140,.006,.050),'White')     # door ID plate
                    xh=X(leafw-.065)                                                         # 65 mm backset
                    p.box((xh,ye-.003,1.035),(.040,.011,.240),'Galvanized')                  # long backplate
                    if draft:
                        p.box((xh,ye-.024,1.05),(.022,.032,.022),'Galvanized')
                    else:
                        p.cylinder((xh,ye-.008,1.05),(xh,ye-.040,1.05),.011,'Galvanized',10 if vision else 12)
                        p.cylinder((xh,ye-.008,.958),(xh,ye-.014,.958),.0085,'Galvanized',8)  # euro cylinder
                    p.box((xh-q*.0625,ye-.049,1.05),(.140,.018,.020),'Galvanized')            # lever
                    p.box((xh-q*.1235,ye-.030,1.05),(.018,.020,.020),'Galvanized')            # return to door
                    # Push side: EN 1125 style panic bar between lock case and hinge-end case.
                    p.box((X(leafw-.055),yi+.042,.995),(.080,.085,.110),'SteelDark')
                    p.box((X(.115),yi+.042,.995),(.070,.085,.080),'SteelDark')
                    p.box((X((.150+leafw-.095)/2),yi+.0655,.995),(leafw-.245,.030,.040),'Galvanized')
                if double and i==1:   # astragal: 65 mm cover strip lapping the passive leaf, 2 mm air
                    p.prism([(.040,ye+.003),(.040,ye-.0075),(-.025,ye-.0075),(-.025,ye-.002),(.007,ye-.002),
                             (.007,ye+.003)],(0.,0.,zb+.010),A.IDENTITY,lh-.020,'RoofOlive')
                if double and i==0:   # passive leaf: flush bolts (retracted) and strike in the meeting edge
                    my=(ye+yi)/2
                    for zz in (zb+.135,zt-.135):
                        p.box((L1-.0005,my,zz),(.006,.020,.150),'Galvanized')
                    p.box((L1-.0005,my,1.01),(.006,yi-ye-.012,.220),'Galvanized')
                    if not draft:
                        p.cylinder((L1-.010,my,zb+.0005),(L1-.010,my,.021),.006,'Galvanized',6)
                        p.cylinder((L1-.010,my,zt-.0005),(L1-.010,my,zt+.002),.006,'Galvanized',6)
                # Overhead slide-channel closer on the push side: body, folded arm and slider stud.
                p.box((X(.175),yi+.0225,dh-.155),(.270,.046,.060),'Galvanized')
                p.beam((X(.065),yi+.022,dh-.119),(X(.365),yi+.050,dh-.119),.016,.012,'SteelDark')
                if not draft:
                    p.box((X(.365),ym,dh-.099),(.012,.012,.028),'Galvanized')
                if not double:
                    hw.box((X(.31),ym,dh-.075),(.42,yc1-yc0,.020),'Galvanized')
                    hw.box((ow/2-.0655 if left else -(ow/2-.0655),(ye+yi)/2,1.01),(.002,yi-ye-.012,.220),
                           'Galvanized')                                                     # strike plate
                if not draft:   # three lift-off butt hinges: frame half below, leaf half above, 2 mm split
                    for zc in (zb+.25,zb+.52*lh,zt-.22):
                        hw.cylinder((px,yp,zc-.056),(px,yp,zc-.001),.0075,'Galvanized',10)
                        hw.box((px-q*.0085,yp+.019,zc-.0285),(.004,.042,.049),'Galvanized')
                        p.cylinder((px,yp,zc+.001),(px,yp,zc+.056),.0075,'Galvanized',12)
                        p.box((px-q*.0005,yp+.019,zc+.0285),(.006,.042,.049),'Galvanized')
                self.doors.append({'part':p.name,'closed':pivot,'opened':pivot,
                                   'angle':(-1 if left else 1)*radians(96),
                                   'kind':'HINGE','rest_pose':'closed','runtime_blueprint':False})
            self.ports.append({'name':'ENTRY_OPENING','role':'PEDESTRIAN_OPENING',
                               'location_source':(0,0.,0.),'normal_source':(0.,-1.,0.),
                               'clear_width_m':ow-.15,'surface_offset_m':0.,
                               'landing_required':True,'pk01_bridge_ready':False})
            return
        f=.065; y=min(.095,t*.4); mat=self.cfg.style.frame_material
        for x in (-ow/2+f/2,ow/2-f/2):
            self.box('DoorFrame',(x,y,dh/2),(f,.15,dh),mat,'FACADE',.003)
        self.box('DoorFrame',(0,y,dh-f/2),(ow-.13,.15,f),mat,'FACADE',.003)
        self.box('Threshold',(0,t*.50,.012),(ow-.12,t+.16,.024),'Galvanized','DETAIL',.002)
        count=2 if double else 1
        clear=ow-.15
        leafw=(clear-(.014 if double else 0))/count
        leafh=dh-.10
        for i in range(count):
            c=-clear/2+leafw/2+i*(leafw+.014)
            left = i==0
            px=c-leafw/2 if left else c+leafw/2
            pivot=(px,y-.018,.035)
            p=self.part('DoorLeaf_'+str(i),'DOOR',.003,pivot)
            if glazed:
                a=.065
                for x in (c-leafw/2+a/2,c+leafw/2-a/2):
                    p.box((x,y-.018,.035+leafh/2),(a,.065,leafh),mat)
                for z in (.035+a/2,.035+leafh-a/2):
                    p.box((c,y-.018,z),(leafw-2*a,.065,a),mat)
                p.box((c,y-.018,.035+leafh/2),(leafw-2*a,.014,leafh-2*a),'Glass')
            else:
                p.box((c,y-.018,.035+leafh/2),(leafw,.065,leafh),'RoofOlive')
                p.box((c,y-.056,.25),(leafw-.12,.014,.32),'Galvanized')
                p.box((c,y-.056,leafh-.12),(leafw-.16,.012,.055),'Yellow')
            hx=c+(leafw*.34 if left else -leafw*.34)
            p.box((hx,y-.086,1.06),(.035,.046,.24),'Galvanized')
            if self.cfg.detail!='DRAFT':
                for z in (.38,1.85):
                    p.cylinder((px,y-.018,z-.05),(px,y-.018,z+.05),.020,'Galvanized',10)
            self.doors.append({'part':p.name,'closed':pivot,'opened':pivot,
                               'angle':(-1 if left else 1)*radians(96),
                               'kind':'HINGE','rest_pose':'closed','runtime_blueprint':False})
        if canopy:
            z=dh+.24
            self.box('EntryCanopy',(0,-.52,z),(w-.12,1.22,.12),'SteelDark','DETAIL',.007)
            self.box('CanopySoffit',(0,-.52,z-.071),(w-.28,1.04,.020),'ConcreteLight','DETAIL',.002)
            for x in (-(w-.5)/2,(w-.5)/2):
                self.part('CanopyBrackets').beam((x,.08,z-.02),(x,-.72,z-.22),.045,.06,'SteelDark')
            self.box('CanopyLight',(0,-.42,z-.086),(ow*.68,.10,.015),'LightWarm','DETAIL',.001)
        # An opening is not a completed walkway port. A separate landing is required.
        self.ports.append({'name':'ENTRY_OPENING','role':'PEDESTRIAN_OPENING',
                           'location_source':(0,0.,0.),'normal_source':(0.,-1.,0.),
                           'clear_width_m':ow-.15,'surface_offset_m':0.,
                           'landing_required':True,'pk01_bridge_ready':False})

    def finish(self):
        if self._finished:return self
        w,h,t=self.cfg.width,self.cfg.height,self.cfg.thickness
        for p in self.parts:
            p.vertices=[canonical(v) for v in p.vertices]
            p.pivot=canonical(p.pivot)
        for d in self.doors:
            d['closed']=canonical(d['closed']);d['opened']=canonical(d['opened'])
        for p in self.ports:
            p['location_m']=canonical(p.pop('location_source'))
            p['normal']=canonical(p.pop('normal_source'))
        for label,loc,no in (
            ('LEFT',(0.,w/2,0.),(0.,1.,0.)),('RIGHT',(0.,-w/2,0.),(0.,-1.,0.))):
            self.ports.append({'name':'JOIN_'+label,'role':'FACADE_JOIN','location_m':loc,
                               'normal':no,'height_m':h,'thickness_m':t,
                               'profile':'MB01_FACADE_RECT_V1','scenery_only':True})
        self._finished=True
        return self


def build(settings):
    s=settings.checked();m=ModuleModel(s);b=m.spec.builder
    if b=='plain':m.wall()
    elif b=='window':m.window()
    elif b=='narrow':m.window(narrow=True)
    elif b=='sunshade':m.window(shade=True)
    elif b=='unit_window':m.window(unit=True)
    elif b=='glazed':m.window(glazed=True)
    elif b=='clerestory':m.window(clerestory=True)
    elif b=='vent':m.ventilation()
    elif b=='hangar_louver':m.ventilation(hangar=True)
    elif b=='service':m.entry()
    elif b=='double':m.entry(double=True)
    elif b=='lobby':m.entry(double=True,glazed=True,canopy=True)
    elif b=='metal':m.wall(metal=True)
    elif b=='hangar_service':m.entry(metal=True)
    elif b.startswith('hg_'):
        from .expansion_geometry import generate
        generate(m,b)
    else:raise ValueError('Generator is not implemented: '+b)
    return m.finish()


def part_transform(model,part):
    d=next((d for d in model.doors if d['part']==part.name),None)
    return (part.pivot,d['angle']*model.cfg.door_open) if d else (part.pivot,0.)


def geometry_key(model):
    """No cell UUID, door pose or palette in geometry identity; content is hashed."""
    return digest([{'role':p.group,'vertices':p.vertices,'faces':p.faces,
                    'uvs':p.uvs,'mats':p.material_names,'ids':p.material_ids,
                    'pivot':p.pivot,'bevel':p.bevel} for p in model.parts])


def validation(model):
    report=A.validate_model(model)
    report['generator']=VERSION
    report['module_id']=model.spec.id
    report['openings']=model.openings
    report['blender_runtime_verified']=False
    report['ue_runtime_verified']=False
    for p in model.parts:
        if len(p.faces)!=len(p.uvs) or len(p.faces)!=len(p.material_ids):
            report['errors'].append('Face attribute count: '+p.name)
        for f,uv,mi in zip(p.faces,p.uvs,p.material_ids):
            if len(f)!=len(uv):report['errors'].append('UV corner count: '+p.name)
            if not 0<=mi<len(p.material_names):report['errors'].append('Material index: '+p.name)
    # Confirm source wall volumes do not occupy the intended aperture centre.
    for opening in model.openings:
        out=opening['center_output']
        centre=(-out[1],out[0],out[2])
        for box in model.wall_boxes:
            if all(abs(centre[k]-box['center_source'][k]) < box['dims'][k]/2-1e-8 for k in range(3)):
                report['errors'].append('Hidden solid wall behind opening.')
    report['status']='PASS' if not report['errors'] else 'FAIL'
    return report

"""Arched aircraft shelter: steel arch ribs springing from I-columns, purlins and a curved
standing-seam deck over an insulated liner, precast plank side walls with a louvred upper band,
a profiled rear wall (precast dado, trapezoidal sheet) with a steel personnel door, eave gutters,
verge flashings, identity sign and services. Open front.

Design coordinates of core.Model: x across (+-a = column lines), y from the open front (0) to the
rear (d), z up from the slab top (base_height). Rules as in hangar_studio: closed solids, parts that
touch are bedded 1-3 mm or meet face to face with opposite normals, never same-facing coplanar."""
from math import asin, sin, cos, sqrt, ceil, floor, pi, radians
import re
from ..vendor import as07_reference as A
from ..modular.geometry import ModuleModel as C

ARC_SEGMENTS={'DRAFT':28,'WORKING':48,'HERO':64}
SEAM_PITCH=.60                       # standing-seam pan width along the depth
SEAM=((-.016,0.),(-.009,.055),(.009,.055),(.016,0.))   # (y, rise) over the pan
HW=2.30                              # precast plank dado (side and rear walls)
COPE=.06                             # coping height
RIB_D,RIB_W=.40,.20                  # arch rib depth (radial) and flange width
OV_FRONT,OV_REAR=.35,.45             # deck overhang past the end ribs
PLANK=((.031,.756),(.766,1.526),(1.536,HW))   # precast planks with 10 mm sealant joints, on a 31 mm mortar bed


class Arch:
    """Circle through the column heads (+-a, h) and the crown (0, h+rise)."""
    def __init__(self,s):
        b=s.base_height;self.a=a=s.width/2;self.d=s.depth;self.h=s.floor_height;self.b=b;r=s.roof_rise
        self.R=R=(a*a+r*r)/(2*r);self.zc=b+self.h+r-R;self.alpha=asin(a/R)
        self.Rl=R+RIB_D/2+.20;self.Rd=self.Rl+.005            # liner (purlin top), deck pans
        self.te=asin((a+.40)/self.Rd)                           # deck edge 400 mm past the column line
        self.n=ARC_SEGMENTS[s.detail]
    def pt(self,r,t,y):return (r*sin(t),y,self.zc+r*cos(t))
    def T(self,t):return (cos(t),0.,-sin(t))
    def N(self,t):return (sin(t),0.,cos(t))
    def z_at(self,r,x):return self.zc+sqrt(max(0.,r*r-x*x))
    def stations(self,t0,t1,n=None):
        n=n or max(2,round(self.n*(t1-t0)/(2*self.te)));return [t0+(t1-t0)*k/n for k in range(n+1)]


def _oriented(p,pts,want,mat):
    """One planar polygon whose normal points along `want` (single-sided closure)."""
    a,b,c=pts[0],pts[1],pts[2];n=A.cross(A.sub(b,a),A.sub(c,a))
    if A.dot(n,want)<0:pts=pts[::-1]
    p.primitive(list(pts),[tuple(range(len(pts)))],mat,closed=False)


def _surface(p,arch,thetas,profile,radius,mat,out):
    """Single-sided sheet over the arc: rows = arc stations, columns = (y, radial offset) knots.
    out=+1 faces outward (deck), -1 inward (liner). UV0 = (arc length, y) in metres."""
    J=len(profile)
    verts=[arch.pt(radius+o,t,y) for t in thetas for y,o in profile]
    uvv=[(radius*t,y) for t in thetas for y,o in profile]
    faces=[(k*J+j,k*J+j+1,(k+1)*J+j+1,(k+1)*J+j) for k in range(len(thetas)-1) for j in range(J-1)
           if profile[j+1][0]-profile[j][0]>1e-9]
    if out>0:faces=[tuple(reversed(f)) for f in faces]      # (+y) x (+theta) is the inward normal
    f0=len(p.faces);p.primitive(verts,faces,mat,smooth=True,closed=False)
    for i,f in enumerate(faces):p.uvs[f0+i]=[uvv[v] for v in f]


def _deck_profile(y0,y1):
    pts=[(y0,0.)];ys=y0+.30
    while ys<y1-.30+1e-9:
        pts+=[(ys+u,v) for u,v in SEAM];ys+=SEAM_PITCH
    return pts+[(y1,0.)]


def sign_text(name):
    """'AS07_04' -> ('AIRCRAFT SHELTER', '04'): trailing digits become the bay number."""
    found=re.search(r'(\d+)\s*$',name.strip())
    return found.group(1)[-3:] if found else '01'


# ------------------------------------------------------------------------------------- frame
def _frame(m,s,arch):
    a,d,b,n=arch.a,arch.d,arch.b,s.bays;sa,ca=sin(arch.alpha),cos(arch.alpha)
    hero=s.detail=='HERO';bolts=s.detail!='DRAFT'
    rib=A.i_profile(RIB_W,RIB_D,.010,.016)                   # (y, radial)
    col=[(v,u) for u,v in A.i_profile(.25,.40,.010,.016)]   # web in the frame plane, flanges at x +-.20
    z1=b+arch.h-.2*ca-.03;z0=z1-.02                        # shoe seat, cap plate underside
    arc=2*arch.alpha*arch.R;nseg=max(2,2*round(arc/9.))     # spliced rib lengths, crown splice
    fx=m.p('FrameFasteners','DETAIL',.001) if bolts else None
    for i in range(n+1):
        y=i*d/n;rp=m.p(f'ArchRib_{i:02d}','STRUCTURE',.004)
        ts=[-arch.alpha+2*arch.alpha*k/nseg for k in range(nseg+1)]
        for t0,t1 in zip(ts,ts[1:]):
            rp.arch(rib,arch.R,arch.zc,t0,t1,y,max(2,round(arch.n*(t1-t0)/(2*arch.alpha))),'SteelDark',smooth=True)
        for t in ts[1:-1]:      # bolted end-plate pair at each splice
            m.box('RibSplices',arch.pt(arch.R,t,y),(.04,RIB_W+.06,RIB_D+.08),'SteelDark','DETAIL',.002,
                  axes=(arch.T(t),(0,1,0),arch.N(t)))
            if hero:
                for dy in (-.07,.07):
                    for dr in (-.15,.15):
                        c=A.add(arch.pt(arch.R+dr,t,y+dy),A.mul(arch.T(t),-.035))
                        fx.cylinder(c,A.add(c,A.mul(arch.T(t),.07)),.012,'Galvanized',6)
        for sx in (-1,1):
            x=sx*a
            m.p('Columns','STRUCTURE',.004).prism(col,(x,y,b+.03),A.IDENTITY,z0-b-.03,'SteelDark')
            m.box('ColumnCaps',(x,y,z0+.01),(.44,.25,.02),'SteelDark','DETAIL',.002)
            m.box('BasePlates',(x,y,b+.015),(.56,.44,.03),'SteelDark','DETAIL',.002)
            # Springing shoe: welded bearing block from the cap to the rib's radial end plate.
            shoe=[(-.20,z1),(.20,z1),(.2*sa,b+arch.h+.2*ca),(-.2*sa,b+arch.h-.2*ca)]
            m.p('SpringingShoes','STRUCTURE',.003).prism([(x+sx*u,v) for u,v in shoe],(0,y-RIB_W/2,0),
                ((1,0,0),(0,0,1),(0,1,0)),RIB_W,'SteelDark')
            if bolts:
                for dx in (-.20,.20):
                    for dy in (-.17,.17):
                        fx.cylinder((x+dx,y+dy,b+.036),(x+dx,y+dy,b+.075),.016,'Galvanized',6)
                        fx.cylinder((x+dx,y+dy,b+.03),(x+dx,y+dy,b+.042),.03,'Galvanized',6)
    # Purlins: lipped C sections on the rib top flanges, eave purlins clear of the wall heads.
    ta=asin((a-.20)/(arch.Rl))
    npur=max(5,ceil(2*ta*arch.Rl/1.6)+1)
    C_=[(0.,0.),(.065,0.),(.065,.02),(.062,.02),(.062,.003),(.003,.003),(.003,.195),(.062,.195),(.062,.178),
        (.065,.178),(.065,.198),(0.,.198)]
    pur=m.p('Purlins','STRUCTURE',.0015);cl=m.p('PurlinCleats','DETAIL',.0015) if hero else None
    ys0,ys1=-OV_FRONT+.08,d+.12
    for j in range(npur):
        t=-ta+2*ta*j/(npur-1);sg=-1. if t>1e-9 else 1.            # lips face the crown
        prof=[(sg*u,v) for u,v in C_]
        pur.prism(prof,arch.pt(arch.R+RIB_D/2+.001,t,ys0),(arch.T(t),arch.N(t),(0,1,0)),ys1-ys0,'Galvanized')
        if cl:
            for i in range(n+1):
                y=i*d/n;c=A.add(arch.pt(arch.R+RIB_D/2+.075,t,y),A.mul(arch.T(t),-sg*.0055))
                cl.box(c,(.008,.10,.15),'SteelDark',(arch.T(t),(0,1,0),arch.N(t)))
    return npur


# ------------------------------------------------------------------------------------- roof
def _roof(m,s,arch):
    d=arch.d;y0,y1=-OV_FRONT,d+OV_REAR;te=arch.te;th=arch.stations(-te,te)
    prof=_deck_profile(y0,y1)
    _surface(m.p('RoofDeck','ROOF',0.),arch,th,prof,arch.Rd,'RoofOlive',+1)
    _surface(m.p('RoofLiner','ROOF',0.),arch,th,[(y0+.004,0.),(y1-.004,0.)],arch.Rl,'Plaster',-1)
    # Seam ends: closed at both eaves (the deck runs on to the drip over the gutter).
    caps=m.p('RoofDeck')
    for t,sg in ((te,1.),(-te,-1.)):
        for k in range(1,len(prof)-1,4):
            q=[arch.pt(arch.Rd+o,t,yy) for yy,o in prof[k:k+4]]
            _oriented(caps,q,A.mul(arch.T(t),sg),'RoofOlive')
    # Eave closure / drip under the deck edge, 0.5 mm beyond the seam-end plane.
    for t,sg in ((te,1.),(-te,-1.)):
        c=A.add(arch.pt(arch.Rd-.0275,t,(y0+y1)/2),A.mul(arch.T(t),sg*.0015))
        m.box('EaveTrims',c,(.002,y1-y0-.008,.065),'SteelDark','DETAIL',0.,axes=(arch.T(t),(0,1,0),arch.N(t)))
    # Verge (barge) flashings: face leg over the deck/liner edge, return over the pans clear of the seams.
    barge=[(-.006,-.20),(-.003,-.20),(-.003,.070),(.10,.070),(.10,.075),(-.006,.075)]
    for yy,sg in ((y0,1.),(y1,-1.)):
        m.p('VergeFlashings','DETAIL',.001).arch([(sg*u,v) for u,v in barge],arch.Rd,arch.zc,-te,te,yy,
            arch.n,'SteelDark',smooth=True)
        m.p('VergeAccents','DETAIL',0.).arch([(sg*u,v) for u,v in ((-.010,-.13),(-.006,-.13),(-.006,-.085),(-.010,-.085))],
            arch.Rd,arch.zc,-te*.985,te*.985,yy,arch.n,'Yellow',smooth=True)


def _gutters(m,s,arch):
    a,d,b=arch.a,arch.d,arch.b;te=arch.te;y0,y1=-OV_FRONT+.012,d+OV_REAR-.012
    xe=arch.Rd*sin(te);ze=arch.zc+arch.Rd*cos(te);top=ze-.06;w,h=.16,.13
    body=((0.,0.),(0.,-h),(w,-h),(w+.030,-.016),(w+.042,-.016),(w+.042,-.008),(w+.022,-.008),(w-.0045,-h+.004),
          (.004,-h+.004),(.004,0.))
    ys=sorted({(k+.5)*d/s.bays for k in (0,s.bays-1)}|({(s.bays//2+.5)*d/s.bays} if s.bays>=8 else set()))
    for sx in (-1.,1.):
        x0=sx*(xe-.06)
        m.p('Gutters','FACADE',.001).prism(body,(x0,y0,top),((sx,0,0),(0,0,1),(0,1,0)),y1-y0,'Galvanized')
        for yy,ln in ((y0-.002,.002),(y1,.002)):
            m.p('Gutters').prism([(-.002,.002),(-.002,-h-.002),(w+.0015,-h-.002),(w+.0315,-.0175),(w+.044,-.0175),(w+.044,-.0065)],
                (x0,yy,top),((sx,0,0),(0,0,1),(0,1,0)),ln,'Galvanized')
        xg=x0+sx*.08;xp=sx*(a+.27)
        for yy in ys:
            pts=[(xg,yy,top-h+.01),(xg,yy,top-h-.16),(xp,yy,top-h-.38),(xp,yy,b+.24),(xp+sx*.16,yy,b+.09)]
            m.p('Downpipes','FACADE',0.).pipe(pts,.05,'Galvanized',12)
            for zz in (b+.90,b+1.85):     # stand-off clamps into the plank face
                cp=m.p('PipeClamps','DETAIL',.001)
                cp.cylinder((xp,yy,zz-.02),(xp,yy,zz+.02),.058,'Galvanized',12)
                cp.box((sx*(a+.165),yy,zz),(.11,.02,.02),'Galvanized')
            m.box('GutterOutlets',(xg,yy,top-h-.016),(.11,.11,.03),'Galvanized','DETAIL',.001)
    return ys


# ------------------------------------------------------------------------------------- walls
def _side_walls(m,s,arch):
    a,d,b,n=arch.a,arch.d,arch.b,s.bays;bp=d/n
    zt=b+HW+COPE;zh=b+arch.h-.62;zb1=zh+.30            # louvre band, eave beam
    for sx in (-1.,1.):
        def X(u):return sx*(a+u)
        for i in range(n):
            y0,y1=i*bp+.011,(i+1)*bp-.011;yc=(y0+y1)/2;L=y1-y0
            for z0,z1 in PLANK:
                m.box('WallPlanks',(X(.02),yc,b+(z0+z1)/2),(.20,L,z1-z0),'ConcreteLight','BODY',.012,True)
            for z0,z1 in zip([q[1] for q in PLANK[:-1]],[q[0] for q in PLANK[1:]]):
                m.box('PlankJoints',(X(.02),yc,b+(z0+z1)/2),(.16,L-.004,z1-z0+.004),'Joint','DETAIL',0.)
            m.box('MortarBeds',(X(.02),yc,b+.0155),(.18,bp-.44-.002,.031),'Joint','DETAIL',0.)
            m.box('Copings',(X(.03),yc,b+HW+COPE/2),(.26,L,COPE),'Concrete','FACADE',.006)
            # Louvre panel: welded RHS frame, Z blades at 100 mm, mullions at <= 2.6 m.
            fr=m.p('LouvreFrames','FACADE',.002);bl=m.p('LouvreBlades','DETAIL',0.)
            fr.box((X(.01),yc,zt+.03),(.10,L,.06),'SteelDark');fr.box((X(.01),yc,zh-.03),(.10,L,.06),'SteelDark')
            nm=max(1,ceil(L/2.6));edges=[y0+L*k/nm for k in range(nm+1)]
            for k,e in enumerate(edges):
                w=.06;c=e+w/2 if k==0 else (e-w/2 if k==nm else e)
                fr.box((X(.01),c,(zt+zh)/2),(.10,w,zh-zt-.12),'SteelDark')
            nb=max(1,floor((zh-zt-.16)/.10))
            for k in range(nb):
                zc=zt+.06+.08+(zh-zt-.12-.16)*k/max(1,nb-1)
                for e0,e1 in zip(edges,edges[1:]):
                    lo=e0+(.06 if e0==edges[0] else .03)-.002;hi=e1-(.06 if e1==edges[-1] else .03)+.002
                    bl.prism([(sx*(a+.075-u),zc+v) for u,v in C.BLADE],(0,lo,0),((1,0,0),(0,0,1),(0,1,0)),hi-lo,'RoofOlive')
            # Eave beam (C channel, toes inward) and the infill closing the band head to the soffit.
            ch=[(0.,0.),(.10,0.),(.10,.012),(.008,.012),(.008,.288),(.10,.288),(.10,.30),(0.,.30)]
            m.p('EaveBeams','STRUCTURE',.002).prism([(sx*(a+.09-u),zh+v) for u,v in ch],(0,y0,0),((1,0,0),(0,0,1),(0,1,0)),L,'SteelDark')
            x_in,x_out=X(-.08),X(.12)
            prof=[(x_in,zb1+.002),(x_out,zb1+.002),(x_out,arch.z_at(arch.Rl,abs(x_out))-.004),(x_in,arch.z_at(arch.Rl,abs(x_in))-.004)]
            m.p('EaveInfills','BODY',.002).prism(prof,(0,i*bp+.13,0),((1,0,0),(0,0,1),(0,1,0)),bp-.26,'RoofOlive')
    return zt,zh


def _rear_wall(m,s,arch):
    a,d,b=arch.a,arch.d,arch.b;zt=b+HW+COPE
    yi,yo=d+.13,d+.33                         # precast dado (outside the end frame)
    yc=yo-.046                                # sheet crest plane; pans 35 mm, core 47 mm inside it
    X=a+.20
    npost=max(3,ceil(2*a/5.));posts=[-a+2*a*k/npost for k in range(1,npost)]
    # Door between the two posts nearest x = +a/2.
    gaps=list(zip([-X]+posts,posts+[X]));g=min(gaps,key=lambda q:abs((q[0]+q[1])/2-a/2))
    xd=(g[0]+g[1])/2;ow,oh=1.10,2.12
    col=A.i_profile(.20,.30,.010,.014)
    arc=2*arch.alpha*arch.R;nseg=max(2,2*round(arc/9.));splices=[-arch.alpha+2*arch.alpha*k/nseg for k in range(1,nseg)]
    for x in posts:
        near=any(abs(arch.R*sin(t)-x)<.30 for t in splices)
        top=arch.z_at(arch.R-RIB_D/2-(.05 if near else 0.),x)-.015
        m.p('WindPosts','STRUCTURE',.003).prism(col,(x,d-.02,b+.03),A.IDENTITY,top-b-.03,'SteelDark')
        m.box('BasePlates',(x,d-.02,b+.015),(.34,.30,.03),'SteelDark','DETAIL',.002)
    # Planks between posts (sealant joints on the post lines), opening at the door.
    cuts=[-X]+posts+[X];yc_=(yi+yo)/2
    for x0,x1 in zip(cuts,cuts[1:]):
        u0,u1=x0+(.005 if x0>-X else 0.),x1-(.005 if x1<X else 0.)
        spans=[(u0,xd-ow/2,0.,HW),(xd+ow/2,u1,0.,HW),(xd-ow/2,xd+ow/2,oh,HW)] if (x0,x1)==g else [(u0,u1,0.,HW)]
        for v0,v1,w0,w1 in spans:
            for z0,z1 in PLANK:
                z0,z1=max(z0,w0),min(z1,w1)
                if z1-z0>.05:m.box('RearPlanks',((v0+v1)/2,yc_,b+(z0+z1)/2),(v1-v0,yo-yi,z1-z0),'ConcreteLight','BODY',.012,True)
        if x1<X:m.box('PlankJoints',(x1,yc_,b+(PLANK[0][0]+HW)/2),(.012,yo-yi-.04,HW-PLANK[0][0]-.004),'Joint','DETAIL',0.)
    plates=sorted([(-a-.28,-a+.28),(a-.28,a+.28),(xd-ow/2,xd+ow/2)]+[(x-.17,x+.17) for x in posts])
    lo=-X+.01
    for p0,p1 in plates+[(X-.01,X)]:
        if p0-lo>.05:m.box('MortarBeds',((lo+p0)/2,yc_,b+.0155),(p0-lo-.002,yo-yi-.02,.031),'Joint','DETAIL',0.)
        lo=max(lo,p1)
    m.box('Copings',(0,(yi+.002+yo+.005)/2,b+HW+COPE/2),(2*X+.04,yo-yi+.003,COPE),'Concrete','FACADE',.006)
    # Insulated core (liner inside) under the arch, trapezoidal sheet and flashings outside.
    def soffit(x):return arch.z_at(arch.Rl,x)-.006
    top=[(x,soffit(x)) for x in [X-2*X*k/48 for k in range(49)]]
    core=m.p('RearCore','BODY',0.)
    core.prism([(-X,zt+.004),(X,zt+.004)]+top,(0,yc-C.CLAD_CORE-.10,0),((1,0,0),(0,0,1),(0,1,0)),.10,'RoofOlive')
    C.tone_faces(core,[(0.,1.,0.)],'RoofOlive','Plaster')
    back=((0.,yc,0.),(-1.,0.,0.),(0.,-1.,0.));pr=C.clad_pitch(2*X)
    fans=[-xd] if abs(xd)>1.5 else [-a/2]
    zf=zt+1.0;holes=[(-xf-.52,zf-.52,-xf+.52,zf+.52) for xf in fans]
    C.profile_sheet(m.p('RearCladding','BODY',0.),-X,X,pr,-X+pr/2,zt+.013,lambda u:soffit(-u),holes,(0.,),back,'RoofOlive')
    m.p('RearBaseFlashing','DETAIL',0.).prism([(yc-py,zt-.48+pz) for py,pz in C.BASE_FLASH],(-X-.0015,0,0),
        ((0,1,0),(0,0,1),(1,0,0)),2*X+.003,'SteelDark')
    if s.detail=='HERO':
        rows=C.girt_rows(zt+.35,soffit(X)-.2,top=arch.zc+arch.Rl-.3)
        C.fixings(m.p('RearFixings','DETAIL',0.),-X+.15,X-.15,pr,-X+pr/2,rows,holes,lambda u:soffit(-u),back,'SteelDark')
    # Corner angles over the sheet edge and the column's rear face.
    for sx in (-1.,1.):
        L=[(sx*(X-.15),yc+.0015),(sx*(X+.0015),yc+.0015),(sx*(X+.0015),d+.127),(sx*(X+.004),d+.127),(sx*(X+.004),yc+.004),(sx*(X-.15),yc+.004)]
        m.p('RearCornerTrims','FACADE',.001).prism(L,(0,0,zt+.016),A.IDENTITY,soffit(X)-zt-.016,'SteelDark')
    # Exhaust fans: housing through the wall, gravity shutters, finger guard.
    for xf in fans:
        f=m.p('ExhaustFans','FACADE',.002)
        for u0,u1,v0,v1 in ((-.52,.52,.46,.52),(-.52,.52,-.52,-.46),(-.52,-.46,-.46,.46),(.46,.52,-.46,.46)):
            f.box((xf+(u0+u1)/2,yc-.0075,zf+(v0+v1)/2),(u1-u0,.275,v1-v0),'SteelDark')
        for k in range(6):
            f.box((xf,yc+.05,zf-.38+k*.152),(.92,.012,.12),'Galvanized',A.euler_axes(radians(-30),0,0))
        f.cylinder((xf,yc-.10,zf),(xf,yc-.06,zf),.40,'SteelDark',24)
    return xd,ow,oh,yi,yo,yc,zt


def _rear_door(m,s,arch,xd,ow,oh,yi,yo,yc,zt):
    b=arch.b;w=ow-.12;hl=oh-.075                          # leaf in a 60 mm pressed frame
    fr=m.p('RearDoorFrame','FACADE',.002)
    for x in (xd-ow/2+.03,xd+ow/2-.03):fr.box((x,(yi+yo)/2+.005,b+oh/2),(.06,yo-yi+.01,oh),'SteelDark')
    fr.box((xd,(yi+yo)/2+.005,b+oh-.03),(ow-.12,yo-yi+.01,.06),'SteelDark')
    fr.box((xd,(yi+yo)/2,b+.005),(ow-.12,yo-yi-.02,.01),'Galvanized')          # threshold
    hinge=(xd-w/2,yo-.012,b+.012)
    dp=m.p('RearPersonnelDoor','DOOR',.003);dp.pivot=hinge
    lx0,lx1=xd-w/2+.003,xd+w/2-.003;ly0,ly1=yo-.062,yo-.012
    dp.box(((lx0+lx1)/2,(ly0+ly1)/2,b+.012+hl/2),(lx1-lx0,ly1-ly0,hl),'RoofOlive')
    dp.box(((lx0+lx1)/2,ly1+.002,b+.18),(lx1-lx0-.06,.007,.30),'Galvanized')                 # kick plate
    dp.box((xd,ly1+.002,b+1.595),(.30,.007,.15),'White');dp.box((xd,ly1+.002,b+1.695),(.30,.007,.05),'Red')
    for zz in (.25,1.05,1.85):dp.cylinder((lx0-.006,ly1+.006,b+zz-.06),(lx0-.006,ly1+.006,b+zz+.06),.012,'Galvanized',10)
    xh=lx1-.09
    dp.box((xh,ly1+.004,b+1.05),(.05,.008,.24),'Galvanized')                            # back plate
    dp.beam((xh,ly1+.008,b+1.10),(xh,ly1+.055,b+1.10),.022,.022,'Galvanized')
    dp.beam((xh,ly1+.055,b+1.10),(xh-.13,ly1+.055,b+1.10),.022,.016,'Galvanized')     # lever
    dp.box(((lx0+lx1)/2,ly0-.035,b+1.00),(lx1-lx0-.20,.03,.04),'Galvanized')          # panic bar inside
    for x in (lx0+.10,lx1-.10):dp.box((x,ly0-.02,b+1.00),(.04,.04,.08),'Galvanized')
    m.doors.append(dict(part=dp.name,kind='HINGE',closed=hinge,opened=hinge,angle=radians(95),open_fraction=s.door_open))
    m.collisions.append(dict(part=dp.name,center=((lx0+lx1)/2,(ly0+ly1)/2,b+.012+hl/2),dims=(lx1-lx0,ly1-ly0,hl),axes=A.IDENTITY))
    # Canopy with tie rods, wall pack and exit signs over the door.
    zc=zt+.30;cy=yc+.90
    m.box('DoorCanopy',(xd,(yc+cy)/2,zc),(1.70,cy-yc,.06),'SteelDark','FACADE',.003)
    m.box('DoorCanopy',(xd,yc+.007,zc+.07),(1.70,.014,.08),'SteelDark','FACADE',.002)
    for x in (xd-.70,xd+.70):
        m.p('CanopyTies','DETAIL',.001).pipe([(x,cy-.06,zc+.03),(x,yc+.01,zc+.85)],.012,'Galvanized',8)
        m.box('CanopyTies',(x,yc+.004,zc+.85),(.08,.008,.12),'Galvanized','DETAIL',.001)
    m.box('WallPacks',(xd,yc+.06,zc+.45),(.32,.12,.22),'SteelDark','DETAIL',.003)
    m.box('WallPackDiffusers',(xd,yc+.06,zc+.335),(.26,.09,.012),'LightWarm','DETAIL',0.)
    m.label('EXIT',(xd,yi-.003,b+oh+.12),.10,'LightGreen',rotation=(pi/2,0,0),name='ShelterExit',font='BigShoulders-Bold.ttf',anchor='CENTER')


# ------------------------------------------------------------------------------------- front
def _front(m,s,arch):
    a,b=arch.a,arch.b
    if s.signage:
        number=sign_text(s.name)
        W=min(5.6,max(4.2,a*.42));H=round(W/5.2,3);zs=arch.zc+arch.R-RIB_D/2-.30-H/2;ys=-.12
        xb=-W/2+H
        for x in (-W/2+.35,W/2-.35):                       # flat straps from the rib's bottom flange
            z0,z1=zs+H/2-.12,arch.z_at(arch.R-RIB_D/2,abs(x))+.002
            m.box('SignHangers',(x,-.091,(z0+z1)/2),(.05,.008,z1-z0),'SteelDark','DETAIL',.001)
        m.box('SignField',((xb+W/2)/2,ys,zs),(W/2-xb,.05,H),'SteelDark','DETAIL',.002)
        m.box('SignNumberBlock',((-W/2+xb)/2,ys,zs),(H,.05,H),'Yellow','DETAIL',.002)
        fr=m.p('SignFrame','DETAIL',.002);f=.022
        for zz in (zs-H/2-f/2,zs+H/2+f/2):fr.box((0,ys-.003,zz),(W+2*f,.050,f),'Galvanized')
        for xx in (-W/2-f/2,W/2+f/2):fr.box((xx,ys-.003,zs),(f,.050,H),'Galvanized')
        face=ys-.025
        m.label(number,((-W/2+xb)/2,face-.01,zs),H*.6,'SteelDark',name='ShelterNumber',extrude=.010,bevel=.002,
                font='BigShoulders-Bold.ttf',anchor='CENTER',cap_height=.58*H,max_width=.74*H)
        xt=xb+.2*H;xr=W/2-.16*H
        m.label('AIRCRAFT SHELTER',(xt,face-.008,zs+.10*H),H*.4,'White',name='ShelterTitle',extrude=.008,bevel=.0015,
                font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.30*H,max_width=xr-xt,tracking=1.04)
        m.box('SignRule',((xt+xr)/2,face-.002,zs-.11*H),(xr-xt,.004,max(.006,.011*H)),'Galvanized','DETAIL',.001)
        m.label(re.sub(r'[_-]+',' ',s.name).strip().upper()[:28],(xt,face-.004,zs-.26*H),H*.15,'Yellow',name='ShelterSubtitle',
                extrude=.004,font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.10*H,max_width=xr-xt,tracking=1.45)
    # Impact protection at the open front: filled bollards ahead of both front columns.
    for sx in (-1.,1.):
        for dy in (-.55,):
            for dx in (-.25,.25):
                x,y=sx*a+dx,dy
                bo=m.p('Bollards','PROPS',.004)
                bo.cylinder((x,y,b),(x,y,b+1.05),.085,'Yellow',16)
                for z0 in (.55,.85):bo.cylinder((x,y,b+z0),(x,y,b+z0+.10),.087,'SteelDark',16)
                bo.cylinder((x,y,b+1.05),(x,y,b+1.08),.075,'SteelDark',16)
        m.collisions.append(dict(part='SM_MB01_Bollards',center=(sx*a,-.55,b+.54),dims=(.68,.20,1.08),axes=A.IDENTITY))


def _floor(m,s,arch,xd):
    a,d,b=arch.a,arch.d,arch.b
    from ..core import local_ground
    local_ground(m)
    if s.local_ground:
        m.box('Foundation',(0,d+.30,b-.16),(2*a+.65,.60,.32),'Concrete','GROUND',.009,True)
        m.box('RearLanding',(xd,d+.60+.65,b-.08),(s.walkway_width,1.3,.16),'Concrete','GROUND',.006,True)
    # Saw-cut joints (raised 1 mm sealant lines), bay grid; trench drain across the open front.
    jt=m.p('FloorJoints','GROUND',0.)
    xs=[-a/2,0.,a/2]
    for x in xs:jt.box((x,(.64+d-.20)/2,b+.0005),(.008,d-.84,.001),'Joint')
    for i in range(1,s.bays):
        for u0,u1 in zip([-(a-.40)]+[x+.004 for x in xs],[x-.004 for x in xs]+[a-.40]):
            jt.box(((u0+u1)/2,i*d/s.bays,b+.0005),(u1-u0,.008,.001),'Joint')
    m.box('TrenchDrain',(0,.45,b+.001),(2*a-.70,.30,.002),'Galvanized','GROUND',0.)
    gr=m.p('TrenchGrate','DETAIL',0.)
    for k in range(int((2*a-.80)/.15)):
        gr.box((-a+.40+.075+k*.15,.45,b+.0035),(.012,.26,.003),'SteelDark')
    mk=m.p('FloorMarkings','GROUND',0.)
    mk.box((0,d*.45,b+.0012),(.12,d*.80,.0012),'Yellow')                    # taxi centreline
    mk.box((0,d-2.4,b+.0012),(2.4,.20,.0012),'Yellow')                      # nose stop bar
    for sx in (-1.,1.):mk.box((sx*(a-1.1),(.80+d-.40)/2,b+.0012),(.10,d-1.2,.0012),'White')   # equipment zone lines


def _services(m,s,arch,zh):
    a,d,b,n=arch.a,arch.d,arch.b,s.bays
    lx=[-a*.5,a*.5];li=m.p('Luminaires','DETAIL',.002)
    for i in range(n):
        y=(i+.5)*d/n
        for x in lx:
            z=arch.z_at(arch.Rl,abs(x))-1.25
            li.box((x,y,z),(.24,1.60,.09),'SteelDark');li.box((x,y,z-.050),(.18,1.50,.012),'LightWarm')
            for dy in (-.60,.60):
                m.p('LuminaireHangers','DETAIL',0.).cylinder((x,y+dy,z+.045),(x,y+dy,arch.z_at(arch.Rl,abs(x))-.002),.006,'Galvanized',6)
    for sx in (-1.,1.):               # cable tray on brackets off the column inner flanges
        x=sx*(a-.45);z=zh-.25
        tr=m.p('CableTrays','DETAIL',.001)
        for dx in (-.15,.15):tr.box((x+dx,d/2,z),(.02,d-.40,.08),'Galvanized')
        tr.box((x,d/2,z-.035),(.28,d-.40,.01),'Galvanized')
        for i in range(1,s.bays):tr.box((sx*(a-.4035),i*d/s.bays,z-.05),(.3935,.04,.02),'SteelDark')
        m.box('FireCabinets',(sx*(a-.20),1.0,b+1.15),(.24,.60,.84),'Red','PROPS',.006)
        m.box('FireCabinets',(sx*(a-.33),1.0,b+1.42),(.02,.40,.10),'White','PROPS',.001)
    m.box('PowerBoard',(-(a-.23),d-1.6,b+1.40),(.30,1.0,1.20),'SteelDark','PROPS',.008)
    m.box('PowerBoard',(-(a-.39),d-1.6,b+1.40),(.02,.90,1.10),'RoofOliveLight','PROPS',.002)


def build_shelter(m):
    s=m.cfg;arch=Arch(s)
    _frame(m,s,arch);_roof(m,s,arch);_gutters(m,s,arch)
    zt,zh=_side_walls(m,s,arch)
    xd,ow,oh,yi,yo,yc,zt=_rear_wall(m,s,arch)
    _rear_door(m,s,arch,xd,ow,oh,yi,yo,yc,zt)
    _front(m,s,arch)
    _floor(m,s,arch,xd)
    if s.services:_services(m,s,arch,zh)
    m.port('AIRCRAFT_IN',(0,0,arch.b),-pi/2,max(1,s.width-.8),'HANGAR')
    m.port('PERSONNEL_REAR_OUT',(xd,yo+1.3,0),pi/2,s.walkway_width)
    m.openings.append(dict(kind='HANGAR',width=2*arch.a-.40,height=arch.h,center=(0,0,arch.b)))
    m.notes.append('MB01 arched shelter (AS07 contract, new geometry): open front; arch, profiles and fixings are artistic, not structural design.')

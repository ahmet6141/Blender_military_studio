"""Hardened arched aircraft shelter (core SHELTER, shelter_style='HARDENED').

A cast-in-place concrete vault (walls to the springline, segmental arch) poured bay by bay with
recessed construction joints, framed at the front by a thick concrete portal arch. The opening is
closed by two bi-parting steel leaves whose tops follow the arch, so the closed door reads as one
round door sealed against the portal; each leaf is a 700 mm box with a raked outrigger foot and
bogies on two crane rails (no overhead guide beam crossing the opening) and parks in full beside
the shelter in front of low wing walls. Rear: exhaust port with a steel louvre grille and a concrete
blast deflector, steel personnel door with canopy.
Fictional CGI scenery: thicknesses and profiles are artistic, with no protective or structural claim.

Design coordinates of core.Model: x across, y from the front face of the vault (0) to the rear (d),
z up from the slab top. Same topology rules as shelter.geometry: closed solids, 1-3 mm beds or
opposite-facing contact, never same-facing coplanar overlap."""
from math import asin, sin, cos, sqrt, ceil, floor, pi, radians
import re
from ..vendor import as07_reference as A
from .geometry import sign_text

TK=.80                 # vault shell
TKR=.80                # rear wall
RING_D,RING_W=1.20,.50 # front portal arch: depth, width beyond the vault shell
NIB=.40                # opening inset from the vault's inner face (jamb nib)
LEAF_T,OUTRIG=.70,.90  # door leaf body thickness, raked outrigger foot ahead of it
LAP=.30                # leaves lap the portal by this much (sealed against its face)
ARC={'DRAFT':24,'WORKING':40,'HERO':56}
YZX=((0,1,0),(0,0,1),(1,0,0))     # prism: profile (y, z), extruded along +x
XZY=((1,0,0),(0,0,1),(0,1,0))     # prism: profile (x, z), extruded along +y
RAIL=((-.06,.02),(.06,.02),(.06,.035),(.016,.05),(.016,.085),(.036,.09),(.036,.12),(-.036,.12),(-.036,.09),
      (-.016,.085),(-.016,.05),(-.06,.035))  # crane rail on its sole plate (y, z above the slab)


class Vault:
    def __init__(self,s):
        self.b=b=s.base_height;self.a=a=s.width/2;self.d=s.depth;self.h=h=s.floor_height;r=s.roof_rise
        self.R=R=(a*a+r*r)/(2*r);self.zc=b+h+r-R;self.n=ARC[s.detail]
        self.xo=a+TK;self.Ro=R+TK
        # Door: the opening is the inner profile inset by the nib; two bi-parting leaves whose tops follow
        # the arch LAP beyond the opening, so the closed door reads as one round door in the portal.
        self.ai,self.Ri=a-NIB,R-NIB;self.ow=2*self.ai
        self.wt,self.Rt=self.ai+LAP-.004,self.Ri+LAP+.004       # door outline: half width, top radius
        self.zb0=b+.30;self.zl0=self.zb0+.95                     # outrigger foot bottom / body bottom
        self.yi=-RING_D-.08;self.yo=self.yi-LEAF_T;self.yc=(self.yi+self.yo)/2
        self.rails=(self.yc,self.yo-.55)                         # two rails under every leaf
        self.Lw=self.wt-.012;self.shift=self.wt+.40-.012         # leaf width, travel to the parked position
        self.xe=2*self.wt+.40+.60                                # rail / trench end (parked leaf + stop)
        self.F=self.xe+1.50                                      # half width of the front apron
        self.xr=self.xo+RING_W;self.Rr=self.Ro+RING_W            # portal arch outer profile
    def T(self,x):return self.zc+sqrt(max(0.,self.Rt**2-x*x))   # top of the closed door at x
    def path(self,ai,Ri,zb):
        """Left foot -> wall -> arch -> wall -> right foot, walls at +-ai, arch radius Ri."""
        zw=self.zc+sqrt(Ri*Ri-ai*ai);t=asin(ai/Ri);n=self.n
        arc=[(Ri*sin(-t+2*t*k/n),self.zc+Ri*cos(-t+2*t*k/n)) for k in range(n+1)]
        return [(-ai,zb),(-ai,zw)]+arc[1:-1]+[(ai,zw),(ai,zb)]
    def ring(self,off_in=0.,off_out=0.,zb=None):
        zb=self.b if zb is None else zb
        return self.path(self.a+off_in,self.R+off_in,zb)+self.path(self.xo+off_out,self.Ro+off_out,zb)[::-1]
    def z_in(self,x):return self.zc+sqrt(max(0.,self.R**2-x*x))
    def z_out(self,x):return self.zc+sqrt(max(0.,self.Ro**2-x*x))


# ------------------------------------------------------------------------------------- shell
def _vault(m,s,v):
    b,d,n=v.b,v.d,s.bays;bp=d/n
    for i in range(n):
        y0=i*bp+(.01 if i else 0.);y1=(i+1)*bp-(.01 if i<n-1 else 0.)
        m.p('VaultShell','STRUCTURE',.015).prism(v.ring(),(0,y0,0),XZY,y1-y0,'ConcreteLight')
        if i:   # recessed sealant joint between pours
            m.p('VaultJoints','DETAIL',0.).prism(v.ring(.03,-.03,b+.003),(0,i*bp-.012,0),XZY,.024,'Joint')
    # Formwork lift lines on the outer arch, per pour (3 mm proud, bedded 3 mm).
    if s.detail!='DRAFT':
        to=asin(v.xo/v.Ro);k=max(2,round(2*to*v.Ro/2.4))
        fl=m.p('FormworkLines','DETAIL',0.)
        for j in range(1,k):
            t=-to+2*to*j/k;N=(sin(t),0.,cos(t));T=(cos(t),0.,-sin(t))
            for i in range(n):
                y0=i*bp+.03;y1=(i+1)*bp-.03
                c=(v.Ro*sin(t),(y0+y1)/2,v.zc+v.Ro*cos(t))
                fl.box(c,(.03,y1-y0,.006),'Concrete',(T,(0,1,0),N))
    for sx in (-1.,1.):     # foot plinth along the outer walls
        m.box('VaultPlinth',(sx*(v.xo+.125),d/2,b+.15),(.25,d,.30),'Concrete','FACADE',.008)


def _portal(m,s,v):
    """Portal arch around the opening, steel seal plate, steel rim coping and rim floodlights. No wing
    walls: the leaves run on rails set flush in the apron and park free-standing beside the shelter."""
    b=v.b
    m.p('PortalArch','STRUCTURE',.015).prism(v.path(v.ai,v.Ri,b)+v.path(v.xr,v.Rr,b)[::-1],(0,-RING_D,0),XZY,RING_D,'ConcreteLight')
    band=v.path(v.ai+LAP,v.Ri+LAP,b)+v.path(v.ai,v.Ri,b)[::-1]           # embedded seal plate (door lap zone)
    m.p('SealFrame','FACADE',0.).prism(band,(0,-RING_D-.012,0),XZY,.012,'SteelDark')
    # Steel coping over the portal's outer rim, flush with the face: nothing on the face stands in the
    # sliding leaves' path (their inner seals pass 14 mm in front of it).
    cap=v.path(v.xr+.03,v.Rr+.03,b)+v.path(v.xr,v.Rr,b)[::-1]
    m.p('PortalCoping','FACADE',.002).prism(cap,(0,-RING_D,0),XZY,RING_D,'SteelDark')
    for sx in (-1.,1.):     # LED floodlights on the rim, behind the face (clear of the leaves)
        t_=sx*radians(40);T_,N_=(cos(t_),0.,-sin(t_)),(sin(t_),0.,cos(t_))
        def at(r,y):return (r*sin(t_),y,v.zc+r*cos(t_))
        R0=v.Rr+.03
        m.box('Floodlights',at(R0+.035,-.95),(.12,.10,.07),'SteelDark','DETAIL',.002,axes=(T_,(0,1,0),N_))
        m.box('Floodlights',at(R0+.20,-.95),(.42,.30,.26),'SteelDark','DETAIL',.004,axes=(T_,(0,1,0),N_))
        m.box('FloodlightLenses',at(R0+.20,-1.102),(.34,.004,.20),'LightWarm','DETAIL',0.,axes=(T_,(0,1,0),N_))


def _rails(m,s,v):
    """Crane rails in trenches cast into the apron: rail heads 5 mm under the slab, galvanised edge angles
    flush with it, sole plates and clips on the trench floor, raised stops only at the trench ends."""
    b,xe=v.b,v.xe;hero=s.detail=='HERO';z0=b-.125          # rail base reference (head top at b-.005)
    rp=m.p('DoorRails','STRUCTURE',.002);sp=m.p('RailSolePlates','DETAIL',.002);ea=m.p('TrenchEdges','DETAIL',.001)
    for yc in v.rails:
        sp.box((0,yc,z0+.01),(2*xe-.02,.24,.02),'SteelDark')
        rp.prism([(yc+u,z0+w) for u,w in RAIL],(-xe+.45,0,0),YZX,2*xe-.90,'Galvanized')
        for sy in (-1,1):ea.box((0,yc+sy*(.15-.004),b-.03),(2*xe,.008,.06),'Galvanized')
        if hero:
            cl=m.p('RailClips','DETAIL',.001)
            for k in range(int((2*xe-.90)/1.0)):
                for sy in (-1,1):cl.box((-xe+.95+k,yc+sy*.085,z0+.035),(.08,.05,.03),'SteelDark')
        for sx in (-1.,1.):     # end stops with rubber buffers at wheel-centre height
            m.box('RailEndStops',(sx*(xe-.225),yc,z0+.02+(b+.20-z0-.02)/2),(.45,.22,b+.20-z0-.02),'Yellow','DETAIL',.006)
            m.p('RailBuffers','DETAIL',.002).cylinder((sx*(xe-.45),yc,b+.145),(sx*(xe-.57),yc,b+.145),.08,'Rubber',16)
    for sx in (-1.,1.):         # warning bollards beyond the track ends
        for dy in (-.45,.45):
            x,y=sx*(xe+.60),(v.rails[0]+v.rails[1])/2+dy
            bo=m.p('Bollards','PROPS',.004)
            bo.cylinder((x,y,b),(x,y,b+1.0),.085,'Yellow',16)
            for zz in (.50,.80):bo.cylinder((x,y,b+zz),(x,y,b+zz+.10),.087,'SteelDark',16)
            bo.cylinder((x,y,b+1.0),(x,y,b+1.03),.075,'SteelDark',16)
        m.collisions.append(dict(part='SM_MB01_Bollards',center=(sx*(xe+.60),sum(v.rails)/2,b+.52),dims=(.20,1.10,1.04),axes=A.IDENTITY))


def _leaf(m,s,v,side):
    """Bi-parting leaf: 700 mm box body with an arched top, raked outrigger foot on two rails."""
    b,yi,yo,T=v.b,v.yi,v.yo,v.T
    xl,xt=side*.012,side*v.wt                                  # leading (meeting) and trailing edge
    lo,hi=sorted((xl,xt));cx=(lo+hi)/2
    p=m.p(f'BlastDoor_{"L" if side<0 else "R"}','DOOR',.004);p.pivot=(cx,v.yc,b)
    N=max(6,ceil(v.Lw/.6));xs=[xt+(xl-xt)*k/N for k in range(N+1)]           # trailing -> leading
    top=[(x,T(x)) for x in xs]
    p.prism([(xl,v.zl0),(xt,v.zl0)]+top,(0,yo,0),XZY,LEAF_T,'RoofOlive')
    p.prism([(yi,v.zb0),(yo-OUTRIG,v.zb0),(yo-OUTRIG,v.zb0+.30),(yo,v.zl0),(yi,v.zl0)],(lo,0,0),YZX,hi-lo,'RoofOlive')
    # Outer face (30 mm flats): arched top band, edge stiles, bottom rail, horizontal panel joints.
    f=.25;pr=.03;fo=(0,yo-pr,0)
    p.prism([(x,z) for x,z in top]+[(x,z-f) for x,z in top[::-1]],fo,XZY,pr,'SteelDark')
    for x,z in ((xl+side*f/2,T(xl+side*f)-.02),(xt-side*f/2,T(xt)-.02)):  # stiles stop under the band (chords)
        p.box((x,yo-pr/2,(v.zl0+f+z-f)/2),(f,pr,z-f-v.zl0-f),'SteelDark')
    p.box((cx,yo-pr/2,v.zl0+f/2),(hi-lo,pr,f),'SteelDark')
    zk=v.zl0+1.8
    while zk<T(xl)-f-.30:
        reach=sqrt(max(0.,v.Rt**2-(zk+.06+f+.06-v.zc)**2))
        u0,u1=abs(xl)+f,min(abs(xt)-f,reach)
        if u1-u0>.6:p.box((side*(u0+u1)/2,yo-pr/2,zk),(u1-u0,pr,.08),'SteelDark')
        zk+=1.8
    for j in range(int((T(xl)-2*f-v.zl0-.25)/.50)+1):            # impact stripes on the meeting stile
        p.box((xl+side*f/2,yo-pr-.003,v.zl0+f+.20+j*.50),(f-.03,.009,.25),'Yellow')
    p.box((side*.007,v.yc,(v.zb0+T(.012))/2-.02),(.009,LEAF_T-.10,T(.012)-v.zb0-.06),'Rubber')    # meeting seal
    # Inner face: rubber seal along the lapped top and trailing edge, shallow stiffener flats.
    sb=.20
    p.prism([(x,z) for x,z in top]+[(x,z-sb) for x,z in top[::-1]],(0,yi,0),XZY,.066,'Rubber')
    p.box((xt-side*sb/2,yi+.033,(v.zl0+T(xt)-sb)/2),(sb,.066,T(xt)-sb-v.zl0),'Rubber')
    nv=max(2,round(v.Lw/2.0))
    for k in range(1,nv):
        x=xl+(xt-xl)*k/nv;zt=min(T(x-.075),T(x+.075))-sb-.03
        p.box((x,yi+.015,(v.zl0+zt)/2),(.15,.03,zt-v.zl0),'SteelDark')
    # Running gear: bogies with a wheel on each rail at both ends, skirts between them.
    for e in (lo+.60,hi-.60):
        p.box((e,(yi+yo-OUTRIG)/2,b+.20),(.90,yi-yo+OUTRIG-.06,.20),'SteelDark')
        for yr in v.rails:p.cylinder((e,yr-.05,b+.145),(e,yr+.05,b+.145),.15,'Galvanized',16)
    L=hi-lo-2.10
    p.box((cx,yo-OUTRIG-.0085,b+.1675),(L,.015,.305),'Rubber');p.box((cx,yi+.0085,b+.1675),(L,.015,.305),'Rubber')
    p.box((cx,yo-OUTRIG/2-.05,v.zb0+.45),(1.0,.55,.40),'SteelDark')        # rack drive on the outrigger
    for x in (xl+(xt-xl)*.3,xl+(xt-xl)*.7):                               # lifting lugs on the top
        p.box((x,v.yc,T(x)+.065),(.04,.20,.18),'SteelDark')
    m.doors.append(dict(part=p.name,kind='SLIDE',closed=(cx,v.yc,b),opened=(cx+side*v.shift,v.yc,b),
                        open_fraction=s.door_open,track=0,channel='GATE'))
    m.collisions.append(dict(part=p.name,center=(cx,(yi+yo-OUTRIG)/2,(v.zb0+T(xl))/2),
                             dims=(hi-lo,yi-yo+OUTRIG,T(xl)-v.zb0),axes=A.IDENTITY))


# ------------------------------------------------------------------------------------- rear
def _rear(m,s,v):
    b,d,xo=v.b,v.d,v.xo;y0=d;ze=b+1.20;ze1=b+3.60;xe=1.50
    xd=round(v.a*.55,2);dw,dh=1.10,2.25
    rw=m.p('RearWall','STRUCTURE',.015)
    for x0,x1 in ((-xo,xd-dw/2),(xd+dw/2,xo)):
        rw.box(((x0+x1)/2,y0+TKR/2,(b+ze)/2),(x1-x0,TKR,ze-b),'ConcreteLight')
    to=asin(xo/v.Ro);n=v.n
    arc=[(v.Ro*sin(to-2*to*k/n),v.zc+v.Ro*cos(to-2*to*k/n)) for k in range(n+1)]
    poly=[(-xo,ze),(-xe,ze),(-xe,ze1),(xe,ze1),(xe,ze),(xd-dw/2,ze),(xd-dw/2,b+dh),(xd+dw/2,b+dh),(xd+dw/2,ze),(xo,ze)]+arc
    rw.prism(poly,(0,y0,0),XZY,TKR,'ConcreteLight')
    m.collisions.append(dict(part=rw.name,center=(0,y0+TKR/2,(b+ze)/2),dims=(2*xo,TKR,ze-b),axes=A.IDENTITY))
    # Exhaust port: steel reveal lining, 45 deg louvre blades, outer frame.
    g=m.p('ExhaustGrille','FACADE',.002)
    for x in (-xe+.004,xe-.004):g.box((x,y0+TKR/2,(ze+ze1)/2),(.008,TKR,ze1-ze),'SteelDark')
    for z in (ze+.004,ze1-.004):g.box((0,y0+TKR/2,z),(2*xe-.016,TKR,.008),'SteelDark')
    for k in range(int((ze1-ze-.20)/.22)):
        g.box((0,y0+TKR/2,ze+.18+k*.22),(2*xe-.018,.012,.30),'RoofOlive',A.euler_axes(radians(45),0,0))
    fr=.12
    for x in (-xe-fr/2,xe+fr/2):g.box((x,y0+TKR+.015,(ze+ze1)/2),(fr,.03,ze1-ze+2*fr),'SteelDark')
    for z in (ze-fr/2,ze1+fr/2):g.box((0,y0+TKR+.015,z),(2*xe,.03,fr),'SteelDark')
    # Blast deflector: sloped concrete wall facing the port.
    yd=y0+TKR+2.4
    m.p('BlastDeflector','STRUCTURE',.015).prism([(yd,b),(yd+1.0,b),(yd+1.0,b+4.6),(yd+.6,b+4.6)],(-2.6,0,0),YZX,5.2,'ConcreteLight')
    m.collisions.append(dict(part='SM_MB01_BlastDeflector',center=(0,yd+.6,b+2.3),dims=(5.2,1.2,4.6),axes=A.IDENTITY))
    _personnel_door(m,s,v,xd,y0,y0+TKR,dw,dh)
    return xd


def _personnel_door(m,s,v,xd,yi,yo,ow,oh):
    """Heavy steel door at the outer face of a thick wall: lined reveal, 70 mm leaf opening outward."""
    b=v.b;w=ow-.12;hl=oh-.075
    fr=m.p('RearDoorFrame','FACADE',.002)
    for x in (xd-ow/2+.003,xd+ow/2-.003):fr.box((x,(yi+yo)/2,b+oh/2),(.006,yo-yi,oh),'SteelDark')
    fr.box((xd,(yi+yo)/2,b+oh-.003),(ow-.012,yo-yi,.006),'SteelDark')
    for x in (xd-ow/2+.03,xd+ow/2-.03):fr.box((x,yo+.01,b+oh/2),(.06,.02,oh),'SteelDark')
    fr.box((xd,yo+.01,b+oh-.03),(ow-.12,.02,.06),'SteelDark')
    fr.box((xd,yo-.20,b+.005),(ow-.012,.40,.01),'Galvanized')
    hinge=(xd-w/2,yo-.003,b+.012)
    dp=m.p('RearPersonnelDoor','DOOR',.003);dp.pivot=hinge
    lx0,lx1=xd-w/2+.003,xd+w/2-.003;ly0,ly1=yo-.073,yo-.003
    dp.box(((lx0+lx1)/2,(ly0+ly1)/2,b+.012+hl/2),(lx1-lx0,ly1-ly0,hl),'RoofOlive')
    dp.box(((lx0+lx1)/2,ly1+.002,b+.18),(lx1-lx0-.06,.007,.30),'Galvanized')
    dp.box((xd,ly1+.002,b+1.595),(.30,.007,.15),'White');dp.box((xd,ly1+.002,b+1.695),(.30,.007,.05),'Red')
    for zz in (.25,1.05,1.85):dp.cylinder((lx0-.008,ly1+.012,b+zz-.07),(lx0-.008,ly1+.012,b+zz+.07),.016,'Galvanized',10)
    xh=lx1-.09
    dp.box((xh,ly1+.004,b+1.05),(.05,.008,.24),'Galvanized')
    dp.beam((xh,ly1+.008,b+1.10),(xh,ly1+.055,b+1.10),.022,.022,'Galvanized')
    dp.beam((xh,ly1+.055,b+1.10),(xh-.13,ly1+.055,b+1.10),.022,.016,'Galvanized')
    dp.box(((lx0+lx1)/2,ly0-.035,b+1.00),(lx1-lx0-.20,.03,.04),'Galvanized')
    for x in (lx0+.10,lx1-.10):dp.box((x,ly0-.02,b+1.00),(.04,.04,.08),'Galvanized')
    m.doors.append(dict(part=dp.name,kind='HINGE',closed=hinge,opened=hinge,angle=radians(95),open_fraction=s.door_open,channel='PERSONNEL'))
    m.collisions.append(dict(part=dp.name,center=((lx0+lx1)/2,(ly0+ly1)/2,b+.012+hl/2),dims=(lx1-lx0,ly1-ly0,hl),axes=A.IDENTITY))
    zc=b+oh+.35;cy=yo+1.0
    m.box('DoorCanopy',(xd,(yo+cy)/2,zc),(1.80,cy-yo,.06),'SteelDark','FACADE',.003)
    for x in (xd-.75,xd+.75):
        m.p('CanopyTies','DETAIL',.001).pipe([(x,cy-.06,zc+.03),(x,yo+.01,zc+.90)],.014,'Galvanized',8)
        m.box('CanopyTies',(x,yo+.005,zc+.90),(.10,.01,.14),'Galvanized','DETAIL',.002)
    m.box('WallPacks',(xd,yo+.06,zc+.48),(.32,.12,.22),'SteelDark','DETAIL',.003)
    m.box('WallPackDiffusers',(xd,yo+.06,zc+.365),(.26,.09,.012),'LightWarm','DETAIL',0.)
    m.label('EXIT',(xd,yi-.003,b+oh+.15),.12,'LightGreen',name='ShelterExit',font='BigShoulders-Bold.ttf',anchor='CENTER')


# ------------------------------------------------------------------------------------- site
def _ground(m,s,v,xd):
    b,d,F=v.b,v.d,v.F
    if s.local_ground:
        r1,r2=sorted(v.rails,reverse=True);tw=.15            # apron strips around the two rail trenches
        for y0,y1 in ((r1+tw,0.),(r2+tw,r1-tw),(-9.,r2-tw)):
            m.box('Foundation',(0,(y0+y1)/2,b-.16),(2*F,y1-y0,.32),'Concrete','GROUND',.009,True)
        for r in (r1,r2):
            m.box('TrenchFloors',(0,r,b-.2225),(2*v.xe,2*tw,.195),'Concrete','GROUND',0.)
            for sx in (-1.,1.):
                x0,x1=sorted((sx*v.xe,sx*F))
                m.box('Foundation',((x0+x1)/2,r,b-.16),(x1-x0,2*tw,.32),'Concrete','GROUND',.009,True)
        m.box('Foundation',(0,(d+TKR+6.0)/2,b-.16),(2*v.xo+2.0,d+TKR+6.0,.32),'Concrete','GROUND',.009,True)
        jt=m.p('ApronJoints','GROUND',0.)
        nx=max(2,round((2*F-.4)/5.0))
        for j in range(1,nx):jt.box((-(F-.2)+(2*F-.4)*j/nx,-6.3075,b+.0005),(.01,4.985,.001),'Joint')
        jt.box((0,-3.8,b+.0005),(2*F-.4,.01,.001),'Joint')
    jt=m.p('FloorJoints','GROUND',0.);a=v.a
    xs=[-a/2,0.,a/2]
    for x in xs:jt.box((x,(1.6+d-.3)/2,b+.0005),(.008,d-1.9,.001),'Joint')
    for i in range(1,s.bays):
        for u0,u1 in zip([-(a-.3)]+[x+.004 for x in xs],[x-.004 for x in xs]+[a-.3]):
            jt.box(((u0+u1)/2,i*d/s.bays,b+.0005),(u1-u0,.008,.001),'Joint')
    m.box('TrenchDrain',(0,1.0,b+.001),(2*a-.40,.30,.002),'Galvanized','GROUND',0.)
    gr=m.p('TrenchGrate','DETAIL',0.)
    for k in range(int((2*a-.50)/.15)):gr.box((-a+.25+.075+k*.15,1.0,b+.0035),(.012,.26,.003),'SteelDark')
    mk=m.p('FloorMarkings','GROUND',0.)
    mk.box((0,(1.3+d-3.2)/2,b+.0012),(.12,d-4.5,.0012),'Yellow')                     # taxi centreline
    mk.box((0,d-3.0,b+.0012),(2.4,.20,.0012),'Yellow')
    mk.box((0,-6.2,b+.0012),(.12,4.4,.0012),'Yellow')                             # lead-in on the apron
    mk.box((0,v.yo-OUTRIG-.35,b+.0012),(2*(v.xe+1.0),.15,.0012),'Yellow')             # door-track keep-clear line
    for sx in (-1.,1.):mk.box((sx*(a-1.2),(1.3+d-1.0)/2,b+.0012),(.10,d-2.3,.0012),'White')


def _sign(m,s,v):
    """Identity sign on the portal face above the closed door (clear of the leaves' seals and lugs)."""
    if not s.signage:return
    number=sign_text(s.name);W=4.6;H=.70;x=0.;y=-RING_D;zs=v.T(0)+.12+H/2
    ys=y-.03;xb=x-W/2+H
    m.box('SignField',((xb+x+W/2)/2,ys,zs),(x+W/2-xb,.04,H),'SteelDark','DETAIL',.002)
    m.box('SignNumberBlock',((x-W/2+xb)/2,ys,zs),(H,.04,H),'Yellow','DETAIL',.002)
    face=ys-.02
    m.label(number,((x-W/2+xb)/2,face-.006,zs),H*.6,'SteelDark',name='ShelterNumber',extrude=.006,bevel=.0015,
            font='BigShoulders-Bold.ttf',anchor='CENTER',cap_height=.58*H,max_width=.74*H)
    xt=xb+.2*H;xr=x+W/2-.16*H
    m.label('HARDENED SHELTER',(xt,face-.005,zs+.10*H),H*.4,'White',name='ShelterTitle',extrude=.005,bevel=.001,
            font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.28*H,max_width=xr-xt,tracking=1.04)
    m.box('SignRule',((xt+xr)/2,face-.002,zs-.11*H),(xr-xt,.004,.01),'Galvanized','DETAIL',.001)
    m.label(re.sub(r'[_-]+',' ',s.name).strip().upper()[:28],(xt,face-.003,zs-.26*H),H*.15,'Yellow',name='ShelterSubtitle',
            extrude=.003,font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.10*H,max_width=xr-xt,tracking=1.45)


def _services(m,s,v):
    b,d,a,n=v.b,v.d,v.a,s.bays;zf=v.zc+sqrt(v.R**2-a*a)-.50
    for i in range(n):
        y=(i+.5)*d/n
        for sx in (-1.,1.):     # wall floodlights on brackets under the springline
            x=sx*(a-.20)
            m.box('WallFloods',(x,y,zf),(.30,.46,.30),'SteelDark','DETAIL',.004)
            m.box('WallFloodLenses',(x-sx*.152,y,zf),(.004,.38,.22),'LightWarm','DETAIL',0.)
            m.box('WallFloods',(sx*(a-.025),y,zf),(.05,.10,.10),'SteelDark','DETAIL',.002)
    zc=v.zc+v.R-.95;y0,y1=1.0,d-1.0
    m.p('VentDuct','DETAIL',.002).cylinder((0,y0,zc),(0,y1,zc),.35,'Galvanized',20)
    for i in range(1,n):
        y=i*d/n
        hp=m.p('DuctHangers','DETAIL',.001)
        hp.cylinder((0,y,zc),(0,y+.10,zc),.37,'SteelDark',20)
        for sx in (-1,1):hp.cylinder((sx*.30,y+.05,zc+.20),(sx*.30,y+.05,v.zc+v.R-.30*.30/v.R+.02),.012,'Galvanized',6)
    for sx in (-1.,1.):
        x=sx*(a-.35);z=b+v.h-1.2
        tr=m.p('CableTrays','DETAIL',.001)
        for dx in (-.15,.15):tr.box((x+dx,d/2,z),(.02,d-.40,.08),'Galvanized')
        tr.box((x,d/2,z-.035),(.28,d-.40,.01),'Galvanized')
        for i in range(1,n):tr.box((sx*(a-.1305),i*d/n,z-.05),(.261,.04,.02),'SteelDark')
        m.box('FireCabinets',(sx*(a-.12),2.0,b+1.15),(.24,.60,.84),'Red','PROPS',.006)
        m.box('FireCabinets',(sx*(a-.25),2.0,b+1.42),(.02,.40,.10),'White','PROPS',.001)
    m.box('PowerBoard',(-(a-.15),d-1.6,b+1.40),(.30,1.0,1.20),'SteelDark','PROPS',.008)
    m.box('PowerBoard',(-(a-.31),d-1.6,b+1.40),(.02,.90,1.10),'RoofOliveLight','PROPS',.002)


def build_hardened(m):
    s=m.cfg;v=Vault(s)
    _vault(m,s,v);_portal(m,s,v);_rails(m,s,v)
    for side in (-1,1):_leaf(m,s,v,side)
    xd=_rear(m,s,v);_ground(m,s,v,xd);_sign(m,s,v)
    if s.services:_services(m,s,v)
    m.port('AIRCRAFT_IN',(0,v.yo-OUTRIG-.6,v.b),-pi/2,v.ow,'HANGAR')
    m.port('PERSONNEL_REAR_OUT',(xd,v.d+TKR+1.3,0),pi/2,s.walkway_width)
    m.port('PERSONNEL_OUT',(0,-9.0,0),-pi/2,s.walkway_width)
    m.openings.append(dict(kind='HANGAR',width=v.ow,height=v.zc+v.Ri-v.b,center=(0,-RING_D,v.b)))
    m.notes.append('MB01 hardened shelter (fictional CGI): bi-parting arched steel leaves on twin rails; no protective, ballistic or structural claim.')

"""Hardened arched aircraft shelter (core SHELTER, shelter_style='HARDENED').

A cast-in-place concrete vault (walls to the springline, segmental arch) poured bay by bay with
recessed construction joints; a massive front headwall with an arch-shaped opening closed by four
heavy steel door leaves. The leaves run telescopically on crane rails (two tracks), are guided at
the top by a box-girder gantry and park in side pockets behind buttress end walls. Rear: exhaust
port with a steel louvre grille and a concrete blast deflector, steel personnel door with canopy.
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
HWT=1.00               # front headwall
NIB=.40                # opening inset from the vault's inner face (jamb nib)
LEAF_T=.50             # door leaf thickness
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
        # Door geometry: opening = inner profile inset by the nib; 2 x 2 telescopic leaves.
        self.ow=2*(a-NIB);self.Lw=self.ow/4+.25
        self.zl0=b+.45;self.zl1=self.zc+R-NIB+.30         # leaf bottom beam / top (laps the head .30)
        self.g0=self.zl1+.28;self.g1=self.g0+.90;self.top=self.g1+.35
        self.F=self.ow/2+self.Lw+2.0                       # half width of the front (pockets + end walls)
        self.yc=(-(HWT+.30+LEAF_T/2),-(HWT+.30+LEAF_T+.28+LEAF_T/2))   # track 1 (wall side), track 0 (outer)
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


def _headwall(m,s,v):
    b,F,top=v.b,v.F,v.top;ai,Ri=v.a-NIB,v.R-NIB
    poly=[(-F,b)]+v.path(ai,Ri,b)+[(F,b),(F,top),(-F,top)]
    m.p('Headwall','STRUCTURE',.015).prism(poly,(0,-HWT,0),XZY,HWT,'ConcreteLight')
    # Embedded steel door-seal frame around the opening (12 mm plate on the face).
    band=v.path(ai+.30,Ri+.30,b)+v.path(ai,Ri,b)[::-1]
    m.p('SealFrame','FACADE',0.).prism(band,(0,-HWT-.012,0),XZY,.012,'SteelDark')
    m.box('Copings',(0,-HWT/2,top+.025),(2*F+.10,HWT+.10,.05),'SteelDark','DETAIL',.004)
    # Formwork panel joints on the face (2.4 x 1.2 m panels): horizontal lines 3 mm, vertical 2 mm proud,
    # kept off the seal frame, the gantry and the end walls.
    if s.detail!='DRAFT':
        fw=m.p('FormworkJoints','DETAIL',0.);yf=-HWT
        def half(z):      # opening (+ seal frame) half width at height z, 0 above it
            zw=v.zc+sqrt((Ri+.30)**2-(ai+.30)**2)
            return ai+.30 if z<=zw else (sqrt(max(0.,(Ri+.30)**2-(z-v.zc)**2)) if z<v.zc+Ri+.30 else 0.)
        gz=(v.g0-.02,v.g1+.02);xe=F-1.02;zs=[]
        for j in range(1,int((top-b)/1.2)+1):
            z=b+j*1.2
            if z>top-.15:break
            if gz[0]<z<gz[1]:continue
            zs.append(z);hw=half(z)+.05 if half(z)>0 else 0.;lim=xe
            for x0,x1 in ((-lim,-hw),(hw,lim)) if hw>0 else ((-lim,lim),):
                if x1-x0>.3:fw.box(((x0+x1)/2,yf-.0015,z),(x1-x0,.003,.012),'Concrete')
        cuts=[b]+zs+[top]
        for j in range(1,int(2*xe/2.4)+1):
            x=-xe+j*2.4
            if x>xe-.1:break
            zt=v.zc+sqrt(max(0.,(Ri+.30)**2-x*x))+.05 if abs(x)<ai+.35 else b
            for z0,z1 in zip(cuts,cuts[1:]):
                z0,z1=max(z0+.006,zt),z1-.006
                if z0<gz[1] and z1>gz[0]:z0,z1=(z0,min(z1,gz[0])) if z0<gz[0] else (max(z0,gz[1]),z1)
                if z1-z0>.3:fw.box((x,yf-.001,(z0+z1)/2),(.012,.002,z1-z0),'Concrete')
    # Buttress end walls closing the leaf pockets.
    for sx in (-1.,1.):
        y0,y1=-3.20,-HWT
        m.box('EndWalls',(sx*(F-.5),(y0+y1)/2,(b+top)/2),(1.0,y1-y0,top-b),'ConcreteLight','STRUCTURE',.015,True)
        m.box('Copings',(sx*(F-.5),(y0-.05+y1-HWT*0-.05)/2,top+.025),(1.10,y1-y0,.05),'SteelDark','DETAIL',.004)
        # Corner guard: steel angle with impact stripes at the open pocket edge.
        x=sx*(F-1.0);g=m.p('CornerGuards','DETAIL',.002)
        g.box((x-sx*.004,y0+.25,b+1.0),(.008,.50,2.0),'SteelDark');g.box((x+sx*.25,y0-.004,b+1.0),(.50,.008,2.0),'SteelDark')
        for k in range(5):
            g.box((x-sx*.0105,y0+.25,b+.10+k*.40+.10),(.006,.46,.20),'Yellow')


def _gantry(m,s,v):
    b,F=v.b,v.F;x0,x1=-(F-1.0),F-1.0;y0,y1=-2.95,-HWT
    gp=m.p('DoorGantry','STRUCTURE',.006)
    gp.box((0,(y0+y1)/2,(v.g0+v.g1)/2),(x1-x0,y1-y0,v.g1-v.g0),'SteelDark')
    # Bottom guide channels (toes down) over each track, front stiffeners, top cover strip.
    ch=[(-.15,0.),(-.15,-.20),(-.13,-.20),(-.13,-.02),(.13,-.02),(.13,-.20),(.15,-.20),(.15,0.)]
    for yc in v.yc:
        gp.prism([(yc+u,v.g0+w) for u,w in ch],(x0,0,0),YZX,x1-x0,'SteelDark')
    st=m.p('GantryStiffeners','DETAIL',.002)
    k=max(2,round((x1-x0)/2.0))
    for j in range(1,k):
        st.box((x0+(x1-x0)*j/k,y0-.03,(v.g0+v.g1)/2),(.025,.06,v.g1-v.g0-.04),'SteelDark')
    m.box('GantryCover',(0,(y0+y1)/2,v.g1+.004),(x1-x0-.02,y1-y0+.06,.008),'Galvanized','DETAIL',.002)
    # Floodlights on the gantry face.
    for x in (-v.ow*.30,v.ow*.30):
        m.box('Floodlights',(x,y0-.16,v.g0+.30),(.42,.20,.30),'SteelDark','DETAIL',.004)
        m.box('FloodlightLenses',(x,y0-.262,v.g0+.30),(.34,.004,.22),'LightWarm','DETAIL',0.)
        m.box('Floodlights',(x,y0-.03,v.g0+.30),(.08,.06,.08),'SteelDark','DETAIL',.002)


def _rails(m,s,v):
    b,F=v.b,v.F;x0,x1=-(F-1.0),F-1.0;hero=s.detail=='HERO'
    rp=m.p('DoorRails','STRUCTURE',.002);sp=m.p('RailSolePlates','DETAIL',.002)
    for yc in v.yc:
        sp.box((0,yc,b+.01),(x1-x0,.30,.02),'SteelDark')
        rp.prism([(yc+u,b+w) for u,w in RAIL],(x0+.45,0,0),YZX,x1-x0-.90,'Galvanized')
        if hero:
            cl=m.p('RailClips','DETAIL',.001)
            for k in range(int((x1-x0-.90)/1.0)):
                x=x0+.95+k
                for sy in (-1,1):cl.box((x,yc+sy*.085,b+.035),(.08,.05,.03),'SteelDark')
        for sx in (-1.,1.):     # end stops with rubber buffers at the pocket ends
            m.box('RailEndStops',(sx*(F-1.225),yc,b+.245),(.45,.40,.45),'Yellow','DETAIL',.006)
            m.p('RailBuffers','DETAIL',.002).cylinder((sx*(F-1.45),yc,b+.30),(sx*(F-1.57),yc,b+.30),.10,'Rubber',16)


def _leaf(m,s,v,side,k):
    """One door leaf: k=0 inner (outer track, meeting stile at x=0), k=1 outer (wall track)."""
    b=v.b;Lw=v.Lw;H=v.zl1-v.zl0;yc=v.yc[1-k];t=LEAF_T
    cx=side*(.002+Lw/2) if k==0 else side*(v.ow/2+.30-Lw/2)
    ox=side*(v.ow/2+.40+Lw/2)                                  # parked in the pocket (both tracks)
    name=f'BlastDoor_{"L" if side<0 else "R"}{k}'
    p=m.p(name,'DOOR',.004);p.pivot=(cx,yc,b)
    yo,yi=yc-t/2,yc+t/2;zm=(v.zl0+v.zl1)/2
    lead=-side*Lw/2                                           # leading (meeting / lap) edge offset
    e0=.02 if k==0 else 0.                                    # inner leaves leave room for the seal
    xl,xr=cx+lead+side*e0,cx-lead                             # body from the leading to the trailing edge
    bx,bw=(xl+xr)/2,abs(xr-xl)
    p.box((bx,yc,zm),(bw,t,H),'RoofOlive')
    # Outer face: perimeter flats, horizontal bands (25 mm proud).
    f=.20;pr=.025;yf=yo-pr/2
    for zz in (v.zl0+f/2,v.zl1-f/2):p.box((bx,yf,zz),(bw,pr,f),'SteelDark')
    for x in (xl+side*f/2,xr-side*f/2):p.box((x,yf,zm),(f,pr,H-2*f),'SteelDark')
    nb=max(2,round(H/2.0))
    for j in range(1,nb):
        p.box((bx,yf,v.zl0+H*j/nb),(bw-2*f,pr,.14),'SteelDark')
    # Impact stripes on the inner leaves' meeting stile, meeting seal in the edge recess.
    if k==0:
        xs=xl+side*f/2
        for j in range(int((H-2*f-.20)/.40)+1):
            p.box((xs,yo-pr-.0045,v.zl0+f+.20+j*.40),(f-.02,.009,.20),'Yellow')
        p.box((cx+lead+side*e0/2,yc,zm),(e0-.002,t-.10,H-.04),'Rubber')
    # Bottom: rubber skirts on both faces, wheel bogies at both ends.
    xb=Lw/2-.55
    p.box((cx,yo-.0085,b+.245),(2*xb-.82,.015,.43),'Rubber')
    p.box((cx,yi+.0085,b+.245),(2*xb-.82,.015,.43),'Rubber')
    for sx in (-1,1):
        x=cx+sx*xb
        p.box((x,yc,b+.30),(.80,.40,.30),'SteelDark')
        p.cylinder((x,yc-.06,b+.29),(x,yc+.06,b+.29),.17,'Galvanized',16)
    # Top guide posts + rollers into the gantry channel, lifting lugs.
    for sx in (-1,1):
        x=cx+sx*Lw/3
        p.box((x,yc,v.zl1+.04),(.10,.10,.08),'SteelDark')
        p.cylinder((x,yc,v.zl1+.08),(x,yc,v.zl1+.20),.07,'Galvanized',12)
        x=cx+sx*Lw/5
        p.box((x,yc,v.zl1+.10),(.04,.24,.20),'SteelDark')
    # Inner face: vertical T stiffeners and horizontal ribs between them (200 mm deep).
    nv=max(2,round(Lw/1.5));xs=[cx-Lw/2+.25+(Lw-.50)*j/nv for j in range(nv+1)]
    for x in xs:
        p.box((x,yi+.10,zm),(.016,.20,H-.40),'SteelDark');p.box((x,yi+.2075,zm),(.15,.015,H-.40),'SteelDark')
    for j in range(1,nb):
        z=v.zl0+H*j/nb
        for x0,x1 in zip(xs,xs[1:]):
            p.box(((x0+x1)/2,yi+.09,z),(x1-x0-.016,.18,.016),'SteelDark')
    p.box(((xs[0]+xs[1])/2,yi+.09,v.zl0+.75),(.60,.18,.40),'SteelDark')        # rack drive unit
    m.doors.append(dict(part=p.name,kind='SLIDE',closed=(cx,yc,b),opened=(ox,yc,b),open_fraction=s.door_open,
                        track=k,channel='GATE'))
    m.collisions.append(dict(part=p.name,center=(cx,yc,zm),dims=(Lw,t,H),axes=A.IDENTITY))


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
        m.box('Foundation',(0,-4.5,b-.16),(2*F+2.0,9.0,.32),'Concrete','GROUND',.009,True)
        m.box('Foundation',(0,(d+TKR+6.0)/2,b-.16),(2*v.xo+2.0,d+TKR+6.0,.32),'Concrete','GROUND',.009,True)
        jt=m.p('ApronJoints','GROUND',0.)
        nx=max(2,round((2*F+1.6)/5.0))
        for j in range(1,nx):jt.box((-(F+.8)+(2*F+1.6)*j/nx,-6.3075,b+.0005),(.01,4.985,.001),'Joint')
        jt.box((0,-3.8,b+.0005),(2*F+1.6,.01,.001),'Joint')
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
    mk.box((0,-6.0,b+.0012),(.12,4.0,.0012),'Yellow')                             # lead-in on the apron
    mk.box((0,-3.45,b+.0012),(2*(F-1.0),.15,.0012),'Yellow')                      # door-track keep-clear line
    for sx in (-1.,1.):mk.box((sx*(a-1.2),(1.3+d-1.0)/2,b+.0012),(.10,d-2.3,.0012),'White')


def _sign(m,s,v):
    if not s.signage:return
    number=sign_text(s.name);W=3.6;H=round(W/4.6,3);x=-(v.F-.5);y=-3.20;zs=v.b+4.2
    ys=y-.035;xb=x-W/2+H
    m.box('SignCarrier',(x,y-.015,zs),(W-.2,.03,H-.2),'SteelDark','DETAIL',.002)
    m.box('SignField',((xb+x+W/2)/2,ys-.015,zs),(x+W/2-xb,.04,H),'SteelDark','DETAIL',.002)
    m.box('SignNumberBlock',((x-W/2+xb)/2,ys-.015,zs),(H,.04,H),'Yellow','DETAIL',.002)
    face=ys-.035
    m.label(number,((x-W/2+xb)/2,face-.01,zs),H*.6,'SteelDark',name='ShelterNumber',extrude=.010,bevel=.002,
            font='BigShoulders-Bold.ttf',anchor='CENTER',cap_height=.58*H,max_width=.74*H)
    xt=xb+.2*H;xr=x+W/2-.16*H
    m.label('HARDENED SHELTER',(xt,face-.008,zs+.10*H),H*.4,'White',name='ShelterTitle',extrude=.008,bevel=.0015,
            font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.28*H,max_width=xr-xt,tracking=1.04)
    m.box('SignRule',((xt+xr)/2,face-.002,zs-.11*H),(xr-xt,.004,.01),'Galvanized','DETAIL',.001)
    m.label(re.sub(r'[_-]+',' ',s.name).strip().upper()[:28],(xt,face-.004,zs-.26*H),H*.15,'Yellow',name='ShelterSubtitle',
            extrude=.004,font='BigShoulders-Bold.ttf',anchor='LEFT',cap_height=.10*H,max_width=xr-xt,tracking=1.45)


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
    _vault(m,s,v);_headwall(m,s,v);_gantry(m,s,v);_rails(m,s,v)
    for side in (-1,1):
        for k in (0,1):_leaf(m,s,v,side,k)
    xd=_rear(m,s,v);_ground(m,s,v,xd);_sign(m,s,v)
    if s.services:_services(m,s,v)
    m.port('AIRCRAFT_IN',(0,-3.5,v.b),-pi/2,v.ow,'HANGAR')
    m.port('PERSONNEL_REAR_OUT',(xd,v.d+TKR+1.3,0),pi/2,s.walkway_width)
    m.port('PERSONNEL_OUT',(0,-9.0,0),-pi/2,s.walkway_width)
    m.openings.append(dict(kind='HANGAR',width=v.ow,height=v.zl1-v.b-.30,center=(0,-HWT,v.b)))
    m.notes.append('MB01 hardened shelter (fictional CGI): telescopic steel leaves on two tracks; no protective, ballistic or structural claim.')

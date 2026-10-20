"""Military command headquarters (core HQ, office_style AUTO/COMMAND).

A symmetric three-part block on a stone podium: a central entrance pavilion with a four-column
portico whose roof is the review balcony, punched windows in deep reveals between pilasters,
floor bands, a cornice under the roof line and a 1.05 m parapet with a metal coping. The ground
floor is stone, upper floors plaster (EXECUTIVE), precast concrete (TECHNICAL) or stone
(MONOLITHIC). Three risers and a 1:12 ramp lead up to the entrance terrace; the forecourt is
closed by an anti-ram bollard line with a flag base beside the axis. Rear service door, side
emergency exits, a roof stair exit, an empty louvred plant screen, roof drains, scuppers and
downpipes, and lightning protection complete it. Equipment (lights, cameras, roof plant, street
furniture) is left to dedicated prop assets.
Fictional CGI scenery: the security and accessibility features are visual references to public
design guidance, with no engineering, protective or code-compliance claim.

Design coordinates of core.Model: x across the front, y from the front wall face (0) into the
building (d), z up. Walls tile without overlap (pieces only touch); every other part is bedded
1-3 mm or meets in opposite-facing contact, never same-facing coplanar overlap.
"""
from math import sqrt, pi, radians, sin, cos
from ..vendor import as07_reference as A

T=.40                   # exterior wall
POD=.48                 # podium: three 160 mm risers from the forecourt to the ground floor
RISE,TREAD=.16,.32
PAR=1.05                # parapet above the roof finish
ATTIC=.60               # pavilion attic above the parapet
PW=.50                  # pilaster width
CORN_D,CORN_H=.14,.30   # cornice projection / height under the roof line
BAND_D,BAND_H=.06,.28   # floor band projection / height
COP_T,COP_O=.05,.04     # coping thickness / overhang
PLI=.14                 # plinth projection beyond the wall faces
RAMP=12.                # ramp run per unit rise (1:12)


class Face:
    """Facade plane: o on the outer wall face, u along the facade, n outward. Local s along u,
    t into the wall from the outer face (negative = proud), z up."""
    def __init__(self,o,u,n):self.o,self.u,self.n=o,u,n
    def xy(self,s,t):return (self.o[0]+self.u[0]*s-self.n[0]*t,self.o[1]+self.u[1]*s-self.n[1]*t)
    def box(self,m,name,s0,s1,t0,t1,z0,z1,mat,group='FACADE',bevel=.004):
        (xa,ya),(xb,yb)=self.xy(s0,t0),self.xy(s1,t1)
        lo=(min(xa,xb),min(ya,yb),min(z0,z1));hi=(max(xa,xb),max(ya,yb),max(z0,z1))
        if min(h-l for l,h in zip(lo,hi))<1e-5:return
        m.box(name,tuple((l+h)/2 for l,h in zip(lo,hi)),tuple(h-l for l,h in zip(lo,hi)),mat,group,bevel)
    def cyl(self,m,name,s,t0,t1,z,r,mat,seg=16,group='DETAIL',bevel=.002):   # axis along the normal
        (xa,ya),(xb,yb)=self.xy(s,t0),self.xy(s,t1)
        m.p(name,group,bevel).cylinder((xa,ya,z),(xb,yb,z),r,mat,seg)


class HQ:
    def __init__(self,s):
        self.s=s;self.w=w=s.width;self.d=d=s.depth;self.v=v=s.command_variant
        self.b=b=s.base_height;self.zf=b+POD;self.fh=s.floor_height;self.nf=s.floors
        self.zr=self.zf+self.nf*self.fh
        N=max(5,round(w/3.8));N+=1-N%2                    # odd bay count: the entrance is on the axis
        self.N=N;self.bw=w/N;self.np=3 if N>=7 else 1;self.cw=self.np*self.bw
        self.P=1.0+s.facade_relief                        # pavilion projection
        self.Ns=max(3,round(d/3.6));self.bws=d/self.Ns
        self.mono=v=='MONOLITHIC';self.tech=v=='TECHNICAL'
        self.owmax=1.45 if self.mono else 1.80
        self.oh=min(1.65,self.fh-1.45)
        self.tc=.22 if self.mono else .15                 # window frame plane, from the outer face
        self.base='ConcreteDark' if self.tech else 'Stone'
        self.upper={'EXECUTIVE':'Plaster','TECHNICAL':'ConcreteLight','MONOLITHIC':'Stone'}[v]
        if not s.base_cladding:self.base=self.upper
        self.trim='Concrete' if self.tech else 'ConcreteLight'
        self.pd=0. if self.mono else .10                   # pilaster projection
        self.fin=.10+.45*s.facade_relief if (self.tech and s.vertical_fins>0) else self.pd
        self.full=s.detail!='DRAFT'
        # entrance terrace, steps, ramp and forecourt
        self.tw=self.cw+2.4;self.yc=-self.P-2.30           # column line
        self.yt=-self.P-3.10                               # terrace front edge
        self.ys=self.yt-2*TREAD                            # foot of the steps
        self.Lr=(self.zf-b)*RAMP
        self.yF=self.ys-s.plaza_depth                      # forecourt front edge
        self.FX=max(w/2+2.5,self.tw/2+self.Lr+1.2)
    def z0(self,f):return self.zf+f*self.fh
    def ow(self,bay):return min(self.owmax,bay-PW-.90)


# ------------------------------------------------------------------------------------- walls
def walls(m,h,face,lo,hi,grid,ztop,ops,coll=True):
    """Tile the wall between lo..hi (s) from the ground floor to ztop. grid: bay boundaries;
    ops: openings (s0,s1,z0,z1). Each bay is cut at the floor lines and at every opening's sill
    and head; within an opening's height only the piers either side are built."""
    floors=[h.z0(f) for f in range(1,h.nf)]
    for g0,g1 in zip(grid,grid[1:]):
        c0,c1=max(g0,lo),min(g1,hi)
        if c1-c0<1e-4:continue
        mine=[o for o in ops if c0<(o[0]+o[1])/2<c1]
        cuts=sorted({h.zf,ztop,*[z for z in floors if z<ztop],*[o[2] for o in mine],*[o[3] for o in mine]})
        for za,zb in zip(cuts,cuts[1:]):
            mat=h.base if zb<=h.zf+h.fh+1e-6 else h.upper
            part='HQWallsBase' if mat==h.base else 'HQWalls'
            hit=[o for o in mine if o[2]<=za+1e-6 and o[3]>=zb-1e-6]
            if hit:
                o=hit[0]
                face.box(m,part,c0,o[0],0,T,za,zb,mat,'BODY',.004);face.box(m,part,o[1],c1,0,T,za,zb,mat,'BODY',.004)
            else:
                face.box(m,part,c0,c1,0,T,za,zb,mat,'BODY',.004)


def wall_hulls(m,h,face,lo,hi,ztop,doors):
    """UCX: one box per wall run, split around door openings so they stay passable."""
    def add(s0,s1,z0,z1):
        (xa,ya),(xb,yb)=face.xy(s0,0),face.xy(s1,T)
        c=((xa+xb)/2,(ya+yb)/2,(z0+z1)/2);dm=(abs(xb-xa),abs(yb-ya),z1-z0)
        if min(dm)>1e-4:m.collisions.append(dict(part='SM_MB01_HQWalls',center=c,dims=dm,axes=A.IDENTITY))
    u=lo
    for s0,s1,z1 in sorted(doors):
        add(u,s0,h.zf,ztop);add(s0,s1,z1,ztop);u=s1
    add(u,hi,h.zf,ztop)


# ------------------------------------------------------------------------------------- openings
def window(m,h,face,s0,s1,z0,z1,idx,grille=False,hood=True):
    tc=h.tc;ta,tb=tc-.035,tc+.035;fw=.07;sc=(s0+s1)/2;fr='HQWindowFrames'
    face.box(m,fr,s0,s0+fw,ta,tb,z0,z1,'SteelDark','FACADE',.002);face.box(m,fr,s1-fw,s1,ta,tb,z0,z1,'SteelDark')
    face.box(m,fr,s0+fw,s1-fw,ta,tb,z1-fw,z1,'SteelDark');face.box(m,fr,s0+fw,s1-fw,ta,tb,z0,z0+fw,'SteelDark')
    zt=z0+(z1-z0)*.72
    if s1-s0>=1.2:          # centre mullion, top-hung vents above the transom
        face.box(m,fr,sc-.03,sc+.03,ta+.005,tb-.005,z0+fw,z1-fw,'SteelDark')
        for a,b in ((s0+fw,sc-.03),(sc+.03,s1-fw)):face.box(m,fr,a,b,ta+.005,tb-.005,zt-.03,zt+.03,'SteelDark')
    else:face.box(m,fr,s0+fw,s1-fw,ta+.005,tb-.005,zt-.03,zt+.03,'SteelDark')
    face.box(m,'HQGlass',s0+fw-.015,s1-fw+.015,tc-.008,tc+.008,z0+fw-.015,z1-fw+.015,'Glass','GLASS',0.)
    face.box(m,'HQWindowInterior',s0,s1,T-.02,T,z0,z1,'Interior','DETAIL',0.)
    if h.full:
        bh=(z1-z0)*(.18+((idx*13+h.s.seed)%7)*.07)
        face.box(m,'HQBlinds',s0+.06,s1-.06,tb+.03,tb+.045,z1-.05-bh,z1-.05,'Blind','DETAIL',0.)
    face.box(m,'HQSills',s0-.06,s1+.06,-.06,ta,z0-.05,z0+.02,h.trim,'FACADE',.003)
    if hood and h.s.sunshades:face.box(m,'HQHoods',s0-.10,s1+.10,-.28,0,z1,z1+.12,h.trim,'FACADE',.004)
    if grille and h.full:   # security bars in the reveal, flats behind them
        n=max(3,round((s1-s0)/.15)-1)
        for i in range(n):
            s=s0+(i+1)*(s1-s0)/(n+1);face.box(m,'HQGrilles',s-.0125,s+.0125,.03,.055,z0-.01,z1+.02,'SteelDark','DETAIL',0.)
        for z in (z0+.30,z1-.30):face.box(m,'HQGrilles',s0-.02,s1+.02,.055,.065,z-.025,z+.025,'SteelDark')


def glazed_door(m,h,face,s0,s1,z0,z1,leaf_h,transom=True):
    """Double glazed door in a heavy frame (main entrance / balcony): leaves, transom light."""
    tc=.18;fw=.12;fr='HQDoorFrames';sc=(s0+s1)/2
    face.box(m,fr,s0,s0+fw,tc-.05,tc+.05,z0,z1,'SteelDark','FACADE',.003);face.box(m,fr,s1-fw,s1,tc-.05,tc+.05,z0,z1,'SteelDark')
    face.box(m,fr,s0+fw,s1-fw,tc-.05,tc+.05,z1-fw,z1,'SteelDark')
    zt=z0+leaf_h
    if transom and z1-fw-zt>.25:
        face.box(m,fr,s0+fw,s1-fw,tc-.05,tc+.05,zt,zt+.10,'SteelDark')
        face.box(m,'HQGlass',s0+fw-.015,s1-fw+.015,tc-.008,tc+.008,zt+.085,z1-fw+.015,'Glass','GLASS',0.)
    lf='HQDoorLeaves'
    for a,b in ((s0+fw+.004,sc-.003),(sc+.003,s1-fw-.004)):
        face.box(m,lf,a,a+.10,tc-.03,tc+.03,z0+.015,zt-.004,'SteelDark','DOOR',.002);face.box(m,lf,b-.10,b,tc-.03,tc+.03,z0+.015,zt-.004,'SteelDark')
        face.box(m,lf,a+.10,b-.10,tc-.03,tc+.03,z0+.015,z0+.27,'SteelDark');face.box(m,lf,a+.10,b-.10,tc-.03,tc+.03,zt-.11,zt-.004,'SteelDark')
        face.box(m,'HQGlass',a+.09,b-.09,tc-.006,tc+.006,z0+.26,zt-.10,'Glass','GLASS',0.)
    for s in (sc-.13,sc+.13):   # pull bars on the outside
        face.box(m,'HQDoorHardware',s-.015,s+.015,tc-.09,tc-.03,z0+.75,z0+1.75,'Galvanized','DETAIL',.002)
    face.box(m,'HQThresholds',s0+fw,s1-fw,0,T,z0,z0+.012,'Galvanized','DETAIL',.001)
    face.box(m,'HQWindowInterior',s0,s1,T-.02,T,z0+.012,z1,'Interior','DETAIL',0.)


def steel_door(m,h,face,s0,s1,z0,z1,double=True):
    """Steel service / exit door: frame, solid leaves (vision panels on the double door), kick plates."""
    tc=.12;fw=.08;fr='HQDoorFrames';sc=(s0+s1)/2
    face.box(m,fr,s0,s0+fw,tc-.05,tc+.05,z0,z1,'SteelDark');face.box(m,fr,s1-fw,s1,tc-.05,tc+.05,z0,z1,'SteelDark')
    face.box(m,fr,s0+fw,s1-fw,tc-.05,tc+.05,z1-fw,z1,'SteelDark')
    leaves=((s0+fw+.004,sc-.003),(sc+.003,s1-fw-.004)) if double else ((s0+fw+.004,s1-fw-.004),)
    for a,b in leaves:
        face.box(m,'HQDoorLeaves',a,b,tc-.025,tc+.025,z0+.015,z1-fw-.004,'RoofOlive','DOOR',.003)
        face.box(m,'HQKickPlates',a+.04,b-.04,tc-.028,tc-.024,z0+.05,z0+.30,'Galvanized','DETAIL',0.)
        if double:face.box(m,'HQGlass',(a+b)/2-.11,(a+b)/2+.11,tc-.029,tc-.023,z0+1.35,z0+1.95,'Glass','GLASS',0.)
    if double:
        for s in (sc-.10,sc+.10):face.box(m,'HQDoorHardware',s-.012,s+.012,tc-.08,tc-.025,z0+.95,z0+1.25,'Galvanized','DETAIL',.002)
    face.box(m,'HQThresholds',s0+fw,s1-fw,0,T,z0,z0+.012,'Galvanized','DETAIL',.001)


def door_canopy(m,h,face,sc,half,z):
    face.box(m,'HQDoorCanopies',sc-half,sc+half,-1.20,0,z,z+.16,h.trim,'FACADE',.006)
    face.box(m,'HQDoorCanopies',sc-half,sc+half,-1.22,-1.20,z-.06,z+.16,'SteelDark')      # drip fascia


# ------------------------------------------------------------------------------------- articulation
def pilasters(m,h,face,spans,z0,z1,depth=None):
    for s0,s1,dp in spans:
        face.box(m,'HQPilasters',s0,s1,-(dp if depth is None else depth),0,z0,z1,h.base if h.mono else ('ConcreteDark' if h.tech else 'Stone'),'FACADE',.004)


def bands(m,h,face,segs):
    if h.mono:return
    for f in range(1,h.nf):
        z=h.z0(f)
        for s0,s1 in segs:face.box(m,'HQBands',s0,s1,-BAND_D,0,z-BAND_H/2,z+BAND_H/2,h.trim,'FACADE',.004)


def grid_spans(h,grid,wrap=False,fins=True):
    """Pilaster spans on a bay grid: half pilasters at the run ends (wrap: extended by their own
    projection so they close the building corner against the adjoining face's half pilaster),
    full ones inside (deep fins on TECHNICAL when fins)."""
    e=h.pd if wrap else 0.;g=grid
    return [(g[0]-e,g[0]+PW/2,h.pd)]+[(x-PW/2,x+PW/2,h.fin if fins else h.pd) for x in g[1:-1]]+[(g[-1]-PW/2,g[-1]+e,h.pd)]


def band_segs(grid):
    return [(g0+PW/2,g1-PW/2) for g0,g1 in zip(grid,grid[1:])]


# ------------------------------------------------------------------------------------- building
def build_command(m):
    s=m.cfg;h=HQ(s);w,d,b,zf,zr,fh,nf=h.w,h.d,h.b,h.zf,h.zr,h.fh,h.nf;P,cw,bw=h.P,h.cw,h.bw
    ztop=zr+PAR;ztp=ztop+ATTIC;zcb=zr-CORN_H                # parapet / attic tops, cornice bottom
    Nw=(h.N-h.np)//2
    front=Face((0,0),(1,0),(0,-1));pav=Face((0,-P),(1,0),(0,-1));rear=Face((0,d),(1,0),(0,1))
    left=Face((-w/2,0),(0,1),(-1,0));right=Face((w/2,0),(0,1),(1,0))
    pl=Face((-cw/2,0),(0,1),(-1,0));pr=Face((cw/2,0),(0,1),(1,0))
    idx=[0]
    def win(face,s0,s1,f,grille,hood=True):
        idx[0]+=1;zs=h.z0(f)+.90;window(m,h,face,s0,s1,zs,zs+h.oh,idx[0],grille,hood);return (s0,s1,zs,zs+h.oh)
    # --- front wings
    gl=[-w/2+k*bw for k in range(Nw+1)];gr=[cw/2+k*bw for k in range(Nw+1)]
    for g in (gl,gr):
        ops=[]
        for g0,g1 in zip(g,g[1:]):
            sc,ow=(g0+g1)/2,h.ow(bw)
            for f in range(nf):ops.append(win(front,sc-ow/2,sc+ow/2,f,f==0))
        walls(m,h,front,g[0],g[-1],g,ztop,ops)
        wall_hulls(m,h,front,g[0],g[-1],ztop,[])
    # --- pavilion front: main door, balcony door or glazed strip, windows
    gp=[-cw/2+k*bw for k in range(h.np+1)];ops=[];sc=0.
    od=min(2.6,bw-PW-.70);dh=min(3.1,fh-.50)
    glazed_door(m,h,pav,sc-od/2,sc+od/2,zf,zf+dh,2.45);ops.append((sc-od/2,sc+od/2,zf,zf+dh))
    m.openings.append(dict(kind='LOBBY',center=(0,-P,zf),width=od,height=dh))
    strip=nf>=3 and s.atrium_floors>=2
    if nf>=2:
        z1=h.z0(1)
        if strip:
            fl=min(nf-1,s.atrium_floors);zt=h.z0(fl)+.90+h.oh;ws=min(2.4,bw-PW-.60)
            glazed_strip(m,h,pav,sc-ws/2,sc+ws/2,z1,zt,[h.z0(f) for f in range(2,fl+1)])
            ops.append((sc-ws/2,sc+ws/2,z1,zt));top=fl
        else:
            glazed_door(m,h,pav,sc-.80,sc+.80,z1,z1+2.5,2.5,False);ops.append((sc-.80,sc+.80,z1,z1+2.5));top=1
        for f in range(top+1,nf):ops.append(win(pav,sc-h.ow(bw)/2,sc+h.ow(bw)/2,f,False))
    for g0,g1 in zip(gp,gp[1:]):
        c=(g0+g1)/2
        if abs(c)<1e-6:continue
        for f in range(nf):ops.append(win(pav,c-h.ow(bw)/2,c+h.ow(bw)/2,f,f==0,f!=0))
    walls(m,h,pav,-cw/2,cw/2,gp,ztp,ops)
    wall_hulls(m,h,pav,-cw/2,cw/2,ztp,[(sc-od/2,sc+od/2,zf+dh)])
    for fc,sgn in ((pl,-1),(pr,1)):          # pavilion returns (blank), up to the attic
        walls(m,h,fc,-P+T,T,[-P,T],ztp,[]);wall_hulls(m,h,fc,-P+T,T,ztp,[])
    # --- rear: service door on the axis
    gq=[-w/2+k*bw for k in range(h.N+1)];ops=[]
    for g0,g1 in zip(gq,gq[1:]):
        c=(g0+g1)/2
        if abs(c)<1e-6:
            steel_door(m,h,rear,c-.90,c+.90,zf,zf+2.40);ops.append((c-.90,c+.90,zf,zf+2.40))
            door_canopy(m,h,rear,c,min(1.35,bw/2-PW/2-.05),zf+2.65);m.openings.append(dict(kind='PEDESTRIAN',center=(c,d,zf),width=1.8,height=2.4))
            for f in range(1,nf):ops.append(win(rear,c-h.ow(bw)/2,c+h.ow(bw)/2,f,False))
        else:
            for f in range(nf):ops.append(win(rear,c-h.ow(bw)/2,c+h.ow(bw)/2,f,f==0))
    walls(m,h,rear,-w/2,w/2,gq,ztop,ops);wall_hulls(m,h,rear,-w/2,w/2,ztop,[(-.90,.90,zf+2.40)])
    # --- sides: emergency exit near the rear
    gs=[k*h.bws for k in range(h.Ns+1)];ke=h.Ns-2
    for fc,sx in ((left,-1),(right,1)):
        ops=[]
        for k,(g0,g1) in enumerate(zip(gs,gs[1:])):
            c=(g0+g1)/2
            if k==ke:
                steel_door(m,h,fc,c-.50,c+.50,zf,zf+2.20,False);ops.append((c-.50,c+.50,zf,zf+2.20))
                door_canopy(m,h,fc,c,.85,zf+2.45);m.openings.append(dict(kind='PEDESTRIAN',center=(sx*w/2,c,zf),width=1.0,height=2.2))
                for f in range(1,nf):ops.append(win(fc,c-h.ow(h.bws)/2,c+h.ow(h.bws)/2,f,False))
            else:
                for f in range(nf):ops.append(win(fc,c-h.ow(h.bws)/2,c+h.ow(h.bws)/2,f,f==0))
        walls(m,h,fc,T,d-T,gs,ztop,ops);ce=(gs[ke]+gs[ke+1])/2
        wall_hulls(m,h,fc,T,d-T,ztop,[(ce-.50,ce+.50,zf+2.20)])
    # --- pilasters, corner blocks, bands, cornice
    if not h.mono:
        for g in (gl,gr):pilasters(m,h,front,grid_spans(h,g),zf,zcb)
        z1f=_z1f(h);zu=z1f-.45
        for za,zb in ((zf,zu),(z1f,zcb)):
            if zb-za>.05:pilasters(m,h,pav,grid_spans(h,gp,fins=False),za,zb)
        pilasters(m,h,rear,grid_spans(h,gq),zf,zcb)
        for fc in (left,right):pilasters(m,h,fc,grid_spans(h,gs,wrap=True),zf,zcb)
        for fc in (pl,pr):
            for za,zb in ((zf,zu),(z1f,zcb)):
                if zb-za>.05:pilasters(m,h,fc,[(-P-h.pd,-P+PW/2,h.pd)],za,zb)
        if h.fin>h.pd:      # deep fins come down to the paving in front of the plinth
            for fc,g in ((front,gl),(front,gr),(rear,gq),(left,gs),(right,gs)):
                for gg in g[1:-1]:fc.box(m,'HQPilasters',gg-PW/2,gg+PW/2,-h.fin,-PLI,b,zf,'ConcreteDark')
    bands(m,h,front,band_segs(gl)+band_segs(gr));bands(m,h,rear,band_segs(gq))
    for fc in (left,right):bands(m,h,fc,band_segs(gs))
    for fc in (pl,pr):bands(m,h,fc,[(-P+PW/2,-h.pd if not h.mono else 0.)])
    cn='HQCornice';cm=h.trim
    front.box(m,cn,-w/2-CORN_D,-cw/2-CORN_D,-CORN_D,0,zcb,zr,cm,'FACADE',.005);front.box(m,cn,cw/2+CORN_D,w/2+CORN_D,-CORN_D,0,zcb,zr,cm)
    pav.box(m,cn,-cw/2-CORN_D,cw/2+CORN_D,-CORN_D,0,zcb,zr,cm);rear.box(m,cn,-w/2-CORN_D,w/2+CORN_D,-CORN_D,0,zcb,zr,cm)
    for fc in (left,right):fc.box(m,cn,0,d,-CORN_D,0,zcb,zr,cm)
    for fc in (pl,pr):fc.box(m,cn,-P,0,-CORN_D,0,zcb,zr,cm)
    # --- copings, roof deck, plinth
    cp='HQCoping'
    front.box(m,cp,-w/2-COP_O,-cw/2,-COP_O,T+COP_O,ztop,ztop+COP_T,'Galvanized','ROOF',.003)
    front.box(m,cp,cw/2,w/2+COP_O,-COP_O,T+COP_O,ztop,ztop+COP_T,'Galvanized')
    rear.box(m,cp,-w/2-COP_O,w/2+COP_O,-COP_O,T+COP_O,ztop,ztop+COP_T,'Galvanized')
    for fc in (left,right):fc.box(m,cp,T+COP_O,d-T-COP_O,-COP_O,T+COP_O,ztop,ztop+COP_T,'Galvanized')
    pav.box(m,cp,-cw/2-COP_O,cw/2+COP_O,-COP_O,T+COP_O,ztp,ztp+COP_T,'Galvanized')
    for fc in (pl,pr):fc.box(m,cp,-P+T+COP_O,T,-COP_O,T+COP_O,ztp,ztp+COP_T,'Galvanized')
    for c,dm in (((0,d/2,zr-.15),(w-2*T,d-2*T,.30)),((0,(T-P+T)/2,zr-.15),(cw-2*T,P,.30))):
        m.box('HQRoofDeck',c,dm,'RoofMembrane','ROOF',.003,True)
    pm='ConcreteDark' if h.tech else 'Stone'
    m.box('HQPlinth',(0,d/2,zf/2),(w+2*PLI,d+2*PLI,zf),pm,'GROUND',.006,True)
    m.box('HQPlinth',(0,(-P-PLI-PLI)/2,zf/2),(cw+2*PLI,P,zf),pm,'GROUND',.006,True)
    _attic(m,h);_portico(m,h,_z1f(h));_roof(m,h);_site(m,h)
    if s.micro_details and h.full:_lightning(m,h)
    m.port('PERSONNEL_OUT',(0,h.yF-.2,0),-pi/2,s.walkway_width)
    m.port('REAR_SERVICE_OUT',(0,d+4.0,0),pi/2,s.walkway_width)
    m.notes.append(f'MB01 command HQ ({h.v}): stone podium, portico and review balcony, {h.N}x{h.Ns} bays, '
                   'deep-reveal windows, 1.05 m parapet, 1:12 ramp, anti-ram bollard line. Exterior shell, '
                   'fictional CGI; no engineering or code-compliance claim.')


def _z1f(h):
    """Top of the portico slab: the first floor (review balcony), or under the cornice of a
    single-storey building (no balcony)."""
    return h.z0(1) if h.nf>=2 else h.zr-CORN_H


def glazed_strip(m,h,face,s0,s1,z0,z1,floor_lines):
    """Central curtain strip above the portico: jambs, two mullions, spandrel panels at the floor
    lines, door transom at 2.5 m (the balcony door is its lower centre pane)."""
    tc=h.tc;ta,tb=tc-.035,tc+.035;fw=.08;fr='HQWindowFrames'
    face.box(m,fr,s0,s0+fw,ta,tb,z0,z1,'SteelDark');face.box(m,fr,s1-fw,s1,ta,tb,z0,z1,'SteelDark')
    face.box(m,fr,s0+fw,s1-fw,ta,tb,z1-fw,z1,'SteelDark');face.box(m,fr,s0+fw,s1-fw,ta,tb,z0,z0+fw,'SteelDark')
    xs=[s0+(s1-s0)*k/3 for k in (1,2)]
    for x in xs:face.box(m,fr,x-.035,x+.035,ta+.005,tb-.005,z0+fw,z1-fw,'SteelDark')
    edges=[s0+fw]+[e for x in xs for e in (x-.035,x+.035)]+[s1-fw]
    for a,b in zip(edges[::2],edges[1::2]):face.box(m,fr,a,b,ta+.005,tb-.005,z0+2.47,z0+2.53,'SteelDark')
    for zl in floor_lines:face.box(m,'HQSpandrels',s0+fw,s1-fw,tc-.02,tc+.02,zl-.45,zl+.15,'SteelDark','FACADE',.002)
    face.box(m,'HQGlass',s0+fw-.015,s1-fw+.015,tc-.008,tc+.008,z0+fw-.015,z1-fw+.015,'Glass','GLASS',0.)
    face.box(m,'HQThresholds',s0,s1,0,ta,z0,z0+.012,'Galvanized','DETAIL',.001)
    face.box(m,'HQWindowInterior',s0,s1,T-.02,T,z0,z1,'Interior','DETAIL',0.)


def _attic(m,h):
    """Emblem medallion on the pavilion attic, centred over the entrance."""
    zc=h.zr+(PAR+ATTIC)/2+.05;y=-h.P;e=m.p('HQEmblem','DETAIL',.002)
    e.cylinder((0,y,zc),(0,y-.06,zc),.62,h.trim,32)
    e.tube((0,y-.06,zc),(0,y-.09,zc),.62,.53,'Galvanized',32)
    e.cylinder((0,y-.06,zc),(0,y-.10,zc),.34,'Galvanized',32)
    star=[]
    for k in range(10):
        r=.24 if k%2==0 else .095;a=pi/2+k*pi/5
        star.append((r*cos(a),zc+r*sin(a)))
    e.prism(star,(0,y-.12,0),((1,0,0),(0,0,1),(0,1,0)),.02,'Yellow')


def _portico(m,h,z1f):
    """Entrance terrace, steps and ramp; four-column portico carrying the review balcony; title."""
    s=h.s;b,zf,P,cw,tw=h.b,h.zf,h.P,h.cw,h.tw;yt,ys,yc=h.yt,h.ys,h.yc;st='Stone' if not h.tech else 'ConcreteDark'
    # terrace (podium extension) and steps
    zb=.02 if s.local_ground else b      # down to the paving bed (the forecourt is not bedded under them)
    for c,dm in (((0,(yt-P-PLI)/2,(zb+zf)/2),(tw,-P-PLI-yt,zf-zb)),
                 ((-(tw/2+cw/2+PLI)/2,(-P-PLI-PLI)/2,(zb+zf)/2),(tw/2-cw/2-PLI,P,zf-zb)),
                 (((tw/2+cw/2+PLI)/2,(-P-PLI-PLI)/2,(zb+zf)/2),(tw/2-cw/2-PLI,P,zf-zb))):
        m.box('HQTerrace',c,dm,st,'GROUND',.004,True)
    for k in (1,2):
        y0,y1=yt-k*TREAD,yt-(k-1)*TREAD;zt=zf-k*RISE
        m.box('HQSteps',(0,(y0+y1)/2,(zb+zt)/2),(tw,TREAD,zt-zb),st,'GROUND',.004,True)
    # 1:12 ramp along the left side of the terrace front, curbs either side
    L=h.Lr;x0,x1=-tw/2-L,-tw/2;ya,yb=yt,yt+1.50
    m.p('HQRamp','GROUND',.003).prism([(x0,b),(x1,b),(x1,zf)],(0,ya+.12,0),((1,0,0),(0,0,1),(0,1,0)),yb-ya-.24,'Concrete')
    for y in (ya,yb-.12):
        m.p('HQRamp','GROUND',.003).prism([(x0,b),(x1,b),(x1,zf+.10),(x0,b+.10)],(0,y,0),((1,0,0),(0,0,1),(0,1,0)),.12,st)
    ln=sqrt(L*L+(zf-b)**2);ax=((L/ln,0,(zf-b)/ln),(0,1,0),(-(zf-b)/ln,0,L/ln))
    m.collisions.append(dict(part='SM_MB01_HQRamp',center=((x0+x1)/2-.1*ax[2][0],(ya+yb)/2,(b+zf)/2-.1*ax[2][2]),dims=(ln,yb-ya,.2),axes=ax))
    if h.full:
        rl=m.p('HQHandrails','DETAIL',0.)
        for y in (ya+.06,yb-.06):     # ramp rails over the curbs, extended 300 mm at both ends
            rl.pipe([(x0-.30,y,b+.90),(x0,y,b+.90),(x1,y,zf+.90),(x1+.30,y,zf+.90)],.025,'Galvanized',8)
            for k in range(5):
                x=x0+.15+(L-.30)*k/4;zs=b+.10+(zf-b)*(x-x0)/L
                rl.cylinder((x,y,zs-.02),(x,y,b+.90+(zf-b)*(x-x0)/L),.022,'Galvanized',8)
        for x in sorted({-tw/2+.30,tw/2-.30,*((-cw/6,cw/6) if h.np==3 else ())}):   # stair rails
            rl.pipe([(x,ys-.30,b+.90),(x,ys,b+.90),(x,yt,zf+.90),(x,yt+.30,zf+.90)],.025,'Galvanized',8)
            rl.cylinder((x,ys-.15,b-.01),(x,ys-.15,b+.90),.022,'Galvanized',8)
            rl.cylinder((x,yt+.15,zf-.01),(x,yt+.15,zf+.90),.022,'Galvanized',8)
    # portico: columns (base, shaft, capital) and the balcony slab on them
    zu=z1f-.45;cols=(-cw/2,-cw/6,cw/6,cw/2) if h.np==3 else (-cw/2,cw/2)
    for x in cols:
        m.box('HQColumns',(x,yc,zf+.10),(.75,.75,.20),st,'STRUCTURE',.008)
        m.box('HQColumns',(x,yc,(zf+.20+zu-.18)/2),(.55,.55,zu-.18-zf-.20),st)
        m.box('HQColumns',(x,yc,zu-.09),(.72,.72,.18),st)
        m.collisions.append(dict(part='SM_MB01_HQColumns',center=(x,yc,(zf+zu)/2),dims=(.75,.75,zu-zf),axes=A.IDENTITY))
    ys0=-P-2.85
    m.box('HQPortico',(0,(ys0-P)/2,(zu+z1f)/2),(cw+.60,-P-ys0,.45),h.trim,'STRUCTURE',.006,True)
    pp=1.05;balcony=h.nf>=2
    if balcony:
        m.box('HQPortico',(0,ys0+.125,z1f+pp/2),(cw+.60,.25,pp),st,'STRUCTURE',.006,True)
        for sx in (-1,1):
            m.box('HQPortico',(sx*(cw/2+.20),(ys0+.25-P)/2,z1f+pp/2),(.20,-P-ys0-.25,pp),st,'STRUCTURE',.006,True)
            m.box('HQPorticoCoping',(sx*(cw/2+.20),(ys0+.29-P)/2,z1f+pp+.025),(.28,-P-ys0-.29,.05),'Galvanized','DETAIL',.003)
        m.box('HQPorticoCoping',(0,ys0+.125,z1f+pp+.025),(cw+.68,.33,.05),'Galvanized')
    if s.night_lighting:     # flush soffit panels between the columns
        for a,b_ in zip(cols,cols[1:]):
            m.box('HQSoffitLights',((a+b_)/2,-P-1.30,zu-.002),(.60,.60,.004),'LightWarm','DETAIL',0.)
    # title on the balcony front, building name below it
    yl=ys0-.02;zt,ct,zn=(z1f+.64,.36,z1f+.26) if balcony else (zu+.27,.22,None)
    m.label('KARARGAH',(0,yl,zt),ct,'Galvanized',name='HQTitle',extrude=.02,bevel=.002,
            font='BigShoulders-Bold.ttf',anchor='CENTER',cap_height=ct,max_width=cw*.78,tracking=1.10)
    if zn:m.label(s.name.replace('_',' ').upper()[:28],(0,ys0-.006,zn),.12,'Galvanized',name='HQSubtitle',extrude=.006,
                  font='BigShoulders-Bold.ttf',anchor='CENTER',cap_height=.11,max_width=cw*.6,tracking=1.40)


def _roof(m,h):
    """Roof stair exit, empty louvred plant screen, drains, rear scuppers and downpipes."""
    s=h.s;w,d,zr=h.w,h.d,h.zr;rear=Face((0,d),(1,0),(0,1))
    # stair exit: mass, coping, door, canopy
    px,py,pw,pd,ph=-w/4,d-T-2.2,3.4,2.6,2.7;yf=py-pd/2
    m.box('HQRoofExit',(px,py,zr+ph/2),(pw,pd,ph),h.upper,'BODY',.006,True)
    m.box('HQCoping',(px,py,zr+ph+COP_T/2),(pw+.08,pd+.08,COP_T),'Galvanized')
    for x in (px-.52,px+.52):m.box('HQDoorFrames',(x,yf-.02,zr+1.06),(.08,.04,2.12),'SteelDark')
    m.box('HQDoorFrames',(px,yf-.02,zr+2.16),(1.12,.04,.08),'SteelDark')
    m.box('HQDoorLeaves',(px,yf-.005,zr+1.06),(.96,.03,2.08),'RoofOlive','DOOR',.003)
    m.box('HQDoorCanopies',(px,yf-.45,zr+2.42),(1.6,.90,.10),h.trim)
    # plant screen: posts, angled blades, nothing inside (equipment comes from prop assets)
    if s.roof_screen:
        cx,cy=w/4,d*.55;sx,sy=min(6.0,w/2-3.0),3.6;zb,zt=zr,zr+1.8
        px_=[cx-sx/2,cx,cx+sx/2];py_=[cy-sy/2,cy+sy/2]
        for x in px_:
            for y in py_:m.box('HQScreenPosts',(x,y,(zb+zt)/2),(.10,.10,zt-zb),'SteelDark','DETAIL',.003)
        for x in (cx-sx/2,cx+sx/2):m.box('HQScreenPosts',(x,cy,(zb+zt)/2),(.10,.10,zt-zb),'SteelDark')
        bl=m.p('HQScreenBlades','DETAIL',0.);n=8
        for k in range(n):
            z=zb+.25+k*(zt-zb-.35)/(n-1)
            for y in py_:
                for a,b_ in zip(px_,px_[1:]):bl.box(((a+b_)/2,y,z),(b_-a-.10,.012,.16),'RoofOlive',A.euler_axes(radians(45),0,0))
            for x in (cx-sx/2,cx+sx/2):
                for a,b_ in ((cy-sy/2,cy),(cy,cy+sy/2)):bl.box((x,(a+b_)/2,z),(.012,b_-a-.10,.16),'RoofOlive',A.euler_axes(0,radians(45),0))
    for x in (-w/4,w/4):m.p('HQRoofDrains','DETAIL',.001).cylinder((x,d*.30,zr-.01),(x,d*.30,zr+.012),.16,'Galvanized',16)
    # rear scuppers through the parapet, hoppers and downpipes clear of the end-bay windows
    for sx in (-1,1):
        x=sx*(w/2-PW/2-.20)
        rear.box(m,'HQRainwater',x-.12,x+.12,-.16,.05,zr+.03,zr+.15,'Galvanized','DETAIL',.002)
        rear.box(m,'HQRainwater',x-.16,x+.16,-.42,-.16,zr-.28,zr+.06,'Galvanized')
        yp=d+.28
        m.p('HQRainwater','DETAIL',.002).pipe([(x,yp,zr-.28),(x,yp,h.b+.24),(x,yp+.16,h.b+.06)],.055,'Galvanized',10)
        for f in range(h.nf):rear.box(m,'HQPipeClamps',x-.02,x+.02,-.24,0,h.z0(f)+1.8-.02,h.z0(f)+1.8+.02,'SteelDark','DETAIL',.001)


def _lightning(m,h):
    """Conductor loop on the copings (over the pavilion attic), air terminals, two down conductors."""
    w,d,P,cw=h.w,h.d,h.P,h.cw;z1=h.zr+PAR+COP_T+.025;z2=z1+ATTIC;q=T/2
    loop=[(-cw/2-.10,q,z1),(-cw/2-.10,q,z2),(-cw/2+q,q,z2),(-cw/2+q,-P+q,z2),(cw/2-q,-P+q,z2),(cw/2-q,q,z2),
          (cw/2+.10,q,z2),(cw/2+.10,q,z1),(w/2-q,q,z1),(w/2-q,d-q,z1),(-w/2+q,d-q,z1),(-w/2+q,q,z1),(-cw/2-.16,q,z1)]
    lc=m.p('HQLightning','DETAIL',0.);cl=m.p('HQLightningClips','DETAIL',0.)
    lc.pipe(loop,.008,'Galvanized',6)
    for a,b in zip(loop,loop[1:]):
        if abs(a[2]-b[2])>1e-6:     # risers on the attic sides: one clip to the wall face
            x=a[0]+(.05 if a[0]<0 else -.05);cl.box((x,a[1],(a[2]+b[2])/2),(.10,.03,.03),'Galvanized');continue
        L=sqrt((b[0]-a[0])**2+(b[1]-a[1])**2);n=max(1,int(L/4.0))
        for k in range(n):
            t=(k+.5)/n;cl.box((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]-.0125-.001),(.03,.03,.027),'Galvanized')
    for x,y,z in ((-w/2+q,q,z1),(w/2-q,q,z1),(w/2-q,d-q,z1),(-w/2+q,d-q,z1),(-cw/2+q,-P+q,z2),(cw/2-q,-P+q,z2)):
        lc.cylinder((x,y,z-.027),(x,y,z+.03),.035,'Galvanized',10);lc.cylinder((x,y,z+.03),(x,y,z+.62),.01,'Galvanized',8)
    yd=d-PW/2-.20
    for sx in (-1,1):
        x0,xo=sx*(w/2-q),sx*(w/2+.20)
        lc.pipe([(x0,yd,z1),(xo,yd,z1),(xo,yd,h.b)],.008,'Galvanized',6)
        for f in range(h.nf):cl.box((sx*(w/2+.10),yd,h.z0(f)+1.8),(.21,.03,.03),'Galvanized')
        m.box('HQTestClamps',(xo,yd,h.b+.36),(.07,.07,.12),'SteelDark','DETAIL',.002)


def _site(m,h):
    """Forecourt paving, kerbs, perimeter pavement, anti-ram bollard line, flag base and poles."""
    s=h.s;w,d,b=h.w,h.d,h.b;FX,yF=h.FX,h.yF;tw,yt,ys,cw,P=h.tw,h.yt,h.ys,h.cw,h.P
    _exits(m,h)
    if not s.local_ground:return
    side=w/2+2.5;yb=d+4.0
    beds=[((-FX,FX),(yF,ys)),((-FX,-tw/2),(ys,-PLI)),((tw/2,FX),(ys,-PLI)),
          ((-side,-w/2-PLI),(-PLI,d+PLI)),((w/2+PLI,side),(-PLI,d+PLI)),((-side,side),(d+PLI,yb))]
    for (x0,x1),(y0,y1) in beds:      # bedding under the pavers, lifted off the plinth's base plane
        m.box('HQPavingBed',((x0+x1)/2,(y0+y1)/2,(.02+b-.06)/2),(x1-x0,y1-y0,b-.08),'Joint','GROUND',0.,True)
    # pavers (1.8 x 0.9 m forecourt, 1.25 m slabs round the building), skipped where fully covered
    covers=[((-tw/2,tw/2),(ys,-P-PLI)),((-tw/2,tw/2),(-P-PLI,-PLI)),((-tw/2-h.Lr,-tw/2),(yt,yt+1.5)),((-w/2-PLI,w/2+PLI),(-PLI,d+PLI))]
    fl=_flag_spot(h)
    if fl:covers.append(((fl[0]-2.45,fl[0]+2.45),(fl[1]-.75,fl[1]+.75)))
    def covered(x0,x1,y0,y1):return any(a<=x0+1e-6 and x1<=b_+1e-6 and c<=y0+1e-6 and y1<=e+1e-6 for (a,b_),(c,e) in covers)
    pv=m.p('HQPavers','GROUND',0.)     # the 8 mm gaps over the dark bed read as joints
    def pave(x0,x1,y0,y1,px,py,mats):
        nx,ny=max(1,round((x1-x0)/px)),max(1,round((y1-y0)/py));dx,dy=(x1-x0)/nx,(y1-y0)/ny
        for i in range(nx):
            for j in range(ny):
                a,c=x0+i*dx,y0+j*dy
                if covered(a,a+dx,c,c+dy):continue
                pv.box((a+dx/2,c+dy/2,b-.03),(dx-.008,dy-.008,.06),mats[(i*7+j*3)%9<2])
    pave(-FX,FX,yF,-PLI,1.8,.9,('Concrete','ConcreteLight'))
    for (x0,x1),(y0,y1) in beds[3:]:pave(x0,x1,y0,y1,1.25,1.25,('Concrete','Concrete'))
    kb=m.p('HQKerbs','GROUND',.004)
    kb.box((0,yF-.10,(b+.02)/2),(2*FX+.40,.20,b+.02),'ConcreteLight')
    for sx in (-1,1):
        kb.box((sx*(FX+.10),(yF-PLI)/2,(b+.02)/2),(.20,-PLI-yF,b+.02),'ConcreteLight')
        kb.box((sx*(side+.10),(-PLI+yb)/2,(b+.02)/2),(.20,yb+PLI,b+.02),'ConcreteLight')
        if FX>side+.01:kb.box((sx*(side+.20+FX+.20)/2,-PLI+.10,(b+.02)/2),(FX-side,.20,b+.02),'ConcreteLight')
    kb.box((0,yb+.10,(b+.02)/2),(2*side+.40,.20,b+.02),'ConcreteLight')
    # anti-ram bollards (<=1.2 m clear between them) behind the front kerb
    yb_=yF+.45;n=int((2*FX-1.2)/1.5)+1;x0=-(n-1)*1.5/2
    bo=m.p('HQBollards','PROPS',.003)
    for i in range(n):
        x=x0+i*1.5
        bo.cylinder((x,yb_,b-.05),(x,yb_,b+.95),.135,'Galvanized',16)
        bo.cylinder((x,yb_,b+.95),(x,yb_,b+1.0),.14,'SteelDark',16)
        bo.cylinder((x,yb_,b+.78),(x,yb_,b+.84),.137,'Yellow',16)
        m.collisions.append(dict(part='SM_MB01_HQBollards',center=(x,yb_,b+.5),dims=(.28,.28,1.0),axes=A.IDENTITY))
    if fl:_flags(m,h,*fl)


def _exits(m,h):
    """Landings and three risers at the rear service door and the two side emergency exits."""
    w,d,b,zf=h.w,h.d,h.b,h.zf;st='Stone' if not h.tech else 'ConcreteDark'
    m.box('HQLandings',(0,d+PLI+.73,(b+zf)/2),(3.2,1.46,zf-b),st,'GROUND',.004,True)
    for k in (1,2):
        y0=d+PLI+1.46+(k-1)*TREAD;zt=zf-k*RISE
        m.box('HQSteps',(0,y0+TREAD/2,(b+zt)/2),(3.2,TREAD,zt-b),st,'GROUND',.004,True)
    ce=(h.Ns-1.5)*h.bws
    for sx in (-1,1):
        x0,xl=sx*(w/2+PLI),sx*(w/2+PLI+1.30)
        m.box('HQLandings',((x0+xl)/2,ce,(b+zf)/2),(1.30,1.60,zf-b),st,'GROUND',.004,True)
        for k in (1,2):
            xa,xb=sx*(w/2+PLI+1.30+(k-1)*TREAD),sx*(w/2+PLI+1.30+k*TREAD);zt=zf-k*RISE
            m.box('HQSteps',((xa+xb)/2,ce,(b+zt)/2),(TREAD,1.60,zt-b),st,'GROUND',.004,True)


def _flag_spot(h):
    fx=h.tw/2+3.6;fy=h.yt-.40
    return (fx,fy) if fx+2.6<min(h.FX,h.w/2+2.5)-.3 else None


def _flags(m,h,fx,fy):
    """Stone flag base with three poles (the centre one tallest); flags are left to cloth assets."""
    b=h.b;st='Stone' if not h.tech else 'ConcreteDark';zt=b+.45
    m.box('HQFlagBase',(fx,fy,(b+zt)/2),(4.8,1.40,zt-b),st,'PROPS',.006,True)
    m.box('HQFlagBase',(fx,fy,zt+.025),(4.86,1.46,.05),'ConcreteLight')
    fp=m.p('HQFlagPoles','PROPS',.002)
    for x,H in ((fx-1.6,9.5),(fx,11.0),(fx+1.6,9.5)):
        fp.cylinder((x,fy,zt+.05),(x,fy,zt+.20),.12,'SteelDark',16)
        fp.cylinder((x,fy,zt+.20),(x,fy,zt+H*.5),.085,'Galvanized',16)
        fp.cylinder((x,fy,zt+H*.5),(x,fy,zt+H),.062,'Galvanized',16)
        fp.cylinder((x,fy,zt+H),(x,fy,zt+H+.10),.09,'Galvanized',16)
        m.collisions.append(dict(part='SM_MB01_HQFlagPoles',center=(x,fy,zt+H/2),dims=(.24,.24,H),axes=A.IDENTITY))

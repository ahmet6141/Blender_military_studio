# SPDX-License-Identifier: MIT
"""Explicit datums, interface semantics and tolerances for CGI kit assemblies.
Tolerances below are software acceptance thresholds, not building/military codes.
No bpy dependency. A check never moves, snaps or deletes geometry.
"""
from dataclasses import dataclass, asdict
from math import isfinite, sqrt, acos, degrees
from typing import Tuple
import hashlib, json

Vec3 = Tuple[float, float, float]
SCHEMA = 'base01.assembly/1'


def finite(value, name='value'):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f'{name}: finite real number required')
    return float(value)


def vector(value, name='vector'):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(name + ': exactly three components required')
    return tuple(finite(v, name) for v in value)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(v, name='direction'):
    v = vector(v, name)
    length = sqrt(dot(v, v))
    if length < 1e-12:
        raise ValueError(name + ': zero vector')
    return tuple(x/length for x in v)


@dataclass(frozen=True)
class Tolerances:
    position_m: float = .001
    dimension_m: float = .001
    facing_degrees: float = .1
    uv_area: float = 1e-12
    basis: float = 1e-6

    def checked(self):
        for key, val in asdict(self).items():
            if finite(val, key) <= 0:
                raise ValueError(key + ': must be positive')
        return self


@dataclass(frozen=True)
class Port:
    id: str
    owner: str
    role: str
    origin_m: Vec3
    direction: Vec3
    width_m: float
    surface_offset_m: float = 0.
    up: Vec3 = (0., 0., 1.)
    convention: str = 'OUTWARD'  # TRAVEL_IN is negated to obtain outward normal
    profile: str = 'walkway-v1'

    def checked(self):
        if not self.id or not self.owner:
            raise ValueError('Port identity and owner are required')
        if self.role not in ('PEDESTRIAN', 'PEDESTRIAN_OPENING', 'APRON', 'HANGAR', 'SERVICE_ROAD', 'FACADE'):
            raise ValueError('Unrecognised port role: ' + self.role)
        if self.convention not in ('OUTWARD','TRAVEL_IN','TRAVEL_OUT'):
            raise ValueError('Port direction convention must be explicit')
        vector(self.origin_m); d=unit(self.direction); u=unit(self.up)
        if abs(dot(d,u)) > 1e-6:
            raise ValueError('Port direction must be perpendicular to up; bank/slope adapter required')
        if finite(self.width_m,'width_m') <= 0:
            raise ValueError('Port width must be positive')
        finite(self.surface_offset_m)
        if not isinstance(self.profile,str) or not self.profile:
            raise ValueError('Explicit profile required')
        return self

    @property
    def surface(self):
        self.checked(); u=unit(self.up)
        return tuple(a+self.surface_offset_m*b for a,b in zip(self.origin_m,u))

    @property
    def outward(self):
        d=unit(self.direction)
        return tuple(-x for x in d) if self.convention=='TRAVEL_IN' else d


def inspect_joint(a: Port, b: Port, tolerances=Tolerances()):
    """Inspect a *direct butt joint*, not two distant endpoints of a future path.
    One metre gap intentionally fails; this is not a path router.
    """
    a.checked(); b.checked(); t=tolerances.checked(); issues=[]
    if a.owner==b.owner and a.id==b.id:
        issues.append('SAME_PORT')
    if 'PEDESTRIAN_OPENING' in (a.role,b.role):
        issues.append('LANDING_ADAPTER_REQUIRED')
    elif not (a.role==b.role or {a.role,b.role}=={'HANGAR','APRON'}):
        issues.append('ROLE_MISMATCH')
    if a.profile!=b.profile: issues.append('PROFILE_MISMATCH')
    width_error=abs(a.width_m-b.width_m)
    gap=sqrt(sum((x-y)**2 for x,y in zip(a.surface,b.surface)))
    facing=degrees(acos(max(-1.,min(1.,-dot(a.outward,b.outward)))))
    up_error=degrees(acos(max(-1.,min(1.,dot(unit(a.up),unit(b.up))))))
    if width_error>t.dimension_m: issues.append('WIDTH_MISMATCH')
    if gap>t.position_m: issues.append('SURFACE_GAP')
    if facing>t.facing_degrees: issues.append('FACING_MISMATCH')
    if up_error>t.facing_degrees: issues.append('UP_MISMATCH')
    return dict(schema=SCHEMA,status='FAIL' if issues else 'PASS',issues=issues,
        ports=[a.id,b.id],surface_gap_m=gap,width_error_m=width_error,
        facing_error_degrees=facing,up_error_degrees=up_error,
        a_surface_m=a.surface,b_surface_m=b.surface,geometry_changed=False,
        scope='direct joint only; no certified accessibility or construction suitability')


@dataclass(frozen=True)
class Envelope:
    """One source of truth: nominal *inside datum* width/depth, metre coordinates.
    Structural members can protrude inside nominal datums; this is NOT net aircraft clearance.
    Front/rear walls own the corner squares. Side walls occupy only 0..depth.
    """
    width: float
    depth: float
    thickness: float
    base: float
    eave: float
    rise: float

    @property
    def a(self): return self.width/2
    @property
    def outside_x(self): return self.a+self.thickness
    @property
    def front_y(self): return -self.thickness
    @property
    def back_y(self): return self.depth+self.thickness
    @property
    def roof_y0(self): return self.front_y-.18
    @property
    def roof_y1(self): return self.back_y+.18
    @property
    def roof_x(self): return self.outside_x+.28
    @property
    def floor_x(self): return self.outside_x+.43
    @property
    def floor_back_y(self): return self.back_y+.02
    @property
    def slope(self): return self.rise/self.outside_x
    def roof(self,x): return self.base+self.eave+self.rise*(1.-abs(x)/self.outside_x)
    def to_dict(self):
        return dict(**asdict(self),outside_x=self.outside_x,front_y=self.front_y,
            back_y=self.back_y,roof_y0=self.roof_y0,roof_y1=self.roof_y1,
            roof_x=self.roof_x,floor_x=self.floor_x,floor_back_y=self.floor_back_y,
            width_semantics='nominal inside datum, NOT unobstructed aircraft clearance',
            corner_owner='front/rear wall',units='m')


def envelope(config):
    return Envelope(config.width,config.depth,config.wall_thickness,config.base_height,
                    config.eave_height,config.roof_rise)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
        ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()


def strict_json_loads(text):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise ValueError('Duplicate JSON key: '+k)
            out[k]=v
        return out
    def invalid(value): raise ValueError('Non-finite JSON number: '+value)
    return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid)

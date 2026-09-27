# SPDX-License-Identifier: MIT
"""Compile the SIX new facade modules into pivot-stable LOD0/1/2 game assets.
Not a universal building optimizer. Preserves openings, glazing and moving leaves.
LOD is semantic detail removal, not a blanket decimation percentage or a baked atlas.
"""
from dataclasses import dataclass, replace, asdict
from collections import OrderedDict
from copy import deepcopy
from math import isfinite
import hashlib, json
from ..modular import geometry as MG
from ..modular.contracts import ModuleInput
from ..modular.catalog import require
from ..assembly.meshqa import inspect_parts
A=MG.A
SCHEMA='mb01.gamekit/0.1'
NEW_MODULES=('HANGAR.WALL.CASSETTE','HANGAR.WALL.VISION','HANGAR.WALL.SHADED',
             'HANGAR.WALL.DUAL_VENT','HANGAR.ENTRY.DOUBLE_SERVICE','HANGAR.ENTRY.CANOPY')
FINE=frozenset(('HeadReveal','SillDrip','CassetteReveals','VisionHeadShadow','EntryShadowReveal'))
DISTANT=FINE|frozenset(('PanelSeams','CassetteFold','EntryJambFold','CanopyLight'))


def role(part): return part.name.split('__')[-1]
def triangles(part): return sum(len(f)-2 for f in part.faces)
def bounds(part):
    return [tuple(min(v[i] for v in part.vertices) for i in range(3)),
            tuple(max(v[i] for v in part.vertices) for i in range(3))]


def hull_blocks_aperture(hull, opening, thickness, tolerance=1e-8):
    """Positive-volume intersection with the nominal rectangular wall aperture.
    Deliberate boundary contact is allowed. This does not test a human/aircraft body.
    """
    lo,hi=bounds(hull);x,y,z=opening['center_output']
    alo=(0.,y-opening['width']/2,opening['bottom'])
    ahi=(thickness,y+opening['width']/2,opening['bottom']+opening['height'])
    return all(min(hi[k],ahi[k])-max(lo[k],alo[k])>tolerance for k in range(3))


def _merge(name, group, parts, pivot=(0.,0.,0.)):
    result=A.MeshPart(name,group,0.,pivot)
    result.material_names=sorted({m for p in parts for m in p.material_names})
    lookup={m:i for i,m in enumerate(result.material_names)}
    for p in parts:
        off=len(result.vertices)
        result.vertices.extend(p.vertices)
        result.faces.extend(tuple(i+off for i in f) for f in p.faces)
        result.material_ids.extend(lookup[p.material_names[i]] for i in p.material_ids)
        result.uvs.extend(deepcopy(p.uvs));result.smooth.extend(p.smooth)
        result.primitive_count+=p.primitive_count;result.closed_primitive_count+=p.closed_primitive_count
    return result


def _box_hull(name,lo,hi,pivot):
    dims=tuple(hi[i]-lo[i] for i in range(3))
    if min(dims)<=1e-8:raise ValueError('Degenerate hull: '+name)
    p=A.MeshPart(name,'COLLISION',0.,pivot)
    p.box(tuple((lo[i]+hi[i])/2 for i in range(3)),dims,'Collision')
    return p


def _static_hulls(model):
    """Wall pieces only. Visual frame/glass/awning contact is not full navigation proof."""
    out=[]
    for i,b in enumerate(model.wall_boxes):
        x,y,z=b['center_source'];dx,dy,dz=b['dims']
        center=MG.canonical((x,y,z));dims=(dy,dx,dz)
        lo=tuple(center[k]-dims[k]/2 for k in range(3));hi=tuple(center[k]+dims[k]/2 for k in range(3))
        out.append(_box_hull('Hull_'+str(i),lo,hi,(0.,0.,0.)))
    return out


@dataclass
class CompiledAsset:
    key: str
    part: object
    source_roles: tuple
    sockets: list
    collisions: list
    door: dict | None = None


@dataclass
class ModuleBundle:
    settings: ModuleInput
    levels: dict
    openings: list
    report: dict


def geometry_hash(part):
    data=dict(vertices=[[round(v[j]-part.pivot[j],9) for j in range(3)] for v in part.vertices],
              faces=part.faces,uv=part.uvs,materials=part.material_names,ids=part.material_ids,smooth=part.smooth)
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def compile_module(settings):
    settings.checked()
    if settings.module_id not in NEW_MODULES:
        raise ValueError('Game-kit compiler currently supports the six expansion modules only.')
    levels={};stats={};omitted={};reference=None
    stem='SM_MB03_'+settings.module_id.split('.')[-1]
    dimension_tag=hashlib.sha256(json.dumps([settings.width,settings.height,settings.thickness],separators=(',',':')).encode()).hexdigest()[:8]
    stem+='_'+dimension_tag
    # Every LOD is compiled CLOSED. Door rest pivot/motion is separately recorded.
    for level in (0,1,2):
        m=MG.build(replace(settings,detail='WORKING' if level==0 else 'DRAFT',door_open=0.))
        check=MG.validation(m)
        if check['errors']:raise ValueError('Source module invalid: '+str(check['errors']))
        if reference is None:reference=m
        omit=FINE if level==1 else (DISTANT if level==2 else frozenset())
        parts=[p for p in m.parts if role(p) not in omit]
        omitted[level]=[role(p) for p in m.parts if role(p) in omit]
        groups=OrderedDict()
        for p in parts:
            key='DOOR_'+role(p).split('_')[-1] if p.group=='DOOR' else ('GLASS' if p.group=='GLASS' else 'OPAQUE')
            groups.setdefault(key,[]).append(p)
        assets=[]
        for key,ps in groups.items():
            moving=key.startswith('DOOR_');pivot=ps[0].pivot if moving else (0.,0.,0.)
            name=stem+'_'+key
            merged=_merge(name,'DOOR' if moving else ('GLASS' if key=='GLASS' else 'BODY'),ps,pivot)
            # Keep LOD material SLOT ORDER identical; deliberate unused slots are retained.
            if level:
                base=next(a.part for a in levels[0] if a.key==key)
                remap={i:base.material_names.index(n) for i,n in enumerate(merged.material_names)}
                merged.material_ids=[remap[i] for i in merged.material_ids]
                merged.material_names=list(base.material_names)
            motion=deepcopy(next((d for d in m.doors if d['part']==ps[0].name),None)) if moving else None
            if motion:motion['part']=name
            sockets=deepcopy([p for p in m.ports if p['role']=='FACADE_JOIN']) if key=='OPAQUE' else []
            if key=='OPAQUE':hulls=_static_hulls(reference)
            elif moving:
                # Collision always uses LOD0 rest leaf, not detail-dependent bounds.
                rp=next(p for p in reference.parts if role(p)==role(ps[0]))
                lo,hi=bounds(rp);hulls=[_box_hull('DoorHull',lo,hi,pivot)]
            else:hulls=[]
            assets.append(CompiledAsset(key,merged,tuple(role(p) for p in ps),sockets,hulls,motion))
        levels[level]=assets
        stats[level]=dict(render_meshes=len(assets),triangles=sum(triangles(a.part) for a in assets),
            max_material_slots=max(len(a.part.material_names) for a in assets),
            assets=[dict(key=a.key,name=a.part.name,pivot_m=a.part.pivot,triangles=triangles(a.part),
               materials=a.part.material_names,geometry_sha256=geometry_hash(a.part),collision_hulls=len(a.collisions)) for a in assets])
    errors=[]
    for level,assets in levels.items():
        qa=inspect_parts([a.part for a in assets])
        errors.extend(f"LOD{level}: {i['code']} {i['part']}" for i in qa['issues'] if i['severity']=='ERROR')
        if stats[level]['max_material_slots']>8:errors.append(f'LOD{level} exceeds 8 material slots per asset.')
        if level and stats[level]['triangles']>stats[level-1]['triangles']:errors.append('LOD triangle count increased.')
        if {a.key for a in assets}!={a.key for a in levels[0]}:errors.append('LOD group keys differ.')
        for a,b in zip(assets,levels[0]):
            if a.part.pivot!=b.part.pivot:errors.append('LOD pivot changed.')
            if a.sockets!=b.sockets:errors.append('LOD connector moved.')
            if a.door!=b.door:errors.append('LOD door motion changed.')
            for hull in a.collisions:
                lo,hi=bounds(hull)
                # No positive-volume intrusion into any rectangular wall aperture.
                if a.key=='OPAQUE':
                    for o in reference.openings:
                        if hull_blocks_aperture(hull,o,settings.thickness):
                            errors.append('Wall collision intersects the nominal aperture volume.')
    report=dict(schema=SCHEMA,source_module=settings.module_id,config=asdict(settings),
         levels=stats,omitted_roles=omitted,status='PASS' if not errors else 'FAIL',errors=errors,
         raw_source_triangles_before_blender_modifiers=True,
         policy='semantic simplification; opaque/glass/door split; no texture bake',
         lighting='DYNAMIC_ONLY; UV0_Tile is not a lightmap',native_blender='NOT_RUN',native_unreal='NOT_RUN',
         limitations=['Wall collision excludes ornamental frames, glazing and awning; review player traces.',
           'LOD2 is conservative geometry, not a far-building impostor.',
           'No trim atlas bake, automatic Nanite/HISM or whole-building optimization.'])
    return ModuleBundle(settings,levels,reference.openings,report)

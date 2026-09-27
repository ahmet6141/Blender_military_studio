# SPDX-License-Identifier: MIT
"""Pure-Python whole-building LOD compiler for MB01.
It regenerates the canonical procedural asset at the origin and performs semantic LOD filtering.
No Blender runtime dependency.
"""
from dataclasses import replace
import re
from .. import core
from ..vendor import as07_reference as A

LOD_SCHEMA='mb01.building_lod_bundle/0.4'
_MAJOR={'BODY','FACADE','ROOF','GLASS','DOOR','STRUCTURE','GROUND'}
_SMALL_TOKENS=(
    'Fastener','Handle','Bracket','Shadow','Expansion','Clamp','Rung','Anchor','Soil','Wayfinding',
    'BackSupports','Transoms','Drip','Reveal','SoffitLights','Diffuser','Hanger','Cable','Conduit',
)


def _safe(name):
    return re.sub(r'[^A-Za-z0-9_]+','_',name).strip('_')[:48] or 'BUILDING'


def _include(part,lod):
    if lod==0:return True
    if lod==1:
        if part.group=='PROPS':return False
        if any(t.lower() in part.name.lower() for t in _SMALL_TOKENS):return False
        return True
    if lod==2:
        return part.group in _MAJOR
    raise ValueError('LOD must be 0, 1 or 2.')


def _merge(model,name,lod):
    out=A.MeshPart(name,'BUILDING',0)
    out.pivot=(0.,0.,0.)
    out.vertices=[];out.faces=[];out.material_names=[];out.material_ids=[];out.smooth=[];out.uvs=[]
    out.primitive_count=0;out.closed_primitive_count=0
    included=[]
    for p in model.parts:
        if not _include(p,lod):continue
        included.append(p.name)
        off=len(out.vertices);out.vertices.extend(p.vertices)
        remap=[]
        for mat in p.material_names:
            if mat not in out.material_names:out.material_names.append(mat)
            remap.append(out.material_names.index(mat))
        out.faces.extend(tuple(i+off for i in face) for face in p.faces)
        out.material_ids.extend(remap[i] for i in p.material_ids)
        out.smooth.extend(p.smooth);out.uvs.extend(p.uvs)
        out.primitive_count+=getattr(p,'primitive_count',0)
        out.closed_primitive_count+=getattr(p,'closed_primitive_count',0)
    if not out.faces:raise ValueError('LOD filter produced no geometry.')
    return out,included


def triangle_count(part):
    return sum(max(0,len(f)-2) for f in part.faces)


def compile_building_lods(settings):
    settings=settings.checked()
    levels={};reports={}
    level_detail={0:'HERO',1:'WORKING',2:'DRAFT'}
    base_name='SM_MB01_'+_safe(settings.name)
    for lod,detail in level_detail.items():
        cfg=replace(settings,detail=detail,door_open=0.0)
        model=core.build(cfg);validation=core.validation(model)
        if validation['errors']:raise ValueError('Source geometry failed LOD'+str(lod)+': '+str(validation['errors']))
        part,included=_merge(model,base_name,lod)
        levels[lod]=part
        reports[lod]={
            'detail_source':detail,'triangles_raw':triangle_count(part),'vertices':len(part.vertices),'faces':len(part.faces),
            'materials':list(part.material_names),'source_parts':included,'source_part_count':len(included)
        }
    # LOD triangle counts are expected to be non-increasing; warn/fail on a policy regression.
    if not (reports[0]['triangles_raw']>=reports[1]['triangles_raw']>=reports[2]['triangles_raw']):
        raise ValueError('Semantic LOD triangle counts are not monotonically decreasing.')
    return {'schema':LOD_SCHEMA,'settings':settings,'levels':levels,'reports':reports,
        'policy':{'LOD0':'all HERO geometry','LOD1':'WORKING minus props/micro-detail','LOD2':'major architectural groups only',
                  'doors':'canonical closed pose','manual_locked_objects':'not included; bundle is regenerated from procedural config'}}

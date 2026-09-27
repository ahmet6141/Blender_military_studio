# SPDX-License-Identifier: MIT
"""Blender-native production audit for whole MB01 buildings.
Read-only: reports topology/material/UV/collision metadata and rendering readiness.
"""
import json
import bpy
from ..blender_backend import descendants
from ..assembly.blender_qa import scan_live
from .. import materials


def audit_building(root):
    if root is None or not root.get('mb01_project_root'):
        raise ValueError('MB01 project root required.')
    base=scan_live(root)
    issues=list(base.get('issues',[]));objects=[];total_tri=0;material_names=set()
    deps=bpy.context.evaluated_depsgraph_get()
    for ob in descendants(root):
        if ob.type!='MESH' or ob.get('mb01_owner')!=root.get('mb01_owner'):
            continue
        ev=ob.evaluated_get(deps);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
        try:
            tri=sum(max(0,len(p.vertices)-2) for p in me.polygons);total_tri+=tri
            mats=[m.name for m in me.materials if m];material_names.update(mats)
            uv0=bool(me.uv_layers.get('UV0_Tile'))
            if not uv0:issues.append({'code':'NO_UV0','severity':'ERROR','part':ob.name})
            if any(v<0 for v in ob.scale):issues.append({'code':'NEGATIVE_SCALE','severity':'ERROR','part':ob.name})
            if ob.get('mb01_category') in {'BODY','GROUND','STRUCTURE','ROOF','DOOR'} and not ob.get('mb01_collision_mode'):
                issues.append({'code':'NO_COLLISION_POLICY','severity':'WARNING','part':ob.name})
            objects.append({'name':ob.name,'element':ob.get('mb01_element',''),'category':ob.get('mb01_category',''),
                'triangles':tri,'materials':mats,'uv0_tile':uv0,'collision':ob.get('mb01_collision_mode','NONE')})
        finally:
            ev.to_mesh_clear()
    # Soft budget is informational, not a hard quality claim: Nanite and classic LOD pipelines differ.
    warnings=[]
    if total_tri>1_500_000:warnings.append('High evaluated triangle count for a single building; review Nanite/LOD strategy in target engine.')
    if not any(o['category']=='GLASS' for o in objects):warnings.append('No GLASS category detected; verify material grouping if glazing is expected.')
    texture_resolution=None
    try:
        texture_resolution=materials.resolution_report(materials.recipes(override=root.get('mb01_texture_root','')))
        if not texture_resolution['unified']:
            mix=', '.join(f'{res}px: {sorted(tags)}' for res,tags in sorted(texture_resolution['by_resolution'].items(),reverse=True))
            warnings.append('PBR texture families use mixed resolutions ('+mix+'); unify before a stable release.')
    except (FileNotFoundError,ValueError) as exc:
        issues.append({'code':'PBR_SET_INCOMPLETE','severity':'ERROR','part':str(exc)})
    error=any(i.get('severity')=='ERROR' for i in issues)
    status='FAIL' if error else ('WARNING' if issues or warnings else 'PASS')
    return {'schema':'mb01.game_readiness/0.4','status':status,'root':root.name,'generator':root.get('mb01_version',''),
        'objects':objects,'object_count':len(objects),'evaluated_triangles':total_tri,'material_count':len(material_names),
        'materials':sorted(material_names),'issues':issues,'warnings':warnings,'texture_resolution':texture_resolution,
        'gates':{'evaluated_mesh_qa':base.get('status'),'uv0_tile_required':True,'collision_policy_required':True,
                 'negative_scale_forbidden':True,'native_ue_test_required':True,'visual_review_required':True},
        'limitations':['This is a Blender-side gate, not an Unreal runtime benchmark.',
            'UV0_Tile is tiled PBR UV; unique baked-light UV is not generated automatically.',
            'Visual quality must be reviewed from rendered/multi-view screenshots.']}


def publish(root):
    report=audit_building(root)
    name='MB01_GAME_READY_'+root.get('mb01_owner','')[:8]
    text=bpy.data.texts.get(name) or bpy.data.texts.new(name);text.clear();text.write(json.dumps(report,ensure_ascii=False,indent=2))
    root['mb01_game_ready_report']=json.dumps(report,ensure_ascii=False)
    return name,report

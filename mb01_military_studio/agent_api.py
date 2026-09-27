# SPDX-License-Identifier: MIT
"""Agent-facing MB01 API designed for Glonorce Blender MCP execute_blender_code.
The MCP remains external; this module gives it deterministic high-level functions.
"""
from dataclasses import fields, asdict
import json
import bpy
from . import core
from . import blender_backend as B
from .assembly.blender_qa import root_for


def _allowed_settings():
    return {f.name for f in fields(core.Settings)}


def _find_root(name=None):
    if name:
        ob=bpy.data.objects.get(name)
        r=root_for(ob) if ob else None
        if not r and ob and ob.get('mb01_project_root'):r=ob
        if not r:raise ValueError('MB01 root not found: '+name)
        return r
    r=root_for(bpy.context.active_object)
    if not r:raise ValueError('Select an MB01 root or pass root_name.')
    return r


def contract():
    return {'schema':'mb01.agent_api/0.4','version':core.VERSION,
      'entrypoints':['create_hq','rebuild','audit','prepare_review','export_game_ready','export_building_lods'],
      'recommended_glonorce_flow':['get_scene_graph GET_OBJECTS_FLAT','get_viewport_screenshot_base64 MULTI/MATERIAL',
        'execute_blender_code -> agent_api.rebuild patch','get_scene_graph CHECK_PRODUCTION_READINESS',
        'get_scene_graph DETECT_GEOMETRY_ERRORS','get_viewport_screenshot_base64 ISOMETRIC/MATERIAL'],
      'hq_variants':['EXECUTIVE','TECHNICAL','MONOLITHIC'],
      'quality_rule':'Treat screenshots and structured geometry checks as gates; do not accept a generation from prompt completion alone.'}


def create_hq(spec=None):
    spec=dict(spec or {})
    transform={k:spec.pop(k) for k in list(spec) if k in {'origin','yaw','texture_root'}}
    unknown=set(spec)-_allowed_settings()
    if unknown:raise ValueError('Unknown MB01 settings: '+', '.join(sorted(unknown)))
    base=dict(core.PRESETS['HQ']);base.update(kind='HQ',name='KARARGAH_HERO',detail='HERO',office_style='COMMAND',
        command_variant='EXECUTIVE',corner_glass=True,roof_screen=True,services=True,micro_details=True,night_lighting=True)
    if 'kind' in spec and spec['kind']!='HQ':raise ValueError('create_hq only accepts kind=HQ.')
    base.update(spec);base['kind']='HQ';settings=core.Settings(**base).checked()
    root,report=B.build_sync(settings,origin=tuple(transform.get('origin',bpy.context.scene.cursor.location)),
        yaw=float(transform.get('yaw',0)),override=str(transform.get('texture_root','')))
    return {'root_name':root.name,'owner':root['mb01_owner'],'config':asdict(settings),'build_report':report,
        'next':['get_viewport_screenshot_base64(view_direction="MULTI", display_mode="MATERIAL", target_objects=[root.name])',
                'get_scene_graph(action="CHECK_PRODUCTION_READINESS")','agent_api.audit(root.name)']}


def rebuild(root_name, patch):
    root=_find_root(root_name);cfg=json.loads(root['mb01_config']);patch=dict(patch or {})
    unknown=set(patch)-_allowed_settings()
    if unknown:raise ValueError('Unknown MB01 settings: '+', '.join(sorted(unknown)))
    cfg.update(patch);settings=core.Settings(**cfg).checked()
    new_root,report=B.build_sync(settings,old_root=root,override=root.get('mb01_texture_root',''))
    return {'root_name':new_root.name,'config':asdict(settings),'build_report':report}


def audit(root_name=None):
    from .game_ready.audit import audit_building
    return audit_building(_find_root(root_name))


def prepare_review(root_name=None):
    root=_find_root(root_name);camera=B.preview_scene(root)
    brief={'root':root.name,'camera':camera.name if camera else None,'recommended_views':['FRONT','RIGHT','TOP','ISOMETRIC'],
        'display_mode':'MATERIAL','review':['silhouette','facade depth','entry hierarchy','repetition','PBR scale','glass response','roof clutter','floating/intersections']}
    name='MB01_MCP_REVIEW_'+root.get('mb01_owner','')[:8]
    t=bpy.data.texts.get(name) or bpy.data.texts.new(name);t.clear();t.write(json.dumps(brief,ensure_ascii=False,indent=2))
    return brief


def export_game_ready(root_name=None,directory='//MB01_Exports'):
    from .exporter import export_project
    from .game_ready.audit import audit_building
    root=_find_root(root_name);report=audit_building(root)
    if report['status']=='FAIL':raise ValueError('Game-ready audit failed before export.')
    path=bpy.path.abspath(directory)
    dest=export_project(root,path)
    return {'directory':str(dest),'audit':report,'native_ue_verified':False}


def export_building_lods(root_name=None,directory='//MB01_Exports',mode='CLASSIC_LOD'):
    from .game_ready.building_export import export_building_bundle
    root=_find_root(root_name);cfg=core.Settings(**json.loads(root['mb01_config'])).checked()
    path=bpy.path.abspath(directory)
    dest=export_building_bundle(cfg,path,root.get('mb01_texture_root',''),mode=mode)
    return {'directory':str(dest),'mode':mode,'source_root':root.name,'native_ue_verified':False}

# SPDX-License-Identifier: MIT
"""Blender FBX/PBR exporter for the pure semantic whole-building LOD bundle."""
from pathlib import Path
from datetime import datetime
import hashlib,json,shutil,traceback,uuid
import bpy,bmesh
from .building_bundle import compile_building_lods, LOD_SCHEMA, triangle_count
from .. import materials
from ..blender_backend import mesh_for
from ..assembly.resources import fingerprint_recipe


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _safe(s):
    import re
    return re.sub(r'[^A-Za-z0-9_]+','_',s).strip('_')[:48] or 'BUILDING'


def export_building_bundle(settings,directory,override='',mode='CLASSIC_LOD'):
    if bpy.app.version<(4,5,0):raise RuntimeError('Blender 4.5+ required.')
    if bpy.context.mode!='OBJECT':raise RuntimeError('Object Mode required.')
    if abs(bpy.context.scene.unit_settings.scale_length-1.)>1e-7:raise RuntimeError('Unit Scale=1.0 required.')
    if mode not in {'CLASSIC_LOD','NANITE_HERO'}:raise ValueError('mode must be CLASSIC_LOD or NANITE_HERO')
    bundle=compile_building_lods(settings)
    root=Path(directory).expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
    dest=root/(f"MB04_{_safe(settings.name)}_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}")
    (dest/'Meshes').mkdir(parents=True);(dest/'Textures').mkdir();pending=dest/'EXPORT_INCOMPLETE.txt';pending.write_text('Incomplete',encoding='utf-8')
    levels=[0] if mode=='NANITE_HERO' else [0,1,2]
    used=set()
    for lod in levels:used.update(bundle['levels'][lod].material_names)
    recipes=materials.recipes(settings.palette,settings.wear,override)
    recipes={k:fingerprint_recipe(recipes[k]) for k in used}
    mats=materials.create_blender_materials(recipes)
    scene=bpy.context.scene;win=bpy.context.window;old_scene=win.scene if win else None
    temp=bpy.data.scenes.new('MB04_BUILDING_EXPORT');temp.unit_settings.system='METRIC';temp.unit_settings.scale_length=1.
    manifest={'schema':LOD_SCHEMA,'mode':mode,'source_units':'m','blender_version':bpy.app.version_string,'generator':bundle['settings'].__class__.__module__,
        'config':bundle['settings'].__dict__,'policy':bundle['policy'],'lods':[],'materials':{},'collision_policy':'PROJECT_DEFINED / COMPLEX_AS_SIMPLE_OPTION',
        'uv0':'UV0_Tile repeating PBR UV','uv1_lightmap':'NOT_GENERATED; use Lumen/dynamic lighting or create project-specific unique UV',
        'nanite_enabled_by_exporter':False,'native_ue_verified':False,
        'warnings':['Whole-building bundle is regenerated from procedural config at origin; manually locked scene edits are not included.',
                    'Moving doors use canonical closed pose in merged building LODs; use standard scene export for runtime door assets.',
                    'No guessed whole-building UCX is generated because a coarse hull would incorrectly block architectural openings.']}
    def clean():
        for ob in list(temp.objects):
            data=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and data.users==0:bpy.data.meshes.remove(data)
    try:
        for lod in levels:
            part=bundle['levels'][lod];me=mesh_for(part,mats,settings)
            bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bm.to_mesh(me);bm.free();me.update()
            name=part.name+f'_LOD{lod}';ob=bpy.data.objects.new(name,me);temp.collection.objects.link(ob)
            if lod<2:
                bevel=ob.modifiers.new('MB04_GameEdgeBevel','BEVEL');bevel.width=.007 if lod==0 else .0035;bevel.segments=2 if lod==0 else 1
                bevel.limit_method='ANGLE';bevel.angle_limit=0.6108652382;bevel.use_clamp_overlap=True
                if hasattr(bevel,'harden_normals'):bevel.harden_normals=True
            if win:win.scene=temp
            with bpy.context.temp_override(scene=temp,view_layer=temp.view_layers[0]):
                ob.select_set(True);temp.view_layers[0].objects.active=ob;temp.view_layers[0].update()
                deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);evme=ev.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
                evaluated_triangles=sum(max(0,len(poly.vertices)-2) for poly in evme.polygons);ev.to_mesh_clear()
                fn='Meshes/'+name+'.fbx';res=bpy.ops.export_scene.fbx(filepath=str(dest/fn),use_selection=True,object_types={'MESH'},
                    global_scale=1.,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Y',axis_up='Z',
                    use_space_transform=True,bake_space_transform=False,use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,
                    add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
                if 'FINISHED' not in res:raise RuntimeError('FBX export failed: '+name)
            rec=dict(bundle['reports'][lod]);rec.update(index=lod,file=fn,sha256=_sha(dest/fn),evaluated_triangles_before_fbx=evaluated_triangles,edge_bevel_m=(.007 if lod==0 else (.0035 if lod==1 else 0.0)))
            manifest['lods'].append(rec);clean()
        copied={}
        for key,recipe in recipes.items():
            rr=dict(recipe);rr['textures']={}
            for kind,src in recipe['textures'].items():
                src=Path(src);sha=_sha(src)
                if sha!=recipe['source_hashes'].get(kind):raise RuntimeError('PBR source changed during export: '+str(src))
                if sha not in copied:
                    rel='Textures/'+src.stem+'_'+sha[:12]+src.suffix;shutil.copy2(src,dest/rel);copied[sha]=rel
                rr['textures'][kind]=copied[sha]
            manifest['materials'][key]=rr
        (dest/'BUILDING_GAME_READY.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        (dest/'IMPORT_README_TR.txt').write_text(
            'CLASSIC_LOD modunda LOD0 ana Static Mesh olarak import edilir; LOD1 ve LOD2 aynı mesh içine LOD Import ile bağlanır.\n'
            'NANITE_HERO modunda yalnız LOD0 üretilir; Nanite hedef motor içinde kullanıcı tarafından etkinleştirilir.\n'
            'Collision otomatik uydurulmaz. Mimari açıklıkları kapatmamak için Complex-as-Simple veya proje özel collision üretin.\n'
            'UV0_Tile PBR için tekrar eder; UV1 lightmap otomatik değildir. Lumen/dinamik ışık veya proje bazlı UV1 kullanın.\n'
            'BUILDING_GAME_READY.json PBR ve LOD manifestidir. UE runtime doğrulaması hedef projede yapılmalıdır.\n',encoding='utf-8')
        pending.unlink();return dest
    except Exception:
        pending.write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        if win and old_scene:win.scene=old_scene
        clean();bpy.data.scenes.remove(temp)

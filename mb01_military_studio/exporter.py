# SPDX-License-Identifier: MIT
"""Per-asset evaluated FBX export; no source scene mutation.
Unreal execution is separate and must be verified on the target engine.
"""
from pathlib import Path
from datetime import datetime
import json,hashlib,shutil,uuid,math
import bpy,bmesh
from mathutils import Matrix
from . import core,materials,coordinates
from .blender_backend import descendants


def filehash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def safe_stem(s):
    import re
    return re.sub(r'[^A-Za-z0-9_]','_',s)[:44]

def export_project(root,base):
    if root.get('mb01_project_root') is not True:raise ValueError('MB01 proje kökü gerekli.')
    if bpy.context.mode!='OBJECT':raise RuntimeError('Object Mode gerekli.')
    if abs(bpy.context.scene.unit_settings.scale_length-1.)>1e-7:raise RuntimeError('Unit Scale 1.0 gerekli.')
    source=[o for o in descendants(root) if o.get('mb01_owner')==root['mb01_owner'] and o.type in {'MESH','FONT'}]
    if not source:raise ValueError('Aktif proje içinde export edilecek mesh yok.')
    for o in source:coordinates.convert_matrix([list(row) for row in o.matrix_world],[[1,0,0],[0,1,0],[0,0,1]])
    from .assembly.blender_qa import scan_live
    qa_report=scan_live(root)
    if qa_report['status']=='FAIL':
        from .assembly.blender_qa import publish
        name=publish(qa_report)
        raise ValueError('BASE01 export ön-denetimi başarısız: '+name)
    base=Path(base).expanduser().resolve();base.mkdir(parents=True,exist_ok=True)
    dest=base/(safe_stem(root.name)+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:5]);dest.mkdir()
    for folder in ('Meshes','Textures'):(dest/folder).mkdir()
    failure=dest/'EXPORT_FAILED.txt';failure.write_text('Export not yet complete.',encoding='utf-8')
    if root.get('mb01_modular_root'):
        from types import SimpleNamespace
        settings=SimpleNamespace(**json.loads(root['mb01_modular_style']))
    else:
        settings=core.Settings(**json.loads(root['mb01_config']))
    if root.get('mb01_hangar_root'):
        from .hangar_studio.contracts import from_document
        from .hangar_studio import style as hangar_style
        hangar_config=from_document(json.loads(root['mb01_hangar_document']))
        recipe=hangar_style.recipes(hangar_config,root.get('mb01_texture_root',''))
    else:
        recipe=materials.recipes(settings.palette,settings.wear,root.get('mb01_texture_root',''))
    manifest={'schema':'mb01.scene/0.2','generator':root.get('mb01_version',core.VERSION),'project':root['mb01_owner'],
        'project_name':settings.name,'source_units':'m','blender_version':bpy.app.version_string,
        'asset_map':{},'instances':[],'materials':{},'ports':[],'export_warnings':[],
        'lightmap_note':'UV0_Tile repeats in metres. No unique lightmap UV supplied. Dynamic lighting; lightmap unwrap is a separate operation.',
        'ue_runtime_verified':False,'assembly_preflight':qa_report,
        'mcp_agent_api':'mb01_military_studio.agent_api','pbr_workflow':'BaseColor + ORM(AO/Roughness/Metal) + NormalGL/NormalDX + Height',
        'render_profile':'Cycles/AgX preview only; final lighting remains project-specific'}
    if root.get('mb01_modular_root'):
        manifest['modular_recipe']=json.loads(root['mb01_modular_document'])
        manifest['export_warnings'].append('Modular alpha: single-storey facade only; no automatic building closure or native port joining.')
    if root.get('mb01_hangar_root'):
        manifest['hangar_recipe']=json.loads(root['mb01_hangar_document'])
        manifest['hangar_metadata']=json.loads(root['mb01_hangar_metadata'])
        manifest['door_motion']=[{'id':o['mb01_element'],'data':json.loads(o['mb01_door'])}
                                 for o in source if o.get('mb01_door')]
        manifest['export_warnings'].append('Hangar Studio alpha.3: current door poses only; motion metadata is not a runtime animation Blueprint. Preview practical lights are not UE light actors.')
    scene=bpy.context.scene;win=bpy.context.window;old_scene=win.scene if win else None
    layer=scene.view_layers[0];scene.view_layers[0].update()
    deps=bpy.context.evaluated_depsgraph_get()
    temp=bpy.data.scenes.new('MB01_EXPORT_TEMP');temp.unit_settings.system='METRIC';temp.unit_settings.scale_length=1.
    def clear_temp():
        for obj in list(temp.objects):
            data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and data.users==0:bpy.data.meshes.remove(data)
    def fbx_write(mesh,name,extra=()):
        obj=bpy.data.objects.new(name,mesh);temp.collection.objects.link(obj)
        objects=[obj]
        for hindex,hull in enumerate(extra):
            hm=bpy.data.meshes.new(name+'_Hull');hm.from_pydata(hull.vertices,[],hull.faces);hm.update()
            ho=bpy.data.objects.new(f'UCX_{name}_{hindex:02d}',hm);temp.collection.objects.link(ho);objects.append(ho)
        if win:win.scene=temp
        with bpy.context.temp_override(scene=temp,view_layer=temp.view_layers[0]):
            for ob in objects:ob.select_set(True)
            temp.view_layers[0].objects.active=obj
            result=bpy.ops.export_scene.fbx(filepath=str(dest/'Meshes'/(name+'.fbx')),use_selection=True,
                object_types={'MESH'},global_scale=1.,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
                axis_forward='-Y',axis_up='Z',use_space_transform=True,bake_space_transform=False,
                use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,
                add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
            if 'FINISHED' not in result:raise RuntimeError('FBX export failed: '+name)
        if win:win.scene=scene
        clear_temp()
        return 'Meshes/'+name+'.fbx'
    try:
        for key,center,dims in [('SM_MB01_CalX',(1.,0.,.2),(2.,.2,.4)),('SM_MB01_CalY',(0.,1.5,.3),(.2,3.,.6))]:
            p=core.A.MeshPart(key,'CALIBRATION',0);p.box(center,dims,'Calibration')
            me=bpy.data.meshes.new(key);me.from_pydata(p.vertices,[],p.faces);me.update()
            # Some exporter paths need a UV layer even without textures/tangents.
            me.uv_layers.new(name='UV0_Tile')
            rel=fbx_write(me,key)
            manifest['asset_map'][key]={'file':rel,'sha256':filehash(dest/rel),'materials':[],'collision':'NONE','calibration':True}
        cache={}
        for src in source:
            # Shared evaluated mesh if datablock, material mapping and modifier settings agree.
            modifier_sig=[(m.type,getattr(m,'width',None),getattr(m,'segments',None),m.show_viewport) for m in src.modifiers]
            sig=core.digest({'data':src.data.name,'asset':src.get('mb01_asset_key',src.name),
                'modifiers':modifier_sig,'mats':[m.name if m else '' for m in src.data.materials]})
            if sig not in cache:
                with bpy.context.temp_override(scene=scene,view_layer=layer):
                    evaluated=src.evaluated_get(deps)
                    me=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
                # Ensure UV attributes exist for meshified font geometry too.
                if not me.uv_layers.get('UV0_Tile'):
                    uv=me.uv_layers.new(name='UV0_Tile')
                    uv.data.foreach_set('uv',[v for loop in me.loops for v in me.vertices[loop.vertex_index].co[:2]])
                if not me.color_attributes.get('SW01_Tint'):
                    c=me.color_attributes.new(name='SW01_Tint',type='FLOAT_COLOR',domain='POINT');c.data.foreach_set('color',[1.]*(4*len(me.vertices)))
                me.color_attributes.active_color_index=list(me.color_attributes).index(me.color_attributes['SW01_Tint'])
                bm=bmesh.new();bm.from_mesh(me)
                bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bm.to_mesh(me);bm.free();me.update()
                names=[];slotnames=[]
                for mat in me.materials:
                    semantic=mat.get('mb01_recipe_key') if mat else None
                    if not semantic and mat:
                        semantic=next((k for k in recipe if mat.name==k),None)
                    if semantic not in recipe:
                        raise ValueError('Bilinmeyen / kullanıcıya özel materyal: '+str(mat.name if mat else None)+'. Bu sürüm ortak PBR tariflerini export eder.')
                    names.append(semantic);slotnames.append(mat.name)
                key=safe_stem(src.get('mb01_asset_key',src.name))+'_'+sig[:10]
                coll=src.get('mb01_collision_mode','NONE');hulls=[]
                metadata=json.loads(src.data.get('mb01_metadata','{}')) if src.type=='MESH' else {}
                if src.get('mb01_category')=='DOOR':
                    # A single convex moving-door hull in hinge-local coordinates.
                    lo=[min(v.co[j] for v in me.vertices) for j in range(3)]
                    hi=[max(v.co[j] for v in me.vertices) for j in range(3)]
                    h=core.A.MeshPart('DoorHull','COLLISION',0);h.box(tuple((lo[j]+hi[j])/2 for j in range(3)),tuple(hi[j]-lo[j] for j in range(3)),'C')
                    hulls=[h];coll='HULLS'
                rel=fbx_write(me,key,hulls)
                manifest['asset_map'][key]={'file':rel,'sha256':filehash(dest/rel),'materials':names,'material_slot_names':slotnames,
                    'collision':coll,'metadata':metadata,'source_asset':src.get('mb01_asset_key',''),'calibration':False}
                cache[sig]=key
            manifest['instances'].append({'id':src.get('mb01_element',src.name),'asset':cache[sig],
                'label':src.name,'category':src.get('mb01_category','DETAIL'),
                'matrix_world_m':[list(row) for row in src.matrix_world]})
        used={name for d in manifest['asset_map'].values() for name in d['materials']}
        copied={}
        for name in used:
            r=dict(recipe[name]);r['roughness_scale']=min(1.2,r['roughness']+.18*r.get('wear',0));r['textures']={}
            for kind,filename in recipe[name]['textures'].items():
                p=Path(filename);h=filehash(p);copykey=(h,kind)
                if copykey not in copied:
                    target=dest/'Textures'/(safe_stem(p.stem)+'_'+h[:10]+p.suffix.lower())
                    shutil.copy2(p,target);copied[copykey]=str(target.relative_to(dest)).replace('\\','/')
                r['textures'][kind]=copied[copykey]
            manifest['materials'][name]=r
        for o in descendants(root):
            if o.get('mb01_kind')=='PORT':
                manifest['ports'].append({'id':o.get('mb01_element',o.name),'matrix_world_m':[list(row) for row in o.matrix_world],
                    'data':json.loads(o.get('mb01_data','{}'))})
        manifest['export_warnings'] += [
            'Architectural shells use static complex collision. Moving door pieces carry simple convex hulls. Decorative props/glass have collision disabled.',
            'Preview cameras/lights/world/stage are not exported. Retained owned MB01 pieces are included; unowned user objects are not.',
            'External custom Blender shaders are not converted. Set GLASS_MATERIAL_PATH for your final Unreal glass.',
            'Whole-building export preserves semantic assets and shared meshes. Choose Nanite or project-specific LOD policy in Unreal; the addon does not silently enable engine settings.',
            'Typed connection ports are stored in JSON. UE socket creation and live SW01/AF01 graph binding are not implemented in this release.',
            'Unreal importer must be tested in the target project. No UE execution claim is made by this Blender export.']
        (dest/'MB01_scene.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
        pkg=Path(__file__).resolve().parent
        shutil.copy2(pkg/'unreal/MB01_Import.py',dest/'MB01_Import.py');shutil.copy2(pkg/'coordinates.py',dest/'mb01_coordinates.py')
        (dest/'START_HERE_TR.txt').write_text('UE test projesinde Python Editor Script Plugin + Editor Scripting Utilities etkin olmalı.\n'
            'Bu klasördeki MB01_Import.py dosyasını Execute Python Script ile çalıştırın.\n'
            'İlk çalıştırma DRY_RUN=True: yalnız dosyaları doğrular. Sonra DRY_RUN=False yaparak import edin.\n'
            'Yerleşim ve level kullanıcı kontrolü olmadan kaydedilmez. Ayrıntılar MB01 README içinde.\n',encoding='utf-8')
        failure.unlink()
        return dest
    except Exception:
        import traceback
        failure.write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        if win and old_scene:win.scene=old_scene
        clear_temp();bpy.data.scenes.remove(temp)

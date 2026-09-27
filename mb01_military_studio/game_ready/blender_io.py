# SPDX-License-Identifier: MIT
"""Explicit module-kit Blender export. One render asset per FBX, separate LOD files.
Does not claim automatic UE LOD import/material conversion or modify user's objects.
"""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime
import hashlib, json, shutil, uuid, traceback
import bpy, bmesh
from mathutils import Matrix
from .. import materials
from ..blender_backend import mesh_for
from ..assembly.resources import fingerprint_recipe
from .bundle import compile_module, SCHEMA, geometry_hash


def _check_context():
    if bpy.app.version<(4,5,0):raise RuntimeError('Blender 4.5+ gerekli.')
    if bpy.context.mode!='OBJECT':raise RuntimeError('Object Mode gerekli.')
    if abs(bpy.context.scene.unit_settings.scale_length-1.)>1e-8:raise RuntimeError('Unit Scale=1.0 gerekli.')


def preview(settings, level=0, override=''):
    _check_context()
    if level not in (0,1,2):raise ValueError('LOD 0,1,2 olmalı.')
    bundle=compile_module(settings)
    if bundle.report['errors']:raise ValueError(str(bundle.report['errors']))
    recipes=materials.recipes(settings.style.palette,settings.style.wear,override)
    used={m for a in bundle.levels[level] for m in a.part.material_names}
    mats=materials.create_blender_materials({m:recipes[m] for m in used})
    col=bpy.data.collections.new('MB03_KIT_'+uuid.uuid4().hex[:8]);bpy.context.scene.collection.children.link(col)
    root=bpy.data.objects.new('MB03_'+settings.module_id.split('.')[-1],None);col.objects.link(root)
    root['mb03_gamekit_root']=True;root['mb03_settings']=json.dumps(asdict(settings));root['mb03_lod']=level
    root.location=bpy.context.scene.cursor.location;root.empty_display_size=.4
    for asset in bundle.levels[level]:
        me=mesh_for(asset.part,mats,settings)
        ob=bpy.data.objects.new(asset.part.name+'_LOD'+str(level),me);col.objects.link(ob);ob.parent=root;ob.location=asset.part.pivot
        ob['mb03_asset_key']=asset.key;ob['mb03_pivot_m']=list(asset.part.pivot)
        for spec in asset.sockets:
            socket=bpy.data.objects.new('SOCKET_'+asset.part.name+'_'+spec['name'],None);col.objects.link(socket);socket.parent=root
            socket.location=spec['location_m'];socket.empty_display_type='ARROWS';socket.empty_display_size=.20
            from math import atan2
            socket.rotation_euler.z=atan2(spec['normal'][1],spec['normal'][0])
            socket['mb03_interface']=json.dumps(spec)
        if asset.door:ob['mb03_door_motion']=json.dumps(asset.door)
    for ob in list(bpy.context.selected_objects):ob.select_set(False)
    root.select_set(True);bpy.context.view_layer.objects.active=root
    return root


def export_kit(settings, directory, override=''):
    _check_context();bundle=compile_module(settings)
    if bundle.report['errors']:raise ValueError('Game-kit QA: '+str(bundle.report['errors']))
    directory=Path(directory).expanduser().resolve()
    dest=directory/('MB03_'+settings.module_id.split('.')[-1]+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6])
    (dest/'Meshes').mkdir(parents=True);(dest/'Textures').mkdir()
    pending=dest/'EXPORT_INCOMPLETE.txt';pending.write_text('Export not yet complete.',encoding='utf-8')
    recipes=materials.recipes(settings.style.palette,settings.style.wear,override)
    used={m for a in bundle.levels[0] for m in a.part.material_names}
    recipes={k:fingerprint_recipe(recipes[k]) for k in used}
    mats=materials.create_blender_materials(recipes)
    manifest=dict(schema=SCHEMA,blender_version=bpy.app.version_string,ue_tested=False,
         source_units='m',axes='+X inward,+Y left,+Z up',settings=asdict(settings),
         report=bundle.report,assets={},materials={},auto_ue_lod_binding=False,
         lighting='DYNAMIC_ONLY',native_geometry_qa='SOURCE_CHECKED; FBX roundtrip required')
    scene=bpy.context.scene;window=bpy.context.window
    old_scene=window.scene if window else None
    temp=bpy.data.scenes.new('MB03_EXPORT_TEMP');temp.unit_settings.system='METRIC';temp.unit_settings.scale_length=1.
    def clean():
        for ob in list(temp.objects):
            data=ob.data;bpy.data.objects.remove(ob,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and data.users==0:bpy.data.meshes.remove(data)
    try:
        for level,assets in bundle.levels.items():
            for a in assets:
                # Deliberately no automatic global bevel: LOD0 already contains designed geometry.
                # Preview modifiers on other scenes are never touched.
                name=a.part.name;me=mesh_for(a.part,mats,settings)
                bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
                ob=bpy.data.objects.new(name,me);temp.collection.objects.link(ob)
                objects=[ob]
                if level==0:
                    for i,h in enumerate(a.collisions):
                        hm=bpy.data.meshes.new('MB03_Hull')
                        hm.from_pydata([tuple(v[j]-a.part.pivot[j] for j in range(3)) for v in h.vertices],[],h.faces);hm.update()
                        ho=bpy.data.objects.new(f'UCX_{name}_{i:02d}',hm);temp.collection.objects.link(ho);objects.append(ho)
                    for i,spec in enumerate(a.sockets):
                        so=bpy.data.objects.new('SOCKET_'+name+'_'+spec['name'],None);temp.collection.objects.link(so)
                        so.location=tuple(spec['location_m'][j]-a.part.pivot[j] for j in range(3))
                        # Socket local +X faces its outward interface normal.
                        from math import atan2
                        so.rotation_euler.z=atan2(spec['normal'][1],spec['normal'][0]);objects.append(so)
                if window:window.scene=temp
                filename=name+'_LOD'+str(level)+'.fbx'
                with bpy.context.temp_override(scene=temp,view_layer=temp.view_layers[0]):
                    for o in objects:o.select_set(True)
                    temp.view_layers[0].objects.active=ob
                    result=bpy.ops.export_scene.fbx(filepath=str(dest/'Meshes'/filename),use_selection=True,
                        object_types={'MESH','EMPTY'},global_scale=1.,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
                        axis_forward='-Y',axis_up='Z',use_space_transform=True,bake_space_transform=False,
                        use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,
                        add_leaf_bones=False,bake_anim=False,path_mode='AUTO')
                    if 'FINISHED' not in result:raise RuntimeError('FBX exporter did not finish: '+filename)
                record=manifest['assets'].setdefault(a.key,dict(name=name,pivot_m=a.part.pivot,materials=a.part.material_names,
                    sockets=a.sockets,door=a.door,lods=[]))
                record['lods'].append(dict(index=level,file='Meshes/'+filename,
                    sha256=hashlib.sha256((dest/'Meshes'/filename).read_bytes()).hexdigest(),
                    triangles=len(me.polygons),collision_hulls=len(a.collisions) if level==0 else 0))
                clean()
        copied={}
        for key,recipe in recipes.items():
            r=dict(recipe);r['textures']={}
            for kind,src in recipe['textures'].items():
                p=Path(src);sha=hashlib.sha256(p.read_bytes()).hexdigest()
                if sha!=recipe['source_hashes'].get(kind):raise RuntimeError('PBR source changed during export.')
                if sha not in copied:
                    rel='Textures/'+p.stem+'_'+sha[:12]+p.suffix;shutil.copy2(p,dest/rel);copied[sha]=rel
                r['textures'][kind]=copied[sha]
            manifest['materials'][key]=r
        (dest/'GAME_KIT.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        (dest/'IMPORT_README_TR.txt').write_text(
          'Blender kaynak birimi metre. Unreal hedefi cm; ilk importta gerçek ölçüyü kontrol edin.\n'
          'Her asset için _LOD0.fbx ana modeldir; Custom Collision importunu kontrol edin.\n'
          'LOD1/LOD2 ayrı FBX dosyalarıdır: Static Mesh Editor > LOD Import ile aynı assete ekleyin.\n'
          'UE otomatik LOD bağlayıcısı bu sürümde yok. Aynı pivotu ve yönü kontrol edin.\n'
          'GAME_KIT.json materyal rolleri, normal yönü, UV0_Tile, pivot ve kapı verisini taşır.\n'
          'Textures içindeki PBR haritalarıyla UE materyallerini kurun; Blender shader FBX ile aynen taşınmaz.\n'
          'UV1 lightmap yok; varsayılan dinamik aydınlatma. Baked ışık için ayrı unique UV gerekir.\n'
          'Bu küçük modül kiti; bütün hangarın LOD/collision dönüşümü değildir. UE5.8 test edilmedi.\n',encoding='utf-8')
        pending.unlink();return dest
    except Exception:
        pending.write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        if window and old_scene:window.scene=old_scene
        clean();bpy.data.scenes.remove(temp)

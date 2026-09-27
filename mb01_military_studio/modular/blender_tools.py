# SPDX-License-Identifier: MIT
"""Bounded modular Blender builder. New revision only: never regenerates legacy buildings."""
import json, math, time, uuid, platform
from types import SimpleNamespace
import bpy
from mathutils import Vector, Matrix
from .. import materials
from ..blender_backend import mesh_for, descendants, remove_object, remove_collection_tree
from . import VERSION
from .contracts import ModuleInput, to_document, placements, numeric
from . import geometry


def root_for(obj):
    while obj:
        if obj.get('mb01_modular_root'):
            return obj
        obj=obj.parent
    return None


def build_facade(facade, origin=(0.,0.,0.), yaw_degrees=0., texture_root=''):
    facade.checked()
    if bpy.app.version < (4,5,0):
        raise RuntimeError('Modüler laboratuvar Blender 4.5+ hedefler.')
    if bpy.context.mode != 'OBJECT':
        raise RuntimeError('Object Mode durumuna geçin.')
    if abs(bpy.context.scene.unit_settings.scale_length-1.) > 1e-8:
        raise RuntimeError('Unit Scale 1.0 olmalı; sahnenizin ölçeği değiştirilmedi.')
    numeric('yaw',yaw_degrees,-36000.,36000.)
    if len(origin)!=3:raise ValueError('Invalid origin.')
    for v in origin:numeric('origin',v,-1000000.,1000000.)
    started=time.perf_counter(); models={}; checks=[]
    for cell in facade.cells:
        settings=ModuleInput(cell.module_id,facade.family,cell.width,facade.height,
            facade.thickness,facade.detail,facade.door_open,facade.style)
        if settings not in models:
            model=geometry.build(settings);report=geometry.validation(model)
            if report['errors']:raise ValueError('\n'.join(report['errors']))
            models[settings]=model;checks.append(report)
    recipes=materials.recipes(facade.style.palette,facade.style.wear,texture_root)
    used={mat for model in models.values() for part in model.parts for mat in part.material_names}
    mats=materials.create_blender_materials({k:recipes[k] for k in used})
    owner=uuid.uuid4().hex;coll=None;created_meshes=[]
    previous_selected=list(bpy.context.selected_objects)
    previous_active=bpy.context.view_layer.objects.active
    try:
        coll=bpy.data.collections.new('MB01_MODULAR_'+facade.id+'_'+owner[:6])
        coll['mb01_owner']=owner;coll['mb01_modular']=True
        bpy.context.scene.collection.children.link(coll)
        root=bpy.data.objects.new('MB01_MODULAR_'+facade.id,None);coll.objects.link(root)
        root['mb01_project_root']=True;root['mb01_modular_root']=True
        root['mb01_owner']=owner;root['mb01_element']='ROOT';root['mb01_version']=VERSION
        root['mb01_schema']='mb01.modular_scene/0.2'
        root['mb01_modular_document']=json.dumps(to_document(facade),ensure_ascii=False)
        root['mb01_modular_style']=json.dumps({'name':facade.id,'palette':facade.style.palette,'wear':facade.style.wear})
        root['mb01_texture_root']=texture_root
        root.matrix_world=Matrix.Translation(Vector(origin))@Matrix.Rotation(math.radians(yaw_degrees),4,'Z')
        root.empty_display_size=.7
        cache={}
        for cell,place in zip(facade.cells,placements(facade)):
            settings=ModuleInput(cell.module_id,facade.family,cell.width,facade.height,
                facade.thickness,facade.detail,facade.door_open,facade.style)
            model=models[settings]
            sub=bpy.data.collections.new('MB02_'+cell.id);sub['mb01_owner']=owner;coll.children.link(sub)
            cellroot=bpy.data.objects.new(cell.id,None);sub.objects.link(cellroot);cellroot.parent=root
            cellroot.location=place['location_m'];cellroot.empty_display_size=.3
            cellroot['mb01_owner']=owner;cellroot['mb01_element']=cell.id;cellroot['mb01_module']=cell.module_id
            cellroot['mb01_cell_snapshot']=json.dumps(place)
            gkey=geometry.geometry_key(model)
            for part in model.parts:
                key=(gkey,part.name)
                if key not in cache:
                    me=mesh_for(part,mats,settings)
                    me['mb01_metadata']=json.dumps({'module_id':cell.module_id,'part':part.name,'geometry_hash':gkey})
                    cache[key]=me;created_meshes.append(me)
                obj=bpy.data.objects.new(part.name+'_'+cell.id,cache[key]);sub.objects.link(obj);obj.parent=cellroot
                obj.location, obj.rotation_euler.z=geometry.part_transform(model,part)
                obj['mb01_owner']=owner;obj['mb01_element']=cell.id+'/'+part.name
                obj['mb01_asset_key']=part.name;obj['mb01_kind']='MESH';obj['mb01_category']=part.group
                obj['mb01_collision_mode']='HULLS' if part.group=='DOOR' else ('COMPLEX' if part.group=='BODY' else 'NONE')
                obj['mb01_source_pivot']=list(part.pivot)
                door=next((d for d in model.doors if d['part']==part.name),None)
                if door:obj['mb01_door']=json.dumps(door)
                if part.bevel and facade.detail!='DRAFT':
                    bevel=obj.modifiers.new('MB02_EdgeHighlights','BEVEL');bevel.width=part.bevel
                    bevel.segments=3 if facade.detail=='HERO' else 2
                    bevel.limit_method='ANGLE';bevel.angle_limit=math.radians(35);bevel.use_clamp_overlap=True
                    if hasattr(bevel,'harden_normals'):bevel.harden_normals=True
            for port in model.ports:
                obj=bpy.data.objects.new(cell.id+'_'+port['name'],None);sub.objects.link(obj);obj.parent=cellroot
                obj.location=port['location_m'];obj.rotation_euler.z=math.atan2(port['normal'][1],port['normal'][0])
                obj.empty_display_type='ARROWS';obj.empty_display_size=.22;obj.hide_render=True
                obj['mb01_owner']=owner;obj['mb01_element']=cell.id+'/'+port['name']
                obj['mb01_kind']='PORT';obj['mb01_data']=json.dumps(port)
        bpy.context.view_layer.update()
        for ob in list(bpy.context.selected_objects):ob.select_set(False)
        root.select_set(True);bpy.context.view_layer.objects.active=root
        report={'generator':VERSION,'blender_version':bpy.app.version_string,'platform':platform.platform(),
                'blender_runtime_executed':True,'ue_runtime_executed':False,'seconds':round(time.perf_counter()-started,3),
                'cells':len(facade.cells),'unique_meshes':len(cache),'geometry_checks':checks,
                'limits':['Straight single-storey facade only; not a complete building.',
                          'New revisions are created; existing geometry is not rebuilt or migrated.',
                          'No compliance certification, automatic terrain or live port joining.']}
        root['mb01_blender_report']=json.dumps(report,ensure_ascii=False)
        return root,report
    except Exception:
        if coll:
            for obj in list(coll.all_objects):
                if obj.get('mb01_owner')==owner:remove_object(obj)
            remove_collection_tree(coll)
        for mesh in created_meshes:
            try:
                if mesh.users==0 and mesh.name in bpy.data.meshes:bpy.data.meshes.remove(mesh)
            except ReferenceError:pass
        for obj in previous_selected:
            if obj.name in bpy.data.objects:obj.select_set(True)
        if previous_active and previous_active.name in bpy.data.objects:bpy.context.view_layer.objects.active=previous_active
        raise


def set_door_pose(root,amount):
    numeric('door_open',amount,0.,1.)
    if not root or not root.get('mb01_modular_root'):raise ValueError('Modüler kök seçin.')
    for obj in descendants(root):
        if obj.get('mb01_door') and not obj.get('mb01_keep'):
            d=json.loads(obj['mb01_door']);obj.rotation_euler.z=d['angle']*amount
    d=json.loads(root['mb01_modular_document']);d['facade']['door_open']=amount
    root['mb01_modular_document']=json.dumps(d,ensure_ascii=False)
    return root

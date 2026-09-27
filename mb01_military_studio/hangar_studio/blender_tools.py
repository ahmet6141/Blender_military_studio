# SPDX-License-Identifier: MIT
"""Blender authoring adapter. New revisions only. Never mutates the legacy generator.
No network or runtime pip; bpy writes stay in the main thread.
"""
import bpy
from mathutils import Vector, Matrix
from dataclasses import asdict
from math import radians
import json, uuid, time, platform, hashlib
from .. import core
from ..blender_backend import descendants, mesh_for, remove_object, remove_collection_tree
from . import VERSION, geometry, style
from .contracts import to_document, from_document, number, gate_clear_width


def root_for(obj):
    while obj:
        if obj.get('mb01_hangar_root'):return obj
        obj=obj.parent
    return None


def _shape_key(part):
    # Local geometry, UVs and material semantics define mesh sharing; placement does not.
    local=[[round(v[j]-part.pivot[j],8) for j in range(3)] for v in part.vertices]
    data=[local,part.faces,part.uvs,part.material_names,part.material_ids,part.smooth,part.bevel]
    return hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()


class BuildJob:
    def __init__(self,config,origin=(0.,0.,0.),yaw=0.,override=''):
        config.checked()
        if bpy.app.version<(4,5,0):raise RuntimeError('Hangar Studio için Blender 4.5+ gerekli.')
        if bpy.context.mode!='OBJECT':raise RuntimeError('Object Mode durumuna geçin.')
        if abs(bpy.context.scene.unit_settings.scale_length-1.)>1e-8:raise RuntimeError('Unit Scale = 1.0 gerekli; sahneniz otomatik ölçeklenmedi.')
        if len(origin)!=3:raise ValueError('Konum üç bileşenli olmalı.')
        for v in origin:number('origin',v,-1e6,1e6)
        number('yaw',yaw,-36000.,36000.)
        self.cfg=config;self.scene=bpy.context.scene;self.override=override;self.owner=uuid.uuid4().hex
        self.origin=origin;self.yaw=yaw;self.root=None;self.collection=None;self.meshes=[];self.finished=False;self.report=None
        self.selection=list(bpy.context.selected_objects);self.active=bpy.context.view_layer.objects.active

    def steps(self):
        started=time.perf_counter();c=self.cfg
        model=geometry.build(c);report=geometry.validation(model)
        if report['errors']:raise ValueError('\n'.join(report['errors']))
        yield .03,'Geometri ve bağlantı kontrolleri'
        recipe=style.recipes(c,self.override)
        used={name for p in model.parts for name in p.material_names}|{l['material'] for l in model.labels}
        if used-set(recipe):raise ValueError('Eksik materyal rolleri: '+str(used-set(recipe)))
        mats=style.create_blender_materials({k:recipe[k] for k in used})
        self.collection=bpy.data.collections.new('MB01_HANGAR_'+c.name+'_'+self.owner[:6])
        self.collection['mb01_owner']=self.owner;self.collection.hide_render=True;self.collection.hide_viewport=True
        self.scene.collection.children.link(self.collection)
        groups={}
        def group(name):
            if name not in groups:
                col=bpy.data.collections.new('HG_'+name);col['mb01_owner']=self.owner;self.collection.children.link(col);groups[name]=col
            return groups[name]
        root=bpy.data.objects.new('HG_'+c.name,None);self.collection.objects.link(root);self.root=root
        root['mb01_project_root']=True;root['mb01_hangar_root']=True;root['mb01_owner']=self.owner
        root['mb01_element']='ROOT';root['mb01_version']=VERSION;root['mb01_schema']='mb01.hangar_scene/0.3-alpha.1'
        root['mb01_hangar_document']=json.dumps(to_document(c),ensure_ascii=False)
        root['mb01_config']=json.dumps(asdict(c.legacy_settings()),ensure_ascii=False)
        root['mb01_texture_root']=self.override;root['mb01_hangar_metadata']=json.dumps(model.hangar_meta,ensure_ascii=False)
        root.matrix_world=Matrix.Translation(Vector(self.origin))@Matrix.Rotation(radians(self.yaw),4,'Z')
        root.empty_display_size=1.2
        cache={}
        for i,part in enumerate(model.parts):
            if bpy.context.scene!=self.scene:raise RuntimeError('Üretim sırasında sahne değişti; işlem durduruldu.')
            signature=_shape_key(part)
            if signature not in cache:
                me=mesh_for(part,mats,model.cfg);self.meshes.append(me);cache[signature]=me
                me['mb01_metadata']=json.dumps(dict(producer='HangarStudio',local_geometry_hash=signature))
            ob=bpy.data.objects.new(part.name+'_'+self.owner[:5],cache[signature]);group(part.group).objects.link(ob);ob.parent=root
            ob.location,ob.rotation_euler.z=geometry.pose(model,part)
            ob['mb01_owner']=self.owner;ob['mb01_element']=part.name;ob['mb01_category']=part.group;ob['mb01_kind']='MESH'
            ob['mb01_asset_key']='SM_HG_'+part.group+'_'+signature[:16];ob['mb01_source_pivot']=list(part.pivot)
            ob['mb01_collision_mode']='HULLS' if part.group=='DOOR' else ('COMPLEX' if part.group in ('BODY','STRUCTURE','ROOF','GROUND') else 'NONE')
            door=next((d for d in model.doors if d['part']==part.name),None)
            if door:ob['mb01_door']=json.dumps(door)
            if part.bevel>0 and c.detail!='DRAFT':
                bevel=ob.modifiers.new('HG_EdgeFinish','BEVEL');bevel.width=part.bevel
                bevel.segments=3 if c.detail=='HERO' else 2;bevel.limit_method='ANGLE';bevel.angle_limit=radians(35)
                bevel.use_clamp_overlap=True
                if hasattr(bevel,'harden_normals'):bevel.harden_normals=True
            yield .08+.72*(i+1)/len(model.parts),part.name
        for l in model.labels:
            data=bpy.data.curves.new('HG_'+l['name'],'FONT');data.body=l['body'];data.size=l['size']
            data.align_x='CENTER';data.align_y='CENTER';data.extrude=.0008;data.resolution_u=5;data.materials.append(mats[l['material']])
            ob=bpy.data.objects.new('HG_'+l['name'],data);group('SIGNAGE').objects.link(ob);ob.parent=root
            ob.location=l['location'];ob.rotation_euler=l['rotation']
            for k,v in dict(mb01_owner=self.owner,mb01_element='LABEL_'+l['name'],mb01_kind='TEXT',mb01_category='SIGNAGE',
                mb01_asset_key='LABEL_'+l['name'],mb01_collision_mode='NONE').items():ob[k]=v
        for p in model.ports:
            ob=bpy.data.objects.new('HG_'+p['name'],None);group('PORTS').objects.link(ob);ob.parent=root
            ob.location=p['location'];ob.rotation_euler.z=p['yaw'];ob.empty_display_type='ARROWS';ob.empty_display_size=.55;ob.hide_render=True
            ob['mb01_owner']=self.owner;ob['mb01_element']='PORT_'+p['name'];ob['mb01_kind']='PORT';ob['mb01_data']=json.dumps(p)
            if p['role']=='PEDESTRIAN':
                ob['pk01_width']=p['width'];ob['pk01_height']=p['height'];ob['pk01_role']='OUT'
        self.collection.hide_render=False;self.collection.hide_viewport=False
        bpy.context.view_layer.update()
        for ob in list(bpy.context.selected_objects):ob.select_set(False)
        root.select_set(True);bpy.context.view_layer.objects.active=root
        self.report=dict(generator=VERSION,blender_runtime_executed=True,blender_version=bpy.app.version_string,
            platform=platform.platform(),unreal_runtime_executed=False,seconds=round(time.perf_counter()-started,3),
            unique_meshes=len(cache),geometry=report,revision_policy='new root; no previous scene deletion')
        root['mb01_blender_report']=json.dumps(self.report,ensure_ascii=False)
        self.finished=True;yield 1.,'Hangar oluşturuldu'

    def abort(self):
        if self.finished:return
        if self.collection:
            for ob in list(self.collection.all_objects):
                if ob.get('mb01_owner')==self.owner:remove_object(ob)
            remove_collection_tree(self.collection)
        for me in self.meshes:
            try:
                if me.users==0 and me.name in bpy.data.meshes:bpy.data.meshes.remove(me)
            except ReferenceError:pass
        for ob in self.selection:
            if ob.name in bpy.data.objects:ob.select_set(True)
        if self.active and self.active.name in bpy.data.objects:bpy.context.view_layer.objects.active=self.active


def config_for(root):
    if root is None or not root.get('mb01_hangar_root'):raise ValueError('Hangar Studio kökü seçin.')
    return from_document(json.loads(root['mb01_hangar_document']))


def set_pose(root,gate,personnel):
    number('gate_open',gate,0.,1.);number('personnel_open',personnel,0.,1.)
    config_for(root)
    for ob in descendants(root):
        if ob.get('mb01_door') and not ob.get('mb01_keep'):
            d=json.loads(ob['mb01_door']);t=gate if d.get('channel')=='GATE' else personnel
            ob.location=[a*(1-t)+b*t for a,b in zip(d['closed'],d['opened'])]
            ob.rotation_euler.z=d.get('angle',0.)*t
            d['open_fraction']=t;ob['mb01_door']=json.dumps(d)
    doc=json.loads(root['mb01_hangar_document']);doc['config']['gate_open']=gate;doc['config']['personnel_open']=personnel
    root['mb01_hangar_document']=json.dumps(doc,ensure_ascii=False)
    legacy=json.loads(root['mb01_config']);legacy['door_open']=gate;root['mb01_config']=json.dumps(legacy)
    metadata=json.loads(root['mb01_hangar_metadata']);metadata['gate_clear_width_at_pose_m']=gate_clear_width(config_for(root))
    root['mb01_hangar_metadata']=json.dumps(metadata,ensure_ascii=False)


def preview(root):
    """Opt-in stage. Not part of asset export; creates no duplicate apron geometry."""
    c=config_for(root);scene=bpy.context.scene
    coll=bpy.data.collections.new('HG_PREVIEW_'+root['mb01_owner'][:6]);scene.collection.children.link(coll)
    target=Vector((c.depth*.40,0,c.eave_height*.55))
    views=[('Hero',(-c.width*1.12,-c.width*1.25,c.eave_height*2.7),target,45),
           ('Front',(-c.width*1.6,0,c.eave_height*.68),(c.depth*.12,0,c.eave_height*.60),52),
           ('Interior',(-2.,-c.width*.12,3.),(c.depth*.72,0,4.0),24),
           ('Rear',(c.depth+c.width*.95,c.width*1.1,c.eave_height*2.3),(c.depth*.67,0,4.),46)]
    for name,eye,aim,lens in views:
        data=bpy.data.cameras.new('HG_CAM_'+name);data.lens=lens;data.clip_end=2000
        ob=bpy.data.objects.new(data.name,data);coll.objects.link(ob)
        ob.location=root.matrix_world@Vector(eye);ob.rotation_euler=(root.matrix_world@Vector(aim)-ob.location).to_track_quat('-Z','Y').to_euler()
        if name=='Hero':scene.camera=ob
    sun=bpy.data.lights.new('HG_Sun','SUN');sun.energy=2.0;sun.angle=radians(3)
    ob=bpy.data.objects.new(sun.name,sun);coll.objects.link(ob);ob.rotation_euler=(radians(28),radians(-25),radians(-40))
    world=bpy.data.worlds.new('HG_NeutralWorld');world.use_nodes=True
    bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.42,.49,.56,1.);bg.inputs['Strength'].default_value=.5
    scene.world=world
    meta=json.loads(root['mb01_hangar_metadata'])
    for i,spec in enumerate(meta['light_fixtures_design']):
        data=bpy.data.lights.new('HG_Practical_'+str(i),'AREA');data.energy=spec['watts_artist'];data.shape='RECTANGLE';data.size=.17;data.size_y=1.6;data.color=(1.,.89,.73)
        ob=bpy.data.objects.new(data.name,data);coll.objects.link(ob);ob.parent=root;ob.location=core.canonical(spec['position'])
        ob.rotation_euler.z=-radians(90)
    scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0.
    return scene.camera

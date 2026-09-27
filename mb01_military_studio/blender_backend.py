# SPDX-License-Identifier: MIT
"""Blender adapter. No global scene clearing, no network, no background bpy access."""
import bpy
from mathutils import Vector, Matrix
import json,math,time,uuid,platform
from . import core,materials


def descendants(root):
    out=[root]
    for ch in root.children:out.extend(descendants(ch))
    return out


def remove_object(obj):
    data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
    if data is not None and data.users==0:
        if isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
        elif isinstance(data,bpy.types.Curve):bpy.data.curves.remove(data)


def root_for(obj):
    while obj:
        if obj.get('mb01_modular_root') or obj.get('mb01_hangar_root'):return None
        if obj.get('mb01_project_root'):return obj
        obj=obj.parent
    return None


def remove_collection_tree(c):
    for ch in list(c.children):remove_collection_tree(ch)
    if not c.objects and not c.children:bpy.data.collections.remove(c)


def mesh_for(p,mats,settings):
    me=bpy.data.meshes.new(p.name+'_Mesh')
    vertices=[tuple(v[j]-p.pivot[j] for j in range(3)) for v in p.vertices]
    me.from_pydata(vertices,[],p.faces);me.update(calc_edges=True)
    for k in p.material_names:me.materials.append(mats[k])
    me.polygons.foreach_set('material_index',p.material_ids)
    me.polygons.foreach_set('use_smooth',p.smooth)
    uv=me.uv_layers.new(name='UV0_Tile')
    uv.data.foreach_set('uv',[value for face in p.uvs for pair in face for value in pair])
    vc=me.color_attributes.new(name='SW01_Tint',type='FLOAT_COLOR',domain='POINT')
    # Neutral tint is a compatible reserved field. Material masks do not overwrite it.
    vc.data.foreach_set('color',[1.]*(4*len(vertices)));me.color_attributes.active_color_index=0
    if hasattr(me,'set_sharp_from_angle'):me.set_sharp_from_angle(angle=math.radians(40))
    return me


class BuildJob:
    def __init__(self,settings,old_root=None,origin=(0,0,0),yaw=0,override=''):
        if bpy.app.version<(4,5,0):raise RuntimeError('MB01 için Blender 4.5 veya üzeri gerekli; 5.x ayrıca test edilmemiştir.')
        if bpy.context.mode!='OBJECT':raise RuntimeError('Önce Object Mode durumuna geçin.')
        if abs(bpy.context.scene.unit_settings.scale_length-1.)>1e-7:raise RuntimeError('Scene > Units > Unit Scale 1.0 olmalı; mevcut sahneyi otomatik ölçeklendirmiyorum.')
        if old_root and (old_root.get('mb01_modular_root') or old_root.get('mb01_hangar_root')):
            raise ValueError('Modüler cepheyi eski tam bina üreticisiyle yeniden üretemezsiniz.')
        settings.checked();self.settings=settings;self.old=old_root;self.override=override;self.scene=bpy.context.scene
        if old_root and not old_root.get('mb01_project_root'):raise ValueError('Geçerli MB01 kökü seçilmedi.')
        self.id=old_root['mb01_owner'] if old_root else uuid.uuid4().hex
        self.transform=old_root.matrix_world.copy() if old_root else Matrix.Translation(Vector(origin))@Matrix.Rotation(math.radians(yaw),4,'Z')
        self.keep=[]
        if old_root:
            for o in descendants(old_root):
                if o==old_root:continue
                if o.get('mb01_keep') or o.get('mb01_owner')!=self.id:self.keep.extend(descendants(o))
        self.keep=list(dict.fromkeys(self.keep));self.locked={o.get('mb01_element') for o in self.keep}
        self.collection=None;self.root=None;self.finished=False;self.commit_started=False;self.report=None;self.meshes=[]

    def steps(self):
        start=time.perf_counter();model=core.build(self.settings);r=core.validation(model)
        if r['errors']:raise RuntimeError('\n'.join(r['errors']))
        yield .04,'Geometri kontrol edildi'
        recipe=materials.recipes(self.settings.palette,self.settings.wear,self.override)
        required={x for p in model.parts for x in p.material_names}|{l['material'] for l in model.labels}
        missing=required-set(recipe)
        if missing:raise ValueError('Eksik materyal tarifi: '+str(missing))
        mats=materials.create_blender_materials({k:recipe[k] for k in required})
        coll=bpy.data.collections.new('MB01_STAGING_'+self.id[:8]);self.collection=coll
        coll['mb01_owner']=self.id;coll.hide_viewport=True;coll.hide_render=True;bpy.context.scene.collection.children.link(coll)
        groups={}
        def group(key):
            if key not in groups:
                c=bpy.data.collections.new('MB01_'+key);c['mb01_owner']=self.id;coll.children.link(c);groups[key]=c
            return groups[key]
        root=bpy.data.objects.new('MB01_'+self.settings.name,None);coll.objects.link(root);self.root=root
        root.matrix_world=self.transform;root.empty_display_size=1.3
        root['mb01_project_root']=True;root['mb01_owner']=self.id;root['mb01_element']='ROOT'
        root['mb01_config']=json.dumps(core.asdict(self.settings),ensure_ascii=False);root['mb01_texture_root']=self.override
        root['mb01_schema']='mb01.scene/0.2';root['mb01_version']=core.VERSION
        root['mb01_mcp_ready']=True;root['mb01_agent_api']='mb01_military_studio.agent_api'
        root['mb01_asset_profile']='CGI_PBR_GAME_READY_CANDIDATE'
        for i,p in enumerate(model.parts):
            if bpy.context.scene!=self.scene:raise RuntimeError('Üretim sırasında sahne değişti. İşlem iptal edildi; eski yapı korundu.')
            if p.name not in self.locked:
                me=mesh_for(p,mats,self.settings);self.meshes.append(me)
                ob=bpy.data.objects.new(p.name+'_'+self.id[:6],me);group(p.group).objects.link(ob);ob.parent=root
                ob.location,ob.rotation_euler.z=core.door_transform(model,p)
                ob['mb01_owner']=self.id;ob['mb01_element']=p.name;ob['mb01_category']=p.group
                ob['mb01_asset_key']=p.name;ob['mb01_kind']='MESH';ob['mb01_source_pivot']=list(p.pivot)
                ob['mb01_collision_mode']='HULLS' if p.group=='DOOR' else ('COMPLEX' if p.group in ('GROUND','BODY','STRUCTURE','ROOF') else 'NONE')
                if p.bevel>0 and self.settings.detail!='DRAFT':
                    bevel=ob.modifiers.new('MB01_EdgeHighlights','BEVEL');bevel.width=p.bevel
                    bevel.segments=3 if self.settings.detail=='HERO' else 2
                    bevel.limit_method='ANGLE';bevel.angle_limit=math.radians(35);bevel.use_clamp_overlap=True
                    if hasattr(bevel,'harden_normals'):bevel.harden_normals=True
                door=next((d for d in model.doors if d['part']==p.name),None)
                if door:ob['mb01_door']=json.dumps(door)
            yield .08+.69*(i+1)/len(model.parts),'Parça: '+p.name
        for l in model.labels:
            key='LABEL_'+l['name']
            if key in self.locked:continue
            data=bpy.data.curves.new('MB01_'+key,'FONT');data.body=l['body'];data.size=l['size'];data.align_x='CENTER';data.align_y='CENTER'
            data.extrude=.0008;data.resolution_u=5;data.materials.append(mats[l['material']])
            ob=bpy.data.objects.new('MB01_'+key,data);group('SIGNAGE').objects.link(ob);ob.parent=root
            ob.location=l['location'];ob.rotation_euler=l['rotation']
            ob['mb01_owner']=self.id;ob['mb01_element']=key;ob['mb01_kind']='TEXT';ob['mb01_category']='SIGNAGE'
            ob['mb01_asset_key']=key;ob['mb01_collision_mode']='NONE'
        for p in model.ports:
            key='PORT_'+p['name']
            if key in self.locked:continue
            ob=bpy.data.objects.new('MB01_'+p['name'],None);group('PORTS').objects.link(ob);ob.parent=root
            ob.location=p['location'];ob.rotation_euler.z=p['yaw'];ob.empty_display_type='ARROWS';ob.empty_display_size=.6
            ob['mb01_owner']=self.id;ob['mb01_element']=key;ob['mb01_kind']='PORT';ob['mb01_data']=json.dumps(p)
            if p['role']=='PEDESTRIAN':
                ob['pk01_width']=p['width'];ob['pk01_height']=p['height'];ob['pk01_role']='OUT'
                ob['mb01_surface_level_m']=p['height']
        yield .90,'Kimlik, portlar ve hareketli parçalar hazır'
        self.commit(group)
        self.report=dict(generator=core.VERSION,blender_version=bpy.app.version_string,platform=platform.platform(),
            blender_runtime_executed=True,ue_runtime_executed=False,seconds=round(time.perf_counter()-start,3),
            geometry=r,retained_objects=len(self.keep))
        root['mb01_blender_report']=json.dumps(self.report,ensure_ascii=False)
        self.finished=True;yield 1.,'MB01 oluşturuldu'

    def commit(self,group):
        # Once transfer starts, preserve both old and staging data on failure.
        # Never let abort delete retained/user objects after reparenting.
        self.commit_started=True
        bpy.context.view_layer.update()
        if self.old:
            # Move retained data first, keeping complete world transforms and material overrides.
            retained=set(self.keep)
            for ob in self.keep:
                world=ob.matrix_world.copy()
                if ob.parent not in retained:ob.parent=self.root
                ob.matrix_world=world
                dst=group('MANUAL_LOCKED')
                if ob.name not in dst.objects:dst.objects.link(ob)
                for c in list(ob.users_collection):
                    if c!=dst and c.get('mb01_owner')==self.id:c.objects.unlink(ob)
            old_nodes=[ob for ob in descendants(self.old) if ob not in self.keep]
            oldcolls=list(self.old.users_collection)
            for ob in reversed(old_nodes):
                if ob.get('mb01_owner')==self.id:remove_object(ob)
            for c in oldcolls:
                if c!=self.collection and c.get('mb01_owner')==self.id:remove_collection_tree(c)
        self.collection.hide_viewport=False;self.collection.hide_render=False
        self.collection.name='MB01 | '+self.settings.name
        bpy.context.view_layer.update()
        for ob in list(bpy.context.selected_objects):ob.select_set(False)
        self.root.select_set(True);bpy.context.view_layer.objects.active=self.root

    def abort(self):
        if self.finished or self.commit_started:return
        if self.collection:
            for ob in list(self.collection.all_objects):remove_object(ob)
            remove_collection_tree(self.collection)
        for me in self.meshes:
            try:
                if me.users==0 and me.name in bpy.data.meshes:bpy.data.meshes.remove(me)
            except ReferenceError:pass


def build_sync(settings,old_root=None,origin=(0,0,0),yaw=0,override=''):
    job=BuildJob(settings,old_root,origin,yaw,override)
    try:
        for _ in job.steps():pass
    except Exception:job.abort();raise
    return job.root,job.report


def update_doors(root,amount):
    amount=max(0.,min(1.,float(amount)))
    for ob in descendants(root):
        if ob.get('mb01_door') and not ob.get('mb01_keep'):
            d=json.loads(ob['mb01_door']);ob.location=[d['closed'][j]*(1-amount)+d['opened'][j]*amount for j in range(3)]
            ob.rotation_euler.z=d.get('angle',0)*amount
    cfg=json.loads(root['mb01_config']);cfg['door_open']=amount;root['mb01_config']=json.dumps(cfg)


def preview_scene(root):
    """Explicit camera/light setup; generation itself does not change the active world."""
    s=core.Settings(**json.loads(root['mb01_config']));scene=bpy.context.scene
    collection=bpy.data.collections.new('MB01_Preview_'+root['mb01_owner'][:6]);scene.collection.children.link(collection)
    def point(v):return root.matrix_world@Vector(v)
    target=(s.depth*.42,0,max(2.,s.floor_height*s.floors*.42));extent=max(s.width,s.depth)
    for name,eye,lens in [('Hero',(-extent*1.0,-extent*1.05,extent*.68),48),('Front',(-extent*1.5,0,5),48),('Rear',(s.depth+extent*.8,extent*.9,extent*.6),45)]:
        data=bpy.data.cameras.new('MB01_CAM_'+name);data.lens=lens;data.clip_end=2000
        ob=bpy.data.objects.new(data.name,data);collection.objects.link(ob);ob.location=point(eye)
        ob.rotation_euler=(point(target)-ob.location).to_track_quat('-Z','Y').to_euler()
        if name=='Hero':scene.camera=ob
    data=bpy.data.lights.new('MB01_Sun','SUN');data.energy=2.5;data.angle=math.radians(2.0)
    sun=bpy.data.objects.new(data.name,data);collection.objects.link(sun);sun.rotation_euler=(math.radians(25),math.radians(-30),math.radians(-35))
    world=bpy.data.worlds.new('MB01_NeutralWorld');world.use_nodes=True
    nodes=world.node_tree.nodes;bg=nodes.get('Background');bg.inputs['Color'].default_value=(.34,.40,.47,1);bg.inputs['Strength'].default_value=.32
    sky=nodes.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=math.radians(24);sky.sun_rotation=math.radians(135);sky.altitude=.25;links=world.node_tree.links;links.new(sky.outputs['Color'],bg.inputs['Color'])
    scene.world=world;scene.render.engine='CYCLES';scene.cycles.samples=192 if s.detail=='HERO' else 96;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    try:scene.view_settings.look='AgX - Medium High Contrast'
    except (TypeError,ValueError):pass
    scene.view_settings.exposure=-.15
    # No ground plane is inserted: existing AF01/PK01 terrain is not covered.
    return scene.camera

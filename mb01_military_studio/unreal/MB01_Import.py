"""MB01 UE5.8-targeted EDITOR bridge. Not a runtime game plugin.
Run the exported copy beside MB01_scene.json from Unreal's Execute Python Script.
Native UE execution was NOT available in the development environment.
"""
from pathlib import Path
import hashlib,re
import json,math,traceback,importlib.util,sys
import unreal

EXPORT_ROOT_OVERRIDE = r''
CONTENT_ROOT = '/Game/MB01_Architecture01'
DRY_RUN = True  # First execution validates files only. Set False deliberately to import.

REIMPORT_OWN_ASSETS = False
PLACE_SCENE = True
REPLACE_SAME_SCENE = False
GLASS_MATERIAL_PATH = ''

ROOT=Path(EXPORT_ROOT_OVERRIDE).expanduser().resolve() if EXPORT_ROOT_OVERRIDE else Path(__file__).resolve().parent
EAL=unreal.EditorAssetLibrary;MEL=unreal.MaterialEditingLibrary;TOOLS=unreal.AssetToolsHelpers.get_asset_tools()
OWNER='MB01_MilitaryBuildingStudio_1';WARNINGS=[]

def log(x):unreal.log('[MB01] '+str(x))
def warn(x):WARNINGS.append(str(x));unreal.log_warning('[MB01] '+str(x))
def prop(o,k,v):
    try:o.set_editor_property(k,v)
    except Exception as e:raise RuntimeError(f'Unsupported editor property {k} on {o.get_class().get_name()}: {e}') from e

def owned(o):return EAL.get_metadata_tag(o,'MB01_Owner')==OWNER

def save(o):
    EAL.set_metadata_tag(o,'MB01_Owner',OWNER);EAL.save_loaded_asset(o,only_if_is_dirty=False)

def in_folder(folder,cls):
    if not EAL.does_directory_exist(folder):return []
    return [o for p in EAL.list_assets(folder,recursive=True,include_folder=False) if isinstance(o:=EAL.load_asset(p),cls)]

def import_one(source,folder,name,cls,options=None):
    if not source.is_file():raise FileNotFoundError(str(source))
    prev=in_folder(folder,cls)
    if prev:
        if len(prev)!=1 or not owned(prev[0]):raise RuntimeError('Refusing to replace an unowned/ambiguous asset in '+folder)
        if not REIMPORT_OWN_ASSETS:
            old=EAL.get_metadata_tag(prev[0],'MB01_SourceHash')
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            if old!=digest:raise RuntimeError('Asset content changed. Use a new CONTENT_ROOT or explicitly enable REIMPORT_OWN_ASSETS.')
            return prev[0]
    task=unreal.AssetImportTask()
    for k,v in dict(filename=str(source),destination_path=folder,destination_name=name,automated=True,replace_existing=REIMPORT_OWN_ASSETS,save=True).items():prop(task,k,v)
    if options:prop(task,'options',options)
    try:task.set_editor_property('async_',False)
    except Exception:pass
    EAL.make_directory(folder);TOOLS.import_asset_tasks([task])
    try:result=[o for o in task.get_objects() if isinstance(o,cls)]
    except Exception:result=[]
    if not result:result=in_folder(folder,cls)
    if len(result)!=1:raise RuntimeError(f'{source.name}: expected 1 {cls.__name__}, got {len(result)}. Inspect Interchange / Output Log.')
    obj=result[0];EAL.set_metadata_tag(obj,'MB01_Source',str(source));EAL.set_metadata_tag(obj,'MB01_SourceHash',hashlib.sha256(source.read_bytes()).hexdigest());save(obj);return obj

def get_asset(path,cls,factory):
    if EAL.does_asset_exist(path):
        o=EAL.load_asset(path)
        if not isinstance(o,cls) or not owned(o):raise RuntimeError('Unowned asset exists: '+path)
        return o,False
    folder,name=path.rsplit('/',1);EAL.make_directory(folder);o=TOOLS.create_asset(name,folder,cls,factory)
    if o is None:raise RuntimeError('Cannot create '+path)
    save(o);return o,True


def import_texture(rel,kind):
    name='T_'+Path(rel).stem;folder=f'{CONTENT_ROOT}/Textures/{name}'
    tex=import_one(ROOT/rel,folder,name,unreal.Texture2D)
    prop(tex,'srgb',kind=='BaseColor')
    compression={'BaseColor':unreal.TextureCompressionSettings.TC_DEFAULT,'ORM':unreal.TextureCompressionSettings.TC_MASKS,'NormalGL':unreal.TextureCompressionSettings.TC_NORMALMAP,'NormalDX':unreal.TextureCompressionSettings.TC_NORMALMAP}[kind]
    prop(tex,'compression_settings',compression)
    if kind.startswith('Normal'):prop(tex,'flip_green_channel',kind=='NormalGL')
    save(tex);return tex

def make_material(d):
    key=d.get('key',d['name']);override=GLASS_MATERIAL_PATH if d.get('glass') else ''
    if override:
        mat=EAL.load_asset(override)
        if not isinstance(mat,unreal.MaterialInterface):raise ValueError('Material override not found: '+override)
        return mat
    name=d['name'];path=f'{CONTENT_ROOT}/Materials/{name}_Master'
    mat,new=get_asset(path,unreal.Material,unreal.MaterialFactoryNew())
    recipe_hash=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
    ready=EAL.get_metadata_tag(mat,'MB01_Ready')=='1'
    changed=EAL.get_metadata_tag(mat,'MB01_RecipeHash')!=recipe_hash
    if ready and changed and not REIMPORT_OWN_ASSETS:
        raise RuntimeError('Material recipe changed: '+name+'. Choose a new CONTENT_ROOT or explicitly set REIMPORT_OWN_ASSETS=True.')
    if new or not ready or changed:
        MEL.delete_all_material_expressions(mat)
        def node(cls,x,y,**kw):
            n=MEL.create_material_expression(mat,cls,x,y)
            if n is None:raise RuntimeError('Cannot create material node '+cls.__name__)
            for k,v in kw.items():prop(n,k,v)
            return n
        def conn(a,ap,b,bp):
            if not MEL.connect_material_expressions(a,ap,b,bp):raise RuntimeError('Material pin connection failed: '+str(bp))
        def output(a,p,channel):
            if not MEL.connect_material_property(a,p,channel):raise RuntimeError('Material output failed: '+str(channel))
        def scalar(n,v,x,y):return node(unreal.MaterialExpressionScalarParameter,x,y,parameter_name=n,default_value=float(v))
        color=d.get('color',(1,1,1));tint=node(unreal.MaterialExpressionVectorParameter,-600,-300,parameter_name='Tint',default_value=unreal.LinearColor(*color,1))
        vc=node(unreal.MaterialExpressionVertexColor,-600,-500)
        mul=node(unreal.MaterialExpressionMultiply,-280,-250);conn(tint,'RGB',mul,'A');conn(vc,'RGB',mul,'B');base=mul
        tex=d.get('textures',{})
        uv=node(unreal.MaterialExpressionTextureCoordinate,-1300,200,coordinate_index=0,
                u_tiling=1./d.get('tile_size_m',1.),v_tiling=1./d.get('tile_size_m',1.))
        dry_rough=None

        for kind in ('BaseColor','ORM','NormalDX' if 'NormalDX' in tex else 'NormalGL'):
            if kind not in tex:continue
            t=import_texture(tex[kind],kind)
            sampler=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if kind.startswith('Normal') else (unreal.MaterialSamplerType.SAMPLERTYPE_MASKS if kind=='ORM' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            n=node(unreal.MaterialExpressionTextureSampleParameter2D,-900,{'BaseColor':0,'ORM':400,'NormalDX':800,'NormalGL':800}[kind],parameter_name=kind,texture=t,sampler_type=sampler)
            conn(uv,'',n,'UVs')
            if kind=='BaseColor':
                m=node(unreal.MaterialExpressionMultiply,0,-50);conn(base,'',m,'A');conn(n,'RGB',m,'B');base=m
            elif kind=='ORM':
                rough=scalar('RoughnessScale',d.get('roughness_scale',1.),-580,620);mult=node(unreal.MaterialExpressionMultiply,-160,440);conn(n,'G',mult,'A');conn(rough,'',mult,'B')
                dry_rough=mult;output(n,'R',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
                if d.get('sw01'):output(n,'B',unreal.MaterialProperty.MP_METALLIC)
            else:
                normal_scale=node(unreal.MaterialExpressionVectorParameter,-580,900,parameter_name='NormalXYScale',default_value=unreal.LinearColor(d.get('normal_strength',.28),d.get('normal_strength',.28),1.,1.))
                scaled=node(unreal.MaterialExpressionMultiply,-330,830);conn(n,'RGB',scaled,'A');conn(normal_scale,'RGB',scaled,'B')
                unit=node(unreal.MaterialExpressionNormalize,-60,830);conn(scaled,'',unit,'');output(unit,'',unreal.MaterialProperty.MP_NORMAL)
        if dry_rough is None:dry_rough=scalar('Roughness',d.get('roughness',.7),0,450)
        wet=d.get('wetness',0.)
        if wet:
            maskuv=node(unreal.MaterialExpressionTextureCoordinate,-900,1120,coordinate_index=1)
            mask=node(unreal.MaterialExpressionComponentMask,-650,1120,r=True,g=False,b=False,a=False);conn(maskuv,'',mask,'Input')
            factor=node(unreal.MaterialExpressionMultiply,-400,1120);conn(mask,'',factor,'A');conn(scalar('Wetness',wet,-650,1300),'',factor,'B')
            lerp=node(unreal.MaterialExpressionLinearInterpolate,200,520);conn(dry_rough,'',lerp,'A');conn(scalar('WetRoughness',.22,-40,700),'',lerp,'B');conn(factor,'',lerp,'Alpha');dry_rough=lerp
            dark=node(unreal.MaterialExpressionMultiply,-140,1040);conn(factor,'',dark,'A');conn(scalar('WetDarkening',.20,-400,1450),'',dark,'B')
            one=node(unreal.MaterialExpressionOneMinus,70,1050);conn(dark,'',one,'Input')
            wb=node(unreal.MaterialExpressionMultiply,350,60);conn(base,'',wb,'A');conn(one,'',wb,'B');base=wb
        output(base,'',unreal.MaterialProperty.MP_BASE_COLOR)
        output(dry_rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
        if not(d.get('sw01') and 'ORM' in tex):output(scalar('Metallic',d.get('metallic',0),0,630),'',unreal.MaterialProperty.MP_METALLIC)
        if d.get('emission'):
            strength=scalar('EmissionStrength',d['emission'],0,-630);mul=node(unreal.MaterialExpressionMultiply,250,-500);conn(tint,'RGB',mul,'A');conn(strength,'',mul,'B');output(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        if d.get('glass'):
            # A simple translucent preview, NOT a converted Blender transmission model or WaterBody.
            prop(mat,'blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
            output(scalar('Opacity',.70,250,800),'',unreal.MaterialProperty.MP_OPACITY)
        prop(mat,'two_sided',bool(d.get('two_sided',False)))
        try:MEL.set_material_usage(mat,unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES)
        except Exception as e:warn('Instanced material flag: '+str(e))
        MEL.recompile_material(mat);EAL.set_metadata_tag(mat,'MB01_Ready','1');EAL.set_metadata_tag(mat,'MB01_RecipeHash',recipe_hash);save(mat)
    mi,new=get_asset(f'{CONTENT_ROOT}/Materials/MI_{name.removeprefix("M_")}',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    if new or REIMPORT_OWN_ASSETS:MEL.set_material_instance_parent(mi,mat);MEL.update_material_instance(mi);save(mi)
    if d.get('external_material'):warn('External custom tree material uses a colour fallback; assign your original UE material: '+name)
    return mi


def fbx_options():
    o=unreal.FbxImportUI()
    for k,v in dict(import_mesh=True,import_as_skeletal=False,import_materials=False,import_textures=False,automated_import_should_detect_type=False,mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH).items():prop(o,k,v)
    d=o.get_editor_property('static_mesh_import_data')
    for k,v in dict(combine_meshes=False,auto_generate_collision=False,generate_lightmap_u_vs=False,import_uniform_scale=1.,vertex_color_import_option=unreal.VertexColorImportOption.REPLACE,normal_import_method=unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS).items():prop(d,k,v)
    return o

def bounds(mesh):
    b=mesh.get_bounding_box();return ((b.min.x,b.min.y,b.min.z),(b.max.x,b.max.y,b.max.z))

def main():
    if not CONTENT_ROOT.startswith('/Game/') or len(CONTENT_ROOT)<7:raise ValueError('Use a dedicated /Game/MB01 folder, not /Game itself.')
    if (ROOT/'EXPORT_FAILED.txt').exists():raise RuntimeError('This export was incomplete; export again in Blender.')
    source=ROOT/'MB01_scene.json'
    if not source.is_file():raise FileNotFoundError('Execute the EXPORTED script beside MB01_scene.json, not the add-on source copy.')
    data=json.loads(source.read_text(encoding='utf-8'))
    if data.get('schema')!='mb01.scene/0.1':raise ValueError('Unsupported scene manifest schema.')
    spec=importlib.util.spec_from_file_location('_mb01_coordinates',ROOT/'mb01_coordinates.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
    for key,d in data['asset_map'].items():
        path=(ROOT/d['file']).resolve()
        if not path.is_relative_to(ROOT):raise ValueError('Mesh path escapes export root.')
        if not path.is_file():raise FileNotFoundError(str(path))
        if hashlib.sha256(path.read_bytes()).hexdigest()!=d['sha256']:raise ValueError('Mesh hash mismatch: '+key)
    for d in data['materials'].values():
        for rel in d.get('textures',{}).values():
            path=(ROOT/rel).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Missing/unsafe texture: '+rel)
    if DRY_RUN:
        log(f"Preflight OK: {len(data['asset_map'])} mesh files, {len(data['instances'])} placements. NO assets or actors changed. Set DRY_RUN=False to import.")
        return
    opts=fbx_options();meshes={}
    for key in ('SM_MB01_CalX','SM_MB01_CalY'):
        d=data['asset_map'][key];meshes[key]=import_one(ROOT/d['file'],f'{CONTENT_ROOT}/Meshes/{key}',key,unreal.StaticMesh,opts)
    basis=contract.infer_basis(bounds(meshes['SM_MB01_CalX']),bounds(meshes['SM_MB01_CalY']));log('Measured import basis: '+str(basis))
    # Validate the complete instance list BEFORE touching the current level.
    transforms=[contract.convert_matrix(d['matrix_world_m'],basis) for d in data['instances']]
    mats={name:make_material(d) for name,d in data['materials'].items()}
    for key,d in data['asset_map'].items():
        if key in meshes:continue
        mesh=import_one(ROOT/d['file'],f'{CONTENT_ROOT}/Meshes/{key}',key,unreal.StaticMesh,opts);meshes[key]=mesh
        slots=mesh.get_editor_property('static_materials')
        for i,slot in enumerate(slots):
            candidates=[str(slot.get_editor_property('material_slot_name'))]
            try:candidates.append(str(slot.get_editor_property('imported_material_slot_name')))
            except Exception:pass
            normalize=lambda text:re.sub(r'[^A-Za-z0-9_]','_',text)
            matches={name for name,source_slot in zip(d.get('materials',[]),d.get('material_slot_names',[])) if any(source_slot==s or name==s or normalize(source_slot)==normalize(s) for s in candidates)}
            if len(matches)>1:raise RuntimeError('Ambiguous material slots: '+str(matches))
            match=next(iter(matches),None)
            if match in mats:mesh.set_material(i,mats[match])
            elif d.get('materials'):raise RuntimeError(f'{key}: unmatched material slot {i}: {candidates}. No silent assignment.')
        meta=d.get('metadata',{})
        if d.get('collision')=='COMPLEX':
            body=mesh.get_editor_property('body_setup')
            if body:prop(body,'collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            else:warn('BodySetup missing for static architectural collision: '+key)
        save(mesh)
    api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);spawned=[]
    scene_tag='MB01_SCENE_'+data['project']
    previous=[a for a in api.get_all_level_actors() if a.actor_has_tag(scene_tag)]
    if previous and not REPLACE_SAME_SCENE:raise RuntimeError('This scene already exists. It was preserved. Change revision or explicitly set REPLACE_SAME_SCENE.')
    if PLACE_SCENE:
        try:
            with unreal.ScopedEditorTransaction('MB01 place building scene'):
                for d,(location,quat,scale) in zip(data['instances'],transforms):
                    rotation=unreal.Quat(*quat).rotator();actor=api.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*location),rotation)
                    if actor is None:raise RuntimeError('Cannot spawn static mesh actor.')
                    spawned.append(actor);actor.static_mesh_component.set_static_mesh(meshes[d['asset']]);actor.set_actor_scale3d(unreal.Vector(*scale))
                    if d['category']=='DOOR':actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
                    actor.set_actor_label(d['label']);actor.set_folder_path('MB01/'+data['project']+'/'+d['category']);prop(actor,'tags',[unreal.Name(scene_tag),unreal.Name(OWNER)])
                    if data['asset_map'][d['asset']].get('collision')=='NONE':
                        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                for actor in previous:api.destroy_actor(actor)
        except Exception:
            for actor in spawned:
                try:api.destroy_actor(actor)
                except Exception:pass
            raise
    report=dict(engine_version=unreal.SystemLibrary.get_engine_version(),basis=basis,meshes=len(meshes),actors=len(spawned),warnings=WARNINGS,level_saved=False)
    (ROOT/'MB01_last_unreal_run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    log(f'Created {len(spawned)} actors sharing {len(meshes)} static meshes. Inspect collisions/materials, then save the level manually.')
    log('No automatic HISM/Nanite or runtime animation was applied. UV0 is tiling; no unique lightmap UV is supplied. Level not saved.')

if __name__=='__main__':
    try:main()
    except Exception:
        unreal.log_error('[MB01] Stopped: '+traceback.format_exc());raise

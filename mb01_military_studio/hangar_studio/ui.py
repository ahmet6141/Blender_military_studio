# SPDX-License-Identifier: MIT
"""Categorized Hangar Studio panel. This is an additive legacy MB01 add-on module."""
import bpy, json, traceback
from pathlib import Path
from dataclasses import fields
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty, EnumProperty, PointerProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from .contracts import HangarConfig, PRESETS, PANEL_TYPES, preset, to_document, load_json, gate_clear_width
from . import blender_tools as B

_BUSY=False

class HGSettings(bpy.types.PropertyGroup):
    preset_id:EnumProperty(name='Mimari önayar',items=[(k,k.replace('_',' ').title(),'Kaynak geometri önayarı') for k in PRESETS])
    name:StringProperty(name='Hangar kimliği',default='HG_DAYLIGHT_01',maxlen=48)
    width:FloatProperty(name='Gövde genişliği / m',default=32,min=20,max=48)
    depth:FloatProperty(name='Derinlik / m',default=36,min=18,max=60)
    eave_height:FloatProperty(name='Nominal saçak / m',default=7.6,min=6,max=9)
    roof_rise:FloatProperty(name='Çatı yükselişi / m',default=2.6,min=1.2,max=4.8)
    bays:IntProperty(name='Boyuna hücre sayısı',default=8,min=4,max=12)
    roof_type:EnumProperty(name='Çatı türü',items=[('GABLE','Eğimli çatı',''),('MONITOR','Yükseltilmiş ışıklık çatısı','')],default='MONITOR')
    monitor_width:FloatProperty(name='Işıklık genişliği / m',default=5.2,min=2,max=8)
    monitor_height:FloatProperty(name='Işıklık yükselişi / m',default=1,min=.65,max=1.6)
    opening_width:FloatProperty(name='Nominal ana açıklık / m',default=22,min=10,max=36)
    opening_height:FloatProperty(name='Ana açıklık yüksekliği / m',default=6.15,min=4.3,max=7.7)
    gate_leaves:IntProperty(name='Ana kapı kanatları (4/6/8)',default=6,min=4,max=8)
    gate_open:FloatProperty(name='Ana kapı açık oranı',default=.82,min=0,max=1,subtype='FACTOR')
    gate_glazing:BoolProperty(name='Kapı üst cam bandı',default=True)
    personnel_open:FloatProperty(name='Personel kapıları',default=0,min=0,max=1,subtype='FACTOR')
    left_panels:StringProperty(name='Sol cephe dizisi',default='',description='Boş: otomatik. 10 tür: METAL, CLERESTORY, LOUVER, PERSONNEL, CASSETTE, VISION, SHADED, DUAL_VENT, DOUBLE_SERVICE, CANOPY_ENTRY.')
    right_panels:StringProperty(name='Sağ cephe dizisi',default='',description='Virgülle ayrılmış hücre türleri. Komşu iki personel/servis girişi desteklenmez.')
    edit_side:EnumProperty(name='Düzenlenecek cephe',items=[('LEFT','Sol',''),('RIGHT','Sağ','')])
    edit_cell:IntProperty(name='Hücre (1’den başlar)',default=1,min=1,max=12)
    edit_token:EnumProperty(name='Yeni modül',items=[(t,t.replace('_',' ').title(),'') for t in PANEL_TYPES])
    rear_service_door:BoolProperty(name='Arka personel girişi',default=True)
    wall_thickness:FloatProperty(name='Kabuk kalınlığı / m',default=.22,min=.16,max=.36)
    base_height:FloatProperty(name='Yerel zemin üst kotu / m',default=.18,min=.08,max=.35)
    local_ground:BoolProperty(name='Yerel döşeme + apron',default=True,description='AF01 ortak apronu kullanılırken kapatın ve yüzey kotunu eşitleyin.')
    apron_depth:FloatProperty(name='Ön apron derinliği / m',default=5,min=3,max=8)
    drain:BoolProperty(name='Kesilmiş drenaj kanalı',default=True)
    landings:BoolProperty(name='Personel sahanlıkları',default=True)
    walkway_width:FloatProperty(name='Yaya port genişliği / m',default=3.2,min=2.4,max=4.5)
    gutters:BoolProperty(name='Oluk / iniş / kelepçeler',default=True)
    services:BoolProperty(name='Kablo tavaları / servis kutuları',default=True)
    fixtures:BoolProperty(name='Askılı armatür geometrisi',default=True)
    signage:BoolProperty(name='Kimlik / numara detayları',default=True)
    fasteners:BoolProperty(name='Seçili bağlantı detayları',default=True)
    detail:EnumProperty(name='Ayrıntı',items=[('DRAFT','Draft',''),('WORKING','Working',''),('HERO','Hero','')],default='WORKING')
    palette:EnumProperty(name='Palet',items=[('COASTAL','Coastal',''),('WOODLAND','Woodland',''),('URBAN','Urban','')],default='COASTAL')
    roof_finish:EnumProperty(name='Çatı yüzeyi',items=[('OLIVE','Zeytin',''),('GRAPHITE','Grafit',''),('SILVER','Gümüş boyalı','')],default='OLIVE')
    wall_finish:EnumProperty(name='Cephe yüzeyi',items=[('LIGHT','Açık ton',''),('OLIVE','Zeytin',''),('GRAPHITE','Grafit','')],default='LIGHT')
    wetness:FloatProperty(name='Açık apron ıslaklığı',default=0,min=0,max=1,subtype='FACTOR')
    normal_strength:FloatProperty(name='Mikro normal şiddeti',default=.24,min=0,max=1.4)
    concrete_tile_m:FloatProperty(name='Beton doku kapsaması / m',default=2,min=.25,max=8)
    metal_tile_m:FloatProperty(name='Metal doku kapsaması / m',default=1.2,min=.25,max=8)
    seed:IntProperty(name='Varyasyon tohumu',default=17,min=0,max=2147483647)
    yaw:FloatProperty(name='Yerleşim yönü / derece',default=0,min=-360,max=360)
    texture_root:StringProperty(name='Harici PBR üst klasörü',subtype='DIR_PATH',default='')
    export_directory:StringProperty(name='Aktarım klasörü',subtype='DIR_PATH',default='//MB01_Hangar_Exports')
    active_root:PointerProperty(name='Aktif Hangar Studio',type=bpy.types.Object,poll=lambda self,o:bool(o.get('mb01_hangar_root')))


def settings(context):
    p=context.scene.mb01_hangar
    return HangarConfig(**{f.name:getattr(p,f.name) for f in fields(HangarConfig)}).checked()


def active(context):
    return B.root_for(context.active_object) or context.scene.mb01_hangar.active_root


def error(op,exc):
    text=traceback.format_exc();print('[HangarStudio] '+text)
    block=bpy.data.texts.get('HG_Last_Error') or bpy.data.texts.new('HG_Last_Error');block.write('\n'+text)
    op.report({'ERROR'},str(exc)[:240])


class HG_OT_Preset(bpy.types.Operator):
    bl_idname='mb01hg.preset';bl_label='Hangar önayarını yükle';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        c=preset(context.scene.mb01_hangar.preset_id);p=context.scene.mb01_hangar
        for f in fields(HangarConfig):setattr(p,f.name,getattr(c,f.name))
        return {'FINISHED'}


class HG_OT_Validate(bpy.types.Operator):
    bl_idname='mb01hg.validate';bl_label='Geometri kurallarını kontrol et'
    def execute(self,context):
        try:
            c=settings(context)
            self.report({'INFO'},f'Parametreler geçerli. Hücre {c.depth/c.bays:.3f} m; mevcut görsel kapı açıklığı {gate_clear_width(c):.3f} m. Sertifikasyon değildir.')
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_Build(bpy.types.Operator):
    bl_idname='mb01hg.build';bl_label='YENİ hangar revizyonu oluştur';bl_options={'REGISTER','UNDO'}
    _job=None;_iterator=None;_timer=None;_owns_lock=False
    def begin(self,context):
        global _BUSY
        if _BUSY:raise RuntimeError('Bir Hangar Studio işlemi devam ediyor.')
        p=context.scene.mb01_hangar
        self._job=B.BuildJob(settings(context),tuple(context.scene.cursor.location),p.yaw,bpy.path.abspath(p.texture_root) if p.texture_root else '')
        self._iterator=self._job.steps();_BUSY=True;self._owns_lock=True
    def execute(self,context):
        global _BUSY
        try:
            self.begin(context)
            for _ in self._iterator:pass
            context.scene.mb01_hangar.active_root=self._job.root
            return {'FINISHED'}
        except Exception as exc:
            if self._job:self._job.abort()
            error(self,exc);return {'CANCELLED'}
        finally:
            if self._owns_lock:_BUSY=False;self._owns_lock=False
    def invoke(self,context,event):
        try:self.begin(context)
        except Exception as exc:error(self,exc);return {'CANCELLED'}
        context.window_manager.progress_begin(0,100)
        self._timer=context.window_manager.event_timer_add(.02,window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def finish(self,context):
        global _BUSY
        if self._timer:context.window_manager.event_timer_remove(self._timer);self._timer=None
        context.window_manager.progress_end();_BUSY=False;self._owns_lock=False
        if context.area:context.area.header_text_set(None)
    def modal(self,context,event):
        if event.type=='ESC':self._job.abort();self.finish(context);return {'CANCELLED'}
        if event.type=='TIMER':
            try:
                value,label=next(self._iterator);context.window_manager.progress_update(int(value*100))
                if context.area:context.area.header_text_set('Hangar Studio: '+label)
            except StopIteration:
                context.scene.mb01_hangar.active_root=self._job.root;self.finish(context);return {'FINISHED'}
            except Exception as exc:
                self._job.abort();self.finish(context);error(self,exc);return {'CANCELLED'}
        return {'PASS_THROUGH'}


class HG_OT_EditCell(bpy.types.Operator):
    bl_idname='mb01hg.edit_cell';bl_label='Seçilen hücreye modülü uygula';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            from dataclasses import replace
            p=context.scene.mb01_hangar;c=settings(context)
            if p.edit_cell>c.bays:raise ValueError('Hücre numarası bölme sayısını aşıyor.')
            seq=list(c.panel_sequence(p.edit_side));seq[p.edit_cell-1]=p.edit_token
            key='left_panels' if p.edit_side=='LEFT' else 'right_panels'
            value=','.join(seq);replace(c,**{key:value}).checked();setattr(p,key,value)
            self.report({'INFO'},'Tarif güncellendi; geometri için YENİ revizyon üretin.')
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_Load(bpy.types.Operator):
    bl_idname='mb01hg.load_active';bl_label='Aktif hangarın ayarlarını al'
    def execute(self,context):
        try:
            root=active(context);c=B.config_for(root);p=context.scene.mb01_hangar
            for f in fields(HangarConfig):setattr(p,f.name,getattr(c,f.name))
            p.texture_root=root.get('mb01_texture_root','');p.active_root=root
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_Pose(bpy.types.Operator):
    bl_idname='mb01hg.pose';bl_label='Kapı konumlarını uygula';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            p=context.scene.mb01_hangar;B.set_pose(active(context),p.gate_open,p.personnel_open)
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_Export(bpy.types.Operator):
    bl_idname='mb01hg.export';bl_label='FBX + PBR + UE manifest dışa aktar'
    def execute(self,context):
        try:
            from ..exporter import export_project
            root=active(context);B.config_for(root);p=context.scene.mb01_hangar
            if p.export_directory.startswith('//') and not bpy.data.filepath:raise ValueError('Önce .blend kaydedin veya mutlak çıktı klasörü seçin.')
            path=export_project(root,bpy.path.abspath(p.export_directory));self.report({'INFO'},str(path))
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_Preview(bpy.types.Operator):
    bl_idname='mb01hg.preview';bl_label='Kamera + ışık düzeni ekle';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:B.preview(active(context));return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_Section(bpy.types.Operator):
    bl_idname='mb01hg.section';bl_label='Çatıyı kesit görünümünde gizle/göster';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            root=active(context);B.config_for(root);flag=not root.get('hg_section',False)
            if flag:
                saved={}
                for ob in B.descendants(root):
                    element=ob.get('mb01_element','')
                    roof_detail=any(token in element for token in ('HG_StandingSeams','HG_MonitorGlass','HG_MonitorFrames','HG_MonitorDrip','HG_MonitorEndCaps','HG_MonitorCap','HG_Bargeboards'))
                    if ob.get('mb01_category')=='ROOF' or roof_detail:
                        saved[ob.name]=bool(ob.hide_get());ob.hide_set(True)
                root['hg_section_saved']=json.dumps(saved)
            else:
                for name,hidden in json.loads(root.get('hg_section_saved','{}')).items():
                    ob=bpy.data.objects.get(name)
                    if ob is not None:ob.hide_set(hidden)
            root['hg_section']=flag
            self.report({'INFO'},'Yalnız viewport çatı görünümü değişti; export tam modeli içerir.')
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_SaveJSON(bpy.types.Operator,ExportHelper):
    bl_idname='mb01hg.save_json';bl_label='Hangar tarifini kaydet'
    filename_ext='.json';filter_glob:StringProperty(default='*.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            Path(self.filepath).write_text(json.dumps(to_document(settings(context)),ensure_ascii=False,indent=2),encoding='utf-8')
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_OT_ReadJSON(bpy.types.Operator,ImportHelper):
    bl_idname='mb01hg.read_json';bl_label='Hangar tarifi yükle'
    filename_ext='.json';filter_glob:StringProperty(default='*.json',options={'HIDDEN'})
    def execute(self,context):
        try:
            c=load_json(self.filepath);p=context.scene.mb01_hangar
            for f in fields(HangarConfig):setattr(p,f.name,getattr(c,f.name))
            return {'FINISHED'}
        except Exception as exc:error(self,exc);return {'CANCELLED'}


class HG_PT_Main(bpy.types.Panel):
    bl_idname='HG_PT_main';bl_label='Hangar Expansion | 0.3 alpha.1';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01'
    def draw(self,context):
        p=context.scene.mb01_hangar;l=self.layout
        l.label(text='Kurgusal CGI mimari · yeni revizyon',icon='MOD_BUILD')
        l.prop(p,'preset_id');l.operator('mb01hg.preset',icon='PRESET');l.prop(p,'name');l.prop(p,'detail')
        l.operator('mb01hg.validate',icon='CHECKMARK');l.operator('mb01hg.build',icon='MESH_CUBE')
        l.prop(p,'active_root');l.operator('mb01hg.load_active',icon='IMPORT')


def _panel(name,label,properties,extra=None):
    def draw(self,context):
        p=context.scene.mb01_hangar
        for key in properties:self.layout.prop(p,key)
        if extra:extra(self.layout,p)
    return type(name,(bpy.types.Panel,),dict(__module__=__name__,bl_idname=name,bl_label=label,
        bl_parent_id='HG_PT_main',bl_space_type='VIEW_3D',bl_region_type='UI',bl_category='MB01',
        bl_options={'DEFAULT_CLOSED'},draw=draw))


HG_PT_Body=_panel('HG_PT_body','01 · Aks / gövde / çatı',('width','depth','bays','eave_height','roof_rise','roof_type','monitor_width','monitor_height','yaw'))
HG_PT_Facade=_panel('HG_PT_facade','02 · Cephe hücreleri',('left_panels','right_panels','edit_side','edit_cell','edit_token','wall_thickness','rear_service_door'),
    lambda l,p:l.operator('mb01hg.edit_cell',icon='MOD_BUILD'))
HG_PT_Doors=_panel('HG_PT_doors','03 · Açıklık / teleskopik kapılar',('opening_width','opening_height','gate_leaves','gate_glazing','gate_open','personnel_open'),
    lambda l,p:l.operator('mb01hg.pose',icon='DRIVER'))
HG_PT_Floor=_panel('HG_PT_floor','04 · Zemin / drenaj / portlar',('base_height','local_ground','apron_depth','drain','landings','walkway_width'))
HG_PT_Detail=_panel('HG_PT_detail','05 · Bağlantı / tesisat / kimlik',('gutters','services','fixtures','signage','fasteners','seed'))
HG_PT_Material=_panel('HG_PT_material','06 · PBR yüzey rolleri',('palette','wall_finish','roof_finish','wetness','normal_strength','concrete_tile_m','metal_tile_m','texture_root'))

def extra_tools(l,p):
    l.operator('mb01hg.save_json',icon='EXPORT');l.operator('mb01hg.read_json',icon='IMPORT')
    l.operator('mb01hg.section');l.operator('mb01hg.preview',icon='CAMERA_DATA')
    l.prop(p,'export_directory');l.operator('mb01hg.export',icon='EXPORT')
    l.label(text='Işık düzeni world / render ayarlarını değiştirir.')
HG_PT_Tools=_panel('HG_PT_tools','07 · Kontrol / kayıt / aktarım',(),extra_tools)

CLASSES=(HGSettings,HG_OT_Preset,HG_OT_Validate,HG_OT_Build,HG_OT_EditCell,HG_OT_Load,HG_OT_Pose,HG_OT_Export,HG_OT_Preview,
         HG_OT_Section,HG_OT_SaveJSON,HG_OT_ReadJSON,HG_PT_Main,HG_PT_Body,HG_PT_Facade,HG_PT_Doors,
         HG_PT_Floor,HG_PT_Detail,HG_PT_Material,HG_PT_Tools)

def register():
    registered=[]
    try:
        for cls in CLASSES:bpy.utils.register_class(cls);registered.append(cls)
        bpy.types.Scene.mb01_hangar=PointerProperty(type=HGSettings)
    except Exception:
        for cls in reversed(registered):bpy.utils.unregister_class(cls)
        raise

def unregister():
    global _BUSY
    if _BUSY:raise RuntimeError('Eklentiyi kapatmadan önce üretimi tamamlayın veya Esc ile iptal edin.')
    if hasattr(bpy.types.Scene,'mb01_hangar'):del bpy.types.Scene.mb01_hangar
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)

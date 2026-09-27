# SPDX-License-Identifier: MIT
import bpy,json,traceback
from pathlib import Path
from dataclasses import fields
from bpy.props import StringProperty,FloatProperty,IntProperty,BoolProperty,EnumProperty,PointerProperty
from . import core
from . import blender_backend as B

LABELS={'HQ':'Karargâh / idari yapı','UNIT':'Birlik / personel binası','HANGAR':'Kapalı bakım hangarı','SHELTER':'AS07 açık shelter','RANGE_SET':'Atış alanı dekoru (CGI)'}

class MB01Settings(bpy.types.PropertyGroup):
    kind:EnumProperty(name='Yapı ailesi',items=[(k,v,'') for k,v in LABELS.items()],default='HQ')
    name:StringProperty(name='Bina adı',default='KARARGAH_01',maxlen=48)
    width:FloatProperty(name='Genişlik / m',default=35.2,min=14,max=56)
    depth:FloatProperty(name='Derinlik / m',default=20.4,min=10,max=64)
    floors:IntProperty(name='Kat sayısı',default=3,min=1,max=4)
    floor_height:FloatProperty(name='Kat / saçak yüksekliği',default=3.6,min=2.8,max=10)
    bays:IntProperty(name='Taşıyıcı / set bölümü',default=8,min=4,max=12)
    roof:EnumProperty(name='Çatı',items=[('FLAT','Parapetli',''),('PITCHED','Eğimli',''),('ARCH','AS07 kemerli','')],default='FLAT')
    detail:EnumProperty(name='Ayrıntı',items=[('DRAFT','Draft / hızlı','Bevel kapalı, bazı küçük parçalar azalır'),('WORKING','Working',''),('HERO','Hero / yakın plan','Üç segment bevel; AS07 kemer çözünürlüğü artar')],default='WORKING')
    palette:EnumProperty(name='Palet',items=[('COASTAL','Coastal / açık taş + zeytin',''),('WOODLAND','Woodland / koyu yeşil',''),('URBAN','Urban / grafit','')],default='COASTAL')
    seed:IntProperty(name='Varyasyon tohumu',default=17,min=0,max=999999)
    base_height:FloatProperty(name='Taban / yaya yüzeyi yüksekliği',default=.18,min=.08,max=.35,precision=3)
    walkway_width:FloatProperty(name='SW01 bağlantı genişliği',default=3.2,min=2.4,max=5)
    plaza_depth:FloatProperty(name='Ön sahanlık derinliği',default=4.5,min=2.5,max=7)
    local_ground:BoolProperty(name='Yerel zemin ve sahanlık oluştur',default=True,description='AF01 ortak apronu üzerinde üst üste zemin oluşmaması için kapatın. Otomatik yüzey kesimi yapılmaz.')
    services:BoolProperty(name='Tesisat ve kent mobilyası',default=True)
    signage:BoolProperty(name='Tabela / numaralandırma',default=True)
    sunshades:BoolProperty(name='Pencere güneşlikleri',default=True)
    door_open:FloatProperty(name='Kapı açıklığı',default=.64,min=0,max=1,subtype='FACTOR')
    roof_rise:FloatProperty(name='AS07 kemer yükselişi',default=4.2,min=1.8,max=8)
    wear:FloatProperty(name='Yüzey pürüzlülük varyasyonu',default=.15,min=0,max=1,subtype='FACTOR')
    office_style:EnumProperty(name='İdari / birlik stil modu',items=[('AUTO','Otomatik','HQ=Command, UNIT=Barracks'),('COMMAND','Command HQ','Daha prestijli giriş ve vurgu kütleleri'),('BARRACKS','Barracks / Birlik','Dış merdivenli, tekrar eden oda modülleri'),('SUPPORT','Support / Destek','İdari + servis kapılı destek yapısı'),('LOGISTICS','Logistics / Eğitim','Daha büyük servis cephesi ve lojistik dili')],default='AUTO')
    service_bays:IntProperty(name='Servis kapısı adedi',default=3,min=0,max=5)
    stair_tower:BoolProperty(name='Harici merdiven / kule',default=True)
    roof_screen:BoolProperty(name='Çatı ekipman perdesi',default=True)
    corner_glass:BoolProperty(name='Köşe cam vurgusu',default=False)
    command_variant:EnumProperty(name='Karargâh tasarım dili',items=[('EXECUTIVE','Executive / taş + metal','Prestijli merkezi portal ve dengeli metal aksan'),('TECHNICAL','Technical / grafit teknoloji','Daha derin metal fins ve teknik cephe ritmi'),('MONOLITHIC','Monolithic / ağır kütle','Daha kalın portal ve daha sakin kurumsal cephe')],default='EXECUTIVE')
    facade_relief:FloatProperty(name='Cephe derinliği / m',default=.55,min=.18,max=1.40,precision=2)
    vertical_fins:IntProperty(name='Dikey fin adedi',default=6,min=0,max=12)
    atrium_floors:IntProperty(name='Giriş atrium yüksekliği / kat',default=3,min=1,max=4)
    base_cladding:BoolProperty(name='Dayanıklı alt cephe bandı',default=True)
    night_lighting:BoolProperty(name='Gece / pratik ışık materyalleri',default=True)
    micro_details:BoolProperty(name='Hero mikro detayları',default=True)
    yaw:FloatProperty(name='Yerleşim yönü / derece',default=0,min=-360,max=360)
    override:StringProperty(name='Harici PBR üst klasörü',subtype='DIR_PATH',default='')
    export_directory:StringProperty(name='Export klasörü',subtype='DIR_PATH',default='//MB01_Exports')
    active_root:PointerProperty(name='Aktif MB01 yapı',type=bpy.types.Object,poll=lambda self,o:bool(o.get('mb01_project_root')) and not o.get('mb01_modular_root') and not o.get('mb01_hangar_root'))


def settings(context):
    p=context.scene.mb01
    return core.Settings(**{f.name:getattr(p,f.name) for f in fields(core.Settings)}).checked()

def active(context):
    selected=context.scene.mb01.active_root
    if selected and not selected.get('mb01_modular_root') and not selected.get('mb01_hangar_root'):return selected
    return B.root_for(context.active_object)

def report_error(op,exc):
    text=traceback.format_exc();print('[MB01 ERROR]\n'+text)
    block=bpy.data.texts.get('MB01_Last_Error') or bpy.data.texts.new('MB01_Last_Error');block.write('\n'+text)
    op.report({'ERROR'},str(exc)[:240])

class MB01_OT_Preset(bpy.types.Operator):
    bl_idname='mb01.apply_preset';bl_label='Seçilen aile ölçülerini yükle';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        p=context.scene.mb01
        for k,v in core.PRESETS[p.kind].items():setattr(p,k,v)
        p.name={'HQ':'KARARGAH_01','UNIT':'BIRLIK_02','HANGAR':'HANGAR_03','SHELTER':'AS07_04','RANGE_SET':'EGITIM_SET_05'}[p.kind]
        return {'FINISHED'}

class MB01_OT_Build(bpy.types.Operator):
    bl_idname='mb01.build';bl_label='MB01 Yapı Oluştur';bl_options={'REGISTER','UNDO'}
    rebuild:BoolProperty(default=False)
    _job=None;_iterator=None;_timer=None
    def begin(self,context):
        p=context.scene.mb01;old=active(context) if self.rebuild else None
        if self.rebuild and not old:raise ValueError('Yeniden üretmek için bir MB01 kökü seçin.')
        if self.rebuild and json.loads(old['mb01_config'])['kind']!=p.kind:raise ValueError('Aile değiştirirken yeni yapı oluşturun; eski yapıyı aynı yerinde dönüştürmüyorum.')
        path=bpy.path.abspath(p.override) if p.override else ''
        self._job=B.BuildJob(settings(context),old,tuple(context.scene.cursor.location),p.yaw,path)
        self._iterator=self._job.steps()
    def execute(self,context):
        try:
            self.begin(context)
            for _ in self._iterator:pass
            context.scene.mb01.active_root=self._job.root
            return {'FINISHED'}
        except Exception as e:
            if self._job:self._job.abort()
            report_error(self,e);return {'CANCELLED'}
    def invoke(self,context,event):
        try:self.begin(context)
        except Exception as e:report_error(self,e);return {'CANCELLED'}
        context.window_manager.progress_begin(0,100)
        self._timer=context.window_manager.event_timer_add(.02,window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def finish(self,context):
        if self._timer:context.window_manager.event_timer_remove(self._timer);self._timer=None
        context.window_manager.progress_end()
        if context.area:context.area.header_text_set(None)
    def modal(self,context,event):
        if event.type=='ESC':self._job.abort();self.finish(context);return {'CANCELLED'}
        if event.type=='TIMER':
            try:
                fraction,label=next(self._iterator);context.window_manager.progress_update(int(fraction*100))
                if context.area:context.area.header_text_set('MB01: '+label)
            except StopIteration:
                context.scene.mb01.active_root=self._job.root;self.finish(context);return {'FINISHED'}
            except Exception as e:
                self._job.abort();self.finish(context);report_error(self,e);return {'CANCELLED'}
        return {'PASS_THROUGH'}

class MB01_OT_Load(bpy.types.Operator):
    bl_idname='mb01.load_settings';bl_label='Aktif yapının ayarlarını al'
    def execute(self,context):
        r=active(context)
        if not r:self.report({'ERROR'},'MB01 kökü seçin.');return {'CANCELLED'}
        p=context.scene.mb01
        for k,v in json.loads(r['mb01_config']).items():setattr(p,k,v)
        p.override=r.get('mb01_texture_root','');p.active_root=r
        return {'FINISHED'}

class MB01_OT_Doors(bpy.types.Operator):
    bl_idname='mb01.preview_doors';bl_label='Kapı açıklığını uygula';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        root=active(context)
        if not root:self.report({'ERROR'},'MB01 kökü gerekli.');return {'CANCELLED'}
        B.update_doors(root,context.scene.mb01.door_open);return {'FINISHED'}

class MB01_OT_Keep(bpy.types.Operator):
    bl_idname='mb01.lock_selected';bl_label='Seçilenleri yeniden üretimde koru';bl_options={'REGISTER','UNDO'}
    unlock:BoolProperty(default=False)
    def execute(self,context):
        for ob in context.selected_objects:
            if ob.get('mb01_owner') and not ob.get('mb01_project_root'):ob['mb01_keep']=not self.unlock
        return {'FINISHED'}

class MB01_OT_Export(bpy.types.Operator):
    bl_idname='mb01.export';bl_label='FBX + PBR + UE yerleşimini export et'
    def execute(self,context):
        try:
            from .exporter import export_project
            p=context.scene.mb01;root=active(context)
            if not root:raise ValueError('Aktif MB01 yapı seçin.')
            if p.export_directory.startswith('//') and not bpy.data.filepath:raise ValueError('Önce .blend kaydedin veya mutlak export yolu seçin.')
            dest=export_project(root,bpy.path.abspath(p.export_directory));self.report({'INFO'},'Export: '+str(dest))
            return {'FINISHED'}
        except Exception as e:report_error(self,e);return {'CANCELLED'}

class MB01_OT_Preview(bpy.types.Operator):
    bl_idname='mb01.preview_scene';bl_label='Kamera + güneş düzeni oluştur';bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            r=active(context)
            if not r:raise ValueError('Aktif MB01 yapı seçin.')
            B.preview_scene(r);return {'FINISHED'}
        except Exception as e:report_error(self,e);return {'CANCELLED'}

class MB01_OT_Report(bpy.types.Operator):
    bl_idname='mb01.validation_report';bl_label='Üretim raporunu aç'
    def execute(self,context):
        r=active(context)
        if not r:self.report({'ERROR'},'MB01 kökü seçin.');return {'CANCELLED'}
        name='MB01_Report_'+r['mb01_owner'][:8]
        text=bpy.data.texts.get(name) or bpy.data.texts.new(name);text.clear()
        text.write(json.dumps(json.loads(r.get('mb01_blender_report','{}')),ensure_ascii=False,indent=2))
        self.report({'INFO'},'Text Editor: '+name);return {'FINISHED'}

class MB01_PT_Main(bpy.types.Panel):
    bl_label='MB01 | Military Building Studio';bl_idname='MB01_PT_main';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01'
    def draw(self,context):
        p=context.scene.mb01;l=self.layout
        l.label(text='0.4 alpha.1 · MCP + CGI/PBR HQ',icon='MOD_BUILD')
        l.prop(p,'kind');l.operator('mb01.apply_preset',icon='PRESET')
        l.prop(p,'name');l.prop(p,'width');l.prop(p,'depth')
        if p.kind in ('HQ','UNIT'):
            l.prop(p,'floors');l.prop(p,'roof');l.prop(p,'office_style')
        if p.kind=='HQ' and p.office_style in {'AUTO','COMMAND'}:
            l.prop(p,'command_variant');l.prop(p,'facade_relief');l.prop(p,'vertical_fins');l.prop(p,'atrium_floors')
        if p.kind!='RANGE_SET':l.prop(p,'floor_height')
        if p.kind in ('HANGAR','SHELTER','RANGE_SET'):l.prop(p,'bays')
        if p.kind in ('HQ','UNIT') and p.office_style in {'SUPPORT','LOGISTICS'}:l.prop(p,'service_bays')
        if p.kind=='SHELTER':l.prop(p,'roof_rise')
        if p.kind=='RANGE_SET':l.label(text='Dekor seti; gerçek kullanım projesi değil.',icon='INFO')
        l.prop(p,'detail');l.prop(p,'palette');l.prop(p,'seed');l.prop(p,'yaw')
        l.operator('mb01.build',text='3D Cursor konumunda YENİ yapı',icon='ADD').rebuild=False
        l.separator();l.prop(p,'active_root');l.operator('mb01.load_settings',icon='IMPORT')
        l.operator('mb01.build',text='Aktif yapıyı yeniden üret',icon='FILE_REFRESH').rebuild=True

class MB01_PT_Details(bpy.types.Panel):
    bl_label='Detaylar / bağlantı';bl_idname='MB01_PT_details';bl_parent_id='MB01_PT_main';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01'
    def draw(self,context):
        p=context.scene.mb01;l=self.layout
        for k in ('local_ground','base_height','walkway_width','plaza_depth','services','signage','sunshades','wear'):l.prop(p,k)
        if p.kind in ('HQ','UNIT'):
            for k in ('stair_tower','roof_screen','corner_glass'):l.prop(p,k)
        if p.kind=='HQ':
            for k in ('base_cladding','night_lighting','micro_details'):l.prop(p,k)
        l.label(text='PK01 port metadata; otomatik yol üretmez.')
        l.prop(p,'door_open');l.operator('mb01.preview_doors')
        l.operator('mb01.lock_selected',icon='LOCKED').unlock=False
        l.operator('mb01.lock_selected',text='Seçilenlerin kilidini kaldır',icon='UNLOCKED').unlock=True
        l.label(text='Kilitli parçalar aynı MB01 exportunda kalır.')

class MB01_PT_Export(bpy.types.Panel):
    bl_label='PBR / denetim / Unreal';bl_idname='MB01_PT_export';bl_parent_id='MB01_PT_main';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01'
    def draw(self,context):
        p=context.scene.mb01;l=self.layout
        l.prop(p,'override');l.prop(p,'export_directory');l.operator('mb01.export',icon='EXPORT')
        l.operator('mb01.validation_report',icon='TEXT');l.operator('mb01.preview_scene',icon='CAMERA_DATA')
        l.label(text='Kamera komutu dünya/render ayarını değiştirir.')
        l.label(text='UE 5.8 hedefi; native UE doğrulaması kullanıcı projesinde yapılmalı.',icon='INFO')

CLASSES=(MB01Settings,MB01_OT_Preset,MB01_OT_Build,MB01_OT_Load,MB01_OT_Doors,MB01_OT_Keep,MB01_OT_Export,MB01_OT_Preview,MB01_OT_Report,MB01_PT_Main,MB01_PT_Details,MB01_PT_Export)

def register():
    for cls in CLASSES:bpy.utils.register_class(cls)
    bpy.types.Scene.mb01=PointerProperty(type=MB01Settings)

def unregister():
    if hasattr(bpy.types.Scene,'mb01'):del bpy.types.Scene.mb01
    for cls in reversed(CLASSES):
        if hasattr(cls,'bl_rna'):bpy.utils.unregister_class(cls)

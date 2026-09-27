# SPDX-License-Identifier: MIT
"""Experimental MB01 panels. Does not replace the existing whole-building controls."""
import json, uuid
from datetime import datetime
from pathlib import Path
import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, EnumProperty, PointerProperty, CollectionProperty
from . import catalog, contracts, presets
from . import blender_tools as BT
from .. import exporter

_ENUM_CACHE={}

def module_items(self,context):
    key=(self.family,self.category)
    if key not in _ENUM_CACHE:
        values=catalog.available(self.family,None if self.category=='ALL' else self.category)
        _ENUM_CACHE[key]=[(m.id,m.title,m.id) for m in values] or [('NONE','Bu kategoride üretici yok','Planlanan modüller henüz seçilemez')]
    return _ENUM_CACHE[key]


def filter_changed(self,context):
    items=module_items(self,context)
    self.module_id=items[0][0]


def style_of(p):
    return contracts.Style(p.palette,p.wall_material,p.frame_material,p.plinth_material,p.wear)


def facade_of(p,single=False):
    cells=(contracts.Cell('BAY_001',p.module_id,p.width),) if single else tuple(
        contracts.Cell(c.cell_id,c.module_id,c.width) for c in p.cells)
    return contracts.FacadeInput(p.facade_id,p.family,cells,p.height,p.thickness,p.detail,
                                 style_of(p),p.door_open,p.target_width if not single else 0.,p.seed).checked()


def apply_document(p,facade):
    facade.checked();p.family=facade.family;p.facade_id=facade.id;p.height=facade.height;p.thickness=facade.thickness
    p.detail=facade.detail;p.door_open=facade.door_open;p.target_width=facade.target_width;p.seed=facade.seed
    for k,v in vars(facade.style).items():setattr(p,k,v)
    p.cells.clear()
    for c in facade.cells:
        item=p.cells.add();item.cell_id=c.id;item.module_id=c.module_id;item.width=c.width
    p.index=0


def disk_path(raw,directory=True):
    if not raw:raise ValueError('Bir dosya/klasör yolu seçin.')
    if raw.startswith('//') and not bpy.data.filepath:
        raise ValueError('Göreli yol için önce .blend kaydedin veya mutlak yol seçin.')
    p=Path(bpy.path.abspath(raw)).expanduser().resolve()
    if directory:p.mkdir(parents=True,exist_ok=True)
    return p


class MB02Cell(bpy.types.PropertyGroup):
    cell_id: StringProperty(default='BAY_001')
    module_id: StringProperty(default='COMMON.WALL.WINDOW')
    width: FloatProperty(name='Aks genişliği (m)',default=3.6,min=.1,max=20.,precision=3)


class MB02Settings(bpy.types.PropertyGroup):
    family: EnumProperty(name='Aile',items=[('HQ','Karargâh',''),('UNIT','Birlik binası',''),('HANGAR','Hangar',''),('SUPPORT','Destek / eğitim dekoru','')],update=filter_changed)
    category: EnumProperty(name='Kategori',items=[('ALL','Tüm hazır parçalar',''),('WALL','Duvar / panel',''),('ENTRY','Personel girişi',''),('GLAZING','Camlı bölüm',''),('SHADING','Güneşlik',''),('HANGAR_ENVELOPE','Hangar yan kabuğu',''),('HANGAR_ENTRY','Hangar personel girişi','')],update=filter_changed)
    module_id: EnumProperty(name='Modül',items=module_items)
    facade_id: StringProperty(name='Cephe kimliği',default='FACADE_01')
    width: FloatProperty(name='Yeni modül genişliği (m)',default=3.6,min=.1,max=10.)
    height: FloatProperty(name='Cephe yüksekliği (m)',default=3.6,min=1.,max=10.)
    thickness: FloatProperty(name='Duvar kalınlığı (m)',default=.28,min=.16,max=.50,precision=3)
    detail: EnumProperty(name='Detay',items=[('DRAFT','Draft',''),('WORKING','Working',''),('HERO','Hero','')],default='WORKING')
    palette: EnumProperty(name='Palet',items=[('COASTAL','Coastal',''),('WOODLAND','Woodland',''),('URBAN','Urban','')])
    wall_material: EnumProperty(name='Duvar rolü',items=[(x,x,'') for x in ('Plaster','Concrete','ConcreteLight')])
    frame_material: EnumProperty(name='Çerçeve rolü',items=[(x,x,'') for x in ('SteelDark','RoofOlive','Galvanized')])
    plinth_material: EnumProperty(name='Kaide rolü',items=[(x,x,'') for x in ('Stone','Concrete','ConcreteLight')])
    wear: FloatProperty(name='Pürüzlülük varyasyonu',default=.15,min=0.,max=1.)
    door_open: FloatProperty(name='Kapı açıklığı',default=0.,min=0.,max=1.)
    target_width: FloatProperty(name='Hedef genişlik; 0 = serbest toplam',default=0.,min=0.,max=180.)
    yaw: FloatProperty(name='Yerleşim yönü (derece)',default=0.,min=-360.,max=360.)
    seed: IntProperty(name='Varyasyon kimlik tohumu',default=17)
    cells: CollectionProperty(type=MB02Cell)
    index: IntProperty(default=0)
    texture_root: StringProperty(name='Harici PBR üst klasörü',subtype='DIR_PATH',default='')
    output_dir: StringProperty(name='Çıktı klasörü',subtype='DIR_PATH',default='//MB02_Export')
    plan_file: StringProperty(name='Yüklenecek cephe JSON',subtype='FILE_PATH',default='')


class MB02_UL_Cells(bpy.types.UIList):
    def draw_item(self,context,layout,data,item,icon,active_data,active_propname,index):
        name=catalog.catalog().get(item.module_id)
        row=layout.row(align=True);row.label(text=f'{index+1:02d} '+(name.title if name else item.module_id))
        row.prop(item,'width',text='m')


class MB02_OT_Action(bpy.types.Operator):
    bl_idname='mb02.action';bl_label='MB01 modüler işlem';bl_options={'REGISTER','UNDO'}
    action: StringProperty()
    def execute(self,context):
        p=context.scene.mb02
        try:
            if self.action=='DEFAULTS':
                spec=catalog.require(p.module_id);p.width=spec.default_width;p.height=spec.default_height
            elif self.action=='PRESET':
                apply_document(p,presets.example(p.family));p.width=4.5 if p.family=='HANGAR' else 3.6
            elif self.action=='ADD':
                contracts.ModuleInput(p.module_id,p.family,p.width,p.height,p.thickness,p.detail,p.door_open,style_of(p)).checked()
                if len(p.cells)>=32:raise ValueError('En fazla 32 hücre desteklenir.')
                c=p.cells.add();c.cell_id='BAY_'+uuid.uuid4().hex[:12];c.module_id=p.module_id;c.width=p.width;p.index=len(p.cells)-1
            elif self.action=='REMOVE':
                if p.cells:p.cells.remove(min(p.index,len(p.cells)-1));p.index=max(0,min(p.index,len(p.cells)-1))
            elif self.action in ('UP','DOWN'):
                target=p.index+(-1 if self.action=='UP' else 1)
                if 0<=p.index<len(p.cells) and 0<=target<len(p.cells):p.cells.move(p.index,target);p.index=target
            elif self.action in ('SINGLE','BUILD'):
                facade=facade_of(p,self.action=='SINGLE')
                override=str(disk_path(p.texture_root,False)) if p.texture_root else ''
                root,report=BT.build_facade(facade,tuple(context.scene.cursor.location),p.yaw,override)
                self.report({'INFO'},f"{report['cells']} hücre üretildi; eski yapılar değiştirilmedi.")
            elif self.action=='POSE':
                BT.set_door_pose(BT.root_for(context.active_object),p.door_open)
            elif self.action=='LOAD_ACTIVE':
                root=BT.root_for(context.active_object)
                if not root:raise ValueError('Modüler cephe kökünü veya bir parçasını seçin.')
                apply_document(p,contracts.from_document(json.loads(root['mb01_modular_document'])))
                p.texture_root=root.get('mb01_texture_root','')
            elif self.action=='SAVE':
                doc=contracts.to_document(facade_of(p))
                folder=disk_path(p.output_dir);path=folder/(p.facade_id+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:4]+'.json')
                path.write_text(json.dumps(doc,indent=2,ensure_ascii=False),encoding='utf-8');self.report({'INFO'},str(path))
            elif self.action=='LOAD':
                path=disk_path(p.plan_file,False)
                if path.stat().st_size>1048576:raise ValueError('Cephe JSON dosyası 1 MiB sınırını aşıyor.')
                facade=contracts.from_document(json.loads(path.read_text(encoding='utf-8')))
                apply_document(p,facade)
            elif self.action=='EXPORT':
                root=BT.root_for(context.active_object)
                if not root:raise ValueError('Aktif modüler cepheyi seçin.')
                folder=exporter.export_project(root,disk_path(p.output_dir));self.report({'INFO'},str(folder))
            else:raise ValueError('Unknown modular action.')
            return {'FINISHED'}
        except Exception as exc:
            from ..mb_common import write_error_log
            write_error_log(self,exc,block_name='MB01_Modular_Last_Error',log_prefix='MB01_Modular')
            return {'CANCELLED'}


def button(layout,label,action,icon='NONE'):
    op=layout.operator('mb02.action',text=label,icon=icon);op.action=action


class MB02_PT_Main(bpy.types.Panel):
    bl_idname='MB02_PT_Main';bl_label='MB01 / Modüler Mimari • alpha.1'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01';bl_options={'DEFAULT_CLOSED'}
    def draw(self,context):
        p=context.scene.mb02;l=self.layout
        l.label(text='14 hazır parça • tek kat düz cephe',icon='INFO')
        l.label(text='Tam bina üreticisinin yerine geçmez.')
        l.prop(p,'family');l.prop(p,'category');l.prop(p,'module_id')
        button(l,'Modül ölçülerini yükle','DEFAULTS','PRESET')
        l.prop(p,'width');l.prop(p,'height');l.prop(p,'thickness');l.prop(p,'detail')
        button(l,'Tek modülü 3D Cursor konumuna ekle','SINGLE','ADD')
        button(l,'Bu modülü cephe sırasına ekle','ADD','ADD')


class MB02_PT_Assembly(bpy.types.Panel):
    bl_idname='MB02_PT_Assembly';bl_label='Cephe sırası / preset';bl_parent_id='MB02_PT_Main'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01'
    def draw(self,context):
        p=context.scene.mb02;l=self.layout
        button(l,'Aile örnek sırasını yükle (listeyi değiştirir)','PRESET','PRESET')
        l.prop(p,'facade_id')
        l.template_list('MB02_UL_Cells','',p,'cells',p,'index',rows=6)
        row=l.row(align=True);button(row,'Yukarı','UP','TRIA_UP');button(row,'Aşağı','DOWN','TRIA_DOWN');button(row,'Sil','REMOVE','X')
        l.label(text=f'Toplam nominal genişlik: {sum(c.width for c in p.cells):.3f} m')
        l.prop(p,'target_width');l.prop(p,'yaw')
        button(l,'Cepheyi YENİ revizyon olarak oluştur','BUILD','MOD_BUILD')
        button(l,'Seçili cephe ayarlarını panele al','LOAD_ACTIVE','IMPORT')
        l.prop(p,'door_open');button(l,'Seçili cephenin kapı açısını uygula','POSE')
        l.label(text='Yeni üretim eski cepheyi silmez.')


class MB02_PT_Materials(bpy.types.Panel):
    bl_idname='MB02_PT_Materials';bl_label='Malzeme rolleri / aktarım';bl_parent_id='MB02_PT_Main'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01'
    def draw(self,context):
        p=context.scene.mb02;l=self.layout
        for name in ('palette','wall_material','frame_material','plinth_material','wear','texture_root'):l.prop(p,name)
        l.label(text='Hangar kabuğu boyalı metal rolünü korur.')
        l.prop(p,'output_dir');button(l,'Cephe planını JSON kaydet','SAVE','FILE_TICK')
        l.prop(p,'plan_file');button(l,'JSON planını panele yükle','LOAD','IMPORT')
        button(l,'Aktif cephe: FBX + UE manifest (deneysel)','EXPORT','EXPORT')
        l.label(text='Native Blender/UE testleri henüz bekliyor.',icon='INFO')


CLASSES=(MB02Cell,MB02Settings,MB02_UL_Cells,MB02_OT_Action,MB02_PT_Main,MB02_PT_Assembly,MB02_PT_Materials)


def register():
    registered=[]
    try:
        for cls in CLASSES:bpy.utils.register_class(cls);registered.append(cls)
        bpy.types.Scene.mb02=PointerProperty(type=MB02Settings)
    except Exception:
        if hasattr(bpy.types.Scene,'mb02'):del bpy.types.Scene.mb02
        for cls in reversed(registered):bpy.utils.unregister_class(cls)
        raise


def unregister():
    if hasattr(bpy.types.Scene,'mb02'):del bpy.types.Scene.mb02
    for cls in reversed(CLASSES):
        if hasattr(cls,'bl_rna'):bpy.utils.unregister_class(cls)
    _ENUM_CACHE.clear()

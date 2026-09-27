# SPDX-License-Identifier: MIT
"""Explicit small-asset kit panel; does not silently optimize the user's scene."""
import bpy,json
from bpy.props import EnumProperty,FloatProperty,StringProperty,PointerProperty
from ..modular.contracts import ModuleInput,Style
from ..modular.catalog import require
from .bundle import NEW_MODULES,compile_module
from . import blender_io

ITEMS=[(k,require(k).title,k) for k in NEW_MODULES]
class MB03KitSettings(bpy.types.PropertyGroup):
    module:EnumProperty(name='Yeni cephe modülü',items=ITEMS)
    width:FloatProperty(name='Aks genişliği / m',default=4.5,min=2.8,max=6.)
    height:FloatProperty(name='Cephe yüksekliği / m',default=7.6,min=6.,max=9.)
    thickness:FloatProperty(name='Kalınlık / m',default=.22,min=.16,max=.36)
    level:EnumProperty(name='Önizleme LOD',items=[('0','LOD0',''),('1','LOD1',''),('2','LOD2','')],default='0')
    palette:EnumProperty(name='Malzeme paleti',items=[('COASTAL','Coastal',''),('WOODLAND','Woodland',''),('URBAN','Urban','')])
    directory:StringProperty(name='Kit export klasörü',subtype='DIR_PATH',default='//MB03_GameKits')
    textures:StringProperty(name='Harici PBR üst klasörü',subtype='DIR_PATH',default='')


def settings(p):
    return ModuleInput(p.module,'HANGAR',p.width,p.height,p.thickness,'WORKING',0.,Style(p.palette,'ConcreteLight','SteelDark','Concrete',0.)).checked()

class MB03_OT_Kit(bpy.types.Operator):
    bl_idname='mb03.kit';bl_label='Modül oyun-kiti işlemi';bl_options={'REGISTER','UNDO'}
    action:EnumProperty(items=[('CHECK','Kontrol',''),('PREVIEW','Önizleme',''),('EXPORT','Export','')])
    def execute(self,context):
        p=context.scene.mb03_kit
        try:
            c=settings(p)
            if p.textures.startswith('//') and not bpy.data.filepath:raise ValueError('Göreli texture yolu için .blend kaydedin.')
            override=bpy.path.abspath(p.textures) if p.textures else ''
            if self.action=='CHECK':
                report=compile_module(c).report
                text=bpy.data.texts.new('MB03_GAMEKIT_REPORT');text.write(json.dumps(report,ensure_ascii=False,indent=2))
                if report['errors']:raise ValueError(str(report['errors']))
                self.report({'INFO'},'LOD/geometri kaynak kontrolü geçti; rapor Text Editor içinde.')
            elif self.action=='PREVIEW':
                blender_io.preview(c,int(p.level),override)
            elif self.action=='EXPORT':
                if p.directory.startswith('//') and not bpy.data.filepath:raise ValueError('Önce .blend kaydedin veya mutlak export yolu seçin.')
                if not p.directory:raise ValueError('Export klasörü seçin.')
                path=blender_io.export_kit(c,bpy.path.abspath(p.directory),override)
                self.report({'INFO'},str(path))
            return {'FINISHED'}
        except Exception as exc:
            from ..mb_common import write_error_log
            write_error_log(self,exc,block_name='MB03_LAST_ERROR',log_prefix='MB03')
            return {'CANCELLED'}

class MB03_PT_Kit(bpy.types.Panel):
    bl_idname='MB03_PT_kit';bl_label='Modül Oyun-Kiti | 0.3 alpha.1';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01';bl_options={'DEFAULT_CLOSED'}
    def draw(self,context):
        p=context.scene.mb03_kit;l=self.layout
        l.label(text='6 yeni modül • LOD0/1/2 • dinamik ışık')
        for k in ('module','width','height','thickness','palette','level'):l.prop(p,k)
        l.operator('mb03.kit',text='Kit geometri / LOD raporu',icon='CHECKMARK').action='CHECK'
        l.operator('mb03.kit',text='3D Cursor’da yeni LOD örneği',icon='MESH_CUBE').action='PREVIEW'
        l.prop(p,'textures');l.prop(p,'directory')
        l.operator('mb03.kit',text='FBX LOD + collision + socket kitini export et',icon='EXPORT').action='EXPORT'
        l.label(text='UE LOD bağlama manuel; native test gerekli.')

CLASSES=(MB03KitSettings,MB03_OT_Kit,MB03_PT_Kit)
def register():
    done=[]
    try:
        for cls in CLASSES:bpy.utils.register_class(cls);done.append(cls)
        bpy.types.Scene.mb03_kit=PointerProperty(type=MB03KitSettings)
    except Exception:
        for cls in reversed(done):bpy.utils.unregister_class(cls)
        raise

def unregister():
    if hasattr(bpy.types.Scene,'mb03_kit'):del bpy.types.Scene.mb03_kit
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)

# SPDX-License-Identifier: MIT
"""MB01 Studio: one consolidated, tabbed front panel over the four existing
sub-systems (Core, Hangar Studio, Modular, Game-Kit).

This is a UI-only layer: every field and button here reads/writes the exact
same Scene property groups (mb01 / mb01_hangar / mb02 / mb03_kit) and calls
the exact same operator id-names as the classic panels in ui.py,
hangar_studio/ui.py, modular/ui.py and game_ready/ui.py. Nothing about the
generators, exporters or QA logic changes - this only gives the four of them
one coherent Build / Materials / QA / Export front door instead of five
separately-scrolling accordion panels with duplicated fields.

The classic per-system panels are still registered (now collapsed by
default) as a full-detail fallback for anything not surfaced here.
"""
import bpy
from bpy.props import EnumProperty, PointerProperty

SYSTEMS = [
    ('CORE', 'MB01 Çekirdek', 'HQ / UNIT / HANGAR / SHELTER / RANGE_SET'),
    ('HANGAR', 'Hangar Studio', 'Ayrıntılı hangar üreticisi'),
    ('MODULAR', 'Modüler Mimari', 'Hazır cephe parçaları'),
    ('GAMEKIT', 'Oyun-Kiti', 'LOD/collision export kiti'),
]

TABS = (
    ('BUILD', 'Build', 'MOD_BUILD'),
    ('MATERIALS', 'Materials', 'MATERIAL'),
    ('QA', 'QA', 'CHECKMARK'),
    ('EXPORT', 'Export', 'EXPORT'),
)


class MB01StudioSettings(bpy.types.PropertyGroup):
    system: EnumProperty(name='Sistem', items=[(k, v, d) for k, v, d in SYSTEMS], default='CORE')
    tab: EnumProperty(name='Sekme', items=[(k, v, '') for k, v, _ in TABS], default='BUILD')


class MB01STUDIO_OT_SetTab(bpy.types.Operator):
    bl_idname = 'mb01studio.set_tab'
    bl_label = 'MB01 Studio sekmesi'
    tab: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.mb01studio.tab = self.tab
        return {'FINISHED'}


def _tab_bar(layout, p):
    row = layout.row(align=True)
    for key, label, icon in TABS:
        op = row.operator('mb01studio.set_tab', text=label, icon=icon, depress=(p.tab == key))
        op.tab = key


def _draw_core(l, context, tab):
    p = context.scene.mb01
    if tab == 'BUILD':
        l.prop(p, 'kind', expand=True)
        row = l.row(align=True);row.operator('mb01.apply_preset', icon='PRESET')
        l.prop(p, 'name');l.prop(p, 'width');l.prop(p, 'depth')
        l.prop(p, 'detail');l.prop(p, 'seed')
        l.operator('mb01.build', text='YENİ yapı oluştur', icon='ADD').rebuild = False
        l.separator();l.prop(p, 'active_root')
        l.operator('mb01.build', text='Aktif yapıyı yeniden üret', icon='FILE_REFRESH').rebuild = True
    elif tab == 'MATERIALS':
        l.prop(p, 'palette');l.prop(p, 'wear');l.prop(p, 'override')
    elif tab == 'QA':
        l.prop(p, 'active_root')
        l.operator('mb04.game_audit', text='Game-ready denetimi çalıştır', icon='CHECKMARK')
        l.operator('mb01.validation_report', text='Üretim raporunu aç', icon='TEXT')
    elif tab == 'EXPORT':
        l.prop(p, 'export_directory')
        l.operator('mb01.export', text='FBX + PBR + UE export', icon='EXPORT')
        op = l.operator('mb04.lod_bundle', text='LOD0/1/2 bundle export', icon='EXPORT');op.mode = 'CLASSIC_LOD'


def _draw_hangar(l, context, tab):
    p = context.scene.mb01_hangar
    if tab == 'BUILD':
        l.prop(p, 'preset_id');l.operator('mb01hg.preset', icon='PRESET')
        l.prop(p, 'name');l.prop(p, 'width');l.prop(p, 'depth');l.prop(p, 'bays')
        l.prop(p, 'roof_type');l.prop(p, 'detail')
        l.operator('mb01hg.build', text='YENİ hangar revizyonu', icon='MESH_CUBE')
        l.separator();l.prop(p, 'active_root')
        l.operator('mb01hg.load_active', text='Aktif hangarı yükle', icon='IMPORT')
    elif tab == 'MATERIALS':
        l.prop(p, 'palette');l.prop(p, 'wall_finish');l.prop(p, 'roof_finish')
        l.prop(p, 'wetness');l.prop(p, 'normal_strength');l.prop(p, 'texture_root')
    elif tab == 'QA':
        l.operator('mb01hg.validate', text='Geometri kurallarını kontrol et', icon='CHECKMARK')
    elif tab == 'EXPORT':
        l.prop(p, 'export_directory')
        l.operator('mb01hg.export', text='FBX + PBR + UE manifest', icon='EXPORT')


def _draw_modular(l, context, tab):
    p = context.scene.mb02
    if tab == 'BUILD':
        l.prop(p, 'family');l.prop(p, 'category');l.prop(p, 'module_id')
        l.prop(p, 'width');l.prop(p, 'height');l.prop(p, 'thickness');l.prop(p, 'detail')
        row = l.row(align=True)
        op = row.operator('mb02.action', text='Cepheye ekle', icon='ADD');op.action = 'ADD'
        op = row.operator('mb02.action', text='YENİ cephe üret', icon='MOD_BUILD');op.action = 'BUILD'
        l.label(text=f'{len(p.cells)} hücre • {sum(c.width for c in p.cells):.2f} m toplam')
    elif tab == 'MATERIALS':
        l.prop(p, 'palette');l.prop(p, 'wall_material');l.prop(p, 'frame_material')
        l.prop(p, 'plinth_material');l.prop(p, 'wear');l.prop(p, 'texture_root')
    elif tab == 'QA':
        l.label(text='Kurallar her ADD/BUILD adımında otomatik kontrol edilir.', icon='INFO')
        l.label(text='Ayrı bir denetim düğmesi yok; hata varsa işlem iptal edilir.')
    elif tab == 'EXPORT':
        l.prop(p, 'output_dir')
        op = l.operator('mb02.action', text='Aktif cepheyi export et', icon='EXPORT');op.action = 'EXPORT'


def _draw_gamekit(l, context, tab):
    p = context.scene.mb03_kit
    if tab == 'BUILD':
        l.prop(p, 'module');l.prop(p, 'width');l.prop(p, 'height');l.prop(p, 'thickness');l.prop(p, 'level')
        op = l.operator('mb03.kit', text='3D Cursor’da LOD önizle', icon='MESH_CUBE');op.action = 'PREVIEW'
    elif tab == 'MATERIALS':
        l.prop(p, 'palette');l.prop(p, 'textures')
    elif tab == 'QA':
        op = l.operator('mb03.kit', text='Kit geometri / LOD raporu', icon='CHECKMARK');op.action = 'CHECK'
    elif tab == 'EXPORT':
        l.prop(p, 'directory')
        op = l.operator('mb03.kit', text='FBX LOD + collision + socket kiti', icon='EXPORT');op.action = 'EXPORT'


_DRAW = {'CORE': _draw_core, 'HANGAR': _draw_hangar, 'MODULAR': _draw_modular, 'GAMEKIT': _draw_gamekit}


class MB01_PT_Studio(bpy.types.Panel):
    bl_idname = 'MB01_PT_studio'
    bl_label = 'MB01 Studio'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MB01'
    bl_order = -100

    def draw(self, context):
        p = context.scene.mb01studio
        l = self.layout
        header = l.row(align=True)
        header.label(text='0.4 alpha.1', icon='MOD_BUILD')
        header.label(text='native: beklemede')
        l.prop(p, 'system', expand=True)
        _tab_bar(l, p)
        box = l.box()
        _DRAW[p.system](box, context, p.tab)
        l.separator()
        l.label(text='Tüm ayrıntılı ayarlar için aşağıdaki klasik panelleri açın.', icon='INFO')


CLASSES = (MB01StudioSettings, MB01STUDIO_OT_SetTab, MB01_PT_Studio)


def register():
    registered = []
    try:
        for cls in CLASSES:
            bpy.utils.register_class(cls);registered.append(cls)
        bpy.types.Scene.mb01studio = PointerProperty(type=MB01StudioSettings)
    except Exception:
        for cls in reversed(registered):
            bpy.utils.unregister_class(cls)
        raise


def unregister():
    if hasattr(bpy.types.Scene, 'mb01studio'):
        del bpy.types.Scene.mb01studio
    for cls in reversed(CLASSES):
        if hasattr(cls, 'bl_rna'):
            bpy.utils.unregister_class(cls)

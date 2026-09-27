# SPDX-License-Identifier: MIT
"""Opt-in live inspections. Does not transform or delete user scene objects.
Creates an inspectable Text report only. Must be executed in Blender, not system Python.
"""
import bpy, json, time
from types import SimpleNamespace
from math import sqrt
from mathutils import Vector
from .meshqa import inspect_parts
from .contracts import Port, inspect_joint, dot


def root_for(ob):
    while ob:
        if ob.get('mb01_project_root'):return ob
        ob=ob.parent
    return None


def walk(root):
    yield root
    for child in root.children:yield from walk(child)


def scan_live(root):
    if root is None:raise ValueError('Bir MB01 kökü veya alt parçası seçin.')
    if bpy.context.mode!='OBJECT':raise ValueError('Denetim için Object Mode gerekli.')
    deps=bpy.context.evaluated_depsgraph_get();reports=[];issues=[];ids=set();seen_materials=set()
    for obj in walk(root):
        if obj.type!='MESH' or obj.get('mb01_owner')!=root.get('mb01_owner'):continue
        for mat in obj.data.materials:
            if mat and mat.name not in seen_materials:
                seen_materials.add(mat.name)
                if mat.get('mb01_recipe'):
                    from .resources import inspect_source_hashes
                    from .contracts import strict_json_loads
                    for issue in inspect_source_hashes(strict_json_loads(mat['mb01_recipe'])):
                        issues.append(dict(issue,material=mat.name))
        identity=obj.get('mb01_element',obj.name)
        if identity in ids:issues.append(dict(code='DUPLICATE_ELEMENT',severity='ERROR',part=obj.name))
        ids.add(identity)
        evaluated=obj.evaluated_get(deps)
        try:
            mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
            layer=mesh.uv_layers.get('UV0_Tile')
            p=SimpleNamespace(name=obj.name,vertices=[tuple(v.co) for v in mesh.vertices],
                faces=[tuple(f.vertices) for f in mesh.polygons],
                material_ids=[f.material_index for f in mesh.polygons],
                material_names=[m.name if m else '<missing>' for m in mesh.materials],
                smooth=[f.use_smooth for f in mesh.polygons],
                uvs=[[tuple(layer.data[k].uv) for k in f.loop_indices] for f in mesh.polygons] if layer else [])
            report=inspect_parts([p]);issues.extend(report['issues']);reports.append(report)
            if '<missing>' in p.material_names:issues.append(dict(code='MISSING_MATERIAL',severity='ERROR',part=obj.name))
        finally:evaluated.to_mesh_clear()
    if not reports:issues.append(dict(code='NO_OWNED_MESHES',severity='ERROR',part=root.name))
    return dict(schema='base01.native_mesh_qa/1',status='FAIL' if any(i['severity']=='ERROR' for i in issues) else ('WARNING' if issues else 'PASS'),
        blender_version=bpy.app.version_string,root=root.name,objects=len(reports),issues=issues,
        evaluated_geometry=True,geometry_changed=False,unreal_runtime_verified=False,records=reports,
        scope='Evaluated mesh attributes; not full collision, visual appearance or certification')


def port_from_object(obj):
    if obj is None or obj.type!='EMPTY':raise ValueError('İki port Empty nesnesi seçin.')
    mat=obj.matrix_world
    columns=[tuple(mat.to_3x3().col[i]) for i in range(3)]
    if mat.to_3x3().determinant()<=0 or any(abs(dot(v,v)-1)>1e-5 for v in columns) or any(abs(dot(columns[i],columns[j]))>1e-5 for i,j in ((0,1),(0,2),(1,2))):
        raise ValueError('Portta ölçek/shear/aynalanma var; bağlama öncesi kaynak dönüşümünü inceleyin.')
    data=json.loads(obj.get('mb01_data','{}'))
    parent=obj.parent;cfg=None
    while parent:
        if parent.get('sw01_meta'):
            cfg=json.loads(parent['sw01_meta']).get('config',{});break
        parent=parent.parent
    role=data.get('role')
    convention='OUTWARD'
    if not role:
        if 'pk01_width' in obj or cfg is not None:
            role='PEDESTRIAN'
            flow=obj.get('pk01_role','OUT' if obj.name.upper().endswith('OUT') else 'IN')
            convention='TRAVEL_IN' if flow=='IN' else 'OUTWARD'
        else:raise ValueError('Tanımlı MB01/PK01/SW01 portu değil; bilinmeyen yönü tahmin etmiyorum.')
    width=float(data.get('width',obj.get('pk01_width',(cfg or {}).get('width',0))))
    height=float(data.get('height',obj.get('pk01_height',(cfg or {}).get('height',0)))) if role=='PEDESTRIAN' else 0.
    owner=obj.get('mb01_owner') or (obj.parent.name if obj.parent else obj.name)
    return Port(obj.name,str(owner),role,tuple(mat.translation),columns[0],width,height,columns[2],convention,
                'walkway-v1' if role in ('PEDESTRIAN','PEDESTRIAN_OPENING') else 'aircraft-surface-v1').checked()


def publish(report):
    name='BASE01_QA_'+str(time.time_ns())
    block=bpy.data.texts.new(name);block.write(json.dumps(report,indent=2,ensure_ascii=False))
    bpy.context.scene['base01_last_report']=name
    return name


class BASE01_OT_LiveQA(bpy.types.Operator):
    bl_idname='base01.live_qa';bl_label='Seçili yapının gerçek mesh verisini denetle'
    def execute(self,context):
        try:
            report=scan_live(root_for(context.active_object));name=publish(report)
            self.report({'ERROR'} if report['status']=='FAIL' else {'INFO'},report['status']+' — '+name)
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


class BASE01_OT_Ports(bpy.types.Operator):
    bl_idname='base01.inspect_ports';bl_label='İki portun doğrudan birleşimini denetle'
    def execute(self,context):
        try:
            objects=list(context.selected_objects)
            if len(objects)!=2:raise ValueError('Tam iki bağlantı Empty nesnesi seçin.')
            report=inspect_joint(*(port_from_object(o) for o in objects));name=publish(report)
            self.report({'INFO'},report['status']+' — '+name+' (nesneler taşınmadı)')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


class BASE01_OT_SelectIssues(bpy.types.Operator):
    bl_idname='base01.select_issues';bl_label='Son rapordaki sorunlu parçaları seç'
    def execute(self,context):
        try:
            name=context.scene.get('base01_last_report','');text=bpy.data.texts.get(name)
            if not text:raise ValueError('Önce bir QA raporu oluşturun.')
            from .contracts import strict_json_loads
            report=strict_json_loads(text.as_string());names=set()
            for issue in report.get('issues',[]):
                if isinstance(issue,dict):
                    if issue.get('part'):names.add(issue['part'])
                    names.update(issue.get('parts',[]))
            matches=[o for o in context.view_layer.objects if o.name in names]
            if not matches:
                self.report({'INFO'},'Bu raporda seçilebilir geometri sorunu yok; Text raporunu inceleyin.');return {'FINISHED'}
            for ob in context.selected_objects:ob.select_set(False)
            for ob in matches:
                if not ob.hide_get():ob.select_set(True)
            context.view_layer.objects.active=matches[0]
            self.report({'INFO'},str(len(matches))+' parça bulundu. Gizli nesnelerin görünürlüğü korunur.');return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


class BASE01_PT_QA(bpy.types.Panel):
    bl_idname='BASE01_PT_qa';bl_label='BASE01 | Uyum ve kalite denetimi'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01'
    def draw(self,context):
        l=self.layout
        l.label(text='Salt denetim: geometriyi değiştirmez.')
        l.operator('base01.live_qa',icon='CHECKMARK')
        l.operator('base01.inspect_ports',icon='EMPTY_ARROWS')
        l.operator('base01.select_issues',icon='RESTRICT_SELECT_OFF')
        l.label(text='Port denetimi: bitişik uçlar, yol çizimi değil.')
        name=context.scene.get('base01_last_report','')
        if name:
            l.label(text='Rapor Text Editor içindedir:')
            l.label(text=name)

CLASSES=(BASE01_OT_LiveQA,BASE01_OT_Ports,BASE01_OT_SelectIssues,BASE01_PT_QA)

def register():
    registered=[]
    try:
        for cls in CLASSES:bpy.utils.register_class(cls);registered.append(cls)
    except Exception:
        for cls in reversed(registered):bpy.utils.unregister_class(cls)
        raise


def unregister():
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)

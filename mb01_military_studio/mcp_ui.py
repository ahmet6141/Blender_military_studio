# SPDX-License-Identifier: MIT
import bpy,json,traceback
from .assembly.blender_qa import root_for


def _active(context):
    ob=context.active_object
    if ob and ob.get('mb01_project_root'):return ob
    return root_for(ob)


class MB04_OT_AgentBrief(bpy.types.Operator):
    bl_idname='mb04.agent_brief';bl_label='Glonorce MCP inceleme brifi oluştur'
    def execute(self,context):
        try:
            from . import agent_api
            root=_active(context)
            if not root:raise ValueError('MB01 kökü veya alt parçasını seçin.')
            brief={'contract':agent_api.contract(),'root':root.name,'config':json.loads(root['mb01_config']),
                'example_execute_blender_code':f"from mb01_military_studio import agent_api; print(agent_api.audit({root.name!r}))"}
            name='MB01_MCP_BRIEF_'+root.get('mb01_owner','')[:8]
            t=bpy.data.texts.get(name) or bpy.data.texts.new(name);t.clear();t.write(json.dumps(brief,ensure_ascii=False,indent=2))
            context.window_manager.clipboard=brief['example_execute_blender_code']
            self.report({'INFO'},name+' oluşturuldu; audit çağrısı panoya kopyalandı.')
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'},str(exc)[:240]);return {'CANCELLED'}


class MB04_OT_GameAudit(bpy.types.Operator):
    bl_idname='mb04.game_audit';bl_label='Whole-building game-ready audit'
    def execute(self,context):
        try:
            from .game_ready.audit import publish
            root=_active(context)
            if not root:raise ValueError('MB01 kökü veya alt parçasını seçin.')
            name,report=publish(root)
            self.report({'ERROR'} if report['status']=='FAIL' else {'INFO'},report['status']+' — '+name)
            return {'FINISHED'}
        except Exception as exc:
            block=bpy.data.texts.get('MB04_LAST_ERROR') or bpy.data.texts.new('MB04_LAST_ERROR');block.write(traceback.format_exc())
            self.report({'ERROR'},str(exc)[:240]);return {'CANCELLED'}


class MB04_OT_LODBundle(bpy.types.Operator):
    bl_idname='mb04.lod_bundle';bl_label='Whole-building LOD/Nanite bundle export'
    mode:bpy.props.EnumProperty(items=[('CLASSIC_LOD','Classic LOD0/1/2','Semantic whole-building LOD bundle'),('NANITE_HERO','Nanite Hero','LOD0 hero mesh; Nanite is enabled manually in Unreal')],default='CLASSIC_LOD')
    def execute(self,context):
        try:
            from .game_ready.building_export import export_building_bundle
            from . import core
            root=_active(context)
            if not root:raise ValueError('MB01 root required.')
            cfg=core.Settings(**json.loads(root['mb01_config'])).checked()
            p=context.scene.mb01
            if p.export_directory.startswith('//') and not bpy.data.filepath:raise ValueError('Save the .blend first or use an absolute export directory.')
            dest=export_building_bundle(cfg,bpy.path.abspath(p.export_directory),root.get('mb01_texture_root',''),self.mode)
            self.report({'INFO'},str(dest));return {'FINISHED'}
        except Exception as exc:
            block=bpy.data.texts.get('MB04_LAST_ERROR') or bpy.data.texts.new('MB04_LAST_ERROR');block.write(traceback.format_exc())
            self.report({'ERROR'},str(exc)[:240]);return {'CANCELLED'}


class MB04_PT_MCP(bpy.types.Panel):
    bl_idname='MB04_PT_mcp';bl_label='AI / Glonorce MCP / Game-Ready';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='MB01';bl_options={'DEFAULT_CLOSED'}
    def draw(self,context):
        l=self.layout
        l.label(text='0.4 Agent API: deterministic high-level calls')
        l.operator('mb04.agent_brief',icon='TEXT')
        l.operator('mb04.game_audit',icon='CHECKMARK')
        op=l.operator('mb04.lod_bundle',text='Classic LOD0/1/2 bundle export',icon='EXPORT');op.mode='CLASSIC_LOD'
        op=l.operator('mb04.lod_bundle',text='Nanite Hero bundle export',icon='MESH_DATA');op.mode='NANITE_HERO'
        l.label(text='MCP review: MULTI Material screenshot → geometry gate → patch → recheck.')
        l.label(text='MCP server addondan bağımsız çalışır; execute_blender_code ile agent_api çağrılır.')

CLASSES=(MB04_OT_AgentBrief,MB04_OT_GameAudit,MB04_OT_LODBundle,MB04_PT_MCP)

def register():
    for cls in CLASSES:bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        if hasattr(cls,'bl_rna'):bpy.utils.unregister_class(cls)

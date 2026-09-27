# SPDX-License-Identifier: MIT
"""MB01 Military Building Studio. Install the complete ZIP through Preferences.
The regular Python geometry core can be imported without loading bpy.
"""
bl_info = {
    'name':'MB01 | Military Building Studio + Hangar Studio (0.4 alpha.1 MCP/CGI)',
    'author':'MB01 Project',
    'version':(0,4,1),
    'blender':(4,5,0),
    'location':'3D View > Sidebar > MB01',
    'description':'Parametric fictional HQ/hangar asset studio with CGI PBR, game-ready QA and Glonorce Blender MCP agent API',
    'category':'Add Mesh',
}

def register():
    from . import ui
    from .modular import ui as modular_ui
    from .hangar_studio import ui as hangar_ui
    from .assembly import blender_qa
    from .game_ready import ui as gamekit_ui
    from . import mcp_ui
    registered=[]
    try:
        for module in (ui, modular_ui, hangar_ui, blender_qa, gamekit_ui, mcp_ui):
            module.register();registered.append(module)
    except Exception:
        for module in reversed(registered):module.unregister()
        raise


def unregister():
    from . import ui
    from .modular import ui as modular_ui
    from .hangar_studio import ui as hangar_ui
    from .assembly import blender_qa
    from .game_ready import ui as gamekit_ui
    from . import mcp_ui
    mcp_ui.unregister()
    gamekit_ui.unregister()
    blender_qa.unregister()
    hangar_ui.unregister()
    modular_ui.unregister()
    ui.unregister()

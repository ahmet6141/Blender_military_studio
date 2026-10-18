# SPDX-License-Identifier: MIT
"""Role-specific PBR recipes. Reuses licensed MB01 procedural images; no scans claimed.
Wetness uses separate exposed slab recipes, not undocumented extra UV channels.
"""
from copy import deepcopy
from .. import materials


def recipes(config, override=''):
    c=config.checked()
    out=deepcopy(materials.recipes(c.palette,0.,override))
    for name,r in out.items():
        r['profile']='MB01_HANGAR_ALPHA2'
        r['normal_strength']=c.normal_strength
        if r['tag'] in ('Concrete','Plaster','Stone'):r['tile_size_m']=c.concrete_tile_m
        elif r['tag'] in ('CoatedSteel','Galvanized'):r['tile_size_m']=c.metal_tile_m
    out['Galvanized']['metallic']=1.0
    def clone(name,source,color=None,roughness=None):
        r=deepcopy(out[source]);r['name']=name
        if color is not None:r['color']=list(color)
        if roughness is not None:r['roughness']=roughness
        out[name]=r
        return r
    wallcols={'LIGHT':(.91,.93,.91),'OLIVE':(.27,.34,.28),'GRAPHITE':(.16,.205,.22)}
    roofcols={'OLIVE':(.23,.31,.27),'GRAPHITE':(.10,.145,.16),'SILVER':(.66,.69,.68)}
    clone('HG_Wall','RoofOlive',wallcols[c.wall_finish],.57)
    clone('HG_Roof','RoofOlive',roofcols[c.roof_finish],.49)
    clone('HG_RoofTrim','SteelDark',(.09,.13,.145),.43)
    clone('HG_Gate','RoofOlive',(.22,.30,.26) if c.palette!='URBAN' else (.19,.23,.245),.51)
    clone('HG_GateTrim','RoofOliveLight',(.29,.36,.32) if c.palette!='URBAN' else (.25,.29,.30),.48)
    # Identity sign: matte anthracite cabinet, brushed-aluminium bezel/standoffs, muted subtitle.
    clone('HG_SignFace','SteelDark',(.055,.065,.075),.30)
    clone('HG_Alu','Galvanized',(.80,.83,.85),.26)
    clone('HG_SignSub','White',(.66,.71,.72),.45)
    clone('HG_SignInk','SteelDark',(.022,.025,.028),.55)
    # ---- domain material blocks: add clones only under your own anchor ----------------
    # [GATE MATERIALS] names start with HG_Gate (texture kit set: Gates)


    # [ROOF MATERIALS] names start with HG_Roof (texture kit set: Roof)
    rc=out['HG_Roof']['color']
    # Folded seam heads catch the light; flashings are colour-matched coil (second batch).
    clone('HG_RoofSeam','HG_Roof',[min(1.,x*1.10) for x in rc],.42)
    clone('HG_RoofFlashing','HG_Roof',[x*.86 for x in rc],.45)
    # Interior liner tray (bright polyester) and translucent GRP rooflight sheet.
    clone('HG_RoofLiner','White',(.74,.76,.75),.62)
    lite=clone('HG_RoofLight','Glass',(.90,.92,.82),.40);lite['glass_transmission']=.40;lite['glass_ior']=1.52


    # [WALL MATERIALS] names start with HG_Wall (texture kit set: Cladding)


    # [DOOR MATERIALS] names start with HG_Door (texture kit set: Cladding)


    # ---- end of domain material blocks -----------------------------------------------
    # Surface roles never change the old materials. Variant changes are intentionally subtle.
    for exposed in (False,True):
        wet=c.wetness if exposed else 0.
        for i,scale in enumerate((.96,.99,1.02,1.045)):
            r=clone(f'HG_Concrete_{"EXPOSED" if exposed else "INDOOR"}_{i}','Concrete',
                    (scale*(1-.18*wet),scale*(1-.18*wet),scale*.99*(1-.18*wet)),.84*(1-wet)+.26*wet)
            r['wetness_applied_to_recipe']=wet
            r['surface_role']='exposed_apron' if exposed else 'covered_floor'
    out['Glass']['glass_transmission']=.65
    out['Glass']['glass_ior']=1.46
    out['LightWarm']['color']=[1.,.88,.70]
    out['LightWarm']['emission']=3.0
    return out


def create_blender_materials(recipe):
    result=materials.create_blender_materials(recipe)
    # This field participates in the stamp, so previous MB01 Glass cannot be changed.
    for key,mat in result.items():
        r=recipe[key]
        if r.get('glass_transmission') is not None:
            for node in mat.node_tree.nodes:
                if node.type=='BSDF_PRINCIPLED':
                    node.inputs['Transmission Weight'].default_value=r['glass_transmission']
                    node.inputs['IOR'].default_value=r['glass_ior']
    return result

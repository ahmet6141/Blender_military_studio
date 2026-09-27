# SPDX-License-Identifier: MIT
"""Immutable material recipes; normal/roughness/metal sources are always explicit."""
from pathlib import Path
import json,hashlib
ASSETS=Path(__file__).resolve().parent/'assets'

# Linear tints. Coatings are dielectric; exposed galvanized metal is metallic.
SPECS={
 'Concrete':('Concrete',(1.,1.,1.),.84,0,2.),
 'ConcreteLight':('Concrete',(1.20,1.19,1.18),.82,0,2.),
 'ConcreteDark':('Concrete',(.30,.33,.34),.82,0,1.6),
 'Plaster':('Plaster',(.95,.94,.90),.78,0,2.),
 'Stone':('Stone',(.22,.25,.25),.73,0,1.5),
 'SteelDark':('CoatedSteel',(.07,.10,.115),.37,0,1.2),
 'RoofOlive':('CoatedSteel',(.23,.31,.26),.44,0,1.2),
 'RoofOliveLight':('CoatedSteel',(.29,.37,.31),.46,0,1.2),
 'Galvanized':('Galvanized',(1.,1.,1.),.34,.95,1.),
 'Yellow':('CoatedSteel',(.95,.62,.12),.49,0,1.),
 'White':('CoatedSteel',(.93,.96,.95),.49,0,1.),
 'Red':('CoatedSteel',(.57,.10,.06),.44,0,1.),
 'Rubber':(None,(.014,.020,.022),.87,0,1.),
 'Joint':(None,(.065,.071,.074),.88,0,1.),
 'Interior':(None,(.024,.035,.040),.96,0,1.),
 'Blind':('Plaster',(.48,.48,.42),.83,0,2.),
 'Timber':('Timber',(.76,.62,.43),.63,0,1.5),
 'Glass':(None,(.14,.25,.29),.13,0,1.),
 'RoofMembrane':('Membrane',(.11,.12,.115),.9,0,2.),
 'Walkway':('Concrete',(.18,.31,.25),.84,0,2.),
 'Asphalt':('Asphalt',(1.,1.,1.),.93,0,2.),
 'Gravel':('Stone',(.32,.29,.23),.94,0,2.),
 'LightWarm':(None,(1.,.84,.56),.25,0,1.),
 'LightGreen':(None,(.10,.65,.24),.28,0,1.),
}

def recipes(palette='COASTAL',wear=.15,override=''):
    out={};override=Path(override).expanduser() if override else None
    if override and not override.is_dir():raise FileNotFoundError('External PBR root does not exist: '+str(override))
    for name,(tag,color,rough,metal,tile) in SPECS.items():
        col=list(color)
        if name in ('RoofOlive','RoofOliveLight'):
            if palette=='WOODLAND':col=[col[0]*.82,col[1]*.92,col[2]*.66]
            if palette=='URBAN':col=[sum(col)/3*.85]*3
        if name=='Plaster' and palette=='URBAN':col=[.92,.94,.96]
        r=dict(name=name,tag=tag,color=col,roughness=rough,metallic=metal,tile_size_m=tile,normal_strength=.28,
               emission=2.5 if name.startswith('Light') else 0.,glass=name=='Glass',wear=wear,textures={})
        if tag:
            folder=ASSETS/tag
            if override and (override/tag).is_dir():folder=override/tag
            for kind in ('BaseColor','ORM','NormalGL','NormalDX','Height'):
                p=folder/(tag+'_'+kind+'.png')
                if not p.is_file():raise FileNotFoundError('Incomplete PBR set: '+str(p))
                r['textures'][kind]=str(p)
        out[name]=r
    return out


def create_blender_materials(recipe):
    import bpy
    result={}
    for key,r in recipe.items():
        from .assembly.resources import fingerprint_recipe, managed_image
        r=fingerprint_recipe(r)
        stamp=hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:12]
        existing=next((m for m in bpy.data.materials if m.get('mb01_recipe_stamp')==stamp),None)
        if existing:result[key]=existing;continue
        mat=bpy.data.materials.new('M_MB01_'+key+'_'+stamp[:6]);mat.use_nodes=True
        mat['mb01_recipe_key']=key;mat['mb01_recipe_stamp']=stamp;mat['mb01_recipe']=json.dumps(r)
        mat.diffuse_color=(*[min(1.,x) for x in r['color']],1.)
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
        out=nodes.new('ShaderNodeOutputMaterial');out.location=(900,100)
        bs=nodes.new('ShaderNodeBsdfPrincipled');bs.location=(650,100);links.new(bs.outputs['BSDF'],out.inputs['Surface'])
        bs.inputs['Base Color'].default_value=(*r['color'],1.);bs.inputs['Metallic'].default_value=r['metallic'];bs.inputs['Roughness'].default_value=r['roughness']
        if r['glass']:
            bs.inputs['Transmission Weight'].default_value=.52;bs.inputs['IOR'].default_value=1.46
            bs.inputs['Coat Weight'].default_value=.35;bs.inputs['Coat Roughness'].default_value=.09
        if r['emission']:
            bs.inputs['Emission Color'].default_value=(*r['color'],1.);bs.inputs['Emission Strength'].default_value=r['emission']
        if r['textures']:
            uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UV0_Tile';uv.location=(-950,300)
            scale=nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=1/r['tile_size_m'];scale.location=(-760,300);links.new(uv.outputs['UV'],scale.inputs[0])
            tex={}
            for j,kind in enumerate(('BaseColor','ORM','NormalGL','Height')):
                image=managed_image(bpy,r['textures'][kind],kind,r['source_hashes'][kind])
                image.colorspace_settings.name='sRGB' if kind=='BaseColor' else 'Non-Color'
                n=nodes.new('ShaderNodeTexImage');n.name='MB01_'+kind;n.label=kind;n.image=image;n.extension='REPEAT';n.location=(-520,410-j*300)
                links.new(scale.outputs['Vector'],n.inputs['Vector']);tex[kind]=n
            tint=nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(*r['color'],1.);tint.location=(-210,500)
            links.new(tex['BaseColor'].outputs['Color'],tint.inputs[1])
            vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='SW01_Tint';vc.location=(-210,700)
            mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.location=(20,500)
            links.new(tint.outputs[0],mix.inputs[1]);links.new(vc.outputs['Color'],mix.inputs[2])
            split=nodes.new('ShaderNodeSeparateColor');split.mode='RGB';split.location=(-210,40);links.new(tex['ORM'].outputs['Color'],split.inputs[0])
            ao=nodes.new('ShaderNodeMixRGB');ao.blend_type='MULTIPLY';ao.inputs[0].default_value=1;ao.location=(250,500)
            links.new(mix.outputs[0],ao.inputs[1]);links.new(split.outputs['Red'],ao.inputs[2]);links.new(ao.outputs[0],bs.inputs['Base Color'])
            # Set mean roughness from recipe but retain the supplied roughness variation.
            rough=nodes.new('ShaderNodeMath');rough.operation='MULTIPLY';rough.inputs[1].default_value=min(1.2,r['roughness']+.18*float(r['wear']));rough.location=(200,10)
            links.new(split.outputs['Green'],rough.inputs[0]);links.new(rough.outputs[0],bs.inputs['Roughness'])
            # Source texture metal mask is not used for a painted surface's substrate.
            bs.inputs['Metallic'].default_value=r['metallic']
            normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=r['normal_strength'];normal.uv_map='UV0_Tile';normal.location=(60,-240)
            links.new(tex['NormalGL'].outputs['Color'],normal.inputs['Color'])
            bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.035;bump.location=(350,-220)
            links.new(tex['Height'].outputs['Color'],bump.inputs['Height']);links.new(normal.outputs['Normal'],bump.inputs['Normal']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
        result[key]=mat
    return result

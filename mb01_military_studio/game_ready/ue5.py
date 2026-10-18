# SPDX-License-Identifier: MIT
"""UE5 static-mesh conventions for the per-asset exporter: UCX_ convex collision
built from the generators' own per-primitive collision boxes, real per-asset LOD
meshes, and a unique UV1 lightmap channel.

Everything here works on temporary mesh copies inside the exporter's temp scene;
the user's source objects are never modified.
"""
import json
import bpy, bmesh
from ..vendor import as07_reference as A

UCX_MAX_HULLS = 48           # above this UE simple collision gets slow; fall back to complex-as-simple
LOD_MIN_TRIANGLES = 600      # smaller assets ship LOD0 only
LOD2_COLLAPSE_RATIO = .5
LIGHTMAP_UV = 'UV1_Lightmap'


def triangle_count(me):
    return sum(max(0, len(p.vertices) - 2) for p in me.polygons)


def collision_boxes(ob):
    raw = ob.get('mb01_collision_boxes')
    return json.loads(raw) if raw else []


def hull_parts(boxes, name):
    """One closed convex box MeshPart per generator collision box, in the asset's
    pivot-local frame (same frame as the exported render mesh)."""
    if not boxes or len(boxes) > UCX_MAX_HULLS:
        return []
    hulls = []
    for i, b in enumerate(boxes):
        p = A.MeshPart(f'{name}_Hull{i:02d}', 'COLLISION', 0.)
        p.box(tuple(b['center']), tuple(b['dims']), 'Collision', tuple(tuple(a) for a in b['axes']))
        hulls.append(p)
    return hulls


def _triangulated_copy(ob, scene):
    with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
        scene.view_layers[0].update()
        deps = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps), preserve_all_data_layers=True, depsgraph=deps)
    bm = bmesh.new();bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me);bm.free();me.update()
    return me


def lod_meshes(src, lod0_triangles, scene, name):
    """Returns [(lod_index, mesh), ...] for LOD1/LOD2 or [] for small assets.

    LOD1 drops the generators' edge-bevel modifier: the raw primitive geometry has
    an identical silhouette and UVs at roughly 1/8 of the evaluated triangles,
    which beats any decimation of the bevelled mesh. LOD2 collapses LOD1 further
    and is only kept when it actually reduces the count."""
    if src.type != 'MESH' or lod0_triangles < LOD_MIN_TRIANGLES:
        return []
    tmp = bpy.data.objects.new(name + '_LODSRC', src.data);scene.collection.objects.link(tmp)
    try:
        lod1 = _triangulated_copy(tmp, scene);t1 = triangle_count(lod1)
        out = []
        if 0 < t1 < lod0_triangles:
            out.append((1, lod1))
        else:
            bpy.data.meshes.remove(lod1);t1 = lod0_triangles
        dec = tmp.modifiers.new('MB01_LOD2', 'DECIMATE');dec.decimate_type = 'COLLAPSE'
        dec.ratio = LOD2_COLLAPSE_RATIO;dec.use_collapse_triangulate = True
        lod2 = _triangulated_copy(tmp, scene);t2 = triangle_count(lod2)
        if 0 < t2 < t1:
            out.append((2, lod2))
        else:
            bpy.data.meshes.remove(lod2)
        return out
    finally:
        bpy.data.objects.remove(tmp, do_unlink=True)


def _shelf_pack(boxes):
    """Row ('shelf') packing, O(n log n). Sets boxes[i][0:2] in place and returns
    the used (width, height). mathutils' box_pack_2d is quadratic and takes
    minutes for the tens of thousands of bevel-strip islands a hero mesh has."""
    area = sum(b[2] * b[3] for b in boxes)
    target = max((area * 1.08) ** .5, max(b[2] for b in boxes))
    order = sorted(range(len(boxes)), key=lambda i: -boxes[i][3])
    x = y = shelf = 0.0;width = 0.0
    for i in order:
        w, h = boxes[i][2], boxes[i][3]
        if x > 0 and x + w > target:
            y += shelf;x = 0.0;shelf = 0.0
        boxes[i][0] = x;boxes[i][1] = y
        x += w;shelf = max(shelf, h);width = max(width, x)
    return width, y + shelf


def add_lightmap_uv(me, scene=None):
    """Add a non-overlapping 0..1 UV1 for baked lighting; UV0_Tile stays channel 0.

    Pure data, no operators or edit-mode context: UV0_Tile is a metre-scaled planar
    projection per face, so every connected *coplanar* island already has a
    consistent, overlap-free chart in UV0. Those charts are shelf-packed and
    normalised to the unit square."""
    if me.uv_layers.get(LIGHTMAP_UV):
        return True
    uv0 = me.uv_layers.get('UV0_Tile')
    if uv0 is None or not me.polygons:
        return False
    bm = bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table()
    parent = list(range(len(bm.faces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]];i = parent[i]
        return i

    for e in bm.edges:
        fs = e.link_faces
        if len(fs) == 2 and fs[0].normal.dot(fs[1].normal) > .9995:
            a, b = find(fs[0].index), find(fs[1].index)
            if a != b:
                parent[b] = a
    islands = {}
    for f in bm.faces:
        islands.setdefault(find(f.index), []).append(f.index)
    bm.free()

    n = len(uv0.data);flat = [0.0] * (2 * n);uv0.data.foreach_get('uv', flat)
    loops = {p.index: list(p.loop_indices) for p in me.polygons}
    keys = [];boxes = [];largest = 0.0
    for key, faces in islands.items():
        us = [flat[2 * li] for fi in faces for li in loops[fi]];vs = [flat[2 * li + 1] for fi in faces for li in loops[fi]]
        u0, v0 = min(us), min(vs);w, h = max(us) - u0, max(vs) - v0
        keys.append((key, u0, v0));boxes.append([0.0, 0.0, w, h]);largest = max(largest, w, h)
    pad = max(largest * .01, 1e-4)
    for b in boxes:
        b[2] += pad;b[3] += pad
    width, height = _shelf_pack(boxes)
    scale = 1.0 / max(width, height, 1e-9)
    out = list(flat)
    for (key, u0, v0), b in zip(keys, boxes):
        ox, oy = b[0] + pad / 2, b[1] + pad / 2
        for fi in islands[key]:
            for li in loops[fi]:
                out[2 * li] = (ox + flat[2 * li] - u0) * scale
                out[2 * li + 1] = (oy + flat[2 * li + 1] - v0) * scale
    layer = me.uv_layers.new(name=LIGHTMAP_UV)
    layer.data.foreach_set('uv', out)
    me.uv_layers.active = uv0
    return True

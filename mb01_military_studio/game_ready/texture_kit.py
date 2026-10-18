"""Texture-painting kit for a built MB01 asset (hangars first).

A hangar is thousands of square metres of surface. One unique 0..1 square per material
gives 25-50 px/m at 4K, which is too blurry to paint. The kit therefore uses the three
layouts game environment art is built with, chosen per texture set:

TILING  (Cladding, Roof, Concrete)
    UV_Paint = world-metre planar layout / TILE_M: author one seamless TILE_M x TILE_M
    texture (4 m at 4K = 1024 px/m). Unique dirt/AO goes through UV_Mask.
TRIM    (Structure, Metal, Signage)
    Long members (rails, gutters, girders, columns, floor lines) become horizontal trim
    bands: V walks around the member's cross-section, U runs along its length and tiles,
    so a 48 m rail costs one band. Members with the same profile share a band. Everything
    else (plates, caps, letters, brackets) is packed uniquely in the space above the bands
    at the same texel density.
UNIQUE  (Gates, Glazing)
    Classic unique unwrap: smart projection + packing in 0..1.

Every set also gets UV_Mask (channel 1): a unique non-overlapping 0..1 layout of all its
faces for baking AO/curvature and painting grime masks.

Further rules: modifiers (bevels) are applied once per unique mesh; instanced modules keep
sharing one mesh and identical pieces inside a mesh (bolts, shoes, brackets) are detected,
so in UV_Paint their islands are stacked (paint one, all copies follow); polygons are
assigned to a texture set from their MB01 material recipe and get one TS_<set> material;
a MaterialID corner colour keeps the original recipe split for ID masks.

Outputs: FBX + .blend of the kit, per-set layout PNGs (full-size transparent wire overlay +
a coloured preview, for both channels) and texture_sets.json.
"""
import bpy, bmesh, json, colorsys, hashlib
from math import radians, sqrt, atan2
from pathlib import Path
from mathutils import Vector, Matrix
from ..blender_backend import descendants

TEXTURE_SETS = (   # ordered: first matching rule wins; keys are MB01 material recipe keys
    ('Signage',   'TRIM',   'Sign letters, number block, sign field, floor and safety markings',
                  lambda k: k.startswith('HG_Sign') or k in ('Yellow', 'White', 'Red')),
    ('Glazing',   'UNIQUE', 'Glass, window backing, light lenses',
                  lambda k: k in ('Glass', 'Interior', 'LightWarm', 'Blind') or k.startswith('HG_Glass')),
    ('Gates',     'UNIQUE', 'Main sliding gate leaves (panels, ribs, kick plates)',
                  lambda k: k.startswith('HG_Gate')),
    ('Roof',      'TILING', 'Roof skin, ridge, monitor, roof trims and bargeboards',
                  lambda k: k.startswith('HG_Roof')),
    ('Cladding',  'TILING', 'Wall cladding, facade modules, seams and reveals, personnel doors',
                  lambda k: k.startswith('HG_Wall') or k.startswith('HG_Door') or
                  k in ('RoofOlive', 'RoofOliveLight', 'Joint', 'Plaster', 'Stone', 'Membrane')),
    ('Structure', 'TRIM',   'Painted steel: portal frames, girders, jambs, headers, window frames',
                  lambda k: k in ('SteelDark',)),
    ('Concrete',  'TILING', 'Floor slabs, apron, plinths, loading dock, landings',
                  lambda k: k.startswith('HG_Concrete') or k.startswith('Concrete') or k in ('Asphalt',)),
    ('Metal',     'TRIM',   'Galvanised and aluminium hardware: rails, trolleys, gutters, pipes, rubber',
                  lambda k: True),
)
SET_NAMES = [s[0] for s in TEXTURE_SETS]
MODE = {s[0]: s[1] for s in TEXTURE_SETS}
CONTENTS = {s[0]: s[2] for s in TEXTURE_SETS}
TILE_M = 4.0                 # TILING: metres covered by one 0..1 texture
STRIP_MIN_LEN = 2.0          # TRIM: a member at least this long ...
STRIP_MAX_SECTION = 1.25     # ... with a cross-section no wider than this ...
STRIP_ASPECT = 5.0           # ... and length / section at least this, becomes a band
MAX_DENSITY = 1024.          # px/m cap for TRIM and UNIQUE sets
PACK_EFFICIENCY = .62        # expected island packing efficiency when sizing TRIM sets
BANDED = {}                  # mesh name -> faces laid out as trim bands (last TRIM set)


def recipe_key(mat):
    if mat is None:
        return 'None'
    key = mat.get('mb01_recipe_key')
    if key:
        return key
    name = mat.name
    if name.startswith('M_MB01_'):
        name = name[7:].rsplit('_', 1)[0]
    return name


def texture_set_for(key):
    return next(name for name, _, _, test in TEXTURE_SETS if test(key))


def id_color(key):
    """Stable, well separated colour per recipe key (ID masks and previews)."""
    h = int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)
    return colorsys.hsv_to_rgb((h % 360) / 360., .55 + (h >> 9) % 30 / 100., .80 + (h >> 17) % 18 / 100.)


# --------------------------------------------------------------------------- scene prep
def _bake_unique_meshes(objects):
    """Apply modifiers once per unique mesh; text becomes mesh; instancing is kept."""
    deps = bpy.context.evaluated_depsgraph_get()
    by_mesh = {}
    for ob in objects:
        by_mesh.setdefault(ob.data, []).append(ob)
    out = []
    for data, users in by_mesh.items():
        rep = users[0]
        slot_keys = [recipe_key(s.material) for s in rep.material_slots] or ['None']
        new = bpy.data.meshes.new_from_object(rep.evaluated_get(deps), preserve_all_data_layers=True, depsgraph=deps)
        new.name = 'TK_' + rep.name
        new['mb01_slot_keys'] = json.dumps(slot_keys)
        bm = bmesh.new();bm.from_mesh(new)         # glyph fills leave zero-area triangles
        bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
        flat = [f for f in bm.faces if f.calc_area() < 1e-8]    # collinear fill triangles: invisible
        if flat:
            bmesh.ops.delete(bm, geom=flat, context='FACES_ONLY')
        bm.to_mesh(new);bm.free()
        for a in [a.name for a in new.color_attributes]:
            new.color_attributes.remove(new.color_attributes[a])
        for ob in users:
            if ob.type == 'MESH':
                ob.modifiers.clear();ob.data = new
            else:
                mo = bpy.data.objects.new(ob.name + '_Mesh', new)
                for c in ob.users_collection:
                    c.objects.link(mo)
                mo.parent = ob.parent;mo.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
                mo.matrix_basis = ob.matrix_basis.copy()
                for k in ob.keys():
                    mo[k] = ob[k]
                bpy.data.objects.remove(ob)
                ob = mo
            for i in range(len(ob.material_slots)):
                ob.material_slots[i].link = 'DATA'
            out.append(ob)
    return out


def _set_material(name):
    mat = bpy.data.materials.get('TS_' + name) or bpy.data.materials.new('TS_' + name)
    mat['mb01_texture_set'] = name;mat['mb01_uv_mode'] = MODE[name]
    r, g, b = id_color('TS_' + name);mat.diffuse_color = (r, g, b, 1.)
    return mat


def _assign_sets(meshes):
    """TS_ materials, MaterialID colours, channels UV_Paint (0) + UV_Mask (1)."""
    used = {};tile = {}
    for me in meshes:
        keys = json.loads(me.get('mb01_slot_keys', '["None"]'))
        poly_keys = [keys[min(p.material_index, len(keys) - 1)] for p in me.polygons]
        sets = [texture_set_for(k) for k in poly_keys]
        order = [s for s in SET_NAMES if s in sets]
        me.materials.clear()
        for s in order:
            me.materials.append(_set_material(s))
        idx = {s: i for i, s in enumerate(order)}
        for p, s in zip(me.polygons, sets):
            p.material_index = idx[s]
        me['mb01_poly_sets'] = json.dumps(sets);me['mb01_poly_keys'] = json.dumps(poly_keys)
        attr = me.color_attributes.get('MaterialID') or me.color_attributes.new('MaterialID', 'BYTE_COLOR', 'CORNER')
        me.color_attributes.active_color = attr;me.color_attributes.render_color_index = 0
        for p, k in zip(me.polygons, poly_keys):
            r, g, b = id_color(k)
            for li in p.loop_indices:
                attr.data[li].color = (r, g, b, 1.)
        src = me.uv_layers.get('UV0_Tile') or (me.uv_layers[0] if len(me.uv_layers) else None)
        tile[me] = [tuple(d.uv) for d in src.data] if src else [(0., 0.)] * len(me.loops)
        while len(me.uv_layers):
            me.uv_layers.remove(me.uv_layers[0])
        me.uv_layers.new(name='UV_Paint');me.uv_layers.new(name='UV_Mask')
        me.uv_layers.active_index = 0;me.uv_layers[0].active_render = True
        for s in order:
            used.setdefault(s, []).append(me)
    return used, tile


# --------------------------------------------------------------------------- edit-mode ops
def _edit(reps, selection, layer):
    """Edit mode on reps with exactly the faces in selection[mesh] selected, on UV layer."""
    vl = bpy.context.view_layer
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for ob in vl.objects:
        ob.select_set(False)
    for ob in reps:
        ob.select_set(True);ob.data.uv_layers.active_index = layer
    vl.objects.active = reps[0]
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    for ob in reps:
        bm = bmesh.from_edit_mesh(ob.data);bm.faces.ensure_lookup_table()
        for f in bm.faces:
            f.select_set(False)
        for i in selection.get(ob.data, ()):
            bm.faces[i].select_set(True)
        bm.select_flush_mode();bmesh.update_edit_mesh(ob.data)


def _stack_duplicates(selection):
    """Identical pieces inside one mesh (bolts, shoes, brackets, ribs...) -> one island.

    Pieces are connected face groups; two are identical when every loop has the same
    position relative to the piece's minimum corner (1/10 mm). Returns the reduced
    selection to unwrap and the (mesh, source faces, duplicate faces) copies to apply.
    """
    reduced = {};copies = []
    for me, faces in selection.items():
        seen = {};keep = []
        for comp in _components(me, faces):
            comp = sorted(comp)
            vs = [me.vertices[v].co for f in comp for v in me.polygons[f].vertices]
            base = [min(c[i] for c in vs) for i in range(3)]
            sig = (len(comp), tuple(tuple(round(me.vertices[me.loops[li].vertex_index].co[i] - base[i], 4) for i in range(3))
                                    for f in comp for li in me.polygons[f].loop_indices))
            if sig in seen:
                copies.append((me, seen[sig], comp))
            else:
                seen[sig] = comp;keep += comp
        reduced[me] = keep
    return reduced, copies


def _apply_copies(copies, layer):
    for me, src, dst in copies:
        uv = me.uv_layers[layer].data
        for fs, fd in zip(src, dst):
            for ls, ld in zip(me.polygons[fs].loop_indices, me.polygons[fd].loop_indices):
                uv[ld].uv = uv[ls].uv


def _smart_pack(reps, selection, layer, margin, region=None, stack=False, packer='blender'):
    """Smart-project + pack the selected faces; region=(v0, v1) packs into a full-width
    horizontal strip with uniform scale (pre-stretch, pack without rotation, un-stretch).
    stack=True unwraps one copy of each repeated piece and stacks the others on it."""
    if not any(selection.get(ob.data) for ob in reps):
        return
    copies = []
    if stack:
        selection, copies = _stack_duplicates(selection)
    _edit(reps, selection, layer)
    bpy.ops.uv.smart_project(angle_limit=radians(66), margin_method='FRACTION', island_margin=margin,
                             area_weight=0., correct_aspect=True, scale_to_bounds=False)
    if region is None and packer == 'strip':
        region = (0., 1.)
    if region is None:
        bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, rotate_method='CARDINAL', scale=True,
                                merge_overlap=False, margin_method='FRACTION', margin=margin, shape_method='CONCAVE')
        bpy.ops.object.mode_set(mode='OBJECT')
        _apply_copies(copies, layer)
        return
    bpy.ops.object.mode_set(mode='OBJECT')
    _strip_pack(reps, selection, layer, region, margin)
    _apply_copies(copies, layer)


def _uv_islands(me, faces, layer):
    """UV-connected face groups among `faces` (shared edge with matching UVs)."""
    uv = me.uv_layers[layer].data;parent = {f: f for f in faces}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]];a = parent[a]
        return a
    edge = {}
    for f in faces:
        p = me.polygons[f];li = list(p.loop_indices)
        for k in range(len(li)):
            a, b = li[k], li[(k + 1) % len(li)]
            va, vb = me.loops[a].vertex_index, me.loops[b].vertex_index
            key = (min(va, vb), max(va, vb))
            ua, ub = tuple(round(c, 6) for c in uv[a].uv), tuple(round(c, 6) for c in uv[b].uv)
            sig = (ua, ub) if va < vb else (ub, ua)
            if key in edge and edge[key][1] == sig:
                ra, rb = find(f), find(edge[key][0])
                if ra != rb:
                    parent[ra] = rb
            else:
                edge[key] = (f, sig)
    groups = {}
    for f in faces:
        groups.setdefault(find(f), []).append(f)
    return list(groups.values())


def _strip_pack(reps, selection, layer, region, margin):
    """First-fit-decreasing-height packing of UV islands into the full-width strip
    v0..v1 at one uniform scale (binary search), islands turned 90 deg to lie flat.
    An island longer than the strip at that scale (a 48 m gutter) is shrunk to the strip
    width on its own instead of capping the scale of every other island."""
    v0, v1 = region;H = v1 - v0 - margin
    islands = []
    for ob in reps:
        me = ob.data;faces = selection.get(me, ())
        if not faces:
            continue
        uv = me.uv_layers[layer].data
        for grp in _uv_islands(me, list(faces), layer):
            loops = [li for f in grp for li in me.polygons[f].loop_indices]
            us = [uv[li].uv.x for li in loops];vs = [uv[li].uv.y for li in loops]
            w, h = max(us) - min(us), max(vs) - min(vs)
            if h > w:                       # exact 90 deg turn: (u, v) -> (v, -u)
                for li in loops:
                    x, y = uv[li].uv;uv[li].uv = (y, -x)
                w, h = h, w
            us = [uv[li].uv.x for li in loops];vs = [uv[li].uv.y for li in loops]
            islands.append([me, loops, min(us), min(vs), max(w, 1e-6), max(h, 1e-6)])
    if not islands:
        return

    def place(scale, commit=False):
        shelves = []                        # [y, height, x_used]
        top = 0.
        for it in sorted(islands, key=lambda it: -it[5] * min(scale, (1. - margin) / it[4])):
            k = min(scale, (1. - margin) / it[4]);w, h = it[4] * k + margin, it[5] * k + margin
            for sh in shelves:
                if sh[2] + w <= 1. and h <= sh[1]:
                    x, y = sh[2], sh[0];sh[2] += w;break
            else:
                y = top;x = 0.;shelves.append([top, h, w]);top += h
                if top > H:
                    return False
            if commit:
                me, loops, u0, vv0 = it[0], it[1], it[2], it[3];uv = me.uv_layers[layer].data
                for li in loops:
                    a, b = uv[li].uv
                    uv[li].uv = (x + margin / 2 + (a - u0) * k, v0 + margin / 2 + y + (b - vv0) * k)
        return True
    lo, hi = 0., 4. / sqrt(max(sum(it[4] * it[5] for it in islands), 1e-12))
    for _ in range(36):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if place(mid) else (lo, mid)
    place(lo, commit=True)


def _map_selected(reps, selection, layer, fn):
    for ob in reps:
        me = ob.data;uv = me.uv_layers[layer].data
        for i in selection.get(me, ()):
            for li in me.polygons[i].loop_indices:
                uv[li].uv = fn(*uv[li].uv)


# --------------------------------------------------------------------------- trim bands
def _components(me, faces):
    """Connected face groups (through shared edges) among the given face indices."""
    faces = set(faces);edge_faces = {}
    for i in faces:
        for ek in me.polygons[i].edge_keys:
            edge_faces.setdefault(ek, []).append(i)
    seen = set();out = []
    for start in faces:
        if start in seen:
            continue
        stack = [start];comp = []
        seen.add(start)
        while stack:
            f = stack.pop();comp.append(f)
            for ek in me.polygons[f].edge_keys:
                for g in edge_faces[ek]:
                    if g not in seen:
                        seen.add(g);stack.append(g)
        out.append(comp)
    return out


def _frame(points):
    """Principal axis A (canonical sign), cross-section basis e1, e2, centroid."""
    n = len(points);c = sum(points, Vector()) / n
    cov = [[0.] * 3 for _ in range(3)]
    for p in points:
        d = p - c
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    m = Matrix(cov);a = Vector((.577, .577, .577))
    for _ in range(48):
        b = m @ a
        if b.length < 1e-12:
            break
        a = b.normalized()
    k = max(range(3), key=lambda i: abs(a[i]))
    if a[k] < 0:
        a = -a
    ref = Vector((0., 0., 1.)) if abs(a.z) < .9 else Vector((1., 0., 0.))
    e1 = (ref - a * ref.dot(a)).normalized();e2 = a.cross(e1)
    return c, a, e1, e2


def _profile(me, side, c, a, e1, e2):
    """Walk the cross-section of a member. Returns (per-face {vertex: s}, perimeter, signature)."""
    key = lambda q: (round(q.dot(e1), 3), round(q.dot(e2), 3))
    seg = {}
    for f in side:
        vs = me.polygons[f].vertices;pts = {v: key(me.vertices[v].co - c) for v in vs}
        ks = list(dict.fromkeys(pts.values()))
        if len(ks) < 2:
            continue
        best = max(((p, q) for i, p in enumerate(ks) for q in ks[i + 1:]),
                   key=lambda pq: (pq[0][0] - pq[1][0]) ** 2 + (pq[0][1] - pq[1][1]) ** 2)
        seg[f] = (best, pts)
    adj = {}
    for f, ((p, q), _) in seg.items():
        adj.setdefault(p, []).append((f, q));adj.setdefault(q, []).append((f, p))
    length = lambda p, q: sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)
    svals = {};order = []
    if adj and all(len(v) <= 2 for v in adj.values()):
        todo = set(seg)
        while todo:
            ends = [k for k, v in adj.items() if len(v) == 1 and any(f in todo for f, _ in v)]
            pool = ends or [k for k, v in adj.items() if any(f in todo for f, _ in v)]
            start = min(pool, key=lambda k: (k[1], k[0]))
            cur = start;s = (svals and max(max(d.values()) for d in svals.values()) + .02) or 0.
            nxt = [(f, q) for f, q in adj[cur] if f in todo]
            if len(nxt) == 2:   # closed loop: go counter-clockwise
                nxt.sort(key=lambda fq: atan2(fq[1][1] - cur[1], fq[1][0] - cur[0]))
            while nxt:
                f, q = nxt[0];todo.discard(f)
                L = length(cur, q);svals[f] = {cur: s, q: s + L};order.append(round(L, 3));s += L;cur = q
                nxt = [(g, r) for g, r in adj[cur] if g in todo]
    else:                       # irregular profile: faces side by side
        s = 0.
        for f, ((p, q), _) in seg.items():
            L = length(p, q);svals[f] = {p: s, q: s + L};order.append(round(L, 3));s += L + .02
    per_face = {}
    for f, ((p, q), pts) in seg.items():
        sv = svals[f]
        per_face[f] = {v: sv.get(k, sv[min(sv, key=lambda kk: length(kk, k))]) for v, k in pts.items()}
    perimeter = max((max(d.values()) for d in svals.values()), default=0.)
    return per_face, perimeter, (round(perimeter, 2), tuple(order))


def _trim_plan(name, meshes):
    """Split a TRIM set into band members and unique faces."""
    members = [];unique = {}
    for me in meshes:
        sets = json.loads(me['mb01_poly_sets'])
        faces = [i for i, s in enumerate(sets) if s == name]
        uniq = []
        for comp in _components(me, faces):
            pts = [me.vertices[v].co.copy() for f in comp for v in me.polygons[f].vertices]
            c, a, e1, e2 = _frame(pts)
            along = [p.dot(a) for p in pts];L = max(along) - min(along)
            w = max(max(abs((p - c).dot(e1)) for p in pts), max(abs((p - c).dot(e2)) for p in pts)) * 2
            if L >= STRIP_MIN_LEN and w <= STRIP_MAX_SECTION and L >= STRIP_ASPECT * max(w, 1e-3):
                side = [f for f in comp if abs(me.polygons[f].normal.dot(a)) < .15]
                caps = [f for f in comp if f not in side]
                per_face, perim, sig = _profile(me, side, c, a, e1, e2)
                if perim > 0:
                    members.append(dict(mesh=me, faces=per_face, axis=a, centre=c, perimeter=perim, signature=sig))
                    uniq += caps + [f for f in side if f not in per_face]
                    continue
            uniq += comp
        unique[me] = uniq
    return members, unique


def _layout_trim(name, meshes, reps, resolution, margin):
    members, unique = _trim_plan(name, meshes)
    bands = {}
    for m in members:
        bands.setdefault(m['signature'], []).append(m)
    profiles = sorted(bands, key=lambda s: -s[0])
    sum_p = sum(bands[s][0]['perimeter'] for s in profiles)
    area_u = sum(sum(me.polygons[i].area for i in fs) for me, fs in unique.items())
    gap = 6. / resolution;avail = 1. - gap * (len(profiles) + 2)
    a = area_u / PACK_EFFICIENCY
    x = (-sum_p + sqrt(sum_p ** 2 + 4 * a * avail)) / (2 * a) if a > 0 else (avail / sum_p if sum_p else 1.)
    x = min(x, MAX_DENSITY / resolution)
    for attempt in range(4):
        rows, region = _place_bands(bands, profiles, x, gap, unique)
        if not region:
            break
        _smart_pack(reps, unique, 0, margin, region, stack=True)
        du = _density(name, meshes, 0, resolution, unique)[0] / resolution
        if abs(du - x) <= .08 * x or attempt == 3:
            break
        # Unique density grows ~ sqrt(region height): solve x = du * sqrt(h(x) / h_now).
        h_now = region[1] - region[0];lo, hi = 0., MAX_DENSITY / resolution
        for _ in range(40):
            mid = (lo + hi) / 2;h = 1. - gap - (gap + sum_p * mid + gap * len(profiles))
            if h > 0 and du * sqrt(h / h_now) > mid:
                lo = mid
            else:
                hi = mid
        x = lo
    band_rows = rows
    return dict(bands=band_rows, band_density_px_per_m=round(x * resolution, 1), unique_region=region and
                [round(region[0], 4), round(region[1], 4)], unique_faces=sum(len(f) for f in unique.values()),
                band_faces=sum(len(m['faces']) for m in members)), unique


def _place_bands(bands, profiles, x, gap, unique):
    v = gap;band_rows = [];BANDED.clear()
    for sig in profiles:
        group = bands[sig];h = group[0]['perimeter'] * x
        for m in group:
            me = m['mesh'];uv = me.uv_layers[0].data;c = m['centre'];ax = m['axis']
            BANDED.setdefault(me.name, set()).update(m['faces'])
            for f, sv in m['faces'].items():
                for li in me.polygons[f].loop_indices:
                    vi = me.loops[li].vertex_index
                    uv[li].uv = ((me.vertices[vi].co - c).dot(ax) * x, v + sv[vi] * x)
        band_rows.append(dict(v0=round(v, 5), v1=round(v + h, 5), perimeter_m=round(group[0]['perimeter'], 3),
                              members=len(group), facets=list(group[0]['signature'][1])))
        v += h + gap
    return band_rows, ((v, 1. - gap) if any(unique.values()) else None)


def _layout_tiling(name, meshes, tile):
    for me in meshes:
        sets = json.loads(me['mb01_poly_sets']);uv = me.uv_layers[0].data;t = tile[me]
        for p, s in zip(me.polygons, sets):
            if s == name:
                for li in p.loop_indices:
                    uv[li].uv = (t[li][0] / TILE_M, t[li][1] / TILE_M)


# --------------------------------------------------------------------------- stats / images
def _density(name, meshes, layer, resolution, faces=None):
    a3 = au = 0.
    for me in meshes:
        sets = json.loads(me['mb01_poly_sets']);uv = me.uv_layers[layer].data
        for p, s in zip(me.polygons, sets):
            if s != name or (faces is not None and p.index not in faces.get(me, ())):
                continue
            a3 += p.area;pts = [uv[i].uv for i in p.loop_indices]
            au += abs(sum(pts[i].x * pts[i - 1].y - pts[i - 1].x * pts[i].y for i in range(len(pts)))) / 2
    return (resolution * sqrt(au / a3) if a3 > 0 else 0.), a3, au


def _font(size):
    from PIL import ImageFont
    path = Path(__file__).resolve().parent.parent / 'assets' / 'fonts' / 'BigShoulders-Bold.ttf'
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def _draw(name, meshes, layer, folder, resolution, tag, bands=None):
    """Full-size transparent wire overlay + 1024 coloured preview of one UV channel."""
    from PIL import Image, ImageDraw
    R = 1024
    wire = Image.new('RGBA', (resolution, resolution), (0, 0, 0, 0));dw = ImageDraw.Draw(wire)
    prev = Image.new('RGB', (R, R), (22, 25, 28));dp = ImageDraw.Draw(prev)
    for i in range(1, 8):
        k = i * R // 8
        dp.line([(k, 0), (k, R)], fill=(36, 40, 44));dp.line([(0, k), (R, k)], fill=(36, 40, 44))
    for b in bands or ():
        y0, y1 = (1 - b['v1']), (1 - b['v0'])
        dp.rectangle([0, y0 * R, R - 1, y1 * R], fill=(58, 64, 70), outline=(235, 240, 242))
        dw.rectangle([0, y0 * resolution, resolution - 1, y1 * resolution], outline=(255, 255, 255, 255), width=2)
        s = 0.
        for L in b['facets'][:-1]:
            s += L;yy = 1 - (b['v0'] + s * (b['v1'] - b['v0']) / max(b['perimeter_m'], 1e-6))
            dp.line([(0, yy * R), (R, yy * R)], fill=(150, 158, 164));dw.line([(0, yy * resolution), (resolution, yy * resolution)], fill=(255, 255, 255, 160))
    for me in meshes:
        sets = json.loads(me['mb01_poly_sets']);uv = me.uv_layers[layer].data;col = me.color_attributes['MaterialID'].data
        for p, s in zip(me.polygons, sets):
            if s != name:
                continue
            if bands and p.index in BANDED.get(me.name, ()):
                continue   # band facets wrap in U: the band rectangle stands for them
            pts = [(uv[i].uv.x, 1. - uv[i].uv.y) for i in p.loop_indices]
            fill = tuple(int(255 * v) for v in col[p.loop_indices[0]].color[:3])
            dp.polygon([(x * R, y * R) for x, y in pts], fill=fill, outline=(235, 240, 242))
            dw.polygon([(x * resolution, y * resolution) for x, y in pts], outline=(255, 255, 255, 255))
    wire.save(folder / f'{tag}_{name}_{resolution}.png')
    prev.save(folder / f'{tag}_{name}_preview.png')


def _draw_tile_guide(name, folder, resolution):
    from PIL import Image, ImageDraw
    R = 1024
    img = Image.new('RGB', (R, R), (22, 25, 28));d = ImageDraw.Draw(img)
    for i in range(int(TILE_M * 4) + 1):
        k = round(i * R / (TILE_M * 4));major = i % 4 == 0
        c = (120, 128, 134) if major else (44, 48, 52)
        d.line([(k, 0), (k, R)], fill=c, width=2 if major else 1);d.line([(0, k), (R, k)], fill=c, width=2 if major else 1)
    f = _font(46);g = _font(30)
    d.text((28, 22), f'{name.upper()}  ·  SEAMLESS TILE', font=f, fill=(242, 182, 64))
    d.text((28, 78), f'1 tile = {TILE_M:g} m x {TILE_M:g} m   |   {resolution} px = {resolution / TILE_M:.0f} px/m   |   grid 1 m / 0.25 m',
           font=g, fill=(210, 216, 220))
    img.save(folder / f'UV_Paint_{name}_preview.png')


# --------------------------------------------------------------------------- entry point
def build_texture_kit(root, out_dir, resolution=4096, margin=.0015, stem=None):
    """Turn the built asset under `root` into a texture-painting kit in `out_dir`.

    Destructive for the scene objects it touches (modifiers applied, materials replaced):
    call it on a fresh build. Returns the summary also written to texture_sets.json.
    """
    folder = Path(out_dir);folder.mkdir(parents=True, exist_ok=True)
    stem = stem or root.name
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    objects = [o for o in descendants(root) if o.type in ('MESH', 'FONT') and not o.hide_render]
    objects = _bake_unique_meshes(objects)
    meshes = list({o.data for o in objects})
    used, tile = _assign_sets(meshes)
    rep_for = {}
    for o in objects:
        rep_for.setdefault(o.data, o)
    summary = dict(schema='mb01.texture_kit/0.2', asset=stem, resolution=resolution, tile_m=TILE_M,
                   uv_channels={'UV_Paint (0)': 'paint/author here; layout depends on the set mode',
                                'UV_Mask (1)': 'unique non-overlapping 0..1 per set: AO / curvature bakes, grime masks'},
                   modes={'TILING': f'seamless {TILE_M:g} m tile on world-metre planar UVs',
                          'TRIM': 'cross-section bands tiling in U (bottom) + unique islands (top), one density',
                          'UNIQUE': 'unique islands packed in 0..1'},
                   id_attribute='MaterialID: corner colour per original MB01 material recipe (ID mask bakes)',
                   instancing='UV_Paint: repeated modules and identical pieces share one island (stacked); UV_Mask never overlaps.',
                   texture_sets={})
    for name in SET_NAMES:
        if name not in used:
            continue
        group = used[name];reps = [rep_for[me] for me in group]
        allfaces = {me: [i for i, s in enumerate(json.loads(me['mb01_poly_sets'])) if s == name] for me in group}
        _smart_pack(reps, allfaces, 1, margin, packer='strip')       # UV_Mask
        info = dict(mode=MODE[name], contents=CONTENTS[name], unique_meshes=len(group),
                    objects=sum(1 for o in objects if name in json.loads(o.data['mb01_poly_sets'])))
        bands = None
        if MODE[name] == 'TILING':
            _layout_tiling(name, group, tile)
            info['paint_density_px_per_m'] = round(resolution / TILE_M, 1)
            _draw_tile_guide(name, folder, resolution)
        elif MODE[name] == 'TRIM':
            plan, unique = _layout_trim(name, group, reps, resolution, margin)
            bands = plan['bands'];info.update(plan)
            info['paint_density_px_per_m'] = plan['band_density_px_per_m']
            info['unique_region_density_px_per_m'] = round(_density(name, group, 0, resolution, unique)[0], 1)
        else:
            _smart_pack(reps, allfaces, 0, margin, stack=True)
            info['paint_density_px_per_m'] = round(_density(name, group, 0, resolution)[0], 1)
        mdens, a3, _ = _density(name, group, 1, resolution)
        info['mask_density_px_per_m'] = round(mdens, 1);info['unique_surface_m2'] = round(a3, 1)
        recipes = set()
        for me in group:
            recipes |= {k for k in json.loads(me['mb01_poly_keys']) if texture_set_for(k) == name}
        info['material_ids'] = {k: '#%02x%02x%02x' % tuple(int(255 * v) for v in id_color(k)) for k in sorted(recipes)}
        if MODE[name] != 'TILING':
            _draw(name, group, 0, folder, resolution, 'UV_Paint', bands)
        _draw(name, group, 1, folder, resolution, 'UV_Mask')
        summary['texture_sets'][name] = info
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    for o in objects:
        o.select_set(True)
    root.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(folder / f'{stem}_texture_kit.fbx'), use_selection=True,
                             object_types={'MESH', 'EMPTY'}, apply_unit_scale=True, mesh_smooth_type='FACE',
                             use_mesh_modifiers=False, add_leaf_bones=False, bake_anim=False, path_mode='STRIP',
                             axis_forward='-Z', axis_up='Y', colors_type='SRGB')
    bpy.ops.wm.save_as_mainfile(filepath=str(folder / f'{stem}_texture_kit.blend'), copy=True, compress=True)
    (folder / 'texture_sets.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    return summary

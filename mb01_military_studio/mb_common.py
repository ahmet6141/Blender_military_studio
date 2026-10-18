# SPDX-License-Identifier: MIT
"""Shared, dependency-light helpers used across the MB01 sub-systems (core,
Hangar Studio, Modular, Game-Kit). Pure Python only — no bpy import here, so
this module stays importable and unit-testable outside Blender.
"""


def canonical(v):
    """MB01's fixed world-axis remap: generator space (x, y, z) -> Blender
    scene space. Every sub-system shares this exact mapping; keep one copy so
    it can never drift between core.py, modular/geometry.py and callers that
    reach it through either module (core.canonical / modular.geometry.canonical)."""
    return (v[1], -v[0], v[2])


def _newell_normal(points):
    nx = ny = nz = 0.0
    for i in range(len(points)):
        x1, y1, z1 = points[i];x2, y2, z2 = points[(i + 1) % len(points)]
        nx += (y1 - y2) * (z1 + z2);ny += (z1 - z2) * (x1 + x2);nz += (x1 - x2) * (y1 + y2)
    length = (nx * nx + ny * ny + nz * nz) ** .5
    return (nx / length, ny / length, nz / length) if length > 1e-18 else (0.0, 0.0, 0.0)


def _polygon_area_2d(uv):
    a = 0.0
    for i in range(len(uv)):
        x1, y1 = uv[i];x2, y2 = uv[(i + 1) % len(uv)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def _polygon_area_3d(points):
    n = _newell_normal(points)
    if n == (0.0, 0.0, 0.0):
        return 0.0
    sx = sy = sz = 0.0
    for i in range(1, len(points) - 1):
        ax, ay, az = [points[i][k] - points[0][k] for k in range(3)]
        bx, by, bz = [points[i + 1][k] - points[0][k] for k in range(3)]
        sx += ay * bz - az * by;sy += az * bx - ax * bz;sz += ax * by - ay * bx
    return abs(sx * n[0] + sy * n[1] + sz * n[2]) / 2


def polish_part(part, stretch_tolerance=.005):
    """Game-mesh topology/UV pass applied to every generated part before it
    reaches Blender:

    * n-gon faces (cylinder/pipe end caps) become triangle fans, so the mesh is
      quads and triangles only and the bevel modifier never sees an n-gon;
    * faces whose metre-planar UV chart is stretched (any face not aligned to a
      world axis: pitched rafters, standing seams, downpipes, arch skins) get a
      true planar projection in the face's own plane - same metre scale, zero
      stretch, continuous across coplanar neighbours; deliberately authored
      charts (roof skins) already have ratio 1 and are left alone;
    * all faces are smooth-shaded; blender_backend.mesh_for marks edges above
      40 degrees sharp, so boxes stay crisp while 16-sided pipes read as round.
    """
    faces, uvs, mats, smooth = [], [], [], []
    for face, uv, mat in zip(part.faces, part.uvs, part.material_ids):
        pts = [part.vertices[j] for j in face]
        area3 = _polygon_area_3d(pts)
        if area3 > 1e-14 and abs(_polygon_area_2d(uv) / area3 - 1.0) > stretch_tolerance:
            n = _newell_normal(pts)
            if abs(n[2]) < .999:
                ux, uy, uz = -n[1], n[0], 0.0        # cross((0,0,1), n): horizontal tangent
                l = (ux * ux + uy * uy) ** .5;ux, uy = ux / l, uy / l
                vx, vy, vz = n[1] * uz - n[2] * uy, n[2] * ux - n[0] * uz, n[0] * uy - n[1] * ux   # cross(n, u)
                uv = [(p[0] * ux + p[1] * uy, p[0] * vx + p[1] * vy + p[2] * vz) for p in pts]
        if len(face) > 4:
            for i in range(1, len(face) - 1):
                faces.append((face[0], face[i], face[i + 1]));uvs.append([uv[0], uv[i], uv[i + 1]])
                mats.append(mat);smooth.append(True)
        else:
            faces.append(tuple(face));uvs.append(list(uv));mats.append(mat);smooth.append(True)
    part.faces, part.uvs, part.material_ids, part.smooth = faces, uvs, mats, smooth
    return part


def bevel_segments(part, detail):
    """Edge-bevel segment count for a generated part.

    Multi-segment bevels are only safe on all-quad box assemblies. On prism,
    arch and cylinder primitives (any non-quad face: I-beam and arch-rib end
    caps, pipe caps) Blender's bevel collapses the middle ring's UVs into
    zero-area faces, which the mesh QA rightly rejects and which blocked the
    HANGAR/SHELTER exports. Those parts get a single segment at every detail
    level; the visual difference at 4-8 mm is nil, the triangle saving is not.
    """
    if detail == 'DRAFT' or part.bevel <= 0:
        return 0
    if any(len(face) != 4 for face in part.faces):
        return 1
    # HERO used 3 segments; on 4-5 mm bevels that is invisible, and where two boxes of
    # one part meet (wall apertures, paver grids) the third ring degenerates into
    # zero-area UV faces. Two segments are the clean maximum.
    return 2


def write_error_log(op, exc, *, block_name, log_prefix):
    """Write the current exception's traceback to a named Blender Text
    block and surface a short message on the operator. Shared by every
    sub-system's operator error handling so the pattern (and its behaviour)
    stays identical instead of being re-typed per module.

    Imports bpy/traceback lazily so this module itself stays bpy-free.
    """
    import bpy, traceback
    text = traceback.format_exc()
    print('[' + log_prefix + ' ERROR]\n' + text)
    block = bpy.data.texts.get(block_name) or bpy.data.texts.new(block_name)
    block.write('\n' + text)
    op.report({'ERROR'}, str(exc)[:240])

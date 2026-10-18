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
    return 3 if detail == 'HERO' else 2


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

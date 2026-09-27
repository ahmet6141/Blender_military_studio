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

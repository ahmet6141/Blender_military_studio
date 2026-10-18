# SPDX-License-Identifier: MIT
"""Keyframed door animation for MB01 roots (Hangar Studio and legacy families).

Every door object already carries its motion contract in `mb01_door`
(closed/opened pivot, hinge angle, channel, telescopic track). This module turns
that contract into real Blender F-curves - no new geometry, no change to the
contract - and can bake the result to an animated FBX for DCC interchange. In
Unreal the same contract drives a Blueprint timeline; the FBX is a preview and
cinematic deliverable, not a runtime door system.
"""
import json
import bpy
from ..blender_backend import descendants

ACTION_PREFIX = 'MB01_Doors_'


def _doors(root):
    for ob in descendants(root):
        if ob.get('mb01_door') and not ob.get('mb01_keep'):
            yield ob, json.loads(ob['mb01_door'])


def _pose(ob, d, t):
    ob.location = [a * (1 - t) + b * t for a, b in zip(d['closed'], d['opened'])]
    ob.rotation_euler.z = d.get('angle', 0.) * t


def animate_doors(root, start=1, frames=96, stagger=.22, hold=24, loop=True, interpolation='BEZIER'):
    """Keyframe closed -> open (-> hold -> closed when loop) for every door under root.

    Telescopic gate leaves start one after another (track 0, nearest the wall,
    first) and all arrive together, which reads as the nested leaves pushing each
    other along the rails. Personnel doors swing about their hinge pivot.
    Returns a summary dict that is also stored on the root as mb01_animation."""
    if root is None or not root.get('mb01_project_root'):
        raise ValueError('MB01 kökü gerekli.')
    if frames < 8:
        raise ValueError('En az 8 kare gerekli.')
    scene = bpy.context.scene
    doors = list(_doors(root))
    if not doors:
        raise ValueError('Bu yapıda animasyonlu kapı yok.')
    tracks = max([d.get('track', 0) for _, d in doors] + [0]) + 1
    end_open = start + frames
    end = end_open + hold + frames if loop else end_open
    for ob, d in doors:
        ob.animation_data_clear()
        delay = int(round(d.get('track', 0) * stagger * frames / max(1, tracks - 1))) if d.get('track') is not None and tracks > 1 else 0
        keys = [(start, 0.), (start + delay, 0.), (end_open, 1.)]
        if loop:
            keys += [(end_open + hold, 1.), (end - delay, 0.), (end, 0.)]
        for frame, t in keys:
            _pose(ob, d, t)
            ob.keyframe_insert('location', frame=frame)
            if d.get('angle'):
                ob.keyframe_insert('rotation_euler', index=2, frame=frame)
        action = ob.animation_data.action
        action.name = ACTION_PREFIX + ob.name
        for fc in _fcurves(action):
            for kp in fc.keyframe_points:
                kp.interpolation = interpolation
        # rest at the closed pose so the asset exports in its canonical state
        _pose(ob, d, 0.)
    scene.frame_start, scene.frame_end = start, end
    scene.frame_set(start)
    summary = dict(schema='mb01.door_animation/1', doors=len(doors), tracks=tracks, start=start, open_at=end_open, end=end,
                   loop=loop, fps=scene.render.fps, interpolation=interpolation,
                   note='F-curves from the mb01_door contract; Unreal drives the same contract with a Blueprint timeline.')
    root['mb01_animation'] = json.dumps(summary)
    return summary


def _fcurves(action):
    # Blender 5 slotted actions keep F-curves in layers/strips; 4.x exposes action.fcurves.
    if getattr(action, 'fcurves', None):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out


def clear_door_animation(root):
    for ob, d in _doors(root):
        ob.animation_data_clear();_pose(ob, d, d.get('open_fraction', 0.))
    if 'mb01_animation' in root:
        del root['mb01_animation']


def pose_at(root, frame):
    """World-space door locations at a frame (used by tests and the QA report)."""
    scene = bpy.context.scene;old = scene.frame_current;scene.frame_set(frame)
    out = {ob.name: (tuple(ob.matrix_world.translation), ob.rotation_euler.z) for ob, _ in _doors(root)}
    scene.frame_set(old)
    return out


def export_door_animation(root, filepath):
    """Bake the keyed doors (plus the static shell for context) to one animated FBX."""
    if not root.get('mb01_animation'):
        raise ValueError('Önce kapı animasyonu oluşturun.')
    objects = [ob for ob in descendants(root) if ob.type == 'MESH' and ob.get('mb01_owner') == root.get('mb01_owner')]
    scene = bpy.context.scene
    for ob in scene.objects:
        ob.select_set(False)
    for ob in objects:
        ob.select_set(True)
    scene.view_layers[0].objects.active = objects[0]
    result = bpy.ops.export_scene.fbx(filepath=str(filepath), use_selection=True, object_types={'MESH'},
                                      global_scale=1., apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                                      axis_forward='-Y', axis_up='Z', use_space_transform=True, bake_space_transform=False,
                                      use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=True, add_leaf_bones=False,
                                      bake_anim=True, bake_anim_use_all_bones=False, bake_anim_use_nla_strips=False,
                                      bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
                                      bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='AUTO')
    if 'FINISHED' not in result:
        raise RuntimeError('Animated FBX export failed.')
    return filepath

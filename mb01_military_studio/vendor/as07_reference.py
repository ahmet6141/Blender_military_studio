# SPDX-License-Identifier: MIT
# -*- coding: utf-8 -*-
"""
AS07 | PARAMETRIC AIRCRAFT PARKING SHELTER
=======================================
Original fictional environment asset. Not a construction / structural design.

BLENDER: Scripting > Open > select this file > Run Script (Alt+P).
The generator creates a NEW scene. Existing scenes/objects are not deleted.
No downloads, paid add-ons, third-party Python packages, or external textures.

Target API: Blender 4.2+; use a current 4.5 LTS build as the baseline.
Blender runtime and Unreal import have NOT been tested in the authoring runtime.
The dependency-free geometry core can be tested with ordinary Python:
    python AS07_Shelter_Generator.py --self-test

Only change CONFIG below. Units are metres. Entrance faces -Y, roof apex is +Z.
UV0_Tile = repeatable, metre-scaled surface UVs (intentional overlaps).
Optional UV1_Packed = automatic per-object Smart UV Project, NOT artist-authored UVs.
Procedural Blender shaders are NOT converted to Unreal shaders by FBX.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

# ----------------------------- USER SETTINGS -------------------------------
CONFIG = {
    "span": 24.0,                    # nominal frame centre-to-centre width
    "depth": 32.0,
    "eave_height": 4.8,
    "roof_rise": 4.2,
    "bay_count": 8,
    "sidewall_height": 2.3,
    "wall_thickness": 0.32,
    "apron_front": 8.0,
    "apron_side": 2.0,
    "apron_back": 2.0,
    "detail": "HIGH",                 # PREVIEW / HIGH / CINEMATIC
    "roof_arc_segments": 72,            # HIGH base; detail preset scales this
    "roof_seam_spacing": 1.0,
    "door_open_degrees": 12.0,          # rear personnel door, not aircraft gates
    "add_service_props": True,
    "add_louvers": True,
    "add_fasteners": True,
    "add_signage": True,
    "add_practical_lights": True,
    "create_packed_uv": False,           # True: slower, automatic UV1_Packed
    "bevel_segments": 3,
    "bevel_width": 0.008,
    "render_engine": "CYCLES",          # CYCLES / EEVEE
    "render_samples": 96,
    "resolution_x": 1600,
    "resolution_y": 1100,
    "render_now": False,                # no automatic rendering by default
    "save_blend": False,                # no automatic saving by default
    "export_fbx": False,                # opt-in; see README for limitations
    "export_glb": False,                # flat PBR factors; not full node shaders
    "output_directory": "",            # empty => ~/AS07_Output/<timestamp>/
    "seed": 7,                         # reserved in metadata for reproducibility
}

EPS = 1.0e-9
VERSION = "1.0.0"
MATERIALS = {
    # Values are artist-selected linear RGB, not measured reflectance data.
    "Concrete": {"color": (0.36, 0.385, 0.38), "roughness": 0.82, "metallic": 0.0, "noise": 2.5, "bump": 0.004},
    "ConcreteLight": {"color": (0.48, 0.495, 0.465), "roughness": 0.80, "metallic": 0.0, "noise": 2.0, "bump": 0.003},
    "SteelDark": {"color": (0.055, 0.073, 0.078), "roughness": 0.34, "metallic": 0.72, "noise": 7.0, "bump": 0.0004},
    "RoofOlive": {"color": (0.18, 0.22, 0.205), "roughness": 0.42, "metallic": 0.55, "noise": 4.0, "bump": 0.0006},
    "RoofOliveLight": {"color": (0.205, 0.25, 0.23), "roughness": 0.45, "metallic": 0.50, "noise": 4.0, "bump": 0.0006},
    "Galvanized": {"color": (0.44, 0.49, 0.51), "roughness": 0.30, "metallic": 0.88, "noise": 35.0, "bump": 0.00025},
    "Yellow": {"color": (0.73, 0.43, 0.065), "roughness": 0.54, "metallic": 0.12, "noise": 12.0, "bump": 0.00025},
    "White": {"color": (0.71, 0.735, 0.685), "roughness": 0.61, "metallic": 0.05, "noise": 11.0, "bump": 0.0002},
    "Rubber": {"color": (0.021, 0.026, 0.025), "roughness": 0.83, "metallic": 0.0, "noise": 14.0, "bump": 0.0004},
    "Red": {"color": (0.43, 0.055, 0.035), "roughness": 0.38, "metallic": 0.35, "noise": 8.0, "bump": 0.0004},
    "Walkway": {"color": (0.12, 0.19, 0.175), "roughness": 0.78, "metallic": 0.0, "noise": 6.0, "bump": 0.0005},
    "Asphalt": {"color": (0.072, 0.083, 0.083), "roughness": 0.91, "metallic": 0.0, "noise": 20.0, "bump": 0.004},
    "Gravel": {"color": (0.18, 0.17, 0.14), "roughness": 0.95, "metallic": 0.0, "noise": 13.0, "bump": 0.01},
    "LightWarm": {"color": (0.92, 0.81, 0.60), "roughness": 0.27, "metallic": 0.0, "emission": 5.0},
    "LightGreen": {"color": (0.03, 0.70, 0.24), "roughness": 0.35, "metallic": 0.0, "emission": 2.0},
}

# -------------------- PURE PYTHON GEOMETRY / TESTABLE CORE ------------------
def add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def mul(a, s):
    return tuple(v * s for v in a)


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    n = math.sqrt(dot(a, a))
    if n < EPS:
        raise ValueError("Cannot normalize a zero-length vector.")
    return mul(a, 1.0 / n)


def local_to_world(p, c, axes):
    return tuple(c[i] + sum(p[j] * axes[j][i] for j in range(3)) for i in range(3))


def euler_axes(rx=0.0, ry=0.0, rz=0.0):
    """Column vectors of Rz * Ry * Rx, angles in radians."""
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return ((cz * cy, sz * cy, -sy), (cz * sy * sx - sz * cx, sz * sy * sx + cz * cx, cy * sx),
            (cz * sy * cx + sz * sx, sz * sy * cx - cz * sx, cy * cx))


IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def polygon_area(points):
    return 0.5 * sum(points[i][0] * points[(i + 1) % len(points)][1] - points[(i + 1) % len(points)][0] * points[i][1] for i in range(len(points)))


def triangulate_polygon(points):
    """Ear clipping for simple 2D polygons, including concave I-sections."""
    idx = list(range(len(points)))
    if polygon_area(points) < 0:
        idx.reverse()
    out = []

    def cross2(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def in_tri(p, a, b, c):
        return min(cross2(a, b, p), cross2(b, c, p), cross2(c, a, p)) >= -EPS

    while len(idx) > 3:
        found = False
        for q in range(len(idx)):
            ia, ib, ic = idx[q - 1], idx[q], idx[(q + 1) % len(idx)]
            a, b, c = points[ia], points[ib], points[ic]
            if cross2(a, b, c) <= EPS:
                continue
            if any(in_tri(points[j], a, b, c) for j in idx if j not in (ia, ib, ic)):
                continue
            out.append((ia, ib, ic))
            idx.pop(q)
            found = True
            break
        if not found:
            raise ValueError("Invalid, self-intersecting or degenerate polygon.")
    out.append(tuple(idx))
    return out


class MeshPart:
    """A render mesh assembled from individually closed primitives.

    Overlaps between separate primitives are intentional assembly joints.
    This is a DCC mesh, not a boolean-unioned CAD/3D-print solid.
    """
    def __init__(self, name, group, bevel=0.008, pivot=(0, 0, 0)):
        self.name, self.group, self.bevel, self.pivot = name, group, bevel, tuple(pivot)
        self.vertices = []
        self.faces = []
        self.material_ids = []
        self.smooth = []
        self.uvs = []
        self.material_names = []
        self.primitive_count = 0
        self.closed_primitive_count = 0

    def primitive(self, verts, faces, material, smooth=False, closed=True):
        verts = [tuple(float(v) for v in p) for p in verts]
        faces = [tuple(f) for f in faces]
        # Ensure outward orientation for the complete primitive.
        if closed:
            volume6 = 0.0
            o = verts[0]
            for f in faces:
                a = sub(verts[f[0]], o)
                for k in range(1, len(f) - 1):
                    volume6 += dot(a, cross(sub(verts[f[k]], o), sub(verts[f[k + 1]], o)))
            if volume6 < 0:
                faces = [tuple(reversed(f)) for f in faces]
        if material not in self.material_names:
            self.material_names.append(material)
        mat_id = self.material_names.index(material)
        off = len(self.vertices)
        self.vertices.extend(verts)
        for f in faces:
            self.faces.append(tuple(off + j for j in f))
            self.material_ids.append(mat_id)
            self.smooth.append(bool(smooth))
            a, b, c = (verts[f[j]] for j in range(3))
            normal = cross(sub(b, a), sub(c, a))
            axis = max(range(3), key=lambda k: abs(normal[k]))
            uv_axes = ((1, 2), (0, 2), (0, 1))[axis]
            # World-scaled planar UVs, 1 UV unit = 1 metre; repeated by design.
            self.uvs.append([(verts[j][uv_axes[0]], verts[j][uv_axes[1]]) for j in f])
        self.primitive_count += 1
        self.closed_primitive_count += int(closed)

    def box(self, center, dims, material, axes=IDENTITY):
        if min(dims) <= EPS:
            raise ValueError(f"{self.name}: box dimensions must be positive: {dims}")
        x, y, z = (s / 2 for s in dims)
        v = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
             (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
        v = [local_to_world(p, center, axes) for p in v]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self.primitive(v, f, material)

    def beam(self, a, b, width, depth, material):
        z = unit(sub(b, a))
        ref = (0, 0, 1) if abs(z[2]) < 0.95 else (0, 1, 0)
        x = unit(cross(ref, z))
        y = cross(z, x)
        self.box(mul(add(a, b), 0.5), (width, depth, math.sqrt(dot(sub(b, a), sub(b, a)))), material, (x, y, z))

    def cylinder(self, a, b, radius, material, segments=16):
        z = unit(sub(b, a))
        ref = (0, 0, 1) if abs(z[2]) < 0.95 else (0, 1, 0)
        x, n = unit(cross(ref, z)), segments
        y = cross(z, x)
        v = [add(p, add(mul(x, radius * math.cos(i * 2 * math.pi / n)), mul(y, radius * math.sin(i * 2 * math.pi / n)))) for p in (a, b) for i in range(n)]
        f = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
        f.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
        self.primitive(v, f, material)

    def tube(self, a, b, outer, inner, material, segments=20):
        if not 0 < inner < outer:
            raise ValueError("tube requires 0 < inner < outer")
        z, n = unit(sub(b, a)), segments
        ref = (0, 0, 1) if abs(z[2]) < 0.95 else (0, 1, 0)
        x = unit(cross(ref, z)); y = cross(z, x)
        v = [add(p, add(mul(x, r * math.cos(i * 2 * math.pi / n)), mul(y, r * math.sin(i * 2 * math.pi / n)))) for p, r in ((a, outer), (b, outer), (a, inner), (b, inner)) for i in range(n)]
        f = []
        for i in range(n):
            j = (i + 1) % n
            f += [(i, j, n + j, n + i), (2 * n + j, 2 * n + i, 3 * n + i, 3 * n + j),
                  (j, i, 2 * n + i, 2 * n + j), (n + i, n + j, 3 * n + j, 3 * n + i)]
        self.primitive(v, f, material)

    def prism(self, profile, origin, axes, length, material):
        """Extrude 2D profile along the third axis. Caps are ear-clipped."""
        p = list(profile)
        if polygon_area(p) < 0:
            p.reverse()
        n = len(p)
        v = [local_to_world((x, y, z), origin, axes) for z in (0.0, length) for x, y in p]
        t = triangulate_polygon(p)
        f = [tuple(reversed(tr)) for tr in t] + [tuple(j + n for j in tr) for tr in t]
        f += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
        self.primitive(v, f, material)

    def arch(self, profile, radius, zcenter, a0, a1, ycenter, segments, material, smooth=False):
        """Sweep (Y-offset, radial-offset) profile along a circular arc."""
        p = list(profile)
        if polygon_area(p) < 0:
            p.reverse()
        m, n = len(p), segments
        v = []
        for i in range(n + 1):
            t = a0 + (a1 - a0) * i / n
            for py, pr in p:
                v.append(((radius + pr) * math.sin(t), ycenter + py, zcenter + (radius + pr) * math.cos(t)))
        f = []
        for i in range(n):
            for j in range(m):
                k = (j + 1) % m
                f.append((i * m + j, i * m + k, (i + 1) * m + k, (i + 1) * m + j))
        cap = triangulate_polygon(p)
        f += [tuple(reversed(t)) for t in cap]
        f += [tuple(n * m + j for j in t) for t in cap]
        self.primitive(v, f, material, smooth=smooth)
        # Keep end caps flat when the curved sheet uses smooth shading.
        if smooth:
            for i in range(len(self.smooth) - 2 * len(cap), len(self.smooth)):
                self.smooth[i] = False

    def pipe(self, points, radius, material, sides=10):
        """Mitered polyline tube with closed ends; keeps material continuity."""
        if len(points) < 2:
            return
        v = []
        previous_x = None
        for i, p in enumerate(points):
            if i == 0:
                tangent = unit(sub(points[1], p))
            elif i == len(points) - 1:
                tangent = unit(sub(p, points[i - 1]))
            else:
                tangent = unit(add(unit(sub(p, points[i - 1])), unit(sub(points[i + 1], p))))
            ref = previous_x or ((1, 0, 0) if abs(tangent[0]) < 0.85 else (0, 1, 0))
            projected = sub(ref, mul(tangent, dot(ref, tangent)))
            if dot(projected, projected) < EPS:
                projected = cross(tangent, (0, 0, 1))
            x = unit(projected); y = cross(tangent, x); previous_x = x
            for j in range(sides):
                angle = j * math.tau / sides
                v.append(add(p, add(mul(x, radius * math.cos(angle)), mul(y, radius * math.sin(angle)))))
        f = [tuple(reversed(range(sides))), tuple((len(points) - 1) * sides + j for j in range(sides))]
        for i in range(len(points) - 1):
            for j in range(sides):
                k = (j + 1) % sides
                f.append((i * sides + j, i * sides + k, (i + 1) * sides + k, (i + 1) * sides + j))
        self.primitive(v, f, material, smooth=True)

    def floor_polygon(self, xy, z, material):
        p = list(xy)
        if polygon_area(p) < 0:
            p.reverse()
        self.primitive([(x, y, z) for x, y in p], triangulate_polygon(p), material, closed=False)


def rect_profile(width, height):
    return [(-width / 2, -height / 2), (width / 2, -height / 2), (width / 2, height / 2), (-width / 2, height / 2)]


def i_profile(width=0.28, height=0.46, web=0.034, flange=0.035):
    w, h, t = width / 2, height / 2, web / 2
    return [(-w, -h), (w, -h), (w, -h + flange), (t, -h + flange), (t, h - flange),
            (w, h - flange), (w, h), (-w, h), (-w, h - flange), (-t, h - flange),
            (-t, -h + flange), (-w, -h + flange)]


def clip_polygon(poly, axis, bound, keep_less):
    """Clip 2D polygon to an axis-aligned half-plane, used for hazard stripes."""
    result = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        ina = a[axis] <= bound + EPS if keep_less else a[axis] >= bound - EPS
        inb = b[axis] <= bound + EPS if keep_less else b[axis] >= bound - EPS
        if ina:
            result.append(a)
        if ina != inb:
            t = (bound - a[axis]) / (b[axis] - a[axis])
            result.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return result


class ShelterModel:
    def __init__(self, config):
        self.cfg = validate_config(config)
        c = self.cfg
        self.half = c["span"] / 2
        self.depth = c["depth"]
        self.radius = (self.half ** 2 + c["roof_rise"] ** 2) / (2 * c["roof_rise"])
        self.zcenter = c["eave_height"] + c["roof_rise"] - self.radius
        self.alpha = math.asin(self.half / self.radius)
        factor = {"PREVIEW": 0.55, "HIGH": 1.0, "CINEMATIC": 1.5}[c["detail"]]
        self.arc_segments = max(24, int(c["roof_arc_segments"] * factor))
        self.parts = []
        self.labels = []
        self.lights = []
        self.collisions = []

    def part(self, name, group="Structure", bevel=None, pivot=(0, 0, 0)):
        p = MeshPart("SM_AS07_" + name, group, self.cfg["bevel_width"] if bevel is None else bevel, pivot)
        self.parts.append(p)
        return p

    def zroof(self, x):
        return self.zcenter + math.sqrt(max(0.0, self.radius ** 2 - x ** 2))

    def collision_box(self, group, center, dims):
        self.collisions.append({"group": group, "center": tuple(center), "dims": tuple(dims)})

    def label(self, body, location, size, material="White", rotation=(math.pi / 2, 0, 0), align="CENTER", group="Fittings"):
        self.labels.append({"body": body, "location": location, "size": size, "material": material,
                            "rotation": rotation, "align": align, "group": group})

    def build(self):
        self.build_apron()
        self.build_frame()
        self.build_roof()
        self.build_walls()
        self.build_services()
        if self.cfg["add_service_props"]:
            self.build_props()
        self.build_signage()
        self.build_presentation()
        return self

    def build_apron(self):
        c, a, d = self.cfg, self.half, self.depth
        floor = self.part("ApronSlabs", "Apron", 0.005)
        xlo, xhi = -a - c["apron_side"], a + c["apron_side"]
        ylo, yhi = -c["apron_front"], d + c["apron_back"]
        nx = max(4, math.ceil((xhi - xlo) / 5.0))
        ny = max(4, math.ceil((yhi - ylo) / 4.0))
        sx, sy = (xhi - xlo) / nx, (yhi - ylo) / ny
        for i in range(nx):
            for j in range(ny):
                mat = "ConcreteLight" if (i * 5 + j * 3) % 7 < 2 else "Concrete"
                floor.box((xlo + (i + .5) * sx, ylo + (j + .5) * sy, -.145), (sx - .018, sy - .018, .29), mat)
        joints = self.part("JointBed", "Apron", 0)
        joints.box(((xlo + xhi) / 2, (ylo + yhi) / 2, -.21), (xhi - xlo, yhi - ylo, .16), "Rubber")
        self.collision_box("Apron", ((xlo + xhi) / 2, (ylo + yhi) / 2, -.15), (xhi - xlo, yhi - ylo, .30))
        paint = self.part("FloorMarkings", "Markings", 0)
        for s in (-1, 1):
            x = s * (a - 1.1)
            paint.floor_polygon([(x - .70, .35), (x + .70, .35), (x + .70, d - .35), (x - .70, d - .35)], .004, "Walkway")
            for xx in (x - .74, x + .74):
                paint.floor_polygon([(xx - .035, .35), (xx + .035, .35), (xx + .035, d - .35), (xx - .035, d - .35)], .005, "White")
        # Continuous lead-in, dashed interior centre line, stop bar and arrow.
        paint.floor_polygon([(-.065, ylo + .4), (.065, ylo + .4), (.065, .25), (-.065, .25)], .006, "Yellow")
        for j in range(max(1, int(d / 3.5))):
            yy = .6 + j * 3.1
            if yy + 1.6 < d * .78:
                paint.floor_polygon([(-.06, yy), (.06, yy), (.06, yy + 1.6), (-.06, yy + 1.6)], .006, "Yellow")
        yy = d * .78
        paint.floor_polygon([(-1.4, yy), (1.4, yy), (1.4, yy + .13), (-1.4, yy + .13)], .006, "Yellow")
        paint.floor_polygon([(-.18, -4.8), (.18, -4.8), (.18, -3.25), (.64, -3.25), (0, -2.45), (-.64, -3.25), (-.18, -3.25)], .007, "Yellow")
        # Actual clipped diagonal polygons, no overlapping rotated boxes.
        left, right, bottom, top = -a + .55, a - .55, -.62, -.15
        paint.floor_polygon([(left, bottom), (right, bottom), (right, top), (left, top)], .007, "Yellow")
        k = left - 1.0
        while k < right + 1.0:
            poly = [(k, bottom), (k + .24, bottom), (k + .24 + top - bottom, top), (k + top - bottom, top)]
            poly = clip_polygon(poly, 0, left, False)
            poly = clip_polygon(poly, 0, right, True) if poly else []
            if len(poly) >= 3 and abs(polygon_area(poly)) > EPS:
                paint.floor_polygon(poly, .009, "SteelDark")
            k += .56
        drain = self.part("ThresholdDrain", "Fittings", .002)
        drain.box((0, -1.15, -.04), (a * 2 + .7, .28, .07), "Rubber")
        for yy in (-1.27, -1.03):
            drain.box((0, yy, .009), (a * 2 + .75, .026, .018), "Galvanized")
        for i in range(int((a * 2 + .6) / .18)):
            xx = -a - .22 + i * .18
            drain.box((xx, -1.15, .007), (.035, .23, .025), "Galvanized")
        curb = self.part("SideCurbs", "Apron", .014)
        for s in (-1, 1):
            curb.box((s * (a + 1.57), d / 2, .09), (.2, d + .6, .18), "ConcreteLight")
            curb.box((s * (a + .99), d / 2, -.015), (.85, d + .25, .05), "Gravel")

    def build_frame(self):
        c, a, d = self.cfg, self.half, self.depth
        bays, eave = c["bay_count"], c["eave_height"]
        base = self.part("BasePlates", "Structure", .004)
        bolts = self.part("FrameFasteners", "Fittings", .0015)
        columns = self.part("SteelColumns", "Structure", .007)
        for i in range(bays + 1):
            yy = i * d / bays
            rib = self.part(f"ArchRib_{i:02d}", "Structure", .005)
            rib.arch(i_profile(), self.radius, self.zcenter, -self.alpha, self.alpha, yy, self.arc_segments, "SteelDark")
            for s in (-1, 1):
                xx = s * a
                # Columns use a true I cross-section rather than a scaled cube.
                columns.prism(i_profile(.40, .33, .040, .036), (xx, yy, .085), IDENTITY, eave - .085, "SteelDark")
                base.box((xx, yy, .055), (.68, .68, .11), "SteelDark")
                base.box((xx, yy, eave - .12), (.46, .43, .18), "SteelDark")
                if c["add_fasteners"] and c["detail"] != "PREVIEW":
                    for dx in (-.25, .25):
                        for dy in (-.25, .25):
                            bolts.cylinder((xx + dx, yy + dy, .11), (xx + dx, yy + dy, .155), .043, "Galvanized", 6)
                            bolts.cylinder((xx + dx, yy + dy, .103), (xx + dx, yy + dy, .118), .063, "Galvanized", 16)
                    # Visible connection bolts on the aisle-facing flange.
                    for dz in (-.20, .0):
                        bolts.cylinder((xx, yy - .245, eave + dz), (xx, yy - .206, eave + dz), .036, "Galvanized", 6)
        purlins = self.part("RoofPurlins", "Structure", .004)
        for j in range(11):
            t = -self.alpha + (j + .5) * (2 * self.alpha / 11)
            rr = self.radius + .17
            xx, zz = rr * math.sin(t), self.zcenter + rr * math.cos(t)
            purlins.box((xx, d / 2, zz), (.11, d + .30, .12), "Galvanized", euler_axes(0, t, 0))
        braces = self.part("SideBraces", "Structure", .002)
        for s in (-1, 1):
            for i in range(bays):
                if i % 3 != 1:
                    y0, y1 = i * d / bays + .24, (i + 1) * d / bays - .24
                    xx = s * (a - .16)
                    braces.beam((xx, y0, 2.47), (xx, y1, eave - .32), .045, .06, "Galvanized")
                    braces.beam((xx, y1, 2.47), (xx, y0, eave - .32), .045, .06, "Galvanized")

    def build_roof(self):
        c, d = self.cfg, self.depth
        bays = c["bay_count"]
        for i in range(bays):
            roof = self.part(f"RoofBay_{i:02d}", "Structure", .003)
            roof.arch(rect_profile(d / bays - .012, .075), self.radius + .30, self.zcenter,
                      -self.alpha, self.alpha, (i + .5) * d / bays, self.arc_segments,
                      "RoofOliveLight" if i % 3 == 0 else "RoofOlive", smooth=True)
        seams = self.part("StandingSeams", "Structure", .002)
        count = max(2, math.ceil(d / c["roof_seam_spacing"]))
        for i in range(count + 1):
            seams.arch(rect_profile(.045, .065), self.radius + .359, self.zcenter,
                       -self.alpha, self.alpha, i * d / count, self.arc_segments, "SteelDark", smooth=True)
        fascia = self.part("PortalFascia", "Structure", .006)
        accents = self.part("FasciaAccents", "Fittings", .002)
        for yy in (-.22, d + .22):
            fascia.arch(rect_profile(.30, .57), self.radius + .09, self.zcenter,
                         -self.alpha, self.alpha, yy, self.arc_segments, "SteelDark", smooth=True)
            accents.arch(rect_profile(.014, .035), self.radius + .23, self.zcenter,
                         -self.alpha, self.alpha, yy + (-.156 if yy < 0 else .156), self.arc_segments, "Yellow", smooth=True)
        # Open U-profile gutters, not a solid rectangular bar.
        gutters = self.part("GuttersAndDownpipes", "Fittings", .003)
        profile = [(-.19, -.12), (.19, -.12), (.19, .13), (.16, .13), (.16, -.085), (-.16, -.085), (-.16, .13), (-.19, .13)]
        for s in (-1, 1):
            xx = s * (self.half + .25)
            zz = c["eave_height"] + .10
            gutters.prism(profile, (xx, -.4, zz), ((1, 0, 0), (0, 0, 1), (0, 1, 0)), d + .8, "Galvanized")
            for yy in (1.0, d - 1.0):
                xo = s * (self.half + .58)
                gutters.pipe([(xx, yy, zz - .1), (xo, yy, zz - .38), (xo, yy, .45), (xo + s * .19, yy, .22)], .064, "Galvanized", 12)
                for h in (.7, 2.2, 3.7):
                    if h < zz - .45:
                        gutters.box((xo - s * .08, yy, h), (.20, .035, .045), "SteelDark")
        # Convex roof collision segments are built at Blender export time.

    def build_walls(self):
        c, a, d = self.cfg, self.half, self.depth
        bays, h, t = c["bay_count"], c["sidewall_height"], c["wall_thickness"]
        walls = self.part("SideConcretePanels", "Structure", .014)
        reveals = self.part("WallReveals", "Structure", .002)
        louvers = self.part("SideLouvers", "Structure", .002)
        frames = self.part("LouverFrames", "Structure", .004)
        for s in (-1, 1):
            xx = s * (a + .05)
            for i in range(bays):
                yy, length = (i + .5) * d / bays, d / bays - .075
                walls.box((xx, yy, h / 2), (t, length, h), "ConcreteLight")
                for z in (.76, 1.52):
                    reveals.box((xx - s * (t / 2 + .002), yy, z), (.005, length - .035, .014), "Concrete")
                reveals.box((xx, yy, h + .055), (t + .12, length + .02, .11), "Concrete")
                self.collision_box("Structure", (xx, yy, h / 2), (t, length, h))
                z0, z1 = h + .23, c["eave_height"] - .28
                if c["add_louvers"]:
                    for z in (z0, z1):
                        frames.box((xx + s * .02, yy, z), (.18, length, .085), "SteelDark")
                    n = max(3, int((z1 - z0) / .17))
                    for k in range(n):
                        z = z0 + .11 + k * (z1 - z0 - .20) / max(n - 1, 1)
                        louvers.box((xx + s * .035, yy, z), (.24, length - .08, .035), "RoofOlive", euler_axes(0, s * math.radians(25), 0))
        rear = self.part("RearWall", "Structure", .012)
        door_x, door_w, door_h = a * .55, 1.18, 2.25
        left_edge, right_edge = door_x - door_w / 2, door_x + door_w / 2
        for lo, hi in ((-a, left_edge), (right_edge, a)):
            rear.box(((lo + hi) / 2, d + .02, h / 2), (hi - lo, t, h), "ConcreteLight")
            self.collision_box("Structure", ((lo + hi) / 2, d + .02, h / 2), (hi - lo, t, h))
        if h > door_h:
            rear.box((door_x, d + .02, (h + door_h) / 2), (door_w, t, h - door_h), "ConcreteLight")
            self.collision_box("Structure", (door_x, d + .02, (h + door_h) / 2), (door_w, t, h - door_h))
        # Back arch infill follows the curved roof and is split into narrow panels.
        n = max(12, int(c["span"] / 1.2))
        for j in range(n):
            x0, x1 = -a + j * 2 * a / n + .012, -a + (j + 1) * 2 * a / n - .012
            poly = [(x0, h + .02), (x1, h + .02), (x1, self.zroof(x1) - .20),
                    ((x0 + x1) / 2, self.zroof((x0 + x1) / 2) - .20), (x0, self.zroof(x0) - .20)]
            rear.prism(poly, (0, d + .04, 0), ((1, 0, 0), (0, 0, 1), (0, 1, 0)), .13, "RoofOlive" if j % 2 else "RoofOliveLight")
            frames.box((x0, d - .02, (h + self.zroof(x0) - .20) / 2), (.045, .10, self.zroof(x0) - .20 - h), "SteelDark")
            # Separate collision segments do not block the personnel doorway.
            self.collision_box("Structure", ((x0 + x1) / 2, d + .10, (h + self.zroof(x0) - .28) / 2),
                               (x1 - x0, .13, self.zroof(x0) - .28 - h))
        frame = self.part("PersonnelDoorFrame", "Fittings", .005)
        for xx in (left_edge - .04, right_edge + .04):
            frame.box((xx, d - .175, door_h / 2), (.10, .12, door_h + .04), "SteelDark")
        frame.box((door_x, d - .175, door_h + .02), (door_w + .18, .12, .12), "SteelDark")
        pivot = (left_edge + .035, d - .19, .045)
        door = self.part("PersonnelDoor", "Door", .004, pivot=pivot)
        # Geometry is authored in world space; Blender adapter moves it to hinge-local coordinates.
        door.box((door_x, pivot[1], door_h / 2), (door_w - .07, .07, door_h - .09), "RoofOlive")
        door.box((door_x, pivot[1] - .041, 1.98), (.80, .012, .095), "Yellow")
        door.box((door_x, pivot[1] - .043, .24), (door_w - .16, .014, .34), "Galvanized")
        for z in (.38, 1.82):
            door.cylinder((pivot[0], pivot[1], z - .06), (pivot[0], pivot[1], z + .06), .033, "Galvanized", 12)
        door.box((right_edge - .16, pivot[1] - .056, 1.03), (.05, .025, .18), "SteelDark")
        door.beam((right_edge - .18, pivot[1] - .09, 1.07), (right_edge - .34, pivot[1] - .09, 1.07), .035, .035, "Galvanized")
        self.collision_box("Door", (door_x, pivot[1], door_h / 2), (door_w - .07, .07, door_h - .09))
        self.label("SERVICE", (door_x, d - .25, 2.52), .15)
        self.label("EXIT", (door_x, d - .26, 2.79), .14, "LightGreen")

    def build_services(self):
        c, a, d = self.cfg, self.half, self.depth
        fittings = self.part("CableTrays", "Fittings", .002)
        cable = self.part("ServiceConduits", "Fittings", .001)
        lights = self.part("LightFixtures", "Fittings", .003)
        for s in (-1, 1):
            xx, zz = s * (a - .70), c["eave_height"] - .55
            for dx in (-.16, .16):
                fittings.box((xx + dx, d / 2, zz), (.026, d - .8, .095), "Galvanized")
            for k in range(max(1, int(d / .8))):
                yy = .5 + k * .8
                fittings.box((xx, yy, zz - .028), (.30, .035, .035), "Galvanized")
            for dx in (-.075, 0, .075):
                cable.pipe([(xx + dx, .7, zz + .022), (xx + dx, d - .9, zz + .022)], .016, "Rubber", 8)
            for i in range(c["bay_count"]):
                yy = (i + .5) * d / c["bay_count"]
                lx = s * a * .53
                lz = self.zroof(lx) - .73
                lights.box((lx, yy, lz), (.21, 1.85, .13), "SteelDark")
                lights.box((lx, yy, lz - .073), (.155, 1.75, .019), "LightWarm")
                for dy in (-.65, .65):
                    lights.cylinder((lx, yy + dy, lz + .065), (lx, yy + dy, self.zroof(lx) + .16), .014, "Galvanized", 8)
                self.lights.append({"location": (lx, yy, lz - .095), "power": 85, "size": 1.65})
        # Wall-mounted power panel; face points inward (+X from left wall).
        cabinet = self.part("WallEquipment", "Fittings", .009)
        xx, yy = -a + .50, d * .64
        cabinet.box((xx, yy, 1.38), (.36, 1.05, 1.2), "SteelDark")
        cabinet.box((xx + .19, yy, 1.38), (.035, .96, 1.10), "RoofOliveLight")
        cabinet.box((xx + .218, yy + .32, 1.34), (.035, .07, .24), "Rubber")
        for z in (.90, .96, 1.02):
            cabinet.box((xx + .213, yy, z), (.008, .65, .015), "Rubber")
        cabinet.box((xx + .22, yy - .28, 1.73), (.015, .21, .10), "Yellow")
        cable.pipe([(xx, yy - .30, 1.98), (xx, yy - .30, 2.25), (xx, yy - .3, c["eave_height"] - .55)], .031, "Galvanized", 12)
        for s in (-1, 1):
            # Red fire equipment cabinet, tucked alongside the entry columns.
            ex, ey = s * (a - .42), 1.45
            cabinet.box((ex, ey, 1.10), (.24, .56, .84), "Red")
            cabinet.box((ex - s * .131, ey, 1.10), (.015, .48, .74), "Red")
            cabinet.box((ex - s * .145, ey, 1.31), (.016, .38, .085), "White")
        # Rear ventilation units: cowl, blades, concentric protective rings.
        fans = self.part("RearVentilation", "Fittings", .002)
        for x in (-a * .55, 0.0):
            y, z = d - .20, 3.65
            fans.box((x, y + .065, z), (1.22, .10, 1.22), "SteelDark")
            fans.tube((x, y - .18, z), (x, y + .03, z), .53, .475, "Galvanized", 32)
            fans.cylinder((x, y - .12, z), (x, y - .025, z), .14, "SteelDark", 20)
            for i in range(5):
                t = math.tau * i / 5
                dx, dz = math.sin(t), math.cos(t)
                fans.beam((x + .11 * dx, y - .018, z + .11 * dz), (x + .43 * dx, y - .018, z + .43 * dz), .11, .025, "RoofOlive")
            for rr in (.19, .30, .40, .49):
                points = [(x + rr * math.sin(math.tau * j / 40), y - .195, z + rr * math.cos(math.tau * j / 40)) for j in range(41)]
                fans.pipe(points, .008, "Galvanized", 6)
            for dx in (-.30, 0, .30):
                hh = math.sqrt(.49 ** 2 - dx ** 2)
                fans.beam((x + dx, y - .20, z - hh), (x + dx, y - .20, z + hh), .014, .014, "Galvanized")

    def build_props(self):
        c, a, d = self.cfg, self.half, self.depth
        bollards = self.part("Bollards", "Props", .004)
        for s in (-1, 1):
            for yy in (-1.9, .4, d + .8):
                xx = s * (a + .77)
                bollards.cylinder((xx, yy, .035), (xx, yy, 1.03), .10, "Yellow", 20)
                bollards.cylinder((xx, yy, .53), (xx, yy, .72), .103, "SteelDark", 20)
                bollards.cylinder((xx, yy, .99), (xx, yy, 1.045), .102, "SteelDark", 20)
                bollards.box((xx, yy, .025), (.31, .31, .05), "SteelDark")
                if c["detail"] != "PREVIEW":
                    for dx in (-.11, .11):
                        for dy in (-.11, .11):
                            bollards.cylinder((xx + dx, yy + dy, .05), (xx + dx, yy + dy, .073), .019, "Galvanized", 6)
                self.collision_box("Props", (xx, yy, .53), (.22, .22, 1.06))
        cart = self.part("MaintenanceTrolley", "Props", .009)
        x, y = a - 2.60, d * .29
        cart.box((x, y, .73), (.78, 1.22, .94), "RoofOlive")
        cart.box((x, y, 1.225), (.84, 1.28, .055), "Galvanized")
        for i in range(4):
            zz = .49 + i * .185
            cart.box((x - .405, y, zz), (.035, 1.12, .16), "SteelDark")
            cart.box((x - .441, y, zz + .033), (.037, .54, .035), "Galvanized")
        for sx in (-1, 1):
            for sy in (-1, 1):
                wx, wy = x + sx * .28, y + sy * .47
                cart.box((wx, wy, .21), (.07, .14, .21), "Galvanized")
                cart.cylinder((wx - .047, wy, .12), (wx + .047, wy, .12), .12, "Rubber", 20)
                cart.cylinder((wx - .051, wy, .12), (wx + .051, wy, .12), .045, "Galvanized", 12)
        cart.pipe([(x - .31, y + .67, .90), (x - .31, y + .75, 1.14), (x + .31, y + .75, 1.14), (x + .31, y + .67, .90)], .021, "Galvanized", 10)
        self.collision_box("Props", (x, y, .65), (.87, 1.42, 1.30))
        cases = self.part("ServiceCases", "Props", .014)
        for i in range(3):
            xx, yy = -a + 1.55 + (i % 2) * 1.1, d - 2.0
            zz = .28 if i < 2 else .84
            cases.box((xx, yy, zz), (.92, .64, .52), "SteelDark")
            cases.box((xx, yy, zz + .245), (.935, .655, .065), "RoofOlive")
            for dx in (-.32, .32):
                cases.box((xx + dx, yy - .331, zz + .14), (.07, .025, .12), "Galvanized")
            cases.box((xx, yy - .345, zz + .035), (.27, .035, .045), "Galvanized")
        # Wheel chocks are visual props; no aircraft model is included.
        for yy in (5.0, 5.9):
            cases.prism([(-.20, 0), (.20, 0), (.20, .21), (-.08, .21)], (a - 2.3, yy, .02),
                        ((1, 0, 0), (0, 0, 1), (0, 1, 0)), .34, "Yellow")

    def build_signage(self):
        if not self.cfg["add_signage"]:
            return
        a, d = self.half, self.depth
        sign = self.part("SignPanels", "Fittings", .007)
        apex = self.cfg["eave_height"] + self.cfg["roof_rise"]
        sign.box((0, -.43, apex - .04), (4.20, .12, .87), "SteelDark")
        sign.box((0, -.497, apex - .40), (3.86, .013, .028), "Yellow")
        self.label("AS / 07", (0, -.502, apex - .06), .52)
        self.label("AIRCRAFT SHELTER", (0, -.505, apex - .29), .115, "Yellow")
        sign.box((-a + .07, -.39, 2.78), (.68, .09, 1.12), "SteelDark")
        self.label("07", (-a + .07, -.441, 2.87), .43, "Yellow")
        self.label("BAY", (-a + .07, -.442, 2.49), .12)
        self.label("KEEP CLEAR", (0, -2.0, .016), .56, "White", rotation=(0, 0, 0), group="Markings")
        self.label("GROUND SERVICE", (-a + 1.10, d * .70, .016), .20, "White", rotation=(0, 0, -math.pi / 2), group="Markings")

    def build_presentation(self):
        # Presentation-only ground, deliberately excluded from asset exports.
        ground = self.part("PresentationGround", "Presentation", 0)
        ground.box((0, self.depth * .4, -.15), (180, 180, .20), "Asphalt")


def validate_config(config):
    c = dict(CONFIG)
    unknown = set(config) - set(c)
    if unknown:
        raise ValueError("Unknown config setting(s): " + ", ".join(sorted(unknown)))
    c.update(config)
    for k in ("span", "depth", "eave_height", "roof_rise", "sidewall_height", "wall_thickness", "roof_seam_spacing"):
        if not isinstance(c[k], (int, float)) or isinstance(c[k], bool) or not math.isfinite(c[k]) or c[k] <= 0:
            raise ValueError(f"{k} must be a finite positive number")
    if not 18 <= c["span"] <= 40:
        raise ValueError("Supported span range: 18..40 metres. Details are scaled for this range.")
    if not 20 <= c["depth"] <= 60:
        raise ValueError("Supported depth range: 20..60 metres.")
    if not 4.1 <= c["eave_height"] <= 8.0:
        raise ValueError("Supported eave_height range: 4.1..8 metres.")
    if not 1.8 <= c["roof_rise"] < c["span"] / 2:
        raise ValueError("roof_rise must be >= 1.8 and less than half of span.")
    if not 2.3 <= c["sidewall_height"] < c["eave_height"] - .65:
        raise ValueError("sidewall_height must be >= 2.3 and at least .65 below eave_height.")
    if not isinstance(c["bay_count"], int) or not 4 <= c["bay_count"] <= 16:
        raise ValueError("bay_count must be an integer in 4..16")
    if not 2.3 <= c["depth"] / c["bay_count"] <= 6.5:
        raise ValueError("depth / bay_count must be in 2.3..6.5 metres")
    if c["detail"] not in ("PREVIEW", "HIGH", "CINEMATIC"):
        raise ValueError("detail must be PREVIEW, HIGH or CINEMATIC")
    if not isinstance(c["roof_arc_segments"], int) or not 24 <= c["roof_arc_segments"] <= 160:
        raise ValueError("roof_arc_segments must be an integer in 24..160")
    if c["apron_front"] < 5.5 or c["apron_side"] < 1.85 or c["apron_back"] < 1.2:
        raise ValueError("apron minimums: front=5.5, side=1.85, back=1.2 metres")
    if not 0 <= c["door_open_degrees"] <= 110:
        raise ValueError("door_open_degrees must be in 0..110")
    if not isinstance(c["bevel_segments"], int) or not 1 <= c["bevel_segments"] <= 5:
        raise ValueError("bevel_segments must be in 1..5")
    if not 0 <= c["bevel_width"] <= .025:
        raise ValueError("bevel_width must be in 0..0.025 metres")
    if not .20 <= c["wall_thickness"] <= .80:
        raise ValueError("wall_thickness must be in 0.20..0.80 metres (visual setting only)")
    if not .25 <= c["roof_seam_spacing"] <= 4.0:
        raise ValueError("roof_seam_spacing must be in 0.25..4 metres")
    for key in ("resolution_x", "resolution_y"):
        if not isinstance(c[key], int) or not 512 <= c[key] <= 8192:
            raise ValueError(key + " must be an integer in 512..8192")
    if not isinstance(c["render_samples"], int) or not 1 <= c["render_samples"] <= 2048:
        raise ValueError("render_samples must be an integer in 1..2048")
    if not isinstance(c["output_directory"], str):
        raise ValueError("output_directory must be a string")
    for key in ("add_service_props", "add_louvers", "add_fasteners", "add_signage", "add_practical_lights", "create_packed_uv", "render_now", "save_blend", "export_fbx", "export_glb"):
        if not isinstance(c[key], bool):
            raise ValueError(key + " must be True or False")
    if c["render_engine"] not in ("CYCLES", "EEVEE"):
        raise ValueError("render_engine must be CYCLES or EEVEE")
    return c


def validate_model(model):
    """Checks numeric values, face area, topology indices and open-edge counts.

    Does not replace Blender shading, UV-overlap, collision or UE import tests.
    """
    report = {"version": VERSION, "parts": [], "total_vertices": 0, "total_triangles": 0, "errors": [],
              "notes": ["Triangle counts exclude Blender bevels and font geometry.",
                        "Intersecting assembly components are intentional; not a print-ready union.",
                        "No Blender runtime or Unreal import test was available in the authoring environment."]}
    seen = set()
    for p in model.parts:
        if p.name in seen:
            report["errors"].append("Duplicate part name: " + p.name)
        seen.add(p.name)
        if not p.faces:
            continue
        edges, degenerate = {}, 0
        for v in p.vertices:
            if not all(math.isfinite(q) for q in v):
                report["errors"].append("Non-finite coordinate: " + p.name)
        for f in p.faces:
            if len(f) < 3 or min(f) < 0 or max(f) >= len(p.vertices):
                report["errors"].append("Invalid face indices: " + p.name)
                continue
            area = 0.0
            a = p.vertices[f[0]]
            for j in range(1, len(f) - 1):
                cr = cross(sub(p.vertices[f[j]], a), sub(p.vertices[f[j + 1]], a))
                area += math.sqrt(dot(cr, cr)) * .5
            degenerate += area < 1.0e-12
            for i, j in zip(f, f[1:] + f[:1]):
                e = (min(i, j), max(i, j))
                edges[e] = edges.get(e, 0) + 1
        boundary = sum(n == 1 for n in edges.values())
        nonmanifold = sum(n > 2 for n in edges.values())
        if degenerate or nonmanifold:
            report["errors"].append(f"{p.name}: degenerate={degenerate}, nonmanifold={nonmanifold}")
        if p.primitive_count == p.closed_primitive_count and boundary:
            report["errors"].append(f"{p.name}: closed primitives have {boundary} boundary edges")
        tris = sum(len(f) - 2 for f in p.faces)
        report["parts"].append({"name": p.name, "group": p.group, "vertices": len(p.vertices), "triangles": tris,
                               "material_slots": len(p.material_names), "boundary_edges": boundary,
                               "primitive_count": p.primitive_count})
        report["total_vertices"] += len(p.vertices)
        report["total_triangles"] += tris
    report["part_count"] = len(report["parts"])
    report["status"] = "PASS" if not report["errors"] else "FAIL"
    return report

# ------------------------------ BLENDER ADAPTER ----------------------------
def log(message):
    print("[AS07] " + message, flush=True)


def make_materials(bpy, anchor):
    mats = {}
    for key, cfg in MATERIALS.items():
        mat = bpy.data.materials.new("AS07_" + key)
        mat.use_nodes = True
        col = tuple(cfg["color"]) + (1.0,)
        mat.diffuse_color = col
        mat.roughness = cfg["roughness"]
        mat.metallic = cfg["metallic"]
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial"); output.location = (720, 80)
        bsdf = nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (450, 80)
        bsdf.inputs["Base Color"].default_value = col
        bsdf.inputs["Roughness"].default_value = cfg["roughness"]
        bsdf.inputs["Metallic"].default_value = cfg["metallic"]
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
        if cfg.get("emission"):
            color_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
            if color_input is not None:
                color_input.default_value = col
            if bsdf.inputs.get("Emission Strength") is not None:
                bsdf.inputs["Emission Strength"].default_value = cfg["emission"]
        else:
            texcoord = nodes.new("ShaderNodeTexCoord"); texcoord.object = anchor; texcoord.location = (-820, 120)
            noise = nodes.new("ShaderNodeTexNoise"); noise.location = (-610, 190)
            noise.inputs["Scale"].default_value = cfg.get("noise", 4)
            noise.inputs["Detail"].default_value = 3.0
            noise.inputs["Roughness"].default_value = .64
            links.new(texcoord.outputs["Object"], noise.inputs["Vector"])
            ramp = nodes.new("ShaderNodeValToRGB"); ramp.location = (-340, 260)
            ramp.color_ramp.elements[0].position = .13
            ramp.color_ramp.elements[0].color = tuple(v * .77 for v in cfg["color"]) + (1,)
            ramp.color_ramp.elements[1].position = .87
            ramp.color_ramp.elements[1].color = tuple(min(1.0, v * 1.12) for v in cfg["color"]) + (1,)
            links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
            rough = nodes.new("ShaderNodeMapRange"); rough.location = (-60, -15)
            rough.inputs["From Min"].default_value = 0
            rough.inputs["From Max"].default_value = 1
            rough.inputs["To Min"].default_value = max(.10, cfg["roughness"] - .10)
            rough.inputs["To Max"].default_value = min(.99, cfg["roughness"] + .08)
            links.new(noise.outputs["Fac"], rough.inputs["Value"])
            links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
            fine = nodes.new("ShaderNodeTexNoise"); fine.location = (-360, -230)
            fine.inputs["Scale"].default_value = 135.0 if "Concrete" in key else 70.0
            fine.inputs["Detail"].default_value = 2.0
            links.new(texcoord.outputs["Object"], fine.inputs["Vector"])
            bump = nodes.new("ShaderNodeBump"); bump.location = (200, -160)
            bump.inputs["Strength"].default_value = .22
            bump.inputs["Distance"].default_value = cfg.get("bump", .0003)
            links.new(fine.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        mats[key] = mat
    return mats


def make_mesh_object(bpy, spec, collection, mats):
    mesh = bpy.data.meshes.new(spec.name + "_Mesh")
    vertices = [sub(v, spec.pivot) for v in spec.vertices]
    mesh.from_pydata(vertices, [], spec.faces)
    mesh.update(calc_edges=True)
    obj = bpy.data.objects.new(spec.name, mesh)
    collection.objects.link(obj)
    obj.location = spec.pivot
    obj["AS07_generated"] = True
    obj["AS07_group"] = spec.group
    obj["AS07_asset_name"] = spec.name
    for key in spec.material_names:
        mesh.materials.append(mats[key])
    uv = mesh.uv_layers.new(name="UV0_Tile")
    for polygon, mat_idx, smooth, coords in zip(mesh.polygons, spec.material_ids, spec.smooth, spec.uvs):
        polygon.material_index = mat_idx
        polygon.use_smooth = smooth
        for loop_index, value in zip(polygon.loop_indices, coords):
            uv.data[loop_index].uv = value
    # Mark large dihedral angles sharp where the version exposes the API.
    if hasattr(mesh, "set_sharp_from_angle"):
        mesh.set_sharp_from_angle(angle=math.radians(40))
    if spec.bevel > 0:
        bevel = obj.modifiers.new("AS07_EdgeHighlights", "BEVEL")
        bevel.width = spec.bevel
        bevel.segments = CONFIG.get("bevel_segments", 3)
        bevel.limit_method = "ANGLE"
        bevel.angle_limit = math.radians(32)
        bevel.use_clamp_overlap = True
        if hasattr(bevel, "harden_normals"):
            bevel.harden_normals = True
    return obj


def packed_uv_for_object(bpy, obj, scene):
    """Optional context-controlled automatic UV layout, object kept editable."""
    view_layer = scene.view_layers[0]
    old_active = view_layer.objects.active
    old_selected = [o for o in scene.objects if o.select_get(view_layer=view_layer)]
    try:
        with bpy.context.temp_override(scene=scene, view_layer=view_layer):
            for o in old_selected:
                o.select_set(False, view_layer=view_layer)
            obj.select_set(True, view_layer=view_layer)
            view_layer.objects.active = obj
            layer = obj.data.uv_layers.get("UV1_Packed") or obj.data.uv_layers.new(name="UV1_Packed")
            obj.data.uv_layers.active = layer
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.02,
                                     area_weight=.1, correct_aspect=True, scale_to_bounds=True)
            bpy.ops.object.mode_set(mode="OBJECT")
            obj.data.uv_layers.active_index = 0
    finally:
        with bpy.context.temp_override(scene=scene, view_layer=view_layer):
            if obj.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            obj.select_set(False, view_layer=view_layer)
            for o in old_selected:
                o.select_set(True, view_layer=view_layer)
            view_layer.objects.active = old_active


def aim_object(obj, target):
    from mathutils import Vector
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_stage(bpy, scene, collection, model):
    c = model.cfg
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "METERS"
    world = bpy.data.worlds.new("AS07_Daylight")
    world.use_nodes = True
    n, links = world.node_tree.nodes, world.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputWorld")
    bg = n.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = .35
    sky = n.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(29)
    sky.sun_rotation = math.radians(135)
    sky.sun_intensity = .60
    links.new(sky.outputs["Color"], bg.inputs["Color"])
    links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = world
    sun_data = bpy.data.lights.new("AS07_Sun", "SUN")
    sun_data.energy = 2.0
    sun_data.angle = math.radians(5)
    sun_data.color = (1.0, .88, .72)
    sun = bpy.data.objects.new("AS07_Sun", sun_data); collection.objects.link(sun)
    sun.rotation_euler = (math.radians(32), math.radians(-22), math.radians(-35))
    if c["add_practical_lights"]:
        for i, spec in enumerate(model.lights):
            data = bpy.data.lights.new(f"AS07_Practical_{i:02d}", "AREA")
            data.energy = spec["power"]
            data.shape = "RECTANGLE"
            data.size = .16
            data.size_y = spec["size"]
            data.color = (1.0, .87, .68)
            obj = bpy.data.objects.new(data.name, data); collection.objects.link(obj)
            obj.location = spec["location"]   # default -Z emission faces downward
    apex = c["eave_height"] + c["roof_rise"]
    camera_specs = {
        "CAM_Hero": ((c["span"] * 1.5, -c["depth"] * 1.20, apex * 2.5), (0, c["depth"] * .31, apex * .44), 42),
        "CAM_Interior": ((c["span"] * .23, -6.7, 3.8), (0, c["depth"] * .62, 3.9), 26),
        "CAM_Front": ((0, -c["span"] * 1.85, apex * .6), (0, 3.0, apex * .48), 46),
        "CAM_Detail": ((-model.half + 5.0, -2.7, 3.0), (-model.half, 4.7, 3.8), 52),
    }
    for name, (location, target, lens) in camera_specs.items():
        data = bpy.data.cameras.new(name); data.lens = lens; data.clip_end = 1000
        obj = bpy.data.objects.new(name, data); collection.objects.link(obj)
        obj.location = location; aim_object(obj, target)
        if name == "CAM_Hero":
            scene.camera = obj
    if c["render_engine"] == "CYCLES":
        scene.render.engine = "CYCLES"
        scene.cycles.samples = int(c["render_samples"])
        scene.cycles.use_denoising = True
        # Do not assume CUDA/OptiX availability or mutate the user's preferences.
    else:
        succeeded = False
        for name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            try:
                scene.render.engine = name
                succeeded = True
                break
            except (TypeError, ValueError):
                pass
        if not succeeded:
            log("EEVEE engine unavailable; using Cycles.")
            scene.render.engine = "CYCLES"
    scene.render.resolution_x = int(c["resolution_x"])
    scene.render.resolution_y = int(c["resolution_y"])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    try:
        scene.view_settings.view_transform = "AgX"
    except (TypeError, ValueError):
        pass
    scene.view_settings.exposure = .1
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 240


def create_blender_scene(model):
    import bpy
    if bpy.app.version < (4, 2, 0):
        raise RuntimeError("This script targets Blender 4.2+. Use a current Blender 4.5 LTS build.")
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        raise RuntimeError("Switch Blender to Object Mode before running the generator.")
    scene = bpy.data.scenes.new("AS07_AircraftShelter")
    scene["AS07_generator_version"] = VERSION
    scene["AS07_config"] = json.dumps(model.cfg, ensure_ascii=False)
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    root = bpy.data.collections.new("AS07 | AIRCRAFT SHELTER")
    scene.collection.children.link(root)
    groups = {}
    for name in ("Structure", "Apron", "Markings", "Fittings", "Props", "Door", "Presentation", "Cameras_Lights"):
        coll = bpy.data.collections.new("AS07_" + name)
        root.children.link(coll); groups[name] = coll
    anchor = bpy.data.objects.new("AS07_MaterialCoordinates", None)
    groups["Cameras_Lights"].objects.link(anchor)
    anchor.empty_display_type = "PLAIN_AXES"; anchor.empty_display_size = .5
    anchor.hide_render = True
    mats = make_materials(bpy, anchor)
    objects = []
    for spec in model.parts:
        if not spec.faces:
            continue
        obj = make_mesh_object(bpy, spec, groups[spec.group], mats)
        for mod in obj.modifiers:
            if mod.type == "BEVEL":
                mod.segments = model.cfg["bevel_segments"]
        if spec.group == "Door":
            obj.rotation_euler.z = -math.radians(model.cfg["door_open_degrees"])
            obj["AS07_hinge"] = "Rotate local Z; closed angle = 0 degrees."
        if model.cfg["create_packed_uv"] and spec.group != "Presentation":
            packed_uv_for_object(bpy, obj, scene)
        objects.append(obj)
    for i, label in enumerate(model.labels):
        data = bpy.data.curves.new(f"AS07_Label_{i:02d}", "FONT")
        data.body = label["body"]; data.size = label["size"]
        data.align_x = label["align"]; data.align_y = "CENTER"
        data.space_character = 1.08; data.extrude = .001
        data.resolution_u = 6
        obj = bpy.data.objects.new(f"SM_AS07_Label_{i:02d}", data)
        groups[label["group"]].objects.link(obj)
        obj.location = label["location"]; obj.rotation_euler = label["rotation"]
        data.materials.append(mats[label["material"]])
        obj["AS07_group"] = label["group"]; obj["AS07_generated"] = True
        objects.append(obj)
    setup_stage(bpy, scene, groups["Cameras_Lights"], model)
    scene.view_layers[0].update()
    # Set an uncluttered camera view without changing other scenes or preferences.
    if bpy.context.screen is not None:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.clip_end = 1000
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.overlay.show_floor = False
    log(f"Scene created: {scene.name} | {len(objects)} render objects")
    return scene, objects, mats


def output_directory(config):
    if config["output_directory"].strip():
        return Path(os.path.expandvars(os.path.expanduser(config["output_directory"]))).resolve()
    return Path.home() / "AS07_Output" / time.strftime("%Y%m%d_%H%M%S")


def safe_path(directory, stem, suffix):
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / (stem + suffix)
    i = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{i:02d}{suffix}"
        i += 1
    return candidate


def export_fbx_package(scene, objects, model, directory):
    """Export one render mesh + matching collision per FBX group.

    Geometry is evaluated into a temporary scene; editable source objects survive.
    Door is exported closed with its own hinge pivot. Root groups keep origin 0.
    The manifest intentionally records Blender coordinates; UE import axes/scale
    must be checked on the target project's FBX/Interchange import path.
    """
    import bpy
    from mathutils import Matrix, Vector
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    source_layer = scene.view_layers[0]
    stage = bpy.data.scenes.new("AS07_EXPORT_TEMP")
    stage.unit_settings.system = "METRIC"; stage.unit_settings.scale_length = 1.0
    old_scene = bpy.context.window.scene if bpy.context.window else None
    result = {"generator": VERSION, "blender_version": bpy.app.version_string,
              "units": "metres", "entrance_direction_blender": "-Y", "modules": [],
              "important": "Procedural shaders are not baked. UE5.8 import untested. Confirm scale/orientation in target project."}
    try:
        with bpy.context.temp_override(scene=scene, view_layer=source_layer):
            depsgraph = bpy.context.evaluated_depsgraph_get()
            for group in ("Structure", "Apron", "Markings", "Fittings", "Props", "Door"):
                selected = [o for o in objects if o.get("AS07_group") == group]
                if not selected:
                    continue
                pivot = Vector((0, 0, 0))
                if group == "Door":
                    pivot = selected[0].location.copy()
                vertices, faces, face_materials, material_list, uv_faces, face_smooth = [], [], [], [], [], []
                for src in selected:
                    # Door transform removed so the local model exports in closed rest pose.
                    transform = (Matrix.Translation(src.location) if group == "Door" else src.matrix_world.copy())
                    evaluated = src.evaluated_get(depsgraph)
                    mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
                    try:
                        off = len(vertices)
                        vertices.extend(tuple(transform @ v.co - pivot) for v in mesh.vertices)
                        mapping = []
                        for mat in mesh.materials:
                            if mat not in material_list:
                                material_list.append(mat)
                            mapping.append(material_list.index(mat))
                        layer = mesh.uv_layers.get("UV0_Tile") or mesh.uv_layers.active
                        for poly in mesh.polygons:
                            faces.append(tuple(off + i for i in poly.vertices))
                            face_smooth.append(poly.use_smooth)
                            face_materials.append(mapping[poly.material_index] if mapping else 0)
                            uv_faces.append([tuple(layer.data[j].uv) for j in poly.loop_indices] if layer else [(0, 0)] * len(poly.vertices))
                    finally:
                        bpy.data.meshes.remove(mesh)
                data = bpy.data.meshes.new("AS07_EXPORT_Mesh")
                data.from_pydata(vertices, [], faces); data.update()
                for mat in material_list:
                    data.materials.append(mat)
                uv = data.uv_layers.new(name="UV0_Tile")
                for p, mid, coords, smooth in zip(data.polygons, face_materials, uv_faces, face_smooth):
                    p.material_index = mid
                    p.use_smooth = smooth
                    for j, coord in zip(p.loop_indices, coords):
                        uv.data[j].uv = coord
                obj = bpy.data.objects.new("SM_AS07_" + group, data)
                stage.collection.objects.link(obj)
                # Triangulate the evaluated export copy, never the source mesh.
                import bmesh
                bm = bmesh.new(); bm.from_mesh(data)
                bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method="BEAUTY", ngon_method="BEAUTY")
                bm.to_mesh(data); bm.free(); data.update()
                if hasattr(data, "set_sharp_from_angle"):
                    data.set_sharp_from_angle(angle=math.radians(40))
                if model.cfg["create_packed_uv"]:
                    packed_uv_for_object(bpy, obj, stage)
                exports = [obj]
                index = 0
                for spec in model.collisions:
                    if spec["group"] != group:
                        continue
                    cp = MeshPart("Collision", "Collision", 0)
                    cp.box(sub(spec["center"], pivot), spec["dims"], "Concrete")
                    cd = bpy.data.meshes.new("AS07_CollisionMesh")
                    cd.from_pydata(cp.vertices, [], cp.faces); cd.update()
                    co = bpy.data.objects.new(f"UCX_{obj.name}_{index:02d}", cd)
                    stage.collection.objects.link(co); exports.append(co); index += 1
                if group == "Structure":
                    # Convex trapezoidal roof pieces, preserving the open interior.
                    n = 18
                    for j in range(n):
                        ta = -model.alpha + 2 * model.alpha * j / n + .0002
                        tb = -model.alpha + 2 * model.alpha * (j + 1) / n - .0002
                        r0, r1 = model.radius + .18, model.radius + .40
                        profile = [(r0 * math.sin(ta), model.zcenter + r0 * math.cos(ta)),
                                   (r0 * math.sin(tb), model.zcenter + r0 * math.cos(tb)),
                                   (r1 * math.sin(tb), model.zcenter + r1 * math.cos(tb)),
                                   (r1 * math.sin(ta), model.zcenter + r1 * math.cos(ta))]
                        cp = MeshPart("Collision", "Collision", 0)
                        cp.prism(profile, (0, -.1, 0), ((1, 0, 0), (0, 0, 1), (0, 1, 0)), model.depth + .2, "Concrete")
                        cd = bpy.data.meshes.new("AS07_RoofCollision"); cd.from_pydata(cp.vertices, [], cp.faces); cd.update()
                        co = bpy.data.objects.new(f"UCX_{obj.name}_{index:02d}", cd)
                        stage.collection.objects.link(co); exports.append(co); index += 1
                with bpy.context.temp_override(scene=stage, view_layer=stage.view_layers[0]):
                    if bpy.context.window is not None:
                        bpy.context.window.scene = stage
                    for ob in exports:
                        ob.select_set(True, view_layer=stage.view_layers[0])
                    stage.view_layers[0].objects.active = obj
                    path = safe_path(directory, "SM_AS07_" + group, ".fbx")
                    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={"MESH"},
                        global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                        axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True, mesh_smooth_type="FACE",
                        add_leaf_bones=False, bake_anim=False, path_mode="AUTO")
                result["modules"].append({"file": path.name, "group": group, "source_pivot_blender_m": list(pivot),
                                           "collision_hulls": index, "material_slots": len(material_list)})
                for ob in exports:
                    me = ob.data; bpy.data.objects.remove(ob, do_unlink=True)
                    if me.users == 0:
                        bpy.data.meshes.remove(me)
                if bpy.context.window is not None:
                    bpy.context.window.scene = scene
        result_path = safe_path(directory, "AS07_ExportManifest", ".json")
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result
    finally:
        if bpy.context.window is not None and old_scene is not None:
            bpy.context.window.scene = old_scene
        # Always clean temporary export geometry, including on operator failure.
        for ob in list(stage.objects):
            data = ob.data; bpy.data.objects.remove(ob, do_unlink=True)
            if data and data.users == 0 and isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
        bpy.data.scenes.remove(stage)


def export_glb_scene(scene, objects, directory):
    import bpy
    layer = scene.view_layers[0]
    old_active = layer.objects.active
    old_selected = [o for o in scene.objects if o.select_get(view_layer=layer)]
    try:
        with bpy.context.temp_override(scene=scene, view_layer=layer):
            for obj in old_selected:
                obj.select_set(False, view_layer=layer)
            for obj in objects:
                if obj.get("AS07_group") != "Presentation" and obj.type == "MESH":
                    obj.select_set(True, view_layer=layer)
            path = safe_path(directory, "AS07_Shelter", ".glb")
            bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=True,
                                      export_cameras=False, export_lights=False)
            return path
    finally:
        for obj in scene.objects:
            obj.select_set(False, view_layer=layer)
        for obj in old_selected:
            obj.select_set(True, view_layer=layer)
        layer.objects.active = old_active


def main():
    started = time.perf_counter()
    model = ShelterModel(CONFIG).build()
    report = validate_model(model)
    if report["errors"]:
        raise RuntimeError("Geometry validation failed:\n" + "\n".join(report["errors"]))
    log(f"Geometry PASS: {report['part_count']} parts, {report['total_triangles']:,} base triangles")
    if "--self-test" in sys.argv:
        print(json.dumps(report, indent=2))
        return
    try:
        import bpy
    except ImportError as exc:
        raise RuntimeError("Run this file in Blender's Scripting workspace, not system Python. Use --self-test for geometry-only tests.") from exc
    scene, objects, mats = create_blender_scene(model)
    directory = output_directory(model.cfg)
    if any(model.cfg[k] for k in ("export_fbx", "export_glb", "save_blend", "render_now")):
        directory.mkdir(parents=True, exist_ok=True)
        safe_path(directory, "AS07_GeometryReport", ".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if model.cfg["export_fbx"]:
        try:
            export_fbx_package(scene, objects, model, directory / "Unreal_FBX")
            log("FBX export complete; inspect the export manifest and validate in UE.")
        except Exception:
            log("FBX EXPORT FAILED. Generated source scene is intact.\n" + traceback.format_exc())
    if model.cfg["export_glb"]:
        try:
            log("GLB: " + str(export_glb_scene(scene, objects, directory)))
        except Exception:
            log("GLB EXPORT FAILED. Generated source scene is intact.\n" + traceback.format_exc())
    if model.cfg["save_blend"]:
        path = safe_path(directory, "AS07_Shelter", ".blend")
        # copy=True avoids switching the current project filepath to the export copy.
        bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=True)
        log("Blend copy saved: " + str(path))
    if model.cfg["render_now"]:
        scene.render.filepath = str(safe_path(directory, "AS07_Hero", ".png"))
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
            bpy.ops.render.render(write_still=True, scene=scene.name)
        log("Render: " + scene.render.filepath)
    # Keep handles in Blender's driver namespace for optional console use.
    bpy.app.driver_namespace["AS07"] = {"scene": scene, "objects": objects, "model": model,
        "export_fbx": lambda: export_fbx_package(scene, objects, model, output_directory(model.cfg) / "Unreal_FBX")}
    log(f"Finished in {time.perf_counter() - started:.1f}s. Choose CAM_Hero / CAM_Interior / CAM_Front / CAM_Detail.")
    log("Default run does not save, export or render automatically. Existing scenes were not deleted.")


if __name__ == "__main__":
    main()

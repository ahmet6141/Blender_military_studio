# SPDX-License-Identifier: MIT
"""14 bounded visual facade modules; real openings, shared material roles and pivots.
Source assembly coordinates: X across facade, Y inward, Z upward.
Output coordinates match MB01: +X inward, +Y left, +Z upward, metre units.
This is an artistic mesh assembly, not a structural or protection calculation.
"""
from dataclasses import asdict
from math import pi, radians, floor, ceil
from ..vendor import as07_reference as A
from .catalog import require
from .contracts import ModuleInput, digest
from ..mb_common import canonical, _newell_normal

VERSION = '0.2.0-alpha.1'


class ModuleModel:
    def __init__(self, settings):
        self.cfg = settings.checked()
        self.spec = require(settings.module_id)
        self.parts = []
        self.labels = []
        self.doors = []
        self.ports = []
        self.openings = []
        self.wall_boxes = []
        self.notes = ['One facade module, not a complete building.',
                      'Assembly contacts are intentional; not a Boolean-unioned CAD solid.',
                      'No structural, military-code or ballistic performance is represented.']
        self._parts = {}
        self._finished = False

    def part(self, role, group='DETAIL', bevel=.005, pivot=(0., 0., 0.)):
        if role not in self._parts:
            name = 'SM_MB02_' + self.spec.id.replace('.', '_') + '__' + role
            p = A.MeshPart(name, group, 0. if self.cfg.detail == 'DRAFT' else bevel, pivot)
            self.parts.append(p)
            self._parts[role] = p
        return self._parts[role]

    def box(self, role, center, dims, mat, group='DETAIL', bevel=.005, axes=A.IDENTITY):
        self.part(role, group, bevel).box(center, dims, mat, axes)
        if role == 'Wall':
            self.wall_boxes.append({'center_source': tuple(center), 'dims': tuple(dims)})

    def wall(self, aperture=None, metal=False):
        w, h, t = self.cfg.width, self.cfg.height, self.cfg.thickness
        if metal:
            # Hangar wall: profiled steel skin over an insulated core (clad()). The aperture is
            # a real hole, recorded exactly as before for ports, landings and the hidden-wall QA.
            holes = []
            if aperture is not None:
                ow, bottom, oh = aperture
                top = bottom + oh
                if not (0. < ow < w-.18 and 0. <= bottom < top <= h-.12):
                    raise ValueError('Aperture does not fit the bounded module.')
                self.openings.append({'width': ow, 'bottom': bottom, 'height': oh,
                                      'center_output': canonical((0, t/2, bottom+oh/2))})
                holes = [(-ow/2, bottom, ow/2, top)]
            self.clad(holes)
            return
        material = self.cfg.style.wall_material
        if aperture is None:
            self.box('Wall', (0, t/2, h/2), (w, t, h), material, 'BODY')
        else:
            ow, bottom, oh = aperture
            top = bottom + oh
            if not (0. < ow < w-.18 and 0. <= bottom < top <= h-.12):
                raise ValueError('Aperture does not fit the bounded module.')
            self.openings.append({'width': ow, 'bottom': bottom, 'height': oh,
                                  'center_output': canonical((0, t/2, bottom+oh/2))})
            pier = (w-ow)/2
            for sign in (-1, 1):
                self.box('Wall', (sign*(ow/2+pier/2), t/2, h/2), (pier, t, h), material, 'BODY')
            if bottom > 0:
                self.box('Wall', (0, t/2, bottom/2), (ow, t, bottom), material, 'BODY')
            self.box('Wall', (0, t/2, (top+h)/2), (ow, t, h-top), material, 'BODY')
        # Applied base facing, clipped at all door openings; not a duplicate floor.
        baseh = .38
        spans = [(-w/2, w/2)]
        if aperture is not None and aperture[1] < baseh:
            spans = [(-w/2, -aperture[0]/2), (aperture[0]/2, w/2)]
        for lo, hi in spans:
            self.box('Plinth', ((lo+hi)/2, -.023, baseh/2), (hi-lo, .046, baseh),
                     self.cfg.style.plinth_material, 'FACADE', .004)
        # Fine top reveal: visually coherent with a later continuous coping module.
        self.box('HeadReveal', (0, -.009, h-.105), (w, .018, .014), 'Joint', 'DETAIL', .001)

    # ---- Hangar wall build-up (wall(metal=True)) ------------------------------------------
    # Outside -> inside: trapezoidal steel sheet laid vertically ("35/250": 36 mm crest, 22 mm
    # webs, ~170 mm pan, 35 mm deep), whose crest plane is the module face y=0; a 2 mm air gap;
    # then the girt/insulation/liner core 'Wall' [CLAD_CORE, t] whose inner face is the light
    # liner seen from inside. Pressed-steel flashings are 2-2.5 mm thick, in two layers outside
    # the crest plane: L1 y[-.004,-.0015] (opening face legs, corner angles), L2 y[-.0065,-.0045]
    # (eave/verge trims lapping over L1). Parallel faces of different parts stay >= 1.5 mm apart.
    CLAD_DEPTH = .035; CLAD_CORE = .037; CLAD_PITCH = .25; CLAD_CREST = .036; CLAD_WEB = .022
    CLAD_BASE = .50; CLAD_TOP = .006      # sheet foot (20 mm over the .48 plinth); 6 mm under the top
    YZX = ((0, 1, 0), (0, 0, 1), (1, 0, 0))   # prism axes: profile (y, z), extruded along +x
    # Base drip flashing over the plinth (y, z): top falls ~7 deg outward, drip leg 12 mm proud.
    BASE_FLASH = ((.037, .499), (-.060, .487), (-.060, .450), (-.058, .450), (-.058, .485), (.037, .497))
    # Opening head flashing (y, z-z1): 100 mm face leg (L1), sloped ledge, 24 mm drip leg.
    HEAD_FLASH = ((-.0015, .100), (-.0040, .100), (-.0040, .012), (-.0450, .004), (-.0450, -.012),
                  (-.0430, -.012), (-.0430, .0015), (-.0015, .0095))
    # Rain-defence louvre Z blade (y, z-zc): 2.5 mm pressed blade, kicked-up rear lip, front drip.
    BLADE = ((.130, .035), (.030, -.035), (.030, -.050), (.0275, -.050), (.0275, -.0335), (.1285, .0372))

    @staticmethod
    def eave_profile(h, back=.037):
        """Eave trim (y, z): 100 mm face leg in L2, return into the core under the roof skin."""
        return ((-.0065, h-.100), (-.0045, h-.100), (-.0045, h-.005), (back, h-.005), (back, h-.003), (-.0065, h-.003))

    @staticmethod
    def sill_profile(ys):
        """Sloped sill flashing (y, z-z0): tucks under the frame at ys, ~5 deg fall, 28 mm drip."""
        return ((ys, -.0005), (-.055, -.012), (-.055, -.040), (-.0525, -.040), (-.0525, -.0145), (ys, -.003))

    @staticmethod
    def clad_pitch(width):
        """Rib pitch for a run: an EVEN number of periods with mid-pan at both ends, so abutting
        modules meet pan-to-pan, the rib rhythm and the alternate-pan fixing rhythm continue."""
        return width/(2*max(1, round(width/(2*ModuleModel.CLAD_PITCH))))

    @staticmethod
    def profile_sheet(part, u0, u1, pitch, origin, zlo, zhi, holes=(), cuts=(), frame=None, mat='RoofOlive'):
        """Cap-less trapezoidal sheet: one vertical quad per profile facet and z band. Local
        (u, d, z) maps to o+u*eu+d*ed+z*Z with eu x ed = +Z; d=0 is the crest plane, pans at
        d=CLAD_DEPTH (inward), mid-pan at origin+k*pitch. zlo/zhi: numbers or callables of u,
        holes: (u0, z0, u1, z1), cuts: extra breakpoints (ridge). Returns the face count."""
        C = ModuleModel
        o, eu, ed = frame or ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
        lo_f = zlo if callable(zlo) else (lambda u, v=zlo: v)
        hi_f = zhi if callable(zhi) else (lambda u, v=zhi: v)
        a = (pitch-C.CLAD_CREST-2*C.CLAD_WEB)/2
        # Four facets per period (web, crest, web, pan); mid-pan is a knot only at sheet ends.
        local = ((a, C.CLAD_DEPTH), (a+C.CLAD_WEB, 0.), (a+C.CLAD_WEB+C.CLAD_CREST, 0.), (a+2*C.CLAD_WEB+C.CLAD_CREST, C.CLAD_DEPTH))
        knots = [(origin+k*pitch+r, d) for k in range(floor((u0-origin)/pitch)-1, ceil((u1-origin)/pitch)+2) for r, d in local]
        # Ends, ridge and hole jambs inside a facet are interpolated on its exact knots (split
        # facets stay collinear); a cut within 1e-6 of a knot is represented by that knot.
        cut = sorted({u0, u1} | {c for c in cuts if u0 < c < u1} | {v for q in holes for v in (q[0], q[2]) if u0 < v < u1})
        pts = []
        for (ua, da), (ub, db) in zip(knots, knots[1:]):
            if u0-1e-6 <= ua <= u1+1e-6:
                pts.append((ua, da))
            pts += [(c, da+(db-da)*(c-ua)/(ub-ua)) for c in cut if ua+1e-6 < c < ub-1e-6]
        pts.sort()
        verts, faces, index = [], [], {}
        def pt(u, d, z):
            # Facets of one band share their knot edges: each band is one connected strip
            # (one lightmap island, half the vertices); hole jambs keep T-junctions only.
            key = (round(u, 9), round(z, 9))
            if key not in index:
                index[key] = len(verts); verts.append((o[0]+u*eu[0]+d*ed[0], o[1]+u*eu[1]+d*ed[1], z))
            return index[key]
        for (ua, da), (ub, db) in zip(pts, pts[1:]):
            if ub-ua < 1e-6:
                continue
            um = (ua+ub)/2
            bands = [(lo_f(ua), lo_f(ub), hi_f(ua), hi_f(ub))]
            for q in holes:
                if q[0]-1e-9 <= um <= q[2]+1e-9:
                    bands = [b for la, lb, ha, hb in bands for b in
                             ((la, lb, min(ha, q[1]), min(hb, q[1])), (max(la, q[3]), max(lb, q[3]), ha, hb))]
            for la, lb, ha, hb in bands:
                if min(ha-la, hb-lb) < .004:
                    continue
                faces.append((pt(ua, da, la), pt(ub, db, lb), pt(ub, db, hb), pt(ua, da, ha)))
        if faces:
            part.primitive(verts, faces, mat, closed=False)
        return len(faces)

    @staticmethod
    def fixings(part, u0, u1, pitch, origin, rows, holes=(), zhi=None, frame=None, mat='RoofOliveLight'):
        """Self-drilling screws with sealing washers in alternate pans on girt lines: 4-facet
        heads (16 mm, 6 mm proud). rows: (z, every); pan k carries one when k % every == 1."""
        C = ModuleModel
        o, eu, ed = frame or ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
        def pt(u, d, z):
            return (o[0]+u*eu[0]+d*ed[0], o[1]+u*eu[1]+d*ed[1], z)
        verts, faces = [], []
        db, da = C.CLAD_DEPTH-.0005, C.CLAD_DEPTH-.0065
        for z, every in rows:
            for k in range(ceil((u0-origin)/pitch), floor((u1-origin)/pitch)+1):
                u = origin+k*pitch
                if k % every != 1 or not u0+.05 < u < u1-.05:
                    continue
                if zhi and z > zhi(u)-.20:
                    continue
                if any(q[0]-.06 < u < q[2]+.06 and q[1]-.08 < z < q[3]+.12 for q in holes):
                    continue
                i = len(verts)
                verts += [pt(u, da, z), pt(u-.008, db, z-.008), pt(u+.008, db, z-.008), pt(u+.008, db, z+.008), pt(u-.008, db, z+.008)]
                faces += [(i, i+1, i+2), (i, i+2, i+3), (i, i+3, i+4), (i, i+4, i+1)]
        if faces:
            part.primitive(verts, faces, mat, closed=False)
        return len(faces)

    @staticmethod
    def girt_rows(z0, z1, step=1.8, top=None):
        """Sheeting-rail (girt) lines from z0 to z1, evenly spaced at <= step; with `top` the
        same spacing continues above z1 (gables) while below top. Alternate pans everywhere."""
        n = max(1, ceil((z1-z0)/step)); s = (z1-z0)/n
        return [(z0+s*i, 2) for i in range(n+1 if top is None else int((top-z0)/s)+1)]

    @staticmethod
    def open_prism(part, profile, origin, axes, length, mat):
        """Side faces of a prism only (ends buried in a frame): no hidden caps."""
        p = list(profile)
        if A.polygon_area(p) < 0:
            p.reverse()
        n = len(p)
        v = [A.local_to_world((x, y, z), origin, axes) for z in (0., length) for x, y in p]
        part.primitive(v, [(i, (i+1) % n, (i+1) % n+n, i+n) for i in range(n)], mat, closed=False)

    @staticmethod
    def tone_faces(part, outward, outer, inner):
        """Two-tone core: faces whose unit normal points along any `outward` vector take the
        exterior coating, the rest (interior face, reveals) the liner. Zero triangles."""
        names = [outer, inner]; ids = []
        for f in part.faces:
            n = _newell_normal([part.vertices[j] for j in f]); l = sum(c*c for c in n)**.5 or 1.
            ids.append(0 if any(sum(n[k]*v[k] for k in range(3))/l > .5 for v in outward) else 1)
        part.material_names, part.material_ids = names, ids

    @staticmethod
    def shift(part, pick, move):
        """Move the vertices selected by pick(v) (mitred flashing ends) and re-plan the metre
        UVs of every face that touches them, with the same rule primitive() uses."""
        moved = {i for i, v in enumerate(part.vertices) if pick(v)}
        part.vertices = [move(v) if i in moved else v for i, v in enumerate(part.vertices)]
        for fi, f in enumerate(part.faces):
            if moved.isdisjoint(f):
                continue
            a, b, c = (part.vertices[f[j]] for j in range(3))
            n = A.cross(A.sub(b, a), A.sub(c, a))
            ax = ((1, 2), (0, 2), (0, 1))[max(range(3), key=lambda k: abs(n[k]))]
            part.uvs[fi] = [(part.vertices[j][ax[0]], part.vertices[j][ax[1]]) for j in f]

    def clad(self, holes=(), sheet=True):
        """Hangar wall build-up around real apertures (x0, z0, x1, z1): core, plinth facing,
        base drip flashing, eave trim, profiled sheet and (HERO) girt-line fixings."""
        C = ModuleModel
        w, h, t = self.cfg.width, self.cfg.height, self.cfg.thickness
        # Core: one column of boxes per aperture x-band, no box across a clear opening.
        xs = sorted({-w/2, w/2} | {v for q in holes for v in (q[0], q[2])})
        for a, b in zip(xs, xs[1:]):
            xm = (a+b)/2; z = 0.
            for lo, hi in sorted((q[1], q[3]) for q in holes if q[0] < xm < q[2])+[(h, h)]:
                if lo > z+1e-9:
                    self.box('Wall', (xm, (C.CLAD_CORE+t)/2, (z+lo)/2), (b-a, t-C.CLAD_CORE, lo-z), 'RoofOlive', 'BODY', 0.)
                z = max(z, hi)
        # Concrete plinth facing and its drip flashing, clipped at door cuts. The flashing stops
        # 1 mm short of a door cut so its closed end never meets the door frame.
        spans = []; x = -w/2
        for a, b in sorted((q[0], q[2]) for q in holes if q[1] < .48)+[(w/2, w/2)]:
            if a > x+1e-9:
                spans.append((x, a))
            x = max(x, b)
        for lo, hi in spans:
            self.box('Plinth', ((lo+hi)/2, -.0045, .24), (hi-lo, .083, .48), self.cfg.style.plinth_material, 'FACADE', .004)
            f0, f1 = lo+(.001 if lo > -w/2+1e-9 else 0.), hi-(.001 if hi < w/2-1e-9 else 0.)
            self.part('BaseFlashing', 'DETAIL', 0.).prism(C.BASE_FLASH, (f0, 0., 0.), C.YZX, f1-f0, 'RoofOliveLight')
        self.part('EaveTrim', 'DETAIL', 0.).prism(C.eave_profile(h), (-w/2, 0., 0.), C.YZX, w, 'RoofOliveLight')
        if not sheet:
            return
        # The sheet runs 11 mm under sill flashings (their underside is at z0-.010 at the crest
        # plane); a door cut stays raw at the floor and gets the doors' own jamb trims.
        p = C.clad_pitch(w)
        cut = [(q[0], q[1]-.011 if q[1] > .3 else q[1], q[2], q[3]+.0005) for q in holes]
        C.profile_sheet(self.part('Cladding', 'BODY', 0.), -w/2, w/2, p, -w/2, C.CLAD_BASE, h-C.CLAD_TOP, cut)
        if self.cfg.detail == 'HERO':
            C.fixings(self.part('CladFixings', 'DETAIL', 0.), -w/2, w/2, p, -w/2, C.girt_rows(.58, h-.166), holes)

    def opening_trims(self, x0, z0, x1, z1, yF, ys, sill=True):
        """Pressed-steel trims of one aperture: head flashing with drip, jamb angles (face leg
        + reveal return to the frame face yF), head soffit lining and a sloped sill flashing
        with drip and 100 mm stop ends that tucks under the frame at depth ys."""
        C = ModuleModel; mat = 'RoofOliveLight'
        self.part('HeadFlashing', 'DETAIL', 0.).prism([(y, z1+z) for y, z in C.HEAD_FLASH], (x0-.09, 0., 0.), C.YZX, x1-x0+.18, mat)
        lo = z0-.006 if sill else max(z0, C.CLAD_BASE)
        for s, xe in ((-1, x0), (1, x1)):
            # Face leg butts 1 mm under the head ledge; the return lines the reveal 2.5 mm thick.
            self.box('JambTrims', (xe+s*.045, -.00275, (lo+z1+.008)/2), (.09, .0025, z1+.008-lo), mat, 'DETAIL', 0.)
            if yF > .006:
                self.box('JambTrims', (xe-s*.00125, (yF-.004)/2, (z0+z1-.0025)/2), (.0025, yF+.004, z1-.0025-z0), mat, 'DETAIL', 0.)
        if yF > .006:
            self.box('JambTrims', ((x0+x1)/2, (yF-.0015)/2, z1-.0015), (x1-x0, yF+.0015, .002), mat, 'DETAIL', 0.)
        if sill:
            self.part('SillFlashing', 'DETAIL', 0.).prism([(y, z0+z) for y, z in C.sill_profile(ys)], (x0-.10, 0., 0.), C.YZX, x1-x0+.20, mat)

    def louvre(self, x0, z0, x1, z1):
        """Factory weather louvre in one powder coat: pressed channel frame set 4.5 mm behind
        the crest plane, mid mullion over 1.6 m, Z blades at ~75 mm pitch overlapping 12 mm (no
        sight line) with ends buried 6 mm in the jambs, bird mesh behind, perimeter trims."""
        f = .07; mat = self.cfg.style.frame_material
        for x in (x0+f/2, x1-f/2):
            self.box('VentFrame', (x, .0995, (z0+z1)/2), (f, .15, z1-z0), mat, 'FACADE', .003)
        for z in (z0+f/2, z1-f/2):
            self.box('VentFrame', ((x0+x1)/2, .0995, z), (x1-x0-2*f, .15, f), mat, 'FACADE', .003)
        if x1-x0 > 1.6:
            self.box('VentFrame', ((x0+x1)/2, .0795, (z0+z1)/2), (.05, .13, z1-z0-2*f), mat, 'FACADE', .003)
        first, last = z0+f+.052, z1-f-.0392
        n = max(3, int((last-first)/.075)+1); bl = self.part('VentBlades', 'DETAIL', 0.)
        for i in range(n):
            zc = first+(last-first)*i/(n-1)
            ModuleModel.open_prism(bl, [(y, zc+z) for y, z in ModuleModel.BLADE], (x0+f-.006, 0., 0.), ModuleModel.YZX, x1-x0-2*f+.012, mat)
        self.box('VentScreen', ((x0+x1)/2, .143, (z0+z1)/2), (x1-x0-2*f+.006, .006, z1-z0-2*f+.006), 'Interior', 'DETAIL', 0.)
        self.opening_trims(x0, z0, x1, z1, .004, .0995)

    def cassettes(self):
        """Flat folded cassette trays (secret fixed, no screws): 30 mm returns read as the
        folds, 20 mm shadow joints over dark joint rails."""
        C = ModuleModel
        w, h = self.cfg.width, self.cfg.height; zb, zt, g = C.CLAD_BASE, h-C.CLAD_TOP, .02
        nc = max(1, round(w/2.4)); nr = max(3, round((zt-zb)/1.05)); q = (zt-zb)/nr
        xs = [-w/2+w*j/nc for j in range(nc+1)]; zs = [zb+q*i for i in range(nr+1)]
        for j in range(nc):
            for i in range(nr):
                x0, x1 = xs[j]+g/2, xs[j+1]-g/2; z0 = zs[i]+(g/2 if i else 0.); z1 = zs[i+1]-(g/2 if i < nr-1 else 0.)
                self.box('CassetteTrays', ((x0+x1)/2, .015, (z0+z1)/2), (x1-x0, .030, z1-z0), 'RoofOlive', 'FACADE', .002)
        # Horizontal rails stop 1 mm inside the module edge; vertical rails sit 1.5 mm deeper.
        for i in range(1, nr):
            self.box('CassetteJoints', (0., .0335, zs[i]), (w-.002, .005, .03), 'Joint', 'DETAIL', 0.)
        for x in xs:
            lo, hi = max(-w/2, x-.015), min(w/2, x+.015)
            self.box('CassetteJoints', ((lo+hi)/2, .0335, (zb+zt)/2), (hi-lo, .002, zt-zb), 'Joint', 'DETAIL', 0.)

    def _hangar_glazing(self, ow, bottom, oh, transom, mullion):
        """Aluminium curtain-wall style glazing for hangar walls: perimeter frame, mullions at
        <= 1.5 m with exterior pressure caps, optional transom (2 mm shallower than the mullion
        so no faces coincide at the crossing), glass edges embedded 10 mm, and pressed trims."""
        t = self.cfg.thickness; f, y = .06, min(.09, t*.4); mat = self.cfg.style.frame_material; top = bottom+oh
        for s in (-1, 1):
            self.box('WindowFrames', (s*(ow/2-f/2), y, bottom+oh/2), (f, .11, oh), mat, 'FACADE', .003)
        for z in (bottom+f/2, top-f/2):
            self.box('WindowFrames', (0, y, z), (ow-2*f, .11, f), mat, 'FACADE', .003)
        nb = max(2, ceil(ow/1.5)) if mullion else 1
        for k in range(1, nb):
            x = -ow/2+ow*k/nb
            self.box('WindowFrames', (x, y, bottom+oh/2), (.046, .10, oh-2*f), mat, 'FACADE', .002)
            self.box('PressureCaps', (x, y-.06225, bottom+oh/2), (.050, .0245, oh-2*f), mat, 'DETAIL', .002)
        if transom:
            zt = bottom+oh*.67
            self.box('WindowTransom', (0, y, zt), (ow-2*f, .096, .038), mat, 'FACADE', .002)
            self.box('PressureCaps', (0, y-.06025, zt), (ow-2*f, .0245, .044), mat, 'DETAIL', .002)
        self.box('Glass', (0, y-.010, bottom+oh/2), (ow-2*f+.02, .024, oh-2*f+.02), 'Glass', 'GLASS', 0.)
        self.opening_trims(-ow/2, bottom, ow/2, top, y-.0555, y)

    def frame(self, ow, bottom, oh, transom=False, mullion=True, hangar=False):
        if hangar:
            return self._hangar_glazing(ow, bottom, oh, transom, mullion)
        t = self.cfg.thickness
        f, y = .06, min(.09, t*.4)
        mat = self.cfg.style.frame_material
        for sign in (-1, 1):
            self.box('WindowFrames', (sign*(ow/2-f/2), y, bottom+oh/2), (f, .11, oh), mat, 'FACADE', .003)
        for z in (bottom+f/2, bottom+oh-f/2):
            self.box('WindowFrames', (0, y, z), (ow-2*f, .11, f), mat, 'FACADE', .003)
        if mullion:
            self.box('WindowFrames', (0, y, bottom+oh/2), (.046, .10, oh-.12), mat, 'FACADE', .002)
        if transom:
            self.box('WindowTransom', (0, y, bottom+oh*.67), (ow-.12, .10, .038), mat, 'FACADE', .002)
        self.box('Glass', (0, y+.025, bottom+oh/2), (ow-.12, .014, oh-.12), 'Glass', 'GLASS', 0.)
        # Reveal edges and projecting sill with a shallow underside drip detail.
        for sign in (-1, 1):
            self.box('RevealReturns', (sign*(ow/2+.012), t*.46, bottom+oh/2),
                     (.024, t*.95, oh), self.cfg.style.wall_material, 'FACADE', .002)
        self.box('Sill', (0, .025, bottom-.036), (ow+.16, .38, .072), 'ConcreteLight', 'FACADE', .005)
        self.box('SillDrip', (0, -.119, bottom-.07), (ow+.10, .014, .008), 'Joint', 'DETAIL', .001)

    def window(self, narrow=False, shade=False, unit=False, clerestory=False, glazed=False):
        w, h = self.cfg.width, self.cfg.height
        if clerestory:
            # Hangar clerestory band in the profiled steel wall, aluminium glazing and trims.
            ow, bottom, oh = w-.48, h-1.6, 1.15
            self.wall((ow, bottom, oh), metal=True)
            self.frame(ow, bottom, oh, transom=True, mullion=True, hangar=True)
            return
        if glazed:
            ow, bottom, oh = w-.54, .32, h-.62
        else:
            ow = min(1.20, w*.32) if narrow else min(2.16, w*.55)
            bottom = .88
            oh = min(1.68 if unit else 1.82, h-bottom-.40)
        self.wall((ow, bottom, oh))
        self.frame(ow, bottom, oh, transom=glazed or (not narrow and not unit), mullion=not narrow)
        if unit:
            self.box('Blind', (0, self.cfg.thickness+.05, bottom+oh-.20), (ow-.15, .025, .34), 'Blind', 'DETAIL', .002)
        if shade:
            z = bottom+oh+.14
            for k in range(3):
                self.box('SunshadeFins', (0, -.12-k*.15, z), (ow+.24, .09, .046),
                         'RoofOlive', 'DETAIL', .002)
            for x in (-ow*.37, ow*.37):
                self.box('SunshadeBrackets', (x, -.25, z-.044), (.038, .60, .05),
                         self.cfg.style.frame_material, 'DETAIL', .002)

    def ventilation(self, hangar=False):
        w, h = self.cfg.width, self.cfg.height
        ow = min(w-.60, 2.6)
        if hangar:
            # Hangar louvre: real aperture in the profiled wall, factory weather louvre in it.
            bottom = h*.48; oh = min(1.75, h-bottom-.45)
            self.wall((ow, bottom, oh), metal=True)
            self.louvre(-ow/2, bottom, ow/2, bottom+oh)
            return
        bottom = .98
        oh = min(1.36, h-bottom-.45)
        self.wall((ow, bottom, oh))
        f=.07; mat=self.cfg.style.frame_material
        for x in (-ow/2+f/2, ow/2-f/2):
            self.box('VentFrame', (x, .09, bottom+oh/2), (f, .19, oh), mat, 'FACADE', .003)
        for z in (bottom+f/2, bottom+oh-f/2):
            self.box('VentFrame', (0, .09, z), (ow-.14, .19, f), mat, 'FACADE', .003)
        n=max(4, int((oh-.17)/.13))
        for i in range(n):
            z=bottom+.13+(oh-.26)*i/max(1,n-1)
            self.box('VentBlades', (0, .09, z), (ow-.18, .20, .025), 'RoofOliveLight',
                     'DETAIL', .0015, axes=A.euler_axes(radians(27),0,0))
        # Intentional dark screen; not a claimed performance-rated ventilation assembly.
        self.box('VentScreen', (0,self.cfg.thickness+.017,bottom+oh/2),
                 (ow-.15,.016,oh-.14),'Interior','DETAIL',0.)

    def entry(self, double=False, glazed=False, canopy=False, metal=False):
        w,h,t=self.cfg.width,self.cfg.height,self.cfg.thickness
        ow=min(2.3,w-.7) if double else min(1.18,w-.7)
        dh=2.62 if double else 2.30
        self.wall((ow,0.,dh),metal=metal)
        f=.065; y=min(.095,t*.4); mat=self.cfg.style.frame_material
        for x in (-ow/2+f/2,ow/2-f/2):
            self.box('DoorFrame',(x,y,dh/2),(f,.15,dh),mat,'FACADE',.003)
        self.box('DoorFrame',(0,y,dh-f/2),(ow-.13,.15,f),mat,'FACADE',.003)
        self.box('Threshold',(0,t*.50,.012),(ow-.12,t+.16,.024),'Galvanized','DETAIL',.002)
        count=2 if double else 1
        clear=ow-.15
        leafw=(clear-(.014 if double else 0))/count
        leafh=dh-.10
        for i in range(count):
            c=-clear/2+leafw/2+i*(leafw+.014)
            left = i==0
            px=c-leafw/2 if left else c+leafw/2
            pivot=(px,y-.018,.035)
            p=self.part('DoorLeaf_'+str(i),'DOOR',.003,pivot)
            if glazed:
                a=.065
                for x in (c-leafw/2+a/2,c+leafw/2-a/2):
                    p.box((x,y-.018,.035+leafh/2),(a,.065,leafh),mat)
                for z in (.035+a/2,.035+leafh-a/2):
                    p.box((c,y-.018,z),(leafw-2*a,.065,a),mat)
                p.box((c,y-.018,.035+leafh/2),(leafw-2*a,.014,leafh-2*a),'Glass')
            else:
                p.box((c,y-.018,.035+leafh/2),(leafw,.065,leafh),'RoofOlive')
                p.box((c,y-.056,.25),(leafw-.12,.014,.32),'Galvanized')
                p.box((c,y-.056,leafh-.12),(leafw-.16,.012,.055),'Yellow')
            hx=c+(leafw*.34 if left else -leafw*.34)
            p.box((hx,y-.086,1.06),(.035,.046,.24),'Galvanized')
            if self.cfg.detail!='DRAFT':
                for z in (.38,1.85):
                    p.cylinder((px,y-.018,z-.05),(px,y-.018,z+.05),.020,'Galvanized',10)
            self.doors.append({'part':p.name,'closed':pivot,'opened':pivot,
                               'angle':(-1 if left else 1)*radians(96),
                               'kind':'HINGE','rest_pose':'closed','runtime_blueprint':False})
        if canopy:
            z=dh+.24
            self.box('EntryCanopy',(0,-.52,z),(w-.12,1.22,.12),'SteelDark','DETAIL',.007)
            self.box('CanopySoffit',(0,-.52,z-.071),(w-.28,1.04,.020),'ConcreteLight','DETAIL',.002)
            for x in (-(w-.5)/2,(w-.5)/2):
                self.part('CanopyBrackets').beam((x,.08,z-.02),(x,-.72,z-.22),.045,.06,'SteelDark')
            self.box('CanopyLight',(0,-.42,z-.086),(ow*.68,.10,.015),'LightWarm','DETAIL',.001)
        # An opening is not a completed walkway port. A separate landing is required.
        self.ports.append({'name':'ENTRY_OPENING','role':'PEDESTRIAN_OPENING',
                           'location_source':(0,0.,0.),'normal_source':(0.,-1.,0.),
                           'clear_width_m':ow-.15,'surface_offset_m':0.,
                           'landing_required':True,'pk01_bridge_ready':False})

    def finish(self):
        if self._finished:return self
        w,h,t=self.cfg.width,self.cfg.height,self.cfg.thickness
        for p in self.parts:
            p.vertices=[canonical(v) for v in p.vertices]
            p.pivot=canonical(p.pivot)
        for d in self.doors:
            d['closed']=canonical(d['closed']);d['opened']=canonical(d['opened'])
        for p in self.ports:
            p['location_m']=canonical(p.pop('location_source'))
            p['normal']=canonical(p.pop('normal_source'))
        for label,loc,no in (
            ('LEFT',(0.,w/2,0.),(0.,1.,0.)),('RIGHT',(0.,-w/2,0.),(0.,-1.,0.))):
            self.ports.append({'name':'JOIN_'+label,'role':'FACADE_JOIN','location_m':loc,
                               'normal':no,'height_m':h,'thickness_m':t,
                               'profile':'MB01_FACADE_RECT_V1','scenery_only':True})
        self._finished=True
        return self


def build(settings):
    s=settings.checked();m=ModuleModel(s);b=m.spec.builder
    if b=='plain':m.wall()
    elif b=='window':m.window()
    elif b=='narrow':m.window(narrow=True)
    elif b=='sunshade':m.window(shade=True)
    elif b=='unit_window':m.window(unit=True)
    elif b=='glazed':m.window(glazed=True)
    elif b=='clerestory':m.window(clerestory=True)
    elif b=='vent':m.ventilation()
    elif b=='hangar_louver':m.ventilation(hangar=True)
    elif b=='service':m.entry()
    elif b=='double':m.entry(double=True)
    elif b=='lobby':m.entry(double=True,glazed=True,canopy=True)
    elif b=='metal':m.wall(metal=True)
    elif b=='hangar_service':m.entry(metal=True)
    elif b.startswith('hg_'):
        from .expansion_geometry import generate
        generate(m,b)
    else:raise ValueError('Generator is not implemented: '+b)
    return m.finish()


def part_transform(model,part):
    d=next((d for d in model.doors if d['part']==part.name),None)
    return (part.pivot,d['angle']*model.cfg.door_open) if d else (part.pivot,0.)


def geometry_key(model):
    """No cell UUID, door pose or palette in geometry identity; content is hashed."""
    return digest([{'role':p.group,'vertices':p.vertices,'faces':p.faces,
                    'uvs':p.uvs,'mats':p.material_names,'ids':p.material_ids,
                    'pivot':p.pivot,'bevel':p.bevel} for p in model.parts])


def validation(model):
    report=A.validate_model(model)
    report['generator']=VERSION
    report['module_id']=model.spec.id
    report['openings']=model.openings
    report['blender_runtime_verified']=False
    report['ue_runtime_verified']=False
    for p in model.parts:
        if len(p.faces)!=len(p.uvs) or len(p.faces)!=len(p.material_ids):
            report['errors'].append('Face attribute count: '+p.name)
        for f,uv,mi in zip(p.faces,p.uvs,p.material_ids):
            if len(f)!=len(uv):report['errors'].append('UV corner count: '+p.name)
            if not 0<=mi<len(p.material_names):report['errors'].append('Material index: '+p.name)
    # Confirm source wall volumes do not occupy the intended aperture centre.
    for opening in model.openings:
        out=opening['center_output']
        centre=(-out[1],out[0],out[2])
        for box in model.wall_boxes:
            if all(abs(centre[k]-box['center_source'][k]) < box['dims'][k]/2-1e-8 for k in range(3)):
                report['errors'].append('Hidden solid wall behind opening.')
    report['status']='PASS' if not report['errors'] else 'FAIL'
    return report

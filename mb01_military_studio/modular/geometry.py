# SPDX-License-Identifier: MIT
"""14 bounded visual facade modules; real openings, shared material roles and pivots.
Source assembly coordinates: X across facade, Y inward, Z upward.
Output coordinates match MB01: +X inward, +Y left, +Z upward, metre units.
This is an artistic mesh assembly, not a structural or protection calculation.
"""
from dataclasses import asdict
from math import pi, radians
from ..vendor import as07_reference as A
from .catalog import require
from .contracts import ModuleInput, digest
from ..mb_common import canonical

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
        material = 'RoofOlive' if metal else self.cfg.style.wall_material
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
        baseh = .38 if not metal else .48
        spans = [(-w/2, w/2)]
        if aperture is not None and aperture[1] < baseh:
            spans = [(-w/2, -aperture[0]/2), (aperture[0]/2, w/2)]
        for lo, hi in spans:
            self.box('Plinth', ((lo+hi)/2, -.023, baseh/2), (hi-lo, .046, baseh),
                     self.cfg.style.plinth_material, 'FACADE', .004)
        # Fine top reveal: visually coherent with a later continuous coping module.
        self.box('HeadReveal', (0, -.009, h-.105), (w, .018, .014), 'Joint', 'DETAIL', .001)
        if metal:
            # Ribs remain on piers or below/above aperture; never cross a clear opening.
            n = max(3, int(w/.58))
            for k in range(1, n):
                x = -w/2 + w*k/n
                intervals = [(.5, h-.14)]
                if aperture and abs(x) < aperture[0]/2 + .025:
                    intervals = [(.5, aperture[1]-.025), (aperture[1]+aperture[2]+.025, h-.14)]
                for z0, z1 in intervals:
                    if z1-z0 > .06:
                        self.box('PanelSeams', (x, -.018, (z0+z1)/2), (.024, .036, z1-z0),
                                 'RoofOliveLight', 'DETAIL', .0015)

    def frame(self, ow, bottom, oh, transom=False, mullion=True):
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
            ow, bottom, oh = w-.48, h-1.6, 1.15
        elif glazed:
            ow, bottom, oh = w-.54, .32, h-.62
        else:
            ow = min(1.20, w*.32) if narrow else min(2.16, w*.55)
            bottom = .88
            oh = min(1.68 if unit else 1.82, h-bottom-.40)
        self.wall((ow, bottom, oh), metal=clerestory)
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
        bottom = h*.48 if hangar else .98
        oh = min(1.75 if hangar else 1.36, h-bottom-.45)
        self.wall((ow, bottom, oh), metal=hangar)
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

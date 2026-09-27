# SPDX-License-Identifier: MIT
"""Targeted interface measurements using real emitted vertices, not only metadata."""
from math import sqrt
from .contracts import envelope
from .meshqa import inspect_parts


def design(v):return (-v[1],v[0],v[2])

def vertices(part):return [design(v) for v in part.vertices]

def bounds(part):
    vs=vertices(part)
    return tuple(min(v[i] for v in vs) for i in range(3)),tuple(max(v[i] for v in vs) for i in range(3))


def inspect_hangar(model):
    c=model.hangar_config;env=envelope(c);metrics={};issues=[]
    parts={p.name:p for p in model.parts}
    def find(suffix):return next(p for p in model.parts if p.name.endswith(suffix))
    side=find(f'RIGHT_{c.bays-1:02d}__Wall')
    rear=sorted((p for p in model.parts if '_REAR_' in p.name and p.name.endswith('__Wall')),key=lambda p:bounds(p)[1][0])[-1]
    sl,sh=bounds(side);rl,rh=bounds(rear)
    metrics['rear_plane_gap_m']=rl[1]-sh[1]
    metrics['rear_corner_cover_m']=rh[0]-sh[0]
    if abs(metrics['rear_plane_gap_m'])>.001:
        issues.append(dict(code='REAR_WALL_JOIN',severity='ERROR',parts=[side.name,rear.name],measured_m=metrics['rear_plane_gap_m']))
    if metrics['rear_corner_cover_m']<-.001:
        issues.append(dict(code='REAR_CORNER_COVER',severity='ERROR',parts=[side.name,rear.name]))
    # Check fixed cabinet fronts point toward the room on both sides.
    for keyword in ('HG_ServiceCabinets','HG_ServiceCabinetFaces','HG_CabinetHandles'):
        selected=[p for p in model.parts if p.name.endswith(keyword)]
        if selected:metrics[keyword+'_abs_centers']=[sum(abs(v[0]) for v in vertices(selected[0])[i:i+8])/8 for i in range(0,len(selected[0].vertices),8)]
    body=metrics.get('HG_ServiceCabinets_abs_centers',[]);faces=metrics.get('HG_ServiceCabinetFaces_abs_centers',[])
    if body and faces:
        metrics['cabinet_inward_offsets_m']=[a-b for a,b in zip(body,faces)]
        if any(v<=0 for v in metrics['cabinet_inward_offsets_m']):
            issues.append(dict(code='CABINET_FACE_OUTWARD',severity='ERROR',parts=['HG_ServiceCabinetFaces']))
    shoes=[p for p in model.parts if p.name.endswith('HG_LightShoe')]
    if shoes:
        contact=[]
        vs=vertices(shoes[0])
        for i in range(0,len(vs),8):
            block=vs[i:i+8];dist=[env.roof(v[0])-v[2] for v in block]
            contact.append(min(abs(x) for x in dist))
        metrics['fixture_shoe_contact_max_gap_m']=max(contact,default=0.)
        if metrics['fixture_shoe_contact_max_gap_m']>.001:
            issues.append(dict(code='LIGHT_SHOE_FLOATING',severity='ERROR',parts=[shoes[0].name],measured_m=metrics['fixture_shoe_contact_max_gap_m']))
    # Rainwater fittings must not be swallowed by the outer wall.
    pipes=[p for p in model.parts if p.name.endswith('HG_Downpipes')]
    if pipes:
        low=[v for v in vertices(pipes[0]) if v[2]<c.base_height+1.]
        clearance=min((abs(v[0])-env.outside_x for v in low),default=0.)
        metrics['downpipe_wall_clearance_m']=clearance
        if clearance<-.001:issues.append(dict(code='PIPE_WALL_INTERSECTION',severity='ERROR',parts=[pipes[0].name]))
    mesh=inspect_parts(model.parts)
    issues.extend(mesh['issues'])
    return dict(schema='base01.hangar_inspection/1',status='FAIL' if any(i['severity']=='ERROR' for i in issues) else 'PASS',
        metrics=metrics,issues=issues,mesh=mesh,performs_writes=False,
        scope='Targeted emitted-geometry checks; no full-building collision/structural certification',
        native_blender='NOT_RUN',native_unreal='NOT_RUN')

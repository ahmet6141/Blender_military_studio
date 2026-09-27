# SPDX-License-Identifier: MIT
"""Inspect emitted attributes independently of the producing geometry's metadata.
No automatic cleanup: a malformed UV layer or geometry is reported, not silently repaired.
Closed assembly contacts and intentional tiled-UV overlaps are not generic errors.
"""
from math import isfinite,sqrt
from collections import Counter
from .contracts import Tolerances


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def triangle_area(a,b,c):
    n=cross(tuple(b[i]-a[i] for i in range(3)),tuple(c[i]-a[i] for i in range(3)))
    return sqrt(sum(x*x for x in n))*.5


def uv_area(a,b,c):
    return abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))*.5


def inspect_parts(parts,tolerances=Tolerances()):
    t=tolerances.checked();issues=[];total_uv=total_tri=0;bad_uv_total=0
    names=set();reports=[]
    for p in parts:
        errors=Counter();v=p.vertices;fs=p.faces;uvs=p.uvs
        if p.name in names:errors['DUPLICATE_PART_ID']+=1
        names.add(p.name)
        bad_vertices={i for i,q in enumerate(v) if not isinstance(q,(list,tuple)) or len(q)!=3 or not all(type(x) in (int,float) and isfinite(x) for x in q)}
        if bad_vertices: errors['NONFINITE_VERTEX']+=len(bad_vertices)
        if len(fs)!=len(uvs):errors['UV_FACE_COUNT']+=1
        if len(fs)!=len(p.material_ids):errors['MATERIAL_FACE_COUNT']+=1
        if len(fs)!=len(p.smooth):errors['SMOOTH_FACE_COUNT']+=1
        for i,f in enumerate(fs):
            if len(f)<3 or any(type(k) is not int or k<0 or k>=len(v) for k in f):
                errors['FACE_INDEX']+=1;continue
            if any(k in bad_vertices for k in f):continue
            if len(set(f))!=len(f):errors['REPEATED_CORNER']+=1
            if i>=len(p.material_ids) or type(p.material_ids[i]) is not int or not 0<=p.material_ids[i]<len(p.material_names):
                errors['MATERIAL_INDEX']+=1
            if i>=len(uvs) or len(uvs[i])!=len(f):
                errors['UV_CORNER_COUNT']+=1;continue
            uv=uvs[i]
            if any(len(q)!=2 or not all(isinstance(x,(int,float)) and isfinite(x) for x in q) for q in uv):
                errors['NONFINITE_UV']+=1;continue
            # Generated polygons are triangulated here only for diagnostics. Export remains independent.
            for j in range(1,len(f)-1):
                total_tri+=1
                if triangle_area(v[f[0]],v[f[j]],v[f[j+1]])<=1e-14:
                    # A collinear fan ear in an n-gon is not the export triangulation.
                    errors['DEGENERATE_TRIANGLE' if len(f)==3 else 'DEGENERATE_FAN_TRIANGLE']+=1
                    continue
                if uv_area(uv[0],uv[j],uv[j+1])<=t.uv_area:
                    errors['UV_ZERO_AREA']+=1;bad_uv_total+=1
                total_uv+=1
        for code,count in errors.items():
            severity='WARNING' if code=='DEGENERATE_FAN_TRIANGLE' else 'ERROR'
            issues.append(dict(code=code,severity=severity,part=p.name,count=count))
        reports.append(dict(part=p.name,faces=len(fs),vertices=len(v),issues=dict(errors)))
    status='FAIL' if any(x['severity']=='ERROR' for x in issues) else ('WARNING' if issues else 'PASS')
    return dict(schema='base01.meshqa/1',status=status,parts=len(reports),triangles=total_tri,
        uv_triangles_checked=total_uv,zero_area_uv_triangles=bad_uv_total,issues=issues,
        limitations=['No full self-intersection test','No native tangent/bevel result',
                     'Tiled UV overlaps are allowed','Fan triangulation is diagnostic only'],records=reports)

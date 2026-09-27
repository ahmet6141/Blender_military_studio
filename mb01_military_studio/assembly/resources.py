# SPDX-License-Identifier: MIT
"""Fingerprint actual image bytes before reusing a material. No network operations."""
from pathlib import Path
from copy import deepcopy
from functools import lru_cache
import hashlib


@lru_cache(maxsize=1024)
def _digest(path, size, mtime_ns):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def file_digest(path, fresh=False):
    p=Path(path).resolve()
    if not p.is_file():raise FileNotFoundError(str(p))
    if fresh:
        with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    stat=p.stat()
    return _digest(str(p),stat.st_size,stat.st_mtime_ns)


def fingerprint_recipe(recipe):
    r=deepcopy(recipe)
    r['source_hashes']={k:file_digest(p,fresh=True) for k,p in sorted(r.get('textures',{}).items())}
    return r


def managed_image(bpy,path,kind,digest):
    """A changed source gets a NEW image datablock; other projects stay untouched."""
    color_space='sRGB' if kind=='BaseColor' else 'Non-Color'
    for image in bpy.data.images:
        if image.get('base01_sha256')==digest and image.get('base01_space')==color_space:
            return image
    image=bpy.data.images.load(str(Path(path)),check_existing=False)
    image.name='BASE01_'+Path(path).stem+'_'+digest[:10]
    image.colorspace_settings.name=color_space
    image['base01_sha256']=digest;image['base01_space']=color_space
    return image


def inspect_source_hashes(recipe):
    """Compare recorded bytes with disk contents; no image reload or user-file writes."""
    expected=recipe.get('source_hashes',{})
    issues=[]
    for kind,path in sorted(recipe.get('textures',{}).items()):
        if kind not in expected:
            issues.append(dict(code='LEGACY_SOURCE_HASH_MISSING',severity='WARNING',map=kind,path=path))
            continue
        try:actual=file_digest(path,fresh=True)
        except OSError as exc:
            issues.append(dict(code='MATERIAL_SOURCE_MISSING',severity='ERROR',map=kind,path=path,message=str(exc)))
            continue
        if actual!=expected[kind]:
            issues.append(dict(code='MATERIAL_SOURCE_CHANGED',severity='ERROR',map=kind,path=path,expected=expected[kind],actual=actual))
    return issues

# SPDX-License-Identifier: MIT
"""Versioned visual module catalog. These are scenery rules, not building codes."""
from dataclasses import dataclass
from pathlib import Path
import json

SCHEMA = 'mb01.module_catalog/0.2'

@dataclass(frozen=True)
class ModuleSpec:
    id: str
    title: str
    category: str
    families: tuple
    builder: str
    width_range: tuple
    height_range: tuple
    default_width: float
    default_height: float
    status: str
    note: str

    @classmethod
    def from_record(cls, data):
        d = dict(data)
        for name in ('families', 'width_range', 'height_range'):
            d[name] = tuple(d[name])
        return cls(**d)


def catalog():
    path = Path(__file__).resolve().with_name('module_catalog.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != SCHEMA:
        raise ValueError('Unsupported MB01 module catalog schema.')
    records = [ModuleSpec.from_record(x) for x in data['modules']]
    if len({m.id for m in records}) != len(records):
        raise ValueError('Duplicate module identifiers in catalog.')
    return {m.id: m for m in records}


def require(module_id):
    if not isinstance(module_id, str):
        raise ValueError('Module id must be a string.')
    try:
        result = catalog()[module_id]
    except KeyError as exc:
        raise ValueError('Unknown module: ' + str(module_id)) from exc
    if result.status != 'implemented_core':
        raise ValueError('Module is planned, not implemented: ' + module_id)
    return result


def available(family=None, category=None):
    return [s for s in catalog().values()
            if s.status == 'implemented_core'
            and (family is None or family in s.families)
            and (category is None or s.category == category)]

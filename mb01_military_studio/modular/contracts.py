# SPDX-License-Identifier: MIT
"""Strict declarative input. No eval, no script execution, no hidden dimension scaling."""
from dataclasses import dataclass, asdict
from math import isfinite
import hashlib
import json
import re
from .catalog import require

SCHEMA = 'mb01.facade/0.2'
FAMILIES = ('HQ', 'UNIT', 'HANGAR', 'SUPPORT')


def numeric(name, value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(name + ': finite number required.')
    if not low <= value <= high:
        raise ValueError(f'{name}: supported scenery range {low:g}..{high:g}; received {value!r}.')
    return float(value)


def ident(name, value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', value):
        raise ValueError(name + ': use 1..64 ASCII letters, digits, underscore or hyphen; start with a letter.')
    return value


def digest(data):
    text = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Style:
    palette: str = 'COASTAL'
    wall_material: str = 'Plaster'
    frame_material: str = 'SteelDark'
    plinth_material: str = 'Stone'
    wear: float = .15

    def checked(self):
        if self.palette not in ('COASTAL', 'WOODLAND', 'URBAN'):
            raise ValueError('Unknown material palette.')
        if self.wall_material not in ('Plaster', 'Concrete', 'ConcreteLight'):
            raise ValueError('Unsupported wall material role.')
        if self.frame_material not in ('SteelDark', 'RoofOlive', 'Galvanized'):
            raise ValueError('Unsupported frame material role.')
        if self.plinth_material not in ('Stone', 'Concrete', 'ConcreteLight'):
            raise ValueError('Unsupported plinth material role.')
        numeric('wear', self.wear, 0., 1.)
        return self


@dataclass(frozen=True)
class ModuleInput:
    module_id: str = 'COMMON.WALL.WINDOW'
    family: str = 'HQ'
    width: float = 3.6
    height: float = 3.6
    thickness: float = .28
    detail: str = 'WORKING'
    door_open: float = 0.
    style: Style = Style()

    def checked(self):
        spec = require(self.module_id)
        if self.family not in spec.families:
            raise ValueError(f'{self.module_id} is not allowed in family {self.family}.')
        numeric('width', self.width, *spec.width_range)
        numeric('height', self.height, *spec.height_range)
        numeric('thickness', self.thickness, .16, .50)
        numeric('door_open', self.door_open, 0., 1.)
        if self.detail not in ('DRAFT', 'WORKING', 'HERO'):
            raise ValueError('Unknown detail level.')
        self.style.checked()
        return self


@dataclass(frozen=True)
class Cell:
    id: str
    module_id: str
    width: float = 3.6

    def checked(self):
        ident('cell.id', self.id)
        require(self.module_id)
        numeric('cell.width', self.width, .1, 20.)
        return self


@dataclass(frozen=True)
class FacadeInput:
    id: str
    family: str
    cells: tuple
    height: float = 3.6
    thickness: float = .28
    detail: str = 'WORKING'
    style: Style = Style()
    door_open: float = 0.
    target_width: float = 0.
    seed: int = 17

    def checked(self):
        ident('facade.id', self.id)
        if self.family not in FAMILIES:
            raise ValueError('Unknown facade family.')
        if not isinstance(self.cells, (tuple, list)) or not 1 <= len(self.cells) <= 32:
            raise ValueError('A facade must contain 1..32 explicit cells.')
        if type(self.seed) is not int:
            raise ValueError('Seed must be an integer.')
        numeric('target_width', self.target_width, 0., 180.)
        ids = set()
        for cell in self.cells:
            if not isinstance(cell, Cell):
                raise ValueError('Facade cells must be Cell records.')
            cell.checked()
            if cell.id in ids:
                raise ValueError('Duplicate cell id: ' + cell.id)
            ids.add(cell.id)
            ModuleInput(cell.module_id, self.family, cell.width, self.height,
                        self.thickness, self.detail, self.door_open, self.style).checked()
        total = sum(c.width for c in self.cells)
        if self.target_width and abs(total - self.target_width) > .000001:
            raise ValueError(f'Width mismatch: cells total {total:.4f} m, target {self.target_width:.4f} m. '
                             'No window or door has been silently scaled.')
        return self


def to_document(facade):
    facade.checked()
    return {'schema': SCHEMA, 'scenery_only': True, 'facade': asdict(facade)}


def from_document(data):
    if not isinstance(data, dict) or set(data) != {'schema', 'scenery_only', 'facade'}:
        raise ValueError('Invalid facade JSON envelope.')
    if data['schema'] != SCHEMA or data['scenery_only'] is not True:
        raise ValueError('Unsupported schema or missing scenery-only scope.')
    try:
        d = dict(data['facade'])
        d['cells'] = tuple(Cell(**c) for c in d['cells'])
        d['style'] = Style(**d.get('style', {}))
        return FacadeInput(**d).checked()
    except (TypeError, KeyError) as exc:
        raise ValueError('Invalid or unknown facade field: ' + str(exc)) from exc


def stable_variation(seed, cell_id, channel):
    """Order-independent bounded metadata. Does not promise arbitrary new architecture."""
    return int(digest([seed, ident('cell.id', cell_id), str(channel)])[:12], 16) / float(16**12 - 1)


def placements(facade):
    facade.checked()
    total = sum(c.width for c in facade.cells)
    edge = total / 2.
    out = []
    for cell in facade.cells:
        center = edge - cell.width / 2.
        out.append({'id': cell.id, 'module_id': cell.module_id, 'width': cell.width,
                    'location_m': (0., center, 0.), 'yaw_rad': 0.,
                    'left_edge_m': edge, 'right_edge_m': edge-cell.width,
                    'variation_key': stable_variation(facade.seed, cell.id, 'surface')})
        edge -= cell.width
    return out

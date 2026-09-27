# SPDX-License-Identifier: MIT
"""Strict hangar scenery contract. Numbers are generator bounds, not building codes.
Geometry dimensions are metres. Source: width-X/depth-Y; output: depth+X/left+Y.
"""
from dataclasses import dataclass, asdict, fields, replace
from math import isfinite
import json, hashlib, re
from .. import core

SCHEMA = 'mb01.hangar_studio/0.3-alpha.1'
SUPPORTED_SCHEMAS = (SCHEMA, 'mb01.hangar_studio/0.2-alpha.3', 'mb01.hangar_studio/0.2-alpha.2')
PANEL_TYPES = ('METAL', 'CLERESTORY', 'LOUVER', 'PERSONNEL',
               'CASSETTE', 'VISION', 'SHADED', 'DUAL_VENT', 'DOUBLE_SERVICE', 'CANOPY_ENTRY')
ENTRY_TYPES = frozenset(('PERSONNEL','DOUBLE_SERVICE','CANOPY_ENTRY'))
PANEL_MODULES = dict(METAL='HANGAR.WALL.METAL', CLERESTORY='HANGAR.WALL.CLERES',
                     LOUVER='HANGAR.WALL.LOUVER', PERSONNEL='HANGAR.ENTRY.PERSONNEL',
                     CASSETTE='HANGAR.WALL.CASSETTE', VISION='HANGAR.WALL.VISION',
                     SHADED='HANGAR.WALL.SHADED', DUAL_VENT='HANGAR.WALL.DUAL_VENT',
                     DOUBLE_SERVICE='HANGAR.ENTRY.DOUBLE_SERVICE', CANOPY_ENTRY='HANGAR.ENTRY.CANOPY')


def number(name, value, lo, hi):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f'{name}: sonlu bir sayı gerekli.')
    if not lo <= value <= hi:
        raise ValueError(f'{name}: desteklenen görsel aralık {lo:g}–{hi:g}; alınan {value:g}.')
    return float(value)


@dataclass(frozen=True)
class HangarConfig:
    name: str = 'HG_DAYLIGHT_01'
    width: float = 32.0
    depth: float = 36.0
    eave_height: float = 7.6
    roof_rise: float = 2.6
    bays: int = 8
    roof_type: str = 'MONITOR'
    monitor_width: float = 5.2
    monitor_height: float = 1.0
    opening_width: float = 22.0
    opening_height: float = 6.15
    gate_leaves: int = 6
    gate_open: float = 0.82
    gate_glazing: bool = True
    personnel_open: float = 0.0
    left_panels: str = ''
    right_panels: str = ''
    rear_service_door: bool = True
    wall_thickness: float = 0.22
    base_height: float = 0.18
    local_ground: bool = True
    apron_depth: float = 5.0
    drain: bool = True
    landings: bool = True
    walkway_width: float = 3.2
    gutters: bool = True
    services: bool = True
    fixtures: bool = True
    signage: bool = True
    fasteners: bool = True
    detail: str = 'WORKING'
    palette: str = 'COASTAL'
    roof_finish: str = 'OLIVE'
    wall_finish: str = 'LIGHT'
    wetness: float = 0.0
    normal_strength: float = 0.24
    concrete_tile_m: float = 2.0
    metal_tile_m: float = 1.2
    seed: int = 17

    def panel_sequence(self, side):
        if side not in ('LEFT', 'RIGHT'):
            raise ValueError('Panel tarafı LEFT veya RIGHT olmalı.')
        raw = self.left_panels if side == 'LEFT' else self.right_panels
        if not isinstance(raw, str):
            raise ValueError('Panel dizisi virgülle ayrılmış metin olmalı.')
        if raw.strip():
            items = tuple(token.strip().upper() for token in raw.split(','))
            if len(items) != self.bays:
                raise ValueError(f'{side}: tam {self.bays} cephe hücresi gerekli; {len(items)} verildi.')
            if any(token not in PANEL_TYPES for token in items):
                raise ValueError(f'{side}: desteklenen modüller: '+', '.join(PANEL_TYPES))
            return items
        items = ['CLERESTORY'] * self.bays
        items[0], items[-1] = 'METAL', 'LOUVER'
        items[1 if side == 'LEFT' else self.bays-2] = 'PERSONNEL'
        return tuple(items)

    def checked(self):
        if not isinstance(self.name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}', self.name):
            raise ValueError('Hangar adı: harfle başlayan 1–48 ASCII harf/rakam/_/- kullanın.')
        for name, lo, hi in (
            ('width', 20., 48.), ('depth', 18., 60.), ('eave_height', 6., 9.),
            ('roof_rise', 1.2, 4.8), ('monitor_width', 2., 8.), ('monitor_height', .65, 1.6),
            ('opening_width', 10., 36.), ('opening_height', 4.3, 7.7),
            ('gate_open', 0., 1.), ('personnel_open', 0., 1.), ('wall_thickness', .16, .36),
            ('base_height', .08, .35), ('apron_depth', 3., 8.), ('walkway_width', 2.4, 4.5),
            ('wetness', 0., 1.), ('normal_strength', 0., 1.4),
            ('concrete_tile_m', .25, 8.), ('metal_tile_m', .25, 8.)):
            number(name, getattr(self, name), lo, hi)
        if type(self.bays) is not int or not 4 <= self.bays <= 12:
            raise ValueError('Bölme sayısı 4–12 arasında tam sayı olmalı.')
        pitch = self.depth / self.bays
        if not 2.8 <= pitch <= 6.:
            raise ValueError('Derinlik / bölme sayısı 2.8–6 m olmalı; paneli gizlice esnetmiyorum.')
        if self.roof_type not in ('GABLE', 'MONITOR'):
            raise ValueError('Çatı GABLE veya MONITOR olmalı.')
        if self.monitor_width > self.width * .30:
            raise ValueError('Üst ışıklık genişliği, görsel profil için bina genişliğinin %30’unu geçemez.')
        if self.roof_rise / (self.width / 2) > .36:
            raise ValueError('Çatı profili bu üreticinin desteklediği eğim aralığını aşıyor.')
        if self.opening_height + .95 > self.eave_height:
            raise ValueError('Ana açıklığın üzerinde ray/başlık için en az .95 m geometri payı gerekli.')
        if type(self.gate_leaves) is not int or self.gate_leaves not in (4, 6, 8):
            raise ValueError('Ana kapı 4, 6 veya 8 kanat olmalı.')
        pocket = (self.width - self.opening_width)/2
        leaf = self.opening_width / self.gate_leaves
        if pocket < leaf + .25:
            raise ValueError('Yan kapı cebi dar: açıklığı azaltın, gövdeyi genişletin veya kanat sayısını artırın.')
        if self.detail not in ('DRAFT', 'WORKING', 'HERO'):
            raise ValueError('Detay DRAFT / WORKING / HERO olmalı.')
        if self.palette not in ('COASTAL', 'WOODLAND', 'URBAN'):
            raise ValueError('Bilinmeyen palet.')
        if self.roof_finish not in ('OLIVE', 'GRAPHITE', 'SILVER'):
            raise ValueError('Çatı bitişi OLIVE / GRAPHITE / SILVER olmalı.')
        if self.wall_finish not in ('LIGHT', 'OLIVE', 'GRAPHITE'):
            raise ValueError('Cephe bitişi LIGHT / OLIVE / GRAPHITE olmalı.')
        for field in fields(self):
            if isinstance(field.default, bool) and type(getattr(self, field.name)) is not bool:
                raise ValueError(field.name + ': True/False gerekli.')
        if type(self.seed) is not int or not 0 <= self.seed <= 2147483647:
            raise ValueError('Seed 0–2147483647 arasında tam sayı olmalı.')
        for side in ('LEFT', 'RIGHT'):
            sequence = self.panel_sequence(side)
            if self.local_ground and self.landings and any(t in ENTRY_TYPES for t in sequence) and pitch < self.walkway_width + .12:
                raise ValueError('Personel sahanlığı hücreden geniş: kaldırım genişliğini küçültün veya bölme aralığını büyütün.')
            if any(a in ENTRY_TYPES and b in ENTRY_TYPES for a, b in zip(sequence, sequence[1:])):
                raise ValueError('Bu sürümde bitişik iki personel sahanlığı desteklenmiyor; araya farklı panel koyun.')
        return self

    def legacy_settings(self):
        return core.settings_for('HANGAR', name=self.name, width=self.width, depth=self.depth,
            floor_height=self.eave_height, bays=self.bays, base_height=self.base_height,
            detail=self.detail, palette=self.palette, local_ground=self.local_ground,
            services=self.services, signage=self.signage, door_open=self.gate_open,
            walkway_width=self.walkway_width, seed=self.seed, wear=0.)


PRESETS = {
    'DAYLIGHT_MRO': dict(name='HG_DAYLIGHT_01'),
    'CLASSIC_MAINTENANCE': dict(name='HG_CLASSIC_01', width=28., depth=36., bays=8,
        eave_height=7.2, roof_rise=2.2, roof_type='GABLE', opening_width=18., opening_height=5.85,
        gate_leaves=4, gate_open=.78, wall_finish='OLIVE', roof_finish='GRAPHITE'),
    'COMPACT_SERVICE': dict(name='HG_COMPACT_01', width=24., depth=24., bays=6,
        eave_height=6.8, roof_rise=1.8, roof_type='GABLE', opening_width=14., opening_height=5.35,
        gate_leaves=4, gate_glazing=False, wall_finish='GRAPHITE', roof_finish='SILVER', apron_depth=3.5),
}


PRESETS.update({
    'EXP_COASTAL': dict(name='HG_COASTAL_03', left_panels='CASSETTE,CANOPY_ENTRY,SHADED,SHADED,VISION,SHADED,DUAL_VENT,CASSETTE', right_panels='CASSETTE,VISION,VISION,SHADED,DUAL_VENT,SHADED,DOUBLE_SERVICE,CASSETTE'),
    'EXP_TECHNICAL': dict(name='HG_TECH_03', width=28.,depth=36.,roof_type='GABLE',eave_height=7.2,roof_rise=2.2,opening_width=18.,opening_height=5.8,gate_leaves=4,wall_finish='OLIVE',left_panels='CASSETTE,DOUBLE_SERVICE,VISION,VISION,DUAL_VENT,METAL,METAL,CASSETTE',right_panels='CASSETTE,METAL,DUAL_VENT,VISION,VISION,METAL,CANOPY_ENTRY,CASSETTE'),
    'EXP_COMPACT': dict(name='HG_COMPACT_03',width=24.,depth=24.,bays=6,roof_type='GABLE',eave_height=6.8,roof_rise=1.8,opening_width=14.,opening_height=5.35,gate_leaves=4,gate_glazing=False,wall_finish='GRAPHITE',roof_finish='SILVER',left_panels='CASSETTE,CANOPY_ENTRY,VISION,DUAL_VENT,SHADED,CASSETTE',right_panels='CASSETTE,SHADED,VISION,DUAL_VENT,PERSONNEL,CASSETTE'),
    'EXP_LONG': dict(name='HG_LONG_03',width=32.,depth=48.,bays=10,eave_height=8.,roof_rise=2.8,opening_height=6.3,gate_leaves=6,wall_finish='LIGHT',roof_finish='GRAPHITE',left_panels='CASSETTE,DOUBLE_SERVICE,VISION,VISION,SHADED,SHADED,SHADED,DUAL_VENT,METAL,CASSETTE',right_panels='CASSETTE,METAL,DUAL_VENT,SHADED,SHADED,VISION,VISION,METAL,CANOPY_ENTRY,CASSETTE'),
    'EXP_URBAN': dict(name='HG_URBAN_03',width=36.,depth=36.,bays=8,eave_height=8.,roof_rise=2.8,opening_width=24.,opening_height=6.6,gate_leaves=8,palette='URBAN',wall_finish='GRAPHITE',roof_finish='SILVER',gate_open=.7,left_panels='CASSETTE,CANOPY_ENTRY,VISION,SHADED,SHADED,VISION,DUAL_VENT,CASSETTE',right_panels='CASSETTE,DUAL_VENT,VISION,SHADED,SHADED,VISION,DOUBLE_SERVICE,CASSETTE')
})

def preset(name, **overrides):
    if name not in PRESETS:
        raise ValueError('Bilinmeyen hangar önayarı: ' + str(name))
    args = dict(PRESETS[name]); args.update(overrides)
    return HangarConfig(**args).checked()


def to_document(config):
    config.checked()
    return dict(schema=SCHEMA, scenery_only=True, config=asdict(config))


def from_document(value):
    if not isinstance(value, dict) or set(value) != {'schema', 'scenery_only', 'config'}:
        raise ValueError('Hangar JSON zarfı geçersiz.')
    if value['schema'] not in SUPPORTED_SCHEMAS or value['scenery_only'] is not True or not isinstance(value['config'], dict):
        raise ValueError('Hangar JSON sürümü/kapsamı geçersiz.')
    allowed = {f.name for f in fields(HangarConfig)}
    unknown = set(value['config']) - allowed
    if unknown:
        raise ValueError('Bilinmeyen hangar alanları: ' + ', '.join(sorted(unknown)))
    return HangarConfig(**value['config']).checked()


def load_json(path):
    from pathlib import Path
    p = Path(path)
    if p.stat().st_size > 262144:
        raise ValueError('Hangar JSON en fazla 256 KiB olabilir.')
    from ..assembly.contracts import strict_json_loads
    return from_document(strict_json_loads(p.read_text(encoding='utf-8-sig')))


def stable_variant(config, element_id, count=5):
    if type(count) is not int or count < 1:
        raise ValueError('Varyasyon sayısı pozitif tam sayı olmalı.')
    seed = f'{config.seed}|{element_id}'.encode('utf-8')
    return int.from_bytes(hashlib.sha256(seed).digest()[:8], 'little') % count


def gate_motion(config):
    """Telescopic leaves in design coordinates; returns unambiguous closed/open pivots.
    Fully open leaves live in front-side pockets, not inside the clear aperture.
    Opposing inner leaves retain a .012 m visual meeting gap at closed pose.
    """
    config.checked()
    segment = config.opening_width / config.gate_leaves
    leaf_width = segment - .012
    target = config.opening_width/2 + .045 + leaf_width/2
    rows = []
    for sign, side in ((-1, 'L'), (1, 'R')):
        for j in range(config.gate_leaves//2):
            y = -.43 - j*.24
            rows.append(dict(id=f'GATE_{side}{j+1}', side=side, track=j, width=leaf_width,
                closed=(sign*(j+.5)*segment, y, config.base_height+.025),
                opened=(sign*target, y, config.base_height+.025), angle=0., kind='SLIDE',
                channel='GATE', open_fraction=config.gate_open))
    return rows


def gate_clear_width(config, amount=None):
    t = config.gate_open if amount is None else number('gate_pose', amount, 0., 1.)
    bounds=[]
    for door in gate_motion(config):
        if door['side'] == 'R':
            x = door['closed'][0]*(1-t)+door['opened'][0]*t
            bounds.append(x-door['width']/2)
    return min(config.opening_width, max(0., 2*min(bounds)))

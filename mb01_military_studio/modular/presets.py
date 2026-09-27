# SPDX-License-Identifier: MIT
from .contracts import Cell, FacadeInput

PRESET_CELLS = {
 'HQ': ('COMMON.WALL.PLAIN','COMMON.WALL.SUNSHADE','COMMON.WALL.WINDOW',
        'HQ.ENTRY.LOBBY','COMMON.WALL.WINDOW','COMMON.WALL.SUNSHADE','COMMON.WALL.PLAIN'),
 'UNIT': ('COMMON.WALL.PLAIN','UNIT.WALL.WINDOW','COMMON.ENTRY.SERVICE',
          'UNIT.WALL.WINDOW','UNIT.WALL.WINDOW','COMMON.WALL.PLAIN'),
 'HANGAR': ('HANGAR.WALL.METAL','HANGAR.WALL.CLERES','HANGAR.ENTRY.PERSONNEL',
            'HANGAR.WALL.CLERES','HANGAR.WALL.LOUVER','HANGAR.WALL.METAL'),
 'SUPPORT': ('COMMON.WALL.PLAIN','COMMON.WALL.VENT','COMMON.ENTRY.SERVICE',
             'COMMON.WALL.NARROW','COMMON.WALL.PLAIN'),
}


def example(family='HQ'):
    if family not in PRESET_CELLS:
        raise ValueError('Unknown family preset.')
    width, height = (4.5,6.4) if family == 'HANGAR' else (3.6,3.6)
    cells=tuple(Cell('BAY_'+str(i+1).zfill(3),mid,width) for i,mid in enumerate(PRESET_CELLS[family]))
    return FacadeInput('FACADE_'+family,family,cells,height=height).checked()

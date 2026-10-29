#!/usr/bin/env python3
''' CuraMaterial - A package for reading installed Cura Materials.
A part of the Spool Maker package.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Thanks to:
Thanks to Maeven-Black (GitHub) for supplying fix for newer versions of Ultimaker Cura.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

# /---------------------------------\
#|          Import Modules           |
# \---------------------------------/
import os

import re
import platform
from pathlib import Path

__author__ = 'Dale A. Osborne'
__copyright__ = 'Copyright 2021, Dale Osborne'
__license__ = 'GPL'
__version__ = '1.1.5'



# /---------------------------------\
#|        Material locations         |
# \---------------------------------/
# No network access and no downloads: the Ultimaker material list is bundled
# with the app (materials_fallback.json). Add your own materials by putting
# .xml.fdm_material files in the "custom" folder next to the log file.
import json
import sys


def _data_dir():
    if platform.system() == 'Windows':
        base = os.getenv('LOCALAPPDATA') or str(Path.home())
    elif platform.system() == 'Darwin':
        base = str(Path.home() / 'Library' / 'Application Support')
    else:
        base = os.getenv('XDG_DATA_HOME') or str(Path.home() / '.local' / 'share')
    return os.path.join(base, 'SpoolMaker')


DATA_DIR = _data_dir()
CURA_USER_MAT_DIR = os.path.join(DATA_DIR, 'custom')


def _bundled_json():
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'materials_fallback.json')


print('Bundled materials:', _bundled_json())
print('Custom material directory:', CURA_USER_MAT_DIR)



# /---------------------------------\
#|              Classes              |
# \---------------------------------/
class curaMaterial():
    def __init__(self, brand:str, material:str, color:str, guid:str):
        self.brand = brand
        self.material = material
        self.color = color
        self.guid = guid



# /---------------------------------\
#|          Main Functions           |
# \---------------------------------/
def read_material(cm):
    '''Reads a cura material profile (.xml.fdm_material) and returns a curaMaterial object'''
    brand = material = color = guid = ''
    found = [False]*4 # Corresponds with above values. True once that value is found.
    with open(cm, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if all(found):
                break
            if '<brand>' in line and not found[0]:
                data = re.split('<|>| ', line.strip())
                for b in data[2:]:
                    if b != '/brand':
                        brand += b
                    else:
                        break
                found[0] = True
                continue
            if '<material>' in line and not found[1]:
                data = re.split('<|>| ', line.strip())
                for m in data[2:]:
                    if m != '/material':
                        material += m
                    else:
                        break
                found[1] = True
                continue
            if '<color>' in line and not found[2]:
                data = re.split('<|>| ', line.strip())
                for c in data[2:]:
                    if c != '/color':
                        color += c
                    else:
                        break
                found[2] = True
                continue
            if '<GUID>' in line and not found[3]:
                guid = re.split('<|>| ', line.strip())[2]
                found[3] = True
                continue
    return curaMaterial(brand, material, color, guid)

def get_all_materials():
    '''Returns (list of curaMaterial, list of names for the combobox): bundled list plus your own custom materials'''
    mList = []
    sList = []

    with open(_bundled_json(), encoding='utf-8') as f:
        for b, m, col, g in json.load(f):
            mList.append(curaMaterial(b, m, col, g))

    if os.path.isdir(CURA_USER_MAT_DIR):
        for root, _, files in os.walk(CURA_USER_MAT_DIR):
            for file in files:
                if file.endswith('.xml.fdm_material'):
                    mList.append(read_material(os.path.join(root, file)))

    for mat in mList:
        sList.append(mat.brand + ':' + mat.material + ' (' + mat.color + ')')

    return mList, sList


if __name__ == '__main__':
    # If run directly, list installed materials
    materials, _ = get_all_materials()
    for material in materials:
        print('Material: ', material.brand, '/', material.material, '\t', material.color)
        print('\t', material.guid)

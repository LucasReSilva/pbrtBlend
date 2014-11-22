# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#
from .. import find_luxrender_path
import sys
import re
import bpy

from collections import Iterable
from ..outputs import LuxLog


def ToValidLuxCoreName(name):
    return re.sub('[^_0-9a-zA-Z]+', '_', name)


def FlattenStrCollection(coll):
    for i in coll:
        if isinstance(i, Iterable):
            if (type(i) is str):
                yield i
            else:
                for subc in FlattenStrCollection(i):
                    yield subc


def UseLuxCore():
    return True if bpy.context.scene.luxrender_engine.selected_luxrender_api == 'luxcore' else False


def ScenePrefix():
    return 'importlib.import_module(\'bpy\').context.scene.'


if not 'PYLUXCORE_AVAILABLE' in locals():
    try:
        lux_path = find_luxrender_path()
        LuxLog('Assuming pyluxcore module location is {}'.format(lux_path))
        if not lux_path in sys.path:
            sys.path.insert(0, lux_path)
        import pyluxcore

        pyluxcore.Init()
        LUXCORE_VERSION = pyluxcore.Version()

        PYLUXCORE_AVAILABLE = True
        LuxLog('Using pyluxcore version %s' % LUXCORE_VERSION)

    except ImportError as err:
        LuxLog('WARNING: Binary pyluxcore module not available! Visit \
        http://www.luxrender.net/ to obtain one for your system.')
        LuxLog(' (ImportError was: %s)' % err)
        PYLUXCORE_AVAILABLE = False

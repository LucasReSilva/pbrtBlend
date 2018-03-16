# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 PBRTv3 Add-On
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
import re
import bpy

from collections import Iterable
from ..outputs import PBRTv3Log
from .. import import_bindings_module

PREFIX_MATERIALS = 'scene.materials'
PREFIX_TEXTURES = 'scene.textures'
PREFIX_VOLUMES = 'scene.volumes'
PREFIX_CAMERA = 'scene.camera'


def ToValidPBRTv3CoreName(name):
    return re.sub('[^_0-9a-zA-Z]+', '_', name)


def set_prop(prefix, properties, pbrtv3core_name, property, value):
    """
    Set a PBRTv3Core property.
    Example: set_prop('materials', properties, 'type', 'matte') is the equivalent of
    properties.Set(pypbrtv3core.Property('scene.materials.<name>.type', 'matte'))
    For materials, textures, volumes and the camera you can use the shorter set_prop_mat,
    set_prop_tex, etc. convenience functions where you can omit the prefix.

    :param prefix: PBRTv3Core property prefix (e.g. 'scene.materials')
    :param properties: PBRTv3Core properties that are edited. Type: pypbrtv3core.Properties
    :param pbrtv3core_name: PBRTv3Core name of the material
    :param property: Property string that is set, e.g. 'type' or 'kd'
    :param value: Value for the property (string, number or list)
    """
    key = '.'.join([prefix, pbrtv3core_name, property])
    properties.Set(pypbrtv3core.Property(key, value))

def set_prop_mat(properties, pbrtv3core_name, property, value):
    set_prop(PREFIX_MATERIALS, properties, pbrtv3core_name, property, value)

def set_prop_tex(properties, pbrtv3core_name, property, value):
    set_prop(PREFIX_TEXTURES, properties, pbrtv3core_name, property, value)

def set_prop_vol(properties, pbrtv3core_name, property, value):
    set_prop(PREFIX_VOLUMES, properties, pbrtv3core_name, property, value)

def set_prop_cam(properties, property, value):
    key = '.'.join([PREFIX_CAMERA, property])
    properties.Set(pypbrtv3core.Property(key, value))


def FlattenStrCollection(coll):
    for i in coll:
        if isinstance(i, Iterable):
            if (type(i) is str):
                yield i
            else:
                for subc in FlattenStrCollection(i):
                    yield subc


def UsePBRTv3Core():
    return True if bpy.context.scene.pbrtv3_engine.selected_pbrtv3_api == 'pbrtv3core' else False


def ScenePrefix():
    return 'importlib.import_module(\'bpy\').context.scene.'


if not 'PYpbrtv3core_AVAILABLE' in locals():
    try:
        pypbrtv3core = import_bindings_module('pypbrtv3core')
        pypbrtv3core.Init()
        pbrtv3core_VERSION = pypbrtv3core.Version()

        PYpbrtv3core_AVAILABLE = True
        PBRTv3Log('Using pypbrtv3core version %s' % pbrtv3core_VERSION)

    except ImportError as err:
        PBRTv3Log('WARNING: Binary pypbrtv3core module not available! Visit '
               'http://www.pbrtv3render.net/ to obtain one for your system.')
        PBRTv3Log('(ImportError was: %s)' % err)
        pypbrtv3core = None
        PYpbrtv3core_AVAILABLE = False

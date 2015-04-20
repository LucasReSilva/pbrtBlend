# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli, Jens Verwiebe, Tom Bech, Simon Wendsche
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

import bpy


# TODO: remove after refactoring, should be obsolete


class ExportedObjectData(object):
    def __init__(self, lcObjName, lcMeshName='', lcMaterialName='', matIndex=0, lightType=''):
        """
        :param lcObjName: Unique, "exported" name, used by LuxCore to reference the object
        :param lcMeshName: Unique name of the mesh, used by LuxCore to reference the mesh
        :param lcMaterialName: Unique name of the material, used by LuxCore to reference the material
        :param matIndex: Index of the material slot of the original Blender object (objects are split by material)
        :param lightType: Blender light type (e.g. 'SUN', 'AREA'), used to handle area lights different than other
                          lights in realtime preview updates
        """
        self.lcObjName = lcObjName
        self.lcMeshName = lcMeshName
        self.lcMaterialName = lcMaterialName
        self.matIndex = matIndex
        self.lightType = lightType


class ExportedObject(object):
    def __init__(self, obj, obj_data, luxcore_data):
        """
        :param obj: Blender object
        :param obj_data: Blender object data
        :param luxcore_data: List of ExportedObjectData instances (one per material)
        """
        self.blender_object = obj
        self.blender_data = obj_data
        self.luxcore_data = luxcore_data


class NameCache(object):
    """
    name cache storing the mapping of Blender objects/Blender data to the corresponding exported LuxCore objects.
    The dupli_key, composed of (duplicated_object, duplicator), is the key to a list of all generated duplis for this
    object/particle system combination.
    """

    def __init__(self):
        self.cache = {}

    def add_obj(self, obj, luxcore_data, dupli_key=()):
        exported_object = ExportedObject(obj, obj.data, luxcore_data)
        self.cache[obj] = exported_object
        self.cache[obj.data] = exported_object

        if dupli_key:
            if dupli_key in self.cache:
                self.cache[dupli_key].append(exported_object)
            else:
                self.cache[dupli_key] = [exported_object]

    def has(self, key):
        return key in self.cache

    def get_exported_object(self, key):
        try:
            return self.cache[key]
        except KeyError:
            return None
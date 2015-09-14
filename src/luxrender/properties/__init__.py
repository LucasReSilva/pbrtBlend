# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
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
from ..outputs.luxcore_api import pyluxcore, ToValidLuxCoreName, UseLuxCore


class luxrender_node(bpy.types.Node):
    # This node is only for the Lux node-tree
    @classmethod
    def poll(cls, tree):
        return tree.bl_idname in ['luxrender_material_nodes', 'luxrender_volume_nodes_a']


class luxrender_texture_node(luxrender_node):
    pass


class luxrender_material_node(luxrender_node):
    pass


# For eliminating redundant volume definitions
class ExportedVolumes(object):
    vol_names = []

    @staticmethod
    def list_exported_volumes(name):
        if name not in ExportedVolumes.vol_names:
            ExportedVolumes.vol_names.append(name)

    @staticmethod
    def reset_vol_list():
        ExportedVolumes.vol_names = []


def find_node(material, nodetype):
    if not (material and material.luxrender_material and material.luxrender_material.nodetree):
        return None

    nodetree_name = material.luxrender_material.nodetree

    if not nodetree_name:
        return None

    ntree = bpy.data.node_groups[nodetree_name]

    return find_node_in_nodetree(ntree, nodetype)


def find_node_in_volume(volume, nodetype):
    """
    Volume version of find_node()
    """
    if not (volume and volume.nodetree):
        return None

    nodetree_name = volume.nodetree

    if not nodetree_name:
        return None

    ntree = bpy.data.node_groups[nodetree_name]

    return find_node_in_nodetree(ntree, nodetype)


def find_node_in_nodetree(nodetree, nodetype):
    for node in nodetree.nodes:
        nt = getattr(node, "bl_idname", None)

        if nt == nodetype:
            return node


def find_node_input(node, name):
    for input in node.inputs:
        if input.name == name:
            return input

    return None


def get_linked_node(socket):
    if not socket.is_linked:
        return None
    return socket.links[0].from_node


def has_interior_volume(node):
    mat_output_node = find_node_in_nodetree(node.id_data, 'luxrender_material_output_node')
    if mat_output_node and mat_output_node.interior_volume:
        return True
    else:
        return False


def check_node_export_material(node):
    if not hasattr(node, 'export_material'):
        print('No export_material() for node: ' + node.bl_idname)
        return False
    return True


def check_node_export_texture(node):
    if not hasattr(node, 'export_texture'):
        print('No export_texture() for node: ' + node.bl_idname)
        return False
    return True


def check_node_get_paramset(node):
    if not hasattr(node, 'get_paramset'):
        print('No get_paramset() for node: ' + node.bl_idname)
        return False
    return True

# LuxCore node UI functions (e.g. warning labels)

def warning_luxcore_node(layout):
    """
    Show a warning label if API mode is Classic (this node only works in LuxCore mode)
    """
    if not UseLuxCore():
        layout.label('No Classic support!', icon='ERROR')

def warning_classic_node(layout):
    """
    Show a warning label if API mode is LuxCore (this node only works in Classic mode)
    """
    if UseLuxCore():
        layout.label('No LuxCore support!', icon='ERROR')

# LuxCore node export functions

prefix_materials = 'scene.materials'
prefix_textures = 'scene.textures'
prefix_volumes = 'scene.volumes'

def create_luxcore_name(node, suffix=None, name=None):
    """
    Construct a unique name for the node to be used in the LuxCore scene definitions.
    """
    if name is None:
        name = node.name

    nodetree = node.id_data
    name_parts = [name, nodetree.name]

    if nodetree.library:
        name_parts.append(nodetree.library.name)

    if suffix:
        name_parts.append(suffix)

    return ToValidLuxCoreName('_'.join(name_parts))

def create_luxcore_name_mat(node, name=None):
    return create_luxcore_name(node, 'mat', name)

def create_luxcore_name_vol(node, name=None):
    return create_luxcore_name(node, 'vol', name)

def set_prop(prefix, properties, luxcore_name, property, value):
    """
    Set a LuxCore property.
    Example: set_luxcore_prop(properties, 'type', 'matte') is the equivalent of
    properties.Set(pyluxcore.Property('scene.materials.<name>.type', 'matte'))

    :param prefix: LuxCore property prefix (e.g. 'scene.materials')
    :param properties: LuxCore properties that are edited. Type: pyluxcore.Properties
    :param luxcore_name: LuxCore name of the material
    :param property: Property string that is set, e.g. 'type' or 'kd'
    :param value: Value for the property (string, number or list)
    """
    key = '.'.join([prefix, luxcore_name, property])
    properties.Set(pyluxcore.Property(key, value))

def set_prop_mat(properties, luxcore_name, property, value):
    set_prop(prefix_materials, properties, luxcore_name, property, value)

def set_prop_tex(properties, luxcore_name, property, value):
    set_prop(prefix_textures, properties, luxcore_name, property, value)

def set_prop_vol(properties, luxcore_name, property, value):
    set_prop(prefix_volumes, properties, luxcore_name, property, value)

def export_black_matte(properties):
    luxcore_name = 'BLACK_MATTE'
    set_prop_mat(properties, luxcore_name, 'type', 'matte')
    set_prop_mat(properties, luxcore_name, 'kd', [0, 0, 0])
    return luxcore_name

def export_black_volume(properties):
    luxcore_name = 'BLACK_VOLUME'
    set_prop_vol(properties, luxcore_name, 'type', 'clear')
    set_prop_vol(properties, luxcore_name, 'absorption', [100, 100, 100])
    return luxcore_name

def export_submat_luxcore(properties, socket, name=None):
    """
    NodeSocketShader sockets cannot export themselves, so this function does it
    """
    node = get_linked_node(socket)

    if node is None:
        # Use a black material if socket is not linked
        print('WARNING: Unlinked material socket! Using a black material as fallback.')
        submat_name = export_black_matte(properties)
    else:
        submat_name = node.export_luxcore(properties, name)

    return submat_name

def export_volume_luxcore(properties, socket, name=None):
    """
    NodeSocketShader sockets cannot export themselves, so this function does it
    """
    node = get_linked_node(socket)

    if node is None:
        # Use a black volume if socket is not linked
        print('WARNING: Unlinked volume socket! Using a black volume as fallback.')
        volume_name = export_black_volume(properties)
    else:
        volume_name = node.export_luxcore(properties, name)

    return volume_name

def export_emission_luxcore(properties, socket, parent_luxcore_name, is_volume_emission=False):
    """
    NodeSocketShader sockets cannot export themselves, so this function does it
    """
    node = get_linked_node(socket)

    if node is not None:
        node.export_luxcore(properties, parent_luxcore_name, is_volume_emission)
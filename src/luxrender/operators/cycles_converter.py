# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Simon Wendsche
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

def cycles_converter(report, blender_mat):
    try:
        # Create Lux nodetree
        lux_nodetree = bpy.data.node_groups.new(blender_mat.name, type='luxrender_material_nodes')
        lux_nodetree.use_fake_user = True
        blender_mat.luxrender_material.nodetree = lux_nodetree.name

        # Find active Cycles output node
        output = None

        for node in blender_mat.node_tree.nodes:
            if node.type == 'OUTPUT_MATERIAL' and node.is_active_output:
                output = node
                break

        # Convert surface socket
        first_surface_node, default_value = convert_socket(output.inputs['Surface'], lux_nodetree)

        # Create Lux output node
        lux_output = lux_nodetree.nodes.new('luxrender_material_output_node')
        lux_output.location = output.location
        # Connect Lux output to first converted node (if it could be converted)
        if first_surface_node:
            lux_nodetree.links.new(first_surface_node.outputs[0], lux_output.inputs[0])

        # Use the first emission node if there are any
        emission = None

        for node in blender_mat.node_tree.nodes:
            if node.type == 'EMISSION' and node.outputs[0].is_linked:
                emission = node
                break

        if emission:
            lux_emission = lux_nodetree.nodes.new('luxrender_light_area_node')
            lux_emission.location = lux_output.location.x - 230, lux_output.location.y - 180

            # Color
            linked_node, default_value = convert_socket(emission.inputs['Color'], lux_nodetree)
            # The default value of a Cycles color is always RGBA, but we only need RGB
            default_value = convert_rgba_to_rgb(default_value)
            copy_socket_properties(lux_emission, 0, lux_nodetree, linked_node, default_value)

            # Strenght (gain)
            linked_node, default_value = convert_socket(emission.inputs['Strength'], lux_nodetree)
            if default_value:
                # Gain is not a socket in Lux emission node
                lux_emission.gain = default_value

            # Connect
            lux_nodetree.links.new(lux_emission.outputs[0], lux_output.inputs[1])

        report({'INFO'}, 'Converted Cycles nodetree "%s"' % blender_mat.node_tree.name)
        return {'FINISHED'}
    except Exception as err:
        report({'ERROR'}, 'Cannot convert nodetree "%s": %s' % (blender_mat.node_tree.name, err))
        import traceback
        traceback.print_exc()
        return {'CANCELLED'}

def convert_rgba_to_rgb(color):
        return color[:3] if color is not None else None

def get_linked_node(socket):
    if socket.is_linked:
        return socket.links[0].from_node
    else:
        return None

def copy_socket_properties(lux_node, socket_index, lux_nodetree, linked_node=None, default_value=None):
    if linked_node is not None:
        # Create the link
        lux_nodetree.links.new(linked_node.outputs[0], lux_node.inputs[socket_index])
    elif default_value is not None:
        # Set default value of the socket
        lux_node.inputs[socket_index].default_value = default_value

def convert_socket(socket, lux_nodetree):
    if socket.is_linked:
        node = socket.links[0].from_node
        # Get from_socket information, for nodes with multiple outputs (e.g. image map with color and alpha)
        from_socket = socket.links[0].from_socket
    elif hasattr(socket, 'default_value'):
        return None, socket.default_value
    else:
        # Sockets like NodeSocketShader do not have a default value
        return None, None

    lux_node = None

    if node.type == 'OUTPUT_MATERIAL':
        pass # Output is exported before iterative export

    ### Materials ###
    # TODO: Bump textures

    elif node.type == 'BSDF_DIFFUSE':
        # "Matte" in Lux
        lux_node = lux_nodetree.nodes.new('luxrender_material_matte_node')

        # Color
        linked_node, default_value = convert_socket(node.inputs['Color'], lux_nodetree)
        # The default value of a Cycles color is always RGBA, but we only need RGB
        default_value = convert_rgba_to_rgb(default_value)
        copy_socket_properties(lux_node, 0, lux_nodetree, linked_node, default_value)

    elif node.type == 'BSDF_GLOSSY':
        # "Metal2" in Lux
        lux_node = lux_nodetree.nodes.new('luxrender_material_metal2_node')

        # Color
        linked_node, default_value = convert_socket(node.inputs['Color'], lux_nodetree)
        # The default value of a Cycles color is always RGBA, but we only need RGB
        default_value = convert_rgba_to_rgb(default_value)
        copy_socket_properties(lux_node, 0, lux_nodetree, linked_node, default_value)

        # Roughness
        linked_node, default_value = convert_socket(node.inputs['Roughness'], lux_nodetree)
        copy_socket_properties(lux_node, 2, lux_nodetree, linked_node, default_value)

    elif node.type == 'MIX_SHADER':
        amount_node = get_linked_node(node.inputs['Fac'])
        mat1_node = get_linked_node((node.inputs[1]))
        mat2_node = get_linked_node((node.inputs[2]))

        if (amount_node and mat1_node and mat2_node) and (
                amount_node.type in ('FRESNEL', 'LAYER_WEIGHT') and
                mat1_node.type == 'BSDF_DIFFUSE' and mat2_node.type == 'BSDF_GLOSSY'):
            # Create a LuxRender glossy material
            lux_node = lux_nodetree.nodes.new('luxrender_material_glossy_node')

            # Diffuse Color (from BSDF_DIFFUSE)
            linked_node, default_value = convert_socket(mat1_node.inputs['Color'], lux_nodetree)
            # The default value of a Cycles color is always RGBA, but we only need RGB
            default_value = convert_rgba_to_rgb(default_value)
            copy_socket_properties(lux_node, 0, lux_nodetree, linked_node, default_value)

            # Roughness (from BSDF_GLOSSY)
            linked_node, default_value = convert_socket(mat2_node.inputs['Roughness'], lux_nodetree)
            copy_socket_properties(lux_node, 6, lux_nodetree, linked_node, default_value)

            # TODO: specular color (get brightness from fresnel/layerweight node and color from glossy node?)
        else:
            # "Normal" mix material, no special treatment
            linked_node_amount, default_value_amount = convert_socket(node.inputs['Fac'], lux_nodetree)
            linked_node_1, default_value_1 = convert_socket(node.inputs[1], lux_nodetree)
            linked_node_2, default_value_2 = convert_socket(node.inputs[2], lux_nodetree)

            # Only create the mix material if at least one of the sub-shaders could be converted
            if linked_node_1 or linked_node_2:
                lux_node = lux_nodetree.nodes.new('luxrender_material_mix_node')
                # Amount
                copy_socket_properties(lux_node, 0, lux_nodetree, linked_node_amount, default_value_amount)
                # Material 1
                copy_socket_properties(lux_node, 1, lux_nodetree, linked_node_1, default_value_1)
                # Material 2
                copy_socket_properties(lux_node, 2, lux_nodetree, linked_node_2, default_value_2)

    elif node.type == 'BSDF_TRANSPARENT':
        if node.inputs['Color'].default_value[:3] == (1, 1, 1):
            # In Lux, we ohly have the Null materials as an equivalent to a fully transparent material
            lux_node = lux_nodetree.nodes.new('luxrender_material_null_node')
        # TODO: find an approximation to Cycles' transparent material with non-white colors

    elif node.type == 'BSDF_GLASS':
        lux_node = lux_nodetree.nodes.new('luxrender_material_glass_node')

        # Color (Transmission)
        linked_node, default_value = convert_socket(node.inputs['Color'], lux_nodetree)
        # The default value of a Cycles color is always RGBA, but we only need RGB
        default_value = convert_rgba_to_rgb(default_value)
        copy_socket_properties(lux_node, 0, lux_nodetree, linked_node, default_value)

        # Roughness
        linked_node, default_value = convert_socket(node.inputs['Roughness'], lux_nodetree)

        if default_value != 0:
            # Use roughness
            lux_node.rough = True
            copy_socket_properties(lux_node, 6, lux_nodetree, linked_node, default_value)

        # IOR
        linked_node, default_value = convert_socket(node.inputs['IOR'], lux_nodetree)
        copy_socket_properties(lux_node, 2, lux_nodetree, linked_node, default_value)

    ### Textures ###
    elif node.type == 'TEX_IMAGE':
        lux_node = lux_nodetree.nodes.new('luxrender_texture_blender_image_map_node')

        # Selected Blender image
        lux_node.image = node.image.name

        # Gamma (from color space)
        lux_node.gamma = 2.2 if node.color_space == 'COLOR' else 1

        # Alpha handling (if alpha output of TEX_IMAGE is used)
        if from_socket.name == 'Alpha':
            lux_node.channel = 'alpha'

    else:
        # In case of an unkown node, do nothing
        print('WARNING: Unsupported node type %s' % node.type)
        return None, None

    if lux_node:
        # Copy properties shared by all nodes
        lux_node.location = node.location

    return lux_node, None
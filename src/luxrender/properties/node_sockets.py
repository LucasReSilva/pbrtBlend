# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Jens Verwiebe, Jason Clarke, Asbjørn Heid, Simon Wendsche
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

import re

import bpy, mathutils

from ..extensions_framework import declarative_property_group

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom

from .. import LuxRenderAddon
from ..properties import (luxrender_node, luxrender_material_node, get_linked_node, check_node_export_material,
                          check_node_export_texture, check_node_get_paramset, ExportedVolumes)

from ..properties.texture import (
    import_paramset_to_blender_texture, shorten_name, refresh_preview
)

from ..export import ParamSet, process_filepath_data
from ..export.materials import (
    MaterialCounter, TextureCounter, ExportedMaterials, ExportedTextures, get_texture_from_scene
)

from ..outputs import LuxManager, LuxLog

from ..properties.material import *  # for now just the big hammer for starting autogenerate sockets

from . import set_prop_tex

# Get all float properties
def get_props(TextureParameter, attribute):
    for prop in TextureParameter.get_properties():
        if prop['attr'].endswith('floatvalue'):
            value = prop[attribute]
    return value


# Colors are simpler, so we only get the colortuple here
def get_default(TextureParameter):
    TextureParameter = TextureParameter.default
    return TextureParameter


def export_socket_luxcore(properties, socket, fallback=None):
    """
    Export a socket. If the socket is linked, the linked node is exported and the name of the resulting LuxCore node
    is returned.
    If the socket is not linked, the fallback value is returned.
    """
    linked_node = get_linked_node(socket)

    if linked_node is not None:
        return linked_node.export_luxcore(properties)
    else:
        return fallback

# Custom socket types, lookup parameters here:
# http://www.blender.org/documentation/blender_python_api_2_66a
# release/bpy.props.html?highlight=bpy.props.floatproperty#bpy.props.FloatProperty

# Store our custom socket colors here as vars, so we don't have to remember what they are on every custom socket
float_socket_color = (0.63, 0.63, 0.63, 1.0)  # Same as native NodeSocketFloat
color_socket_color = (0.78, 0.78, 0.16, 1.0)  # Same as native NodeSocketColor
fresnel_socket_color = (0.33, 0.6, 0.85, 1.0)
#shader_socket_color = (0.39, 0.78, 0.39, 1.0) # Same as native NodeSocketShader
coord_2d_color = (0.50, 0.25, 0.60, 1.0)
coord_3d_color = (0.65, 0.55, 0.75, 1.0)

mapping_2d_socketname = '2D Mapping'
mapping_3d_socketname = '3D Mapping'


@LuxRenderAddon.addon_register_class
class luxrender_fresnel_socket(bpy.types.NodeSocket):
    """Fresnel texture input socket"""
    bl_idname = 'luxrender_fresnel_socket'
    bl_label = 'IOR socket'

    def changed_preset(self, context):
        # # connect preset -> property
        self.default_value = self.fresnel_presetvalue

    fresnel_presetvalue = bpy.props.FloatProperty(name='IOR-Preset', description='IOR', update=changed_preset)
    fresnel_presetstring = bpy.props.StringProperty(name='IOR_Preset Name', description='IOR')
    default_value = bpy.props.FloatProperty(name='IOR', description='Optical dataset', default=1.52, precision=6)
    needs_link = bpy.props.BoolProperty(name='Metal Fresnel', default=False) # for hiding inappropiate ui elements

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        if self.is_linked or self.needs_link:
            layout.label(text=self.name)
        else:
            box = layout.box()

            if self.default_value == self.fresnel_presetvalue:
                menu_text = self.fresnel_presetstring
            else:
                menu_text = '-- Choose IOR preset --'

            box.menu('LUXRENDER_MT_ior_presets', text=menu_text)
            box.prop(self, 'default_value', text=self.name)

    # Socket color
    def draw_color(self, context, node):
        return fresnel_socket_color

    # Export routine for this socket
    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)

        if tex_node:
            print('linked from %s' % tex_node.name)

            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)

            fresnel_params = ParamSet() \
                .add_texture('fresnel', tex_name)
        else:
            fresnel_params = ParamSet() \
                .add_float('fresnel', self.default_value)

        return fresnel_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


# #### custom color sockets #####

@LuxRenderAddon.addon_register_class
class luxrender_TC_Ka_socket(bpy.types.NodeSocket):
    """Absorption Color socket"""
    bl_idname = 'luxrender_TC_Ka_socket'
    bl_label = 'Absorption Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Absorption Color', description='Absorption Color',
                                          default=get_default(TC_Ka), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        print('get_paramset diffuse color')
        tex_node = get_linked_node(self)

        if tex_node:
            print('linked from %s' % tex_node.name)

            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            ka_params = ParamSet().add_texture('Ka', tex_name)
        else:
            ka_params = ParamSet().add_color('Ka', self.default_value)

        return ka_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_Kd_socket(bpy.types.NodeSocket):
    """Diffuse Color socket"""
    bl_idname = 'luxrender_TC_Kd_socket'
    bl_label = 'Diffuse Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Diffuse Color', description='Diffuse Color', default=get_default(TC_Kd),
                                          subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        print('get_paramset diffuse color')
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)

            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            kd_params = ParamSet().add_texture('Kd', tex_name)
        else:
            kd_params = ParamSet().add_color('Kd', self.default_value)

        return kd_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_Kr_socket(bpy.types.NodeSocket):
    """Reflection color socket"""
    bl_idname = 'luxrender_TC_Kr_socket'
    bl_label = 'Reflection Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Reflection Color', description='Reflection Color',
                                          default=get_default(TC_Kr), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            kr_params = ParamSet().add_texture('Kr', tex_name)
        else:
            kr_params = ParamSet().add_color('Kr', self.default_value)

        return kr_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks_socket(bpy.types.NodeSocket):
    """Specular color socket"""
    bl_idname = 'luxrender_TC_Ks_socket'
    bl_label = 'Specular Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Specular Color', description='Specular Color',
                                          default=get_default(TC_Ks), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            ks_params = ParamSet() .add_texture('Ks', tex_name)
        else:
            ks_params = ParamSet().add_color('Ks', self.default_value)

        return ks_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks1_socket(bpy.types.NodeSocket):
    """Specular color socket"""
    bl_idname = 'luxrender_TC_Ks1_socket'
    bl_label = 'Specular Color 1 socket'

    default_value = bpy.props.FloatVectorProperty(name='Specular Color 1', description='Specular Color 1',
                                          default=get_default(TC_Ks1), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            ks1_params = ParamSet().add_texture('Ks1', tex_name)
        else:
            ks1_params = ParamSet().add_color('Ks1', self.default_value)

        return ks1_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks2_socket(bpy.types.NodeSocket):
    """Specular color socket"""
    bl_idname = 'luxrender_TC_Ks2_socket'
    bl_label = 'Specular Color 2 socket'

    default_value = bpy.props.FloatVectorProperty(name='Specular Color 2', description='Specular Color 2',
                                          default=get_default(TC_Ks2), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            ks2_params = ParamSet().add_texture('Ks2', tex_name)
        else:
            ks2_params = ParamSet().add_color('Ks2', self.default_value)

        return ks2_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks3_socket(bpy.types.NodeSocket):
    """Specular color socket"""
    bl_idname = 'luxrender_TC_Ks3_socket'
    bl_label = 'Specular Color 3 socket'

    default_value = bpy.props.FloatVectorProperty(name='Specular Color 3', description='Specular Color 3',
                                          default=get_default(TC_Ks3), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            ks3_params = ParamSet().add_texture('Ks3', tex_name)
        else:
            ks3_params = ParamSet().add_color('Ks3', self.default_value)

        return ks3_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_Kt_socket(bpy.types.NodeSocket):
    """Transmission Color socket"""
    bl_idname = 'luxrender_TC_Kt_socket'
    bl_label = 'Transmission Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Transmission Color', description='Transmission Color',
                                          default=get_default(TC_Kt), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            kt_params = ParamSet().add_texture('Kt', tex_name)
        else:
            kt_params = ParamSet().add_color('Kt', self.default_value)

        return kt_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_warp_Kd_socket(bpy.types.NodeSocket):
    """Warp Diffuse Color socket"""
    bl_idname = 'luxrender_TC_warp_Kd_socket'
    bl_label = 'Warp Diffuse socket'

    default_value = bpy.props.FloatVectorProperty(name='Warp Diffuse Color', description='Warp Diffuse Color',
                                          default=get_default(TC_warp_Kd), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)

            warp_kd_params = ParamSet().add_texture('warp_Kd', tex_name)
        else:
            warp_kd_params = ParamSet().add_color('warp_Kd', self.default_value)

        return warp_kd_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_warp_Ks_socket(bpy.types.NodeSocket):
    """Warp Diffuse Color socket"""
    bl_idname = 'luxrender_TC_warp_Ks_socket'
    bl_label = 'Warp Specular socket'

    default_value = bpy.props.FloatVectorProperty(name='Warp Specular Color', description='Warp Specular Color',
                                          default=get_default(TC_warp_Ks), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            warp_ks_params = ParamSet().add_texture('warp_Ks', tex_name)
        else:
            warp_ks_params = ParamSet().add_color('warp_Ks', self.default_value)

        return warp_ks_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_weft_Kd_socket(bpy.types.NodeSocket):
    """Weft Diffuse Color socket"""
    bl_idname = 'luxrender_TC_weft_Kd_socket'
    bl_label = 'Weft Diffuse socket'

    default_value = bpy.props.FloatVectorProperty(name='Weft Diffuse Color', description='Weft Diffuse Color',
                                          default=get_default(TC_weft_Kd), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)

            weft_kd_params = ParamSet().add_texture('weft_Kd', tex_name)
        else:
            weft_kd_params = ParamSet().add_color('weft_Kd', self.default_value)

        return weft_kd_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_weft_Ks_socket(bpy.types.NodeSocket):
    """Weft Specular Color socket"""
    bl_idname = 'luxrender_TC_weft_Ks_socket'
    bl_label = 'Weft Specular socket'

    default_value = bpy.props.FloatVectorProperty(name='Weft Specular Color', description='Weft Specular Color',
                                          default=get_default(TC_weft_Ks), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            weft_ks_params = ParamSet().add_texture('weft_Ks', tex_name)
        else:
            weft_ks_params = ParamSet().add_color('weft_Ks', self.default_value)

        return weft_ks_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_backface_Ka_socket(bpy.types.NodeSocket):
    """Backface Absorption Color socket"""
    bl_idname = 'luxrender_TC_backface_Ka_socket'
    bl_label = 'Backface Absorption socket'

    default_value = bpy.props.FloatVectorProperty(name='Backface Absorption Color', description='Backface Absorption Color',
                                          default=get_default(TC_backface_Ka), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            backface_ka_params = ParamSet().add_texture('backface_Ka', tex_name)
        else:
            backface_ka_params = ParamSet().add_color('backface_Ka', self.default_value)

        return backface_ka_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_backface_Ks_socket(bpy.types.NodeSocket):
    """Backface Specular Color socket"""
    bl_idname = 'luxrender_TC_backface_Ks_socket'
    bl_label = 'Backface Specular socket'

    default_value = bpy.props.FloatVectorProperty(name='Backface Specular Color', description='Backface Specular Color',
                                          default=get_default(TC_backface_Ks), subtype='COLOR', min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            backface_ks_params = ParamSet().add_texture('backface_Ks', tex_name)
        else:
            backface_ks_params = ParamSet().add_color('backface_Ks', self.default_value)

        return backface_ks_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_L_socket(bpy.types.NodeSocket):
    """Light Color socket"""
    bl_idname = 'luxrender_TC_L_socket'
    bl_label = 'Light Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Color', description='Color', default=get_default(TC_L), subtype='COLOR',
                                          min=0.0, max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            L_params = ParamSet().add_texture('L', tex_name)
        else:
            L_params = ParamSet().add_color('L', self.default_value)

        return L_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_AC_absorption_socket(bpy.types.NodeSocket):
    """Volume absorption Color socket"""
    bl_idname = 'luxrender_AC_absorption_socket'
    bl_label = 'Absorption Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Absorption Color', description='Absorption Color',
                                          default=(0.0, 0.0, 0.0), subtype='COLOR', min=0.0, soft_max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            ac_params = ParamSet().add_texture('absorption', tex_name)
        else:
            ac_params = ParamSet().add_color('absorption', self.default_value)

        return ac_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_SC_absorption_socket(bpy.types.NodeSocket):
    """Volume scatter absorption Color socket"""
    bl_idname = 'luxrender_SC_absorption_socket'
    bl_label = 'Scattering Absorption socket'

    default_value = bpy.props.FloatVectorProperty(name='Absorption Color', description='Absorption Color',
                                          default=(0.0, 0.0, 0.0), subtype='COLOR', min=0.0, soft_max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            ac_params = ParamSet().add_texture('sigma_a', tex_name)
        else:
            ac_params = ParamSet().add_color('sigma_a', self.default_value)

        return ac_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_SC_color_socket(bpy.types.NodeSocket):
    """Scattering Color socket"""
    bl_idname = 'luxrender_SC_color_socket'
    bl_label = 'Scattering Color socket'

    default_value = bpy.props.FloatVectorProperty(name='Scattering Color', description='Scattering Color',
                                          default=(0.0, 0.0, 0.0), subtype='COLOR', min=0.0, soft_max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            sc_params = ParamSet().add_texture('sigma_s', tex_name)
        else:
            sc_params = ParamSet().add_color('sigma_s', self.default_value)

        return sc_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


# #### custom float sockets #####

@LuxRenderAddon.addon_register_class
class luxrender_TF_amount_socket(bpy.types.NodeSocket):
    """Amount socket"""
    bl_idname = 'luxrender_TF_amount_socket'
    bl_label = 'Amount socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_amount, 'name'), description=get_props(TF_amount, 'description'),
                                     default=get_props(TF_amount, 'default'), subtype=get_props(TF_amount, 'subtype'),
                                     unit=get_props(TF_amount, 'unit'), min=get_props(TF_amount, 'min'),
                                     max=get_props(TF_amount, 'max'), soft_min=get_props(TF_amount, 'soft_min'),
                                     soft_max=get_props(TF_amount, 'soft_max'),
                                     precision=get_props(TF_amount, 'precision'))

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name, slider=True)

    # Socket color
    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        print('get_paramset amount')
        tex_node = get_linked_node(self)
        if not tex_node is None:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            amount_params = ParamSet().add_texture('amount', tex_name)
        else:
            print('value %f' % self.default_value)
            amount_params = ParamSet().add_float('amount', self.default_value)

        return amount_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_bump_socket(bpy.types.NodeSocket):
    """Bump socket"""
    bl_idname = 'luxrender_TF_bump_socket'
    bl_label = 'Bump socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_bumpmap, 'name'), description=get_props(TF_bumpmap, 'description'),
                                   default=get_props(TF_bumpmap, 'default'), subtype=get_props(TF_bumpmap, 'subtype'),
                                   unit=get_props(TF_bumpmap, 'unit'), min=get_props(TF_bumpmap, 'min'),
                                   max=get_props(TF_bumpmap, 'max'), soft_min=get_props(TF_bumpmap, 'soft_min'),
                                   soft_max=get_props(TF_bumpmap, 'soft_max'),
                                   precision=get_props(TF_bumpmap, 'precision'))

    def draw(self, context, layout, node, text):
        layout.label(text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        bumpmap_params = ParamSet()
        tex_node = get_linked_node(self)

        if tex_node and check_node_export_texture(tex_node):
            # only export linked bumpmap sockets
            tex_name = tex_node.export_texture(make_texture)
            bumpmap_params.add_texture('bumpmap', tex_name)

        return bumpmap_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self)


@LuxRenderAddon.addon_register_class
class luxrender_TF_cauchyb_socket(bpy.types.NodeSocket):
    """Cauchy B socket"""
    bl_idname = 'luxrender_TF_cauchyb_socket'
    bl_label = 'Cauchy B socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_cauchyb, 'name'),
                                      description=get_props(TF_cauchyb, 'description'),
                                      default=get_props(TF_cauchyb, 'default'),
                                      subtype=get_props(TF_cauchyb, 'subtype'), min=get_props(TF_cauchyb, 'min'),
                                      max=get_props(TF_cauchyb, 'max'), soft_min=get_props(TF_cauchyb, 'soft_min'),
                                      soft_max=get_props(TF_cauchyb, 'soft_max'),
                                      precision=get_props(TF_cauchyb, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            cauchyb_params = ParamSet().add_texture('cauchyb', tex_name)
        else:
            cauchyb_params = ParamSet().add_float('cauchyb', self.default_value)

        return cauchyb_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_film_ior_socket(bpy.types.NodeSocket):
    """Thin film IOR socket"""
    bl_idname = 'luxrender_TF_film_ior_socket'
    bl_label = 'Thin Film IOR socket'

    def changed_preset(self, context):
        # # connect preset -> property
        self.default_value = self.filmindex_presetvalue

    filmindex_presetvalue = bpy.props.FloatProperty(name='IOR-Preset', description='IOR', update=changed_preset)
    filmindex_presetstring = bpy.props.StringProperty(name='IOR_Preset Name', description='IOR')
    default_value = bpy.props.FloatProperty(name=get_props(TF_filmindex, 'name'),
                                        description=get_props(TF_filmindex, 'description'),
                                        default=get_props(TF_filmindex, 'default'),
                                        subtype=get_props(TF_filmindex, 'subtype'), min=get_props(TF_filmindex, 'min'),
                                        max=get_props(TF_filmindex, 'max'),
                                        soft_min=get_props(TF_filmindex, 'soft_min'),
                                        soft_max=get_props(TF_filmindex, 'soft_max'),
                                        precision=get_props(TF_filmindex, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            if 'IOR' in self.node.inputs.keys():  # index/filmindex presets interfere, show simple property only then
                layout.prop(self, 'default_value', text=self.name)
            else:  # show presetchooser for all other mat
                box = layout.box()

                if self.default_value == self.filmindex_presetvalue:
                    menu_text = self.filmindex_presetstring
                else:
                    menu_text = '-- Choose IOR preset --'

                box.menu('LUXRENDER_MT_ior_presets', text=menu_text)
                box.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            filmindex_params = ParamSet().add_texture('filmindex', tex_name)
        else:
            filmindex_params = ParamSet().add_float('filmindex', self.default_value)

        return filmindex_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_film_thick_socket(bpy.types.NodeSocket):
    """Thin film thickness socket"""
    bl_idname = 'luxrender_TF_film_thick_socket'
    bl_label = 'Thin Film thickness socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_film, 'name'), description=get_props(TF_film, 'description'),
                                   default=get_props(TF_film, 'default'), subtype=get_props(TF_film, 'subtype'),
                                   min=get_props(TF_film, 'min'), max=get_props(TF_film, 'max'),
                                   soft_min=get_props(TF_film, 'soft_min'), soft_max=get_props(TF_film, 'soft_max'),
                                   precision=get_props(TF_film, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            film_params = ParamSet().add_texture('film', tex_name)
        else:
            film_params = ParamSet().add_float('film', self.default_value)

        return film_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_ior_socket(bpy.types.NodeSocket):
    """IOR socket"""
    bl_idname = 'luxrender_TF_ior_socket'
    bl_label = 'IOR socket'

    def changed_preset(self, context):
        # # connect preset -> property
        self.default_value = self.index_presetvalue

    index_presetvalue = bpy.props.FloatProperty(name='IOR-Preset', description='IOR', update=changed_preset)
    index_presetstring = bpy.props.StringProperty(name='IOR_Preset Name', description='IOR')
    default_value = bpy.props.FloatProperty(name=get_props(TF_index, 'name'), description=get_props(TF_index, 'description'),
                                    default=get_props(TF_index, 'default'), subtype=get_props(TF_index, 'subtype'),
                                    min=get_props(TF_index, 'min'), max=get_props(TF_index, 'max'),
                                    soft_min=get_props(TF_index, 'soft_min'), soft_max=get_props(TF_index, 'soft_max'),
                                    precision=get_props(TF_index, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            box = layout.box()

            if self.default_value == self.index_presetvalue:
                menu_text = self.index_presetstring
            else:
                menu_text = '-- Choose IOR preset --'

            box.menu('LUXRENDER_MT_ior_presets', text=menu_text)
            box.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)

            index_params = ParamSet().add_texture('index', tex_name)
        else:
            index_params = ParamSet().add_float('index', self.default_value)

        return index_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_uroughness_socket(bpy.types.NodeSocket):
    """U-Roughness socket"""
    bl_idname = 'luxrender_TF_uroughness_socket'
    bl_label = 'U-Roughness socket'

    sync_vroughness = bpy.props.BoolProperty(name='Sync V to U', default=True)
    default_value = bpy.props.FloatProperty(name=get_props(TF_uroughness, 'name'),
                                         description=get_props(TF_uroughness, 'description'),
                                         default=get_props(TF_uroughness, 'default'),
                                         subtype=get_props(TF_uroughness, 'subtype'),
                                         min=get_props(TF_uroughness, 'min'), max=get_props(TF_uroughness, 'max'),
                                         soft_min=get_props(TF_uroughness, 'soft_min'),
                                         soft_max=get_props(TF_uroughness, 'soft_max'),
                                         precision=get_props(TF_uroughness, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        print('get_paramset uroughness')
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)

            if self.sync_vroughness:
                print("Syncing V-Roughness: ")
                roughness_params = ParamSet() \
                    .add_texture('uroughness', tex_name) \
                    .add_texture('vroughness', tex_name)
            else:
                roughness_params = ParamSet() \
                    .add_texture('uroughness', tex_name)

        else:
            if self.sync_vroughness:
                print("Syncing V-Roughness: ")
                roughness_params = ParamSet() \
                    .add_float('uroughness', self.default_value) \
                    .add_float('vroughness', self.default_value)
            else:
                roughness_params = ParamSet() \
                    .add_float('uroughness', self.default_value)

        return roughness_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_vroughness_socket(bpy.types.NodeSocket):
    """V-Roughness socket"""
    bl_idname = 'luxrender_TF_vroughness_socket'
    bl_label = 'V-Roughness socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_vroughness, 'name'),
                                         description=get_props(TF_vroughness, 'description'),
                                         default=get_props(TF_vroughness, 'default'),
                                         subtype=get_props(TF_vroughness, 'subtype'),
                                         min=get_props(TF_vroughness, 'min'), max=get_props(TF_vroughness, 'max'),
                                         soft_min=get_props(TF_vroughness, 'soft_min'),
                                         soft_max=get_props(TF_vroughness, 'soft_max'),
                                         precision=get_props(TF_uroughness, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        print('get_paramset vroughness')
        tex_node = get_linked_node(self)
        if tex_node:
            print('linked from %s' % tex_node.name)
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            roughness_params = ParamSet().add_texture('vroughness', tex_name)
        else:
            roughness_params = ParamSet().add_float('vroughness', self.default_value)

        return roughness_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_sigma_socket(bpy.types.NodeSocket):
    """Sigma socket"""
    bl_idname = 'luxrender_TF_sigma_socket'
    bl_label = 'Sigma socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_sigma, 'name'), description=get_props(TF_sigma, 'description'),
                                    default=get_props(TF_sigma, 'default'), subtype=get_props(TF_sigma, 'subtype'),
                                    min=get_props(TF_sigma, 'min'), max=get_props(TF_sigma, 'max'),
                                    soft_min=get_props(TF_sigma, 'soft_min'), soft_max=get_props(TF_sigma, 'soft_max'),
                                    precision=get_props(TF_sigma, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            sigma_params = ParamSet().add_texture('sigma', tex_name)
        else:
            sigma_params = ParamSet().add_float('sigma', self.default_value)

        return sigma_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_SC_asymmetry_socket(bpy.types.NodeSocket):
    """Scattering asymmetry socket"""
    bl_idname = 'luxrender_SC_asymmetry_socket'
    bl_label = 'Scattering Asymmetry socket'

    default_value = bpy.props.FloatVectorProperty(name='Asymmetry',
                                            description='Scattering asymmetry RGB. -1 means backscatter, '
                                            '0 is isotropic, 1 is forwards scattering',
                                            default=(0.0, 0.0, 0.0), min=-1.0, max=1.0, precision=4)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            col = layout.column()
            col.label(text=self.name)
            col.prop(self, 'default_value', text='')

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            sc_asym_params = ParamSet().add_texture('g', tex_name)
        else:
            sc_asym_params = ParamSet().add_color('g', self.default_value)

        return sc_asym_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TF_d_socket(bpy.types.NodeSocket):
    """Absorption depth socket"""
    bl_idname = 'luxrender_TF_d_socket'
    bl_label = 'Absorption Depth socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_d, 'name'), description=get_props(TF_d, 'description'),
                                default=get_props(TF_d, 'default'), subtype=get_props(TF_d, 'subtype'),
                                min=get_props(TF_d, 'min'), max=get_props(TF_d, 'max'),
                                soft_min=get_props(TF_d, 'soft_min'), soft_max=get_props(TF_d, 'soft_max'),
                                precision=get_props(TF_d, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            d_params = ParamSet().add_texture('d', tex_name)
        else:
            d_params = ParamSet().add_float('d', self.default_value)

        return d_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_OP1_socket(bpy.types.NodeSocket):
    """Opacity1 socket"""
    bl_idname = 'luxrender_TF_OP1_socket'
    bl_label = 'Opacity1 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_OP1, 'name'), description=get_props(TF_OP1, 'description'),
                                       default=get_props(TF_OP1, 'default'), subtype=get_props(TF_OP1, 'subtype'),
                                       min=get_props(TF_OP1, 'min'), max=get_props(TF_OP1, 'max'),
                                       soft_min=get_props(TF_OP1, 'soft_min'), soft_max=get_props(TF_OP1, 'soft_max'),
                                       precision=get_props(TF_OP1, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            opacity1_params = ParamSet().add_texture('opacity1', tex_name)
        else:
            opacity1_params = ParamSet().add_float('opacity1', self.default_value)

        return opacity1_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_OP2_socket(bpy.types.NodeSocket):
    """Opacity2 socket"""
    bl_idname = 'luxrender_TF_OP2_socket'
    bl_label = 'Opacity2 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_OP2, 'name'), description=get_props(TF_OP2, 'description'),
                                       default=get_props(TF_OP2, 'default'), subtype=get_props(TF_OP2, 'subtype'),
                                       min=get_props(TF_OP2, 'min'), max=get_props(TF_OP2, 'max'),
                                       soft_min=get_props(TF_OP2, 'soft_min'), soft_max=get_props(TF_OP2, 'soft_max'),
                                       precision=get_props(TF_OP2, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            opacity2_params = ParamSet().add_texture('opacity2', tex_name)
        else:
            opacity2_params = ParamSet().add_float('opacity2', self.default_value)

        return opacity2_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_OP3_socket(bpy.types.NodeSocket):
    """Opacity3 socket"""
    bl_idname = 'luxrender_TF_OP3_socket'
    bl_label = 'Opacity3 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_OP3, 'name'), description=get_props(TF_OP3, 'description'),
                                       default=get_props(TF_OP3, 'default'), subtype=get_props(TF_OP3, 'subtype'),
                                       min=get_props(TF_OP3, 'min'), max=get_props(TF_OP3, 'max'),
                                       soft_min=get_props(TF_OP3, 'soft_min'), soft_max=get_props(TF_OP3, 'soft_max'),
                                       precision=get_props(TF_OP3, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            opacity3_params = ParamSet().add_texture('opacity3', tex_name)
        else:
            opacity3_params = ParamSet().add_float('opacity3', self.default_value)

        return opacity3_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_OP4_socket(bpy.types.NodeSocket):
    """Opacity4 socket"""
    bl_idname = 'luxrender_TF_OP4_socket'
    bl_label = 'Opacity4 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_OP4, 'name'), description=get_props(TF_OP4, 'description'),
                                       default=get_props(TF_OP4, 'default'), subtype=get_props(TF_OP4, 'subtype'),
                                       min=get_props(TF_OP4, 'min'), max=get_props(TF_OP4, 'max'),
                                       soft_min=get_props(TF_OP4, 'soft_min'), soft_max=get_props(TF_OP4, 'soft_max'),
                                       precision=get_props(TF_OP4, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            opacity4_params = ParamSet().add_texture('opacity4', tex_name)
        else:
            opacity4_params = ParamSet().add_float('opacity4', self.default_value)

        return opacity4_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


# Sockets for carpaint nodes

@LuxRenderAddon.addon_register_class
class luxrender_TF_M1_socket(bpy.types.NodeSocket):
    """M1 socket"""
    bl_idname = 'luxrender_TF_M1_socket'
    bl_label = 'M1 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_M1, 'name'), description='1st glossy layer roughness',
                                 default=get_props(TF_M1, 'default'), subtype=get_props(TF_M1, 'subtype'),
                                 min=get_props(TF_M1, 'min'), max=get_props(TF_M1, 'max'),
                                 soft_min=get_props(TF_M1, 'soft_min'), soft_max=get_props(TF_M1, 'soft_max'),
                                 precision=get_props(TF_M1, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            M1_params = ParamSet().add_texture('M1', tex_name)
        else:
            M1_params = ParamSet().add_float('M1', self.default_value)

        return M1_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_M2_socket(bpy.types.NodeSocket):
    """M2 socket"""
    bl_idname = 'luxrender_TF_M2_socket'
    bl_label = 'M2 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_M2, 'name'), description='2nd glossy layer roughness',
                                 default=get_props(TF_M2, 'default'), subtype=get_props(TF_M2, 'subtype'),
                                 min=get_props(TF_M2, 'min'), max=get_props(TF_M2, 'max'),
                                 soft_min=get_props(TF_M2, 'soft_min'), soft_max=get_props(TF_M2, 'soft_max'),
                                 precision=get_props(TF_M2, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            M2_params = ParamSet().add_texture('M2', tex_name)
        else:
            M2_params = ParamSet().add_float('M2', self.default_value)

        return M2_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_M3_socket(bpy.types.NodeSocket):
    """M3 socket"""
    bl_idname = 'luxrender_TF_M3_socket'
    bl_label = 'M3 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_M3, 'name'), description='3rd glossy layer roughness',
                                 default=get_props(TF_M3, 'default'), subtype=get_props(TF_M3, 'subtype'),
                                 min=get_props(TF_M3, 'min'), max=get_props(TF_M3, 'max'),
                                 soft_min=get_props(TF_M3, 'soft_min'), soft_max=get_props(TF_M3, 'soft_max'),
                                 precision=get_props(TF_M3, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            M3_params = ParamSet().add_texture('M3', tex_name)
        else:
            M3_params = ParamSet().add_float('M3', self.default_value)

        return M3_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_R1_socket(bpy.types.NodeSocket):
    """R1 socket"""
    bl_idname = 'luxrender_TF_R1_socket'
    bl_label = 'R1 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_R1, 'name'), description='1st glossy layer normal reflectance',
                                 default=get_props(TF_R1, 'default'), subtype=get_props(TF_R1, 'subtype'),
                                 min=get_props(TF_R1, 'min'), max=get_props(TF_R1, 'max'),
                                 soft_min=get_props(TF_R1, 'soft_min'), soft_max=get_props(TF_R1, 'soft_max'),
                                 precision=get_props(TF_R1, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            R1_params = ParamSet().add_texture('R1', tex_name)
        else:
            R1_params = ParamSet().add_float('R1', self.default_value)

        return R1_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_R2_socket(bpy.types.NodeSocket):
    """R2 socket"""
    bl_idname = 'luxrender_TF_R2_socket'
    bl_label = 'R2 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_R2, 'name'), description='2nd glossy layer normal reflectance',
                                 default=get_props(TF_R2, 'default'), subtype=get_props(TF_R2, 'subtype'),
                                 min=get_props(TF_R2, 'min'), max=get_props(TF_R2, 'max'),
                                 soft_min=get_props(TF_R2, 'soft_min'), soft_max=get_props(TF_R2, 'soft_max'),
                                 precision=get_props(TF_R2, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            R2_params = ParamSet().add_texture('R2', tex_name)
        else:
            R2_params = ParamSet().add_float('R2', self.default_value)

        return R2_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_R3_socket(bpy.types.NodeSocket):
    """R3 socket"""
    bl_idname = 'luxrender_TF_R3_socket'
    bl_label = 'R3 socket'

    default_value = bpy.props.FloatProperty(name=get_props(TF_R3, 'name'), description='3rd glossy layer normal reflectance',
                                 default=get_props(TF_R3, 'default'), subtype=get_props(TF_R3, 'subtype'),
                                 min=get_props(TF_R3, 'min'), max=get_props(TF_R3, 'max'),
                                 soft_min=get_props(TF_R3, 'soft_min'), soft_max=get_props(TF_R3, 'soft_max'),
                                 precision=get_props(TF_R3, 'precision'))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            R3_params = ParamSet().add_texture('R3', tex_name)
        else:
            R3_params = ParamSet().add_float('R3', self.default_value)

        return R3_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


# Sockets for texture/utitlity nodes

@LuxRenderAddon.addon_register_class
class luxrender_TC_brickmodtex_socket(bpy.types.NodeSocket):
    """brickmodtex socket"""
    bl_idname = 'luxrender_TC_brickmodtex_socket'
    bl_label = 'Brick modulation texture socket'

    default_value = bpy.props.FloatVectorProperty(name='Brick Modulation Texture', subtype='COLOR', min=0.0, max=1.0,
                                                default=(0.9, 0.9, 0.9))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            brickmodtex_params = ParamSet().add_texture('brickmodtex', tex_name)
        else:
            brickmodtex_params = ParamSet().add_color('brickmodtex', self.default_value)

        return brickmodtex_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_bricktex_socket(bpy.types.NodeSocket):
    """bricktex socket"""
    bl_idname = 'luxrender_TC_bricktex_socket'
    bl_label = 'Brick texture socket'

    default_value = bpy.props.FloatVectorProperty(name='Brick Texture', subtype='COLOR', min=0.0, max=1.0,
                                             default=(0.8, 0.8, 0.8))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            bricktex_params = ParamSet().add_texture('bricktex', tex_name)
        else:
            bricktex_params = ParamSet().add_color('bricktex', self.default_value)

        return bricktex_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TC_mortartex_socket(bpy.types.NodeSocket):
    """mortartex socket"""
    bl_idname = 'luxrender_TC_mortartex_socket'
    bl_label = 'Mortar texture socket'

    default_value = bpy.props.FloatVectorProperty(name='Mortar Texture', subtype='COLOR', min=0.0, max=1.0,
                                              default=(0.1, 0.1, 0.1))

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            mortartex_params = ParamSet().add_texture('mortartex', tex_name)
        else:
            mortartex_params = ParamSet().add_color('mortartex', self.default_value)

        return mortartex_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


@LuxRenderAddon.addon_register_class
class luxrender_TF_brickmodtex_socket(bpy.types.NodeSocket):
    """brickmodtex socket"""
    bl_idname = 'luxrender_TF_brickmodtex_socket'
    bl_label = 'Brick modulation texture socket'

    default_value = bpy.props.FloatProperty(name='Brick Modulation Texture', min=0.0, max=1.0, default=0.9)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            brickmodtex_params = ParamSet().add_texture('brickmodtex', tex_name)
        else:
            brickmodtex_params = ParamSet().add_float('brickmodtex', self.default_value)

        return brickmodtex_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_bricktex_socket(bpy.types.NodeSocket):
    """bricktex socket"""
    bl_idname = 'luxrender_TF_bricktex_socket'
    bl_label = 'Brick texture socket'

    default_value = bpy.props.FloatProperty(name='Brick Texture', min=0.0, max=1.0, default=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            bricktex_params = ParamSet().add_texture('bricktex', tex_name)
        else:
            bricktex_params = ParamSet().add_float('bricktex', self.default_value)

        return bricktex_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_TF_mortartex_socket(bpy.types.NodeSocket):
    """mortartex socket"""
    bl_idname = 'luxrender_TF_mortartex_socket'
    bl_label = 'Mortar texture socket'

    default_value = bpy.props.FloatProperty(name='Mortar Texture', min=0.0, max=1.0, default=0.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            mortartex_params = ParamSet().add_texture('mortartex', tex_name)
        else:
            mortartex_params = ParamSet().add_float('mortartex', self.default_value)

        return mortartex_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


# Custom sockets for the mix/add/scale/subtract nodes, in all 3 variants. *sigh*
# First, floats...
@LuxRenderAddon.addon_register_class
class luxrender_TF_tex1_socket(bpy.types.NodeSocket):
    """Texture 1 socket"""
    bl_idname = 'luxrender_TF_tex1_socket'
    bl_label = 'Texture 1 socket'

    tex1 = bpy.props.FloatProperty(name='Value 1', min=0.0, max=10.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'tex1', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            tex1_params = ParamSet().add_texture('tex1', tex_name)
        else:
            tex1_params = ParamSet().add_float('tex1', self.tex1)

        return tex1_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.tex1)


@LuxRenderAddon.addon_register_class
class luxrender_TF_tex2_socket(bpy.types.NodeSocket):
    """Texture 2 socket"""
    bl_idname = 'luxrender_TF_tex2_socket'
    bl_label = 'Texture 2 socket'

    tex2 = bpy.props.FloatProperty(name='Value 2', min=0.0, max=10.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'tex2', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            tex2_params = ParamSet().add_texture('tex2', tex_name)
        else:
            tex2_params = ParamSet().add_float('tex2', self.tex2)

        return tex2_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.tex2)


# Now, colors:
@LuxRenderAddon.addon_register_class
class luxrender_TC_tex1_socket(bpy.types.NodeSocket):
    """Texture 1 socket"""
    bl_idname = 'luxrender_TC_tex1_socket'
    bl_label = 'Texture 1 socket'

    tex1 = bpy.props.FloatVectorProperty(name='Color 1', subtype='COLOR', min=0.0, soft_max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'tex1', text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)

            tex1_params = ParamSet().add_texture('tex1', tex_name)
        else:
            tex1_params = ParamSet().add_color('tex1', self.tex1)

        return tex1_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.tex1))


@LuxRenderAddon.addon_register_class
class luxrender_TC_tex2_socket(bpy.types.NodeSocket):
    """Texture 2 socket"""
    bl_idname = 'luxrender_TC_tex2_socket'
    bl_label = 'Texture 2 socket'

    tex2 = bpy.props.FloatVectorProperty(name='Color 2', subtype='COLOR', min=0.0, soft_max=1.0)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'tex2', text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            tex2_params = ParamSet().add_texture('tex2', tex_name)
        else:
            tex2_params = ParamSet().add_color('tex2', self.tex2)

        return tex2_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.tex2))


# And fresnel!
@LuxRenderAddon.addon_register_class
class luxrender_TFR_tex1_socket(bpy.types.NodeSocket):
    """Texture 1 socket"""
    bl_idname = 'luxrender_TFR_tex1_socket'
    bl_label = 'Texture 1 socket'

    tex1 = bpy.props.FloatProperty(name='IOR 1', min=1.0, max=25.0, default=1.52)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'tex1', text=self.name)

    def draw_color(self, context, node):
        return fresnel_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            tex1_params = ParamSet().add_texture('tex1', tex_name)
        else:
            tex1_params = ParamSet().add_float('tex1', self.tex1)

        return tex1_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.tex1)


@LuxRenderAddon.addon_register_class
class luxrender_TFR_tex2_socket(bpy.types.NodeSocket):
    """Texture 2 socket"""
    bl_idname = 'luxrender_TFR_tex2_socket'
    bl_label = 'Texture 2 socket'

    tex2 = bpy.props.FloatProperty(name='IOR 2', min=1.0, max=25.0, default=1.52)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'tex2', text=self.name)

    def draw_color(self, context, node):
        return fresnel_socket_color

    def get_paramset(self, make_texture):
        tex_node = get_linked_node(self)
        if tex_node:
            if not check_node_export_texture(tex_node):
                return ParamSet()

            tex_name = tex_node.export_texture(make_texture)
            tex2_params = ParamSet().add_texture('tex2', tex_name)
        else:
            tex2_params = ParamSet().add_float('tex2', self.tex2)

        return tex2_params

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.tex2)


@LuxRenderAddon.addon_register_class
class luxrender_float_socket(bpy.types.NodeSocket):
    """Float socket"""
    bl_idname = 'luxrender_float_socket'
    bl_label = 'Value'

    default_value = bpy.props.FloatProperty(name='Value', default=0.5)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    # TODO: implement classic export
    #def get_paramset(self, make_texture):

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_float_limited_0_1_socket(bpy.types.NodeSocket):
    """Float socket with soft limits between 0 and 1"""
    bl_idname = 'luxrender_float_limited_0_1_socket'
    bl_label = 'Value'

    default_value = bpy.props.FloatProperty(name='Value', default=0.5, soft_min=0, soft_max=1)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_float_limited_0_2_socket(bpy.types.NodeSocket):
    """Float socket with soft limits between 0 and 2"""
    bl_idname = 'luxrender_float_limited_0_2_socket'
    bl_label = 'Value'

    default_value = bpy.props.FloatProperty(name='Value', default=1, soft_min=0, soft_max=2)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

    def draw_color(self, context, node):
        return float_socket_color

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, self.default_value)


@LuxRenderAddon.addon_register_class
class luxrender_color_socket(bpy.types.NodeSocket):
    """Color socket"""
    bl_idname = 'luxrender_color_socket'
    bl_label = 'Color'

    default_value = bpy.props.FloatVectorProperty(name='Color', default=(0.5, 0.5, 0.5), subtype='COLOR',
                                                  soft_min=0, soft_max=1)

    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text=self.name)
        else:
            row = layout.row()
            row.alignment = 'LEFT'
            row.prop(self, 'default_value', text='')
            row.label(text=self.name)

    def draw_color(self, context, node):
        return color_socket_color

    # TODO: implement classic export
    #def get_paramset(self, make_texture):

    def export_luxcore(self, properties):
        return export_socket_luxcore(properties, self, list(self.default_value))


# 3D coordinate socket, 2D coordinates is luxrender_transform_socket. Blender does not like numbers in these names
@LuxRenderAddon.addon_register_class
class luxrender_coordinate_socket(bpy.types.NodeSocket):
    """3D coordinate socket"""
    bl_idname = 'luxrender_coordinate_socket'
    bl_label = 'Coordinate socket'

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        layout.label(text=self.name)

    # Socket color
    def draw_color(self, context, node):
        return coord_2d_color

    def export_luxcore(self, properties):
        default_mapping_type = 'globalmapping3d'
        default_transformation = mathutils.Matrix()
        return export_socket_luxcore(properties, self, [default_mapping_type, default_transformation])


@LuxRenderAddon.addon_register_class
class luxrender_transform_socket(bpy.types.NodeSocket):
    """2D transform socket"""
    bl_idname = 'luxrender_transform_socket'
    bl_label = 'Transform socket'

    def draw(self, context, layout, node, text):
        layout.label(text=self.name)

    def draw_color(self, context, node):
        return coord_3d_color

    def export_luxcore(self, properties):
        default_mapping_type = 'uvmapping2d'
        # These are not the LuxCore API default values because we have to compensate Blender stuff
        default_uvscale = [1, -1]
        default_uvdelta = [0, 1]
        return export_socket_luxcore(properties, self, [default_mapping_type, default_uvscale, default_uvdelta])

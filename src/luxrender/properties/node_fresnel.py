# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Jens Verwiebe, Jason Clarke
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

import bpy

from extensions_framework import declarative_property_group

from .. import LuxRenderAddon
from ..properties.texture import (
	FloatTextureParameter, ColorTextureParameter, FresnelTextureParameter,
	import_paramset_to_blender_texture, shorten_name, refresh_preview
)
from ..export import ParamSet, process_filepath_data
from ..export.materials import (
	MaterialCounter, ExportedMaterials, ExportedTextures, add_texture_parameter, get_texture_from_scene
)
from ..outputs import LuxManager, LuxLog
from ..util import dict_merge

from ..properties.node_material import luxrender_fresnel_socket

from ..properties.texture import luxrender_tex_fresnelname

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_fresnelcolor(bpy.types.Node):
	'''Fresnel Color Node'''
	bl_idname = 'luxrender_texture_fresnelcolor_node'
	bl_label = 'Fresnel Color'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.inputs.new('NodeSocketColor', 'Reflection Color')
	
		self.outputs.new('luxrender_fresnel_socket', 'Fresnel')
		
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_fresnelname(bpy.types.Node):
	'''Fresnel Name Node'''
	bl_idname = 'luxrender_texture_fresnelname_node'
	bl_label = 'Fresnel Name'
	bl_icon = 'TEXTURE'

	for prop in luxrender_tex_fresnelname.properties:
		if prop['attr'].startswith('name'):
			frname_presets = prop['items']
			
	frname_preset = bpy.props.EnumProperty(name='Preset', description='NK data presets', items=frname_presets, default='aluminium')
	frname_nkfile = bpy.props.StringProperty(name='Nk File', description='Nk file path', subtype='FILE_PATH')

	def init(self, context):
		self.outputs.new('luxrender_fresnel_socket', 'Fresnel')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'frname_preset')
		if self.frname_preset == 'nk':
			layout.prop(self, 'frname_nkfile')
			
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'
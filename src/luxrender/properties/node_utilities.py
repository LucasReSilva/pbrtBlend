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
from ..properties import luxrender_texture_node
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
from ..properties.node_texture import (
	variant_items, triple_variant_items
)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_add(luxrender_texture_node):
	'''Add texture node'''
	bl_idname = 'luxrender_texture_add_node'
	bl_label = 'Add'
	bl_icon = 'TEXTURE'

	variant = bpy.props.EnumProperty(name='Variant', items=variant_items, default='color')

	def draw_buttons(self, context, layout):
		layout.prop(self, 'variant')

		si = self.inputs.keys()
		so = self.outputs.keys()
		if self.variant == 'color':
			if not 'Color 1' in si: #If there aren't color inputs, create them
				self.inputs.new('NodeSocketColor', 'Color 1')
				self.inputs.new('NodeSocketColor', 'Color 2')
			if 'Float 1' in si: #If there are float inputs, destory them
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			if not 'Color' in so: #If there is no color output, create it
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so: #If there is a float output, destroy it
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Float 1' in si:
				self.inputs.new('NodeSocketFloat', 'Float 1')
				self.inputs.new('NodeSocketFloat', 'Float 2')
			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_harlequin(luxrender_texture_node):
	'''Harlequin texture node'''
	bl_idname = 'luxrender_texture_harlequin_node'
	bl_label = 'Harlequin Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_scale(luxrender_texture_node):
	'''Scale texture node'''
	bl_idname = 'luxrender_texture_scale_node'
	bl_label = 'Scale'
	bl_icon = 'TEXTURE'

	variant = bpy.props.EnumProperty(name='Variant', items=variant_items, default='color')

	def draw_buttons(self, context, layout):
		layout.prop(self, 'variant')

		si = self.inputs.keys()
		so = self.outputs.keys()
		if self.variant == 'color':
			if not 'Color 1' in si:
				self.inputs.new('NodeSocketColor', 'Color 1')
				self.inputs.new('NodeSocketColor', 'Color 2')
			if 'Float 1' in si:
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			if not 'Color' in so:
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Float 1' in si:
				self.inputs.new('NodeSocketFloat', 'Float 1')
				self.inputs.new('NodeSocketFloat', 'Float 2')
			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
				
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_subtract(luxrender_texture_node):
	'''Subtract texture node'''
	bl_idname = 'luxrender_texture_subtract_node'
	bl_label = 'Subtract'
	bl_icon = 'TEXTURE'

	variant = bpy.props.EnumProperty(name='Variant', items=variant_items, default='color')

	def draw_buttons(self, context, layout):
		layout.prop(self, 'variant')

		si = self.inputs.keys()
		so = self.outputs.keys()
		if self.variant == 'color':
			if not 'Color 1' in si:
				self.inputs.new('NodeSocketColor', 'Color 1')
				self.inputs.new('NodeSocketColor', 'Color 2')
			if 'Float 1' in si:
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			if not 'Color' in so:
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Float 1' in si:
				self.inputs.new('NodeSocketFloat', 'Float 1')
				self.inputs.new('NodeSocketFloat', 'Float 2')
			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_uv(luxrender_texture_node):
	'''UV texture node'''
	bl_idname = 'luxrender_texture_uv_node'
	bl_label = 'UV Test Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		

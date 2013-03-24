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


@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blackbody(bpy.types.Node):
	'''Blackbody spectrum node'''
	bl_idname = 'luxrender_texture_blackbody_node'
	bl_label = 'Blackbody Spectrum'
	bl_icon = 'TEXTURE'

	temperature = bpy.props.FloatProperty(name='Temperature', default=6500.0)


	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'temperature')
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_colordepth(bpy.types.Node):
	'''Color at Depth node'''
	bl_idname = 'luxrender_texture_colordepth_node'
	bl_label = 'Color at Depth'
	bl_icon = 'TEXTURE'

	depth = bpy.props.FloatProperty(name='Depth', default=1.0, subtype='DISTANCE', unit='LENGTH')


	def init(self, context):
		self.inputs.new('NodeSocketColor', 'Transmission Color')
		
		self.outputs.new('NodeSocketColor', 'Color')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'depth')
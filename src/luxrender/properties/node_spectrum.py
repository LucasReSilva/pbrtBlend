# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Jens Verwiebe, Jason Clarke, Asbjørn Heid
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
from ..properties import (
	luxrender_texture_node, get_linked_node, check_node_export_texture, check_node_get_paramset
)
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
from ..properties.node_material import (
	luxrender_TC_Kt_socket, get_socket_paramsets
	)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blackbody(luxrender_texture_node):
	'''Blackbody spectrum node'''
	bl_idname = 'luxrender_texture_blackbody_node'
	bl_label = 'Blackbody Spectrum'
	bl_icon = 'TEXTURE'
	bl_width_min = 180

	temperature = bpy.props.FloatProperty(name='Temperature', default=6500.0)

	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'temperature')

	def export_texture(self, make_texture):
		blackbody_params = ParamSet()
		blackbody_params.add_float('temperature', self.temperature)
		
		return make_texture('color', 'blackbody', self.name, blackbody_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_colordepth(luxrender_texture_node):
	'''Color at Depth node'''
	bl_idname = 'luxrender_texture_colordepth_node'
	bl_label = 'Color at Depth'
	bl_icon = 'TEXTURE'

	depth = bpy.props.FloatProperty(name='Depth', default=1.0, subtype='DISTANCE', unit='LENGTH')

	def init(self, context):
		self.inputs.new('luxrender_TC_Kt_socket', 'Transmission Color')
		
		self.outputs.new('NodeSocketColor', 'Color')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'depth')

	def export_texture(self, make_texture):
		colordepth_params = ParamSet()
		colordepth_params.update( get_socket_paramsets(self.inputs, make_texture) )
		colordepth_params.add_float('depth', self.depth)
		
		return make_texture('color', 'colordepth', self.name, colordepth_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_gaussian(luxrender_texture_node):
	'''Gaussian spectrum node'''
	bl_idname = 'luxrender_texture_gaussian_node'
	bl_label = 'Gaussian Spectrum'
	bl_icon = 'TEXTURE'
	bl_width_min = 180

	energy = bpy.props.FloatProperty(name='Energy', default=1.0, description='Relative energy level')
	wavelength = bpy.props.FloatProperty(name='Wavelength (nm)', default=550.0, description='Center-point of the spectrum curve')
	width = bpy.props.FloatProperty(name='Width', default=50.0, description='Width of the spectrum curve')

	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'energy')
		layout.prop(self, 'wavelength')
		layout.prop(self, 'width')

	def export_texture(self, make_texture):
		gaussian_params = ParamSet()
		gaussian_params.add_float('energy', self.energy)
		gaussian_params.add_float('wavelength', self.wavelength)
		gaussian_params.add_float('width', self.width)
		
		return make_texture('color', 'gaussian', self.name, gaussian_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_tabulateddata(luxrender_texture_node):
	'''Tabulated Data spectrum node'''
	bl_idname = 'luxrender_texture_tabulateddata_node'
	bl_label = 'Tabulated Data Spectrum'
	bl_icon = 'TEXTURE'

	data_file = bpy.props.StringProperty(name='Data File', description='Data file path', subtype='FILE_PATH')


	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'data_file')
	
	def export_texture(self, make_texture):
		tabulateddata_params = ParamSet()

		process_filepath_data(LuxManager.CurrentScene, self, self.data_file, tabulateddata_params, 'filename')

		return make_texture('color', 'tabulateddata', self.name, tabulateddata_params)


		

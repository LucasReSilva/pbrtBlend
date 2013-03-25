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

#Define the list of noise types globally, this gets used by a few different nodes
noise_basis_items = [
	('blender_original', 'Blender Original', ''),
	('original_perlin', 'Original Perlin', ''),
	('improved_perlin', 'Improved Perlin', ''),
	('voronoi_f1', 'Voronoi F1', ''),
	('voronoi_f2', 'Voronoi F2', ''),
	('voronoi_f3', 'Voronoi F3', ''),
	('voronoi_f4', 'Voronoi F4', ''),
	('voronoi_f2f1', 'Voronoi F2-F1', ''),
	('voronoi_crackle', 'Voronoi Crackle', ''),
	('cell_noise', 'Cell Noise', ''),
	]

noise_type_items = [
	('soft_noise', 'Soft', ''),
	('hard_noise', 'Hard', '')
	]

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_clouds(bpy.types.Node):
	'''Clouds texture node'''
	bl_idname = 'luxrender_texture_blender_clouds_node'
	bl_label = 'Clouds Texture'
	bl_icon = 'TEXTURE'

	noisetype = bpy.props.EnumProperty(name='Noise Type', description='Soft or hard noise', items=noise_type_items, default='soft_noise')
	noisebasis = bpy.props.EnumProperty(name='Noise Basis', description='Type of noise used', items=noise_basis_items, default='blender_original')
	noisesize = bpy.props.FloatProperty(name='Noise Size', default=0.25)
	noisedepth = bpy.props.IntProperty(name='Noise Depth', default=2)
	bright = bpy.props.FloatProperty(name='Brightness', default=1.0)
	contrast = bpy.props.FloatProperty(name='Contrast', default=1.0)


	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'noisetype')
		layout.prop(self, 'noisebasis')
		layout.prop(self, 'noisesize')
		layout.prop(self, 'noisedepth')
		layout.prop(self, 'bright')
		layout.prop(self, 'contrast')
		
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_fbm(bpy.types.Node):
	'''FBM texture node'''
	bl_idname = 'luxrender_texture_fbm_node'
	bl_label = 'FBM Texture'
	bl_icon = 'TEXTURE'

	octaves = bpy.props.IntProperty(name='Octaves', default=8)
	roughness = bpy.props.FloatProperty(name='Roughness', default=0.5)


	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'octaves')
		layout.prop(self, 'roughness')
		
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_musgrave(bpy.types.Node):
	'''Musgrave texture node'''
	bl_idname = 'luxrender_texture_blender_musgrave_node'
	bl_label = 'Musgrave Texture'
	bl_icon = 'TEXTURE'

	musgrave_type_items = [
		('multifractal', 'Multifractal', ''),
		('ridged_multifractal', 'Ridged Multifractal', ''),
		('hybrid_multifractal', 'Hybrid Multifractal', ''),
		('hetero_terrain', 'Hetero Terrain', ''),
		('fbm', 'FBM', ''),
	]

	musgravetype = bpy.props.EnumProperty(name='Noise Type', description='Type of noise used', items=musgrave_type_items, default='multifractal')
	noisebasis = bpy.props.EnumProperty(name='Noise Basis', description='Basis of noise used', items=noise_basis_items, default='blender_original')
	noisesize = bpy.props.FloatProperty(name='Noise Size', default=0.25)
	h = bpy.props.FloatProperty(name='Dimension', default=1.0)
	lacu = bpy.props.FloatProperty(name='Lacunarity', default=2.0)
	octs = bpy.props.FloatProperty(name='Octaves', default=2.0)
	offset = bpy.props.FloatProperty(name='Offset', default=1.0)
	gain = bpy.props.FloatProperty(name='Gain', default=1.0)
	iscale = bpy.props.FloatProperty(name='Intensity', default=1.0)
	bright = bpy.props.FloatProperty(name='Brightness', default=1.0)
	contrast = bpy.props.FloatProperty(name='Contrast', default=1.0)


	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'musgravetype')
		layout.prop(self, 'noisebasis')
		layout.prop(self, 'noisesize')
		layout.prop(self, 'h')
		layout.prop(self, 'lacu')
		layout.prop(self, 'octs')
		if self.musgravetype in ('ridged_multifractal', 'hybrid_multifractal', 'hetero_terrain'):
			layout.prop(self, 'offset')
		if self.musgravetype in ('ridged_multifractal', 'hybrid_multifractal'):
			layout.prop(self, 'gain')
		if self.musgravetype != 'fbm':	
			layout.prop(self, 'iscale')
		layout.prop(self, 'bright')
		layout.prop(self, 'contrast')
		
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_windy(bpy.types.Node):
	'''Windy texture node'''
	bl_idname = 'luxrender_texture_windy_node'
	bl_label = 'Windy Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
		
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_wrinkled(bpy.types.Node):
	'''Wrinkled texture node'''
	bl_idname = 'luxrender_texture_wrinkled_node'
	bl_label = 'Wrinkled Texture'
	bl_icon = 'TEXTURE'

	octaves = bpy.props.IntProperty(name='Octaves', default=8)
	roughness = bpy.props.FloatProperty(name='Roughness', default=0.5)


	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'octaves')
		layout.prop(self, 'roughness')
		
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'

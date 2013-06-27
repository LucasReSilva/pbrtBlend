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
from ..properties import (luxrender_texture_node, get_linked_node, check_node_export_texture, check_node_get_paramset)
from ..properties.texture import (
	import_paramset_to_blender_texture, shorten_name, refresh_preview
)
from ..export import ParamSet, get_worldscale, process_filepath_data
from ..export.materials import (
	ExportedTextures, add_texture_parameter, get_texture_from_scene
)
from ..outputs import LuxManager, LuxLog

from ..properties.texture import (
	luxrender_tex_brick, luxrender_tex_imagemap, luxrender_tex_normalmap, luxrender_tex_transform, luxrender_tex_mapping
)
from ..properties.node_material import get_socket_paramsets

from ..properties.node_sockets import (
	luxrender_TF_brickmodtex_socket, luxrender_TF_bricktex_socket, luxrender_TF_mortartex_socket, luxrender_TC_brickmodtex_socket, luxrender_TC_bricktex_socket, luxrender_TC_mortartex_socket, luxrender_transform_socket, luxrender_coordinate_socket
)

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

variant_items = [
	('color', 'Color', 'This node ouputs color data'),
	('float', 'Float', 'This node outputs floating point data')
	]
	
triple_variant_items = [
	('color', 'Color', 'This node ouputs color data'),
	('float', 'Float', 'This node outputs floating point data'),
	('fresnel', 'Fresnel', 'This node outputs an optical dataset')
	]

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_blend(luxrender_texture_node):
	'''Blend texture node'''
	bl_idname = 'luxrender_texture_blender_blend_node'
	bl_label = 'Blend Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 180
	
	progression_items = [
		('lin', 'Linear', 'linear'),
		('quad', 'Quadratic', 'quadratic'),
		('ease', 'Easing', 'easing'),
		('diag', 'Diagonal', 'diagonal'),
		('sphere', 'Spherical', 'spherical'),
		('halo', 'Quadratic Sphere', 'quadratic sphere'),
		('radial', 'Radial', 'radial'),
		]
	
	flipxy = bpy.props.BoolProperty(name='Flip XY', description='Switch between horizontal and linear gradient', default=False)
	type = bpy.props.EnumProperty(name='Progression', description='progression', items=progression_items, default='lin')
	bright = bpy.props.FloatProperty(name='Brightness', default=1.0)
	contrast = bpy.props.FloatProperty(name='Contrast', default=1.0)
	
	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, 'flipxy')
		layout.prop(self, 'type')
		layout.prop(self, 'bright')
		layout.prop(self, 'contrast')
	
	def export_texture(self, make_texture):
		blend_params = ParamSet() \
			.add_bool('flipxy', self.flipxy) \
			.add_string('type', self.type) \
			.add_float('bright', self.bright) \
			.add_float('contrast', self.contrast)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			blend_params.update( coord_node.get_paramset() )
		
		return make_texture('float', 'blender_blend', self.name, blend_params)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_brick(luxrender_texture_node):
	'''Brick texture node'''
	bl_idname = 'luxrender_texture_brick_node'
	bl_label = 'Brick Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 180
	
	for prop in luxrender_tex_brick.properties:
		if prop['attr'].startswith('brickbond'):
			brickbond_items = prop['items']
	
	variant = bpy.props.EnumProperty(name='Variant', items=variant_items, default='color')
	brickbond = bpy.props.EnumProperty(name='Bond Type', items=brickbond_items, default='running')
	brickrun = bpy.props.FloatProperty(name='Brick Run', default=0.5, subtype='PERCENTAGE')
	mortarsize = bpy.props.FloatProperty(name='Mortar Size', description='Width of mortar segments', default=0.01, subtype='DISTANCE', unit='LENGTH')
	width = bpy.props.FloatProperty(name='Width', default=0.3, subtype='DISTANCE', unit='LENGTH')
	depth = bpy.props.FloatProperty(name='Depth', default=0.15, subtype='DISTANCE', unit='LENGTH')
	height = bpy.props.FloatProperty(name='Height', default=0.10, subtype='DISTANCE', unit='LENGTH')
	
	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, 'variant')
		layout.prop(self, 'brickbond')
		layout.prop(self, 'brickrun')
		layout.prop(self, 'mortarsize')
		layout.prop(self, 'width')
		layout.prop(self, 'depth')
		layout.prop(self, 'height')

		si = self.inputs.keys()
		so = self.outputs.keys()
		if self.variant == 'color':
			if not 'Brick Color' in si: #If there aren't color inputs, create them
				self.inputs.new('luxrender_TC_brickmodtex_socket', 'Brick Modulation Color')
				self.inputs.new('luxrender_TC_bricktex_socket', 'Brick Color')
				self.inputs.new('luxrender_TC_mortartex_socket', 'Mortar Color')
			if 'Brick Value' in si: #If there are float inputs, destory them
				self.inputs.remove(self.inputs['Brick Modulation Value'])
				self.inputs.remove(self.inputs['Brick Value'])
				self.inputs.remove(self.inputs['Mortar Value'])
			if not 'Color' in so: #If there is no color output, create it
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so: #If there is a float output, destroy it
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Brick Value' in si:
				self.inputs.new('luxrender_TF_brickmodtex_socket', 'Brick Modulation Value')
				self.inputs.new('luxrender_TF_bricktex_socket', 'Brick Value')
				self.inputs.new('luxrender_TF_mortartex_socket', 'Mortar Value')
			if 'Brick Color' in si:
				self.inputs.remove(self.inputs['Brick Modulation Color'])
				self.inputs.remove(self.inputs['Brick Color'])
				self.inputs.remove(self.inputs['Mortar Color'])
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
	
	def export_texture(self, make_texture):
		brick_params = ParamSet() \
			.add_string('brickbond', self.brickbond) \
			.add_float('brickrun', self.brickrun) \
			.add_float('mortarsize', self.mortarsize) \
			.add_float('brickwidth', self.width) \
			.add_float('brickdepth', self.depth) \
			.add_float('brickheight', self.height)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			brick_params.update( coord_node.get_paramset() )
		
		brick_params.update( get_socket_paramsets(self.inputs, make_texture) )
		
		return make_texture(self.variant, 'brick', self.name, brick_params)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_clouds(luxrender_texture_node):
	'''Clouds texture node'''
	bl_idname = 'luxrender_texture_blender_clouds_node'
	bl_label = 'Clouds Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 180

	noisetype = bpy.props.EnumProperty(name='Noise Type', description='Soft or hard noise', items=noise_type_items, default='soft_noise')
	noisebasis = bpy.props.EnumProperty(name='Noise Basis', description='Type of noise used', items=noise_basis_items, default='blender_original')
	noisesize = bpy.props.FloatProperty(name='Noise Size', default=0.25)
	noisedepth = bpy.props.IntProperty(name='Noise Depth', default=2)
	bright = bpy.props.FloatProperty(name='Brightness', default=1.0)
	contrast = bpy.props.FloatProperty(name='Contrast', default=1.0)

	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'noisetype')
		layout.prop(self, 'noisebasis')
		layout.prop(self, 'noisesize')
		layout.prop(self, 'noisedepth')
		layout.prop(self, 'bright')
		layout.prop(self, 'contrast')

	def export_texture(self, make_texture):
		clouds_params = ParamSet() \
			.add_string('noisetype', self.noisetype) \
			.add_string('noisebasis', self.noisebasis) \
			.add_float('noisesize', self.noisesize) \
			.add_integer('noisedepth', self.noisedepth) \
			.add_float('bright', self.bright) \
			.add_float('contrast', self.contrast)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			clouds_params.update( coord_node.get_paramset() )
		
		return make_texture('float', 'blender_clouds', self.name, clouds_params)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_distortednoise(luxrender_texture_node):
	'''Distorted noise texture node'''
	bl_idname = 'luxrender_texture_blender_distortednoise_node'
	bl_label = 'Distorted Noise Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 180
	
	noisebasis = bpy.props.EnumProperty(name='Noise Basis', description='Type of noise used', items=noise_basis_items, default='blender_original')
	type = bpy.props.EnumProperty(name='Noise Basis', description='Type of noise used', items=noise_basis_items, default='blender_original')
	distamount = bpy.props.FloatProperty(name='Distortion', default=1.00)
	noisesize = bpy.props.FloatProperty(name='Noise Size', default=0.25)
	noisedepth = bpy.props.IntProperty(name='Noise Depth', default=2)
	bright = bpy.props.FloatProperty(name='Brightness', default=1.0)
	contrast = bpy.props.FloatProperty(name='Contrast', default=1.0)
	
	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, 'noisebasis')
		layout.prop(self, 'type')
		layout.prop(self, 'distamount')
		layout.prop(self, 'noisesize')
		layout.prop(self, 'noisedepth')
		layout.prop(self, 'bright')
		layout.prop(self, 'contrast')
	
	def export_texture(self, make_texture):
		distortednoise_params = ParamSet() \
			.add_string('noisebasis', self.noisebasis) \
			.add_string('type', self.type) \
			.add_float('noisesize', self.noisesize) \
			.add_float('distamount', self.distamount) \
			.add_integer('noisedepth', self.noisedepth) \
			.add_float('bright', self.bright) \
			.add_float('contrast', self.contrast)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			distortednoise_params.update( coord_node.get_paramset() )
		
		return make_texture('float', 'blender_distortednoise', self.name, distortednoise_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_fbm(luxrender_texture_node):
	'''FBM texture node'''
	bl_idname = 'luxrender_texture_fbm_node'
	bl_label = 'FBM Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 160

	octaves = bpy.props.IntProperty(name='Octaves', default=8)
	roughness = bpy.props.FloatProperty(name='Roughness', default=0.5)

	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'octaves')
		layout.prop(self, 'roughness')

	def export_texture(self, make_texture):
		fbm_params = ParamSet() \
			.add_integer('octaves', self.octaves) \
			.add_float('roughness', self.roughness)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			fbm_params.update( coord_node.get_paramset() )
		
		return make_texture('float', 'fbm', self.name, fbm_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_image_map(luxrender_texture_node):
	'''Image map texture node'''
	bl_idname = 'luxrender_texture_image_map_node'
	bl_label = 'Image Map Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 220
	
	for prop in luxrender_tex_imagemap.properties:
		if prop['attr'].startswith('filtertype'):
			filter_items = prop['items']
		if prop['attr'].startswith('wrap'):
			wrap_items = prop['items']
		if prop['attr'].startswith('channel'):
			channel_items = prop['items']

	filename = bpy.props.StringProperty(name='File Name', description='Path to the normal map', subtype='FILE_PATH')
	variant = bpy.props.EnumProperty(name='Variant', items=variant_items, default='color')
	channel = bpy.props.EnumProperty(name='Channel', items=channel_items, default='mean')
	gamma = bpy.props.FloatProperty(name='Gamma', default=2.2, min=0.0, max=5.0)
	gain = bpy.props.FloatProperty(name='Gain', default=1.0, min=-10.0, max=10.0)
	filtertype = bpy.props.EnumProperty(name='Filter Type', description='Texture filtering method', items=filter_items, default='bilinear')
	wrap = bpy.props.EnumProperty(name='Wrapping', description='Texture wrapping method', items=wrap_items, default='repeat')
	maxanisotropy = bpy.props.FloatProperty(name='Max Anisotropy', default=8.0)
	discardmipmaps = bpy.props.IntProperty(name='Discard Mipmaps', default=1)


	def init(self, context):
		self.inputs.new('luxrender_transform_socket', '2D Coordinate')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'filename')
		layout.prop(self, 'variant')
		if self.variant == 'float':
			layout.prop(self, 'channel')
		layout.prop(self, 'gamma')
		layout.prop(self, 'gain')
		layout.prop(self, 'filtertype')
		if self.filtertype in ('mipmap_trilinear', 'mipmap_ewa'):
			layout.prop(self, 'maxanisotropy')
			layout.prop(self, 'discardmipmaps')
		layout.prop(self, 'wrap')
		
		s = self.outputs.keys()
		if self.variant == 'color':
			if not 'Color' in s:
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in s:
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Float' in s:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in s:
				self.outputs.remove(self.outputs['Color'])

	def export_texture(self, make_texture):
		imagemap_params = ParamSet()
		
		process_filepath_data(LuxManager.CurrentScene, self, self.filename, imagemap_params, 'filename')
		if self.variant == 'float':
			imagemap_params.add_string('channel', self.channel)
		imagemap_params.add_string('filtertype', self.filtertype)
		imagemap_params.add_float('gain', self.gain)
		imagemap_params.add_float('gamma', self.gamma)
		imagemap_params.add_string('wrap', self.wrap)
		if self.filtertype in ('mipmap_ewa', 'mipmap_trilinear'):
			imagemap_params.add_float('maxanisotropy', self.maxanisotropy)
			imagemap_params.add_integer('discardmipmaps', self.discardmipmaps)
				
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			imagemap_params.update( coord_node.get_paramset() )
		else:
			imagemap_params.add_float('vscale', -1.0)

		return make_texture(self.variant, 'imagemap', self.name, imagemap_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_musgrave(luxrender_texture_node):
	'''Musgrave texture node'''
	bl_idname = 'luxrender_texture_blender_musgrave_node'
	bl_label = 'Musgrave Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 180

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
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
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

	def export_texture(self, make_texture):
		musgrave_params = ParamSet()
		musgrave_params.add_string('musgravetype', self.musgravetype)
		musgrave_params.add_string('noisebasis', self.noisebasis)
		musgrave_params.add_float('noisesize', self.noisesize)
		musgrave_params.add_float('h', self.h)
		musgrave_params.add_float('lacu', self.lacu)
		musgrave_params.add_float('octs', self.octs)
		if self.musgravetype in ('ridged_multifractal', 'hybrid_multifractal', 'hetero_terrain'):
			musgrave_params.add_float('offset', self.offset)
		if self.musgravetype in ('ridged_multifractal', 'hybrid_multifractal'):
			musgrave_params.add_float('gain', self.gain)
		if self.musgravetype != 'fbm':
			musgrave_params.add_float('iscale', self.iscale)
		musgrave_params.add_float('bright', self.bright)
		musgrave_params.add_float('contrast', self.contrast)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			musgrave_params.update( coord_node.get_paramset() )
		
		return make_texture('float', 'blender_musgrave', self.name, musgrave_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_normal_map(luxrender_texture_node):
	'''Normal map texture node'''
	bl_idname = 'luxrender_texture_normal_map_node'
	bl_label = 'Normal Map Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 220
	
	for prop in luxrender_tex_normalmap.properties:
		if prop['attr'].startswith('filtertype'):
			filter_items = prop['items']
		if prop['attr'].startswith('wrap'):
			wrap_items = prop['items']

	filename = bpy.props.StringProperty(name='File Name', description='Path to the normal map', subtype='FILE_PATH')
	filtertype = bpy.props.EnumProperty(name='Filter Type', description='Texture filtering method', items=filter_items, default='bilinear')
	wrap = bpy.props.EnumProperty(name='Wrapping', description='Texture wrapping method', items=wrap_items, default='repeat')
	maxanisotropy = bpy.props.FloatProperty(name='Max Anisotropy', default=8.0)
	discardmipmaps = bpy.props.IntProperty(name='Discard Mipmaps', default=1)


	def init(self, context):
		self.inputs.new('luxrender_transform_socket', '2D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'filename')
		layout.prop(self, 'filtertype')
		if self.filtertype in ('mipmap_trilinear', 'mipmap_ewa'):
			layout.prop(self, 'maxanisotropy')
			layout.prop(self, 'discardmipmaps')
		layout.prop(self, 'wrap')

	def export_texture(self, make_texture):
		normalmap_params = ParamSet()
		
		process_filepath_data(LuxManager.CurrentScene, self, self.filename, normalmap_params, 'filename')

		normalmap_params.add_string('filtertype', self.filtertype)
		normalmap_params.add_string('wrap', self.wrap)
		if self.filtertype in ('mipmap_ewa', 'mipmap_trilinear'):
			normalmap_params.add_float('maxanisotropy', self.maxanisotropy)
			normalmap_params.add_integer('discardmipmaps', self.discardmipmaps)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			normalmap_params.update( coord_node.get_paramset() )
		else:
			normalmap_params.add_float('vscale', -1.0)

		return make_texture('float', 'normalmap', self.name, normalmap_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_windy(luxrender_texture_node):
	'''Windy texture node'''
	bl_idname = 'luxrender_texture_windy_node'
	bl_label = 'Windy Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 160

	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')

	def export_texture(self, make_texture):
		windy_params = ParamSet()
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			wrinkled_params.update( coord_node.get_paramset() )
		
		return make_texture('float', 'windy', self.name, windy_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_wrinkled(luxrender_texture_node):
	'''Wrinkled texture node'''
	bl_idname = 'luxrender_texture_wrinkled_node'
	bl_label = 'Wrinkled Texture'
	bl_icon = 'TEXTURE'
	bl_width_min = 160

	octaves = bpy.props.IntProperty(name='Octaves', default=8)
	roughness = bpy.props.FloatProperty(name='Roughness', default=0.5)


	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'octaves')
		layout.prop(self, 'roughness')
		
	def export_texture(self, make_texture):
		wrinkled_params = ParamSet() \
			.add_integer('octaves', self.octaves) \
			.add_float('roughness', self.roughness)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			wrinkled_params.update( coord_node.get_paramset() )
		
		return make_texture('float', 'wrinkled', self.name, wrinkled_params)
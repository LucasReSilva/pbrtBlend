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
from ..properties import (luxrender_texture_node, get_linked_node, check_node_export, check_node_get_paramset)
from ..properties.texture import (
	FloatTextureParameter, ColorTextureParameter, FresnelTextureParameter,
	import_paramset_to_blender_texture, shorten_name, refresh_preview
)
from ..export import ParamSet, get_worldscale, process_filepath_data
from ..export.materials import (
	MaterialCounter, ExportedMaterials, ExportedTextures, add_texture_parameter, get_texture_from_scene
)
from ..outputs import LuxManager, LuxLog
from ..util import dict_merge

from ..properties.texture import (
	luxrender_tex_imagemap, luxrender_tex_normalmap, luxrender_tex_transform, luxrender_tex_mapping
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
class luxrender_3d_coordinates_node(luxrender_texture_node):
	'''3D texture coordinates node'''
	bl_idname = 'luxrender_3d_coordinates_node'
	bl_label = '3D Texture Coordinates'
	bl_icon = 'TEXTURE'

	for prop in luxrender_tex_transform.properties:
		if prop['attr'].startswith('coordinates'):
			coordinate_items = prop['items']

	coordinates = bpy.props.EnumProperty(name='Coordinates', items=coordinate_items)
	translate = bpy.props.FloatVectorProperty(name='Translate')
	rotate = bpy.props.FloatVectorProperty(name='Rotate', subtype='DIRECTION', unit='ROTATION')
	scale = bpy.props.FloatVectorProperty(name='Scale', default=(1.0, 1.0, 1.0))


	def init(self, context):
		self.outputs.new('luxrender_coordinate_socket', '3D Coordinate')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'coordinates')
		layout.prop(self, 'translate')
		layout.prop(self, 'rotate')
		layout.prop(self, 'scale')
		
	def get_paramset(self):
		coord_params = ParamSet()
		
		ws = get_worldscale(as_scalematrix=False)
		
		coord_params.add_string('coordinates', self.coordinates)
		coord_params.add_vector('translate', [i*ws for i in self.translate])
		coord_params.add_vector('rotate', self.rotate)
		coord_params.add_vector('scale', [i*ws for i in self.scale])
		
		return coord_params
		
@LuxRenderAddon.addon_register_class
class luxrender_2d_coordinates_node(luxrender_texture_node):
	'''2D texture coordinates node'''
	bl_idname = 'luxrender_2d_coordinates_node'
	bl_label = '2D Texture Coordinates'
	bl_icon = 'TEXTURE'

	for prop in luxrender_tex_mapping.properties:
		if prop['attr'].startswith('type'):
			coordinate_items = prop['items']

	coordinates = bpy.props.EnumProperty(name='Coordinates', items=coordinate_items)
	uscale = bpy.props.FloatProperty(name='U Scale', default=1.0, min=-500.0, max=500.0)
	vscale = bpy.props.FloatProperty(name='V Scale', default=-1.0, min=-500.0, max=500.0)
	udelta = bpy.props.FloatProperty(name='U Offset', default=1.0, min=-500.0, max=500.0)
	vdelta = bpy.props.FloatProperty(name='V Offset', default=1.0, min=-500.0, max=500.0)
	v1 = bpy.props.FloatVectorProperty(name='V1', default=(1.0, 0.0, 0.0))
	v2 = bpy.props.FloatVectorProperty(name='V2', default=(0.0, 1.0, 0.0))


	def init(self, context):
		self.outputs.new('luxrender_transform_socket', '2D Coordinate')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'coordinates')
		if self.coordinates == 'planar':
			layout.prop(self, 'v1')
			layout.prop(self, 'v2')
			layout.prop(self, 'udelta')
		else:
			layout.prop(self, 'uscale')
			layout.prop(self, 'vscale')
			layout.prop(self, 'udelta')
			layout.prop(self, 'vdelta')

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_bump_map(luxrender_texture_node):
	'''Bump map texture node'''
	bl_idname = 'luxrender_texture_bump_map_node'
	bl_label = 'Bump Map Texture'
	bl_icon = 'TEXTURE'

	bump_height = bpy.props.FloatProperty(name='Bump Height', description='Height of the bump map', default=.001, precision=6, subtype='DISTANCE', unit='LENGTH')

	def init(self, context):
		self.inputs.new('NodeSocketFloat', 'Bump Value')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'bump_height')
		
	def export(self, material, export_texture):
		bumpmap_params = ParamSet() \
			.add_float('tex1', self.bump_height)
			
		def export_bumpmap(socket):
			node = get_linked_node(socket)
			if not check_node_export(node):
				return None
			return node.export(material, export_texture)
		
		bumpmap_name = export_bumpmap(self.inputs[0])
		
		bumpmap_params.add_texture("tex2", bumpmap_name)
		
		return export_texture('float', 'scale', self.name, bumpmap_params)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_clouds(luxrender_texture_node):
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
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'noisetype')
		layout.prop(self, 'noisebasis')
		layout.prop(self, 'noisesize')
		layout.prop(self, 'noisedepth')
		layout.prop(self, 'bright')
		layout.prop(self, 'contrast')
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_fbm(luxrender_texture_node):
	'''FBM texture node'''
	bl_idname = 'luxrender_texture_fbm_node'
	bl_label = 'FBM Texture'
	bl_icon = 'TEXTURE'

	octaves = bpy.props.IntProperty(name='Octaves', default=8)
	roughness = bpy.props.FloatProperty(name='Roughness', default=0.5)


	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'octaves')
		layout.prop(self, 'roughness')
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_image_map(luxrender_texture_node):
	'''Image map texture node'''
	bl_idname = 'luxrender_texture_image_map_node'
	bl_label = 'Image Map Texture'
	bl_icon = 'TEXTURE'
	
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
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_blender_musgrave(luxrender_texture_node):
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
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_normal_map(luxrender_texture_node):
	'''Normal map texture node'''
	bl_idname = 'luxrender_texture_normal_map_node'
	bl_label = 'Normal Map Texture'
	bl_icon = 'TEXTURE'
	
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
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_hitpointcolor(luxrender_texture_node):
	'''Vertex Colors texture node'''
	bl_idname = 'luxrender_texture_hitpointcolor_node'
	bl_label = 'Vertex Colors Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		
	def export(self, material, export_texture):
		hitpointcolor_params = ParamSet()
				
		return export_texture('color', 'hitpointcolor', self.name, hitpointcolor_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_hitpointgrey(luxrender_texture_node):
	'''Vertex Grey texture node'''
	bl_idname = 'luxrender_texture_hitpointgrey_node'
	bl_label = 'Vertex Grey Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def export(self, material, export_texture):
		hitpointgrey_params = ParamSet()
				
		return export_texture('float', 'hitpointgrey', self.name, hitpointgrey_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_hitpointalpha(luxrender_texture_node):
	'''Vertex Alpha texture node'''
	bl_idname = 'luxrender_texture_hitpointalpha_node'
	bl_label = 'Vertex Alpha Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def export(self, material, export_texture):
		hitpointalpha_params = ParamSet()
				
		return export_texture('float', 'hitpointalpha', self.name, hitpointalpha_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_windy(luxrender_texture_node):
	'''Windy texture node'''
	bl_idname = 'luxrender_texture_windy_node'
	bl_label = 'Windy Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_wrinkled(luxrender_texture_node):
	'''Wrinkled texture node'''
	bl_idname = 'luxrender_texture_wrinkled_node'
	bl_label = 'Wrinkled Texture'
	bl_icon = 'TEXTURE'

	octaves = bpy.props.IntProperty(name='Octaves', default=8)
	roughness = bpy.props.FloatProperty(name='Roughness', default=0.5)


	def init(self, context):
		self.inputs.new('luxrender_coordinate_socket', '3D Coordinate')
		self.outputs.new('NodeSocketFloat', 'Float')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'octaves')
		layout.prop(self, 'roughness')
		
	def export(self, material, export_texture):
		print('export wrinkled')
		wrinkled_params = ParamSet() \
			.add_integer('octaves', self.octaves) \
			.add_float('roughness', self.roughness)
		
		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			wrinkled_params.update( coord_node.get_paramset() )
		
		return export_texture('float', 'wrinkled', self.name, wrinkled_params)
		
#3D coordinate socket, 2D coordinates is luxrender_transform_socket. Blender does not like numbers in these names
@LuxRenderAddon.addon_register_class
class luxrender_coodinate_socket(bpy.types.NodeSocket):
	# Description string
	'''coordinate socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_coordinate_socket'
	# Label for nice name display
	bl_label = 'Coordinate socket'
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.label(text=self.name)
		
	
	# Socket color
	def draw_color(self, context, node):
		return (0.50, 0.25, 0.60, 1.0)
			
	
@LuxRenderAddon.addon_register_class
class luxrender_transform_socket(bpy.types.NodeSocket):
	# Description string
	'''2D transform socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_transform_socket'
	# Label for nice name display
	bl_label = 'Transform socket'
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.label(text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.65, 0.55, 0.75, 1.0)
		

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
from ..properties.node_texture import (
	variant_items, triple_variant_items
)
from ..properties.node_material import (
	luxrender_fresnel_socket, luxrender_TF_amount_socket, float_socket_color, color_socket_color, fresnel_socket_color, get_socket_paramsets
)

from ..properties.node_texture import luxrender_transform_socket

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
				self.inputs.new('luxrender_TC_tex1_socket', 'Color 1')
				self.inputs.new('luxrender_TC_tex2_socket', 'Color 2')
			if 'Float 1' in si: #If there are float inputs, destory them
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			if not 'Color' in so: #If there is no color output, create it
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so: #If there is a float output, destroy it
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Float 1' in si:
				self.inputs.new('luxrender_TF_tex1_socket', 'Float 1')
				self.inputs.new('luxrender_TF_tex2_socket', 'Float 2')
			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])

	def export_texture(self, make_texture):		
		addtex_params = ParamSet()
		addtex_params.update( get_socket_paramsets(self.inputs, make_texture) )

		return make_texture(self.variant, 'add', self.name, addtex_params)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_constant(luxrender_texture_node):
	'''Constant texture node'''
	bl_idname = 'luxrender_texture_constant_node'
	bl_label = 'Value' #Mimics Cycles/Compositor "input > value" node
	bl_icon = 'TEXTURE'

	variant = bpy.props.EnumProperty(name='Variant', items=triple_variant_items, default='color')
	color = bpy.props.FloatVectorProperty(name='Color', subtype='COLOR', min=0.0, max=4.0)
	float = bpy.props.FloatProperty(name='Float', precision=5)
	fresnel = bpy.props.FloatProperty(name='IOR', default=1.52, min=1.0, max=25.0, precision=5)

	def draw_buttons(self, context, layout):
		layout.prop(self, 'variant')
		if self.variant == 'color':
			layout.prop(self, 'color')
		if self.variant == 'float':
			layout.prop(self, 'float')
		if self.variant == 'fresnel':
			layout.prop(self, 'fresnel')

		si = self.inputs.keys()
		so = self.outputs.keys()
		if self.variant == 'color':
			if not 'Color' in so:
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])
			if 'Fresnel' in so:
				self.outputs.remove(self.outputs['Fresnel'])
		
		if self.variant == 'float':
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
			if 'Fresnel' in so:
				self.outputs.remove(self.outputs['Fresnel'])
		
		if self.variant == 'fresnel':
			if not 'Fresnel' in so:
				self.outputs.new('luxrender_fresnel_socket', 'Fresnel')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])

	def export_texture(self, make_texture):
		constant_params = ParamSet()

		if self.variant == 'float':
			constant_params.add_float('value', self.float)
		if self.variant == 'color':
			constant_params.add_color('value', self.color)
		if self.variant == 'fresnel':
			constant_params.add_float('value', self.fresnel)
		return make_texture(self.variant, 'constant', self.name, constant_params)

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_harlequin(luxrender_texture_node):
	'''Harlequin texture node'''
	bl_idname = 'luxrender_texture_harlequin_node'
	bl_label = 'Harlequin Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')

	def export_texture(self, make_texture):
		harlequin_params = ParamSet()
		return make_texture('color', 'harlequin', self.name, harlequin_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_mix(luxrender_texture_node):
	'''Mix texture node'''
	bl_idname = 'luxrender_texture_mix_node'
	bl_label = 'Mix'
	bl_icon = 'TEXTURE'
	bl_width_min = 180

	variant = bpy.props.EnumProperty(name='Variant', items=triple_variant_items, default='color')
	
	def init(self, context):
		self.inputs.new('luxrender_TF_amount_socket', 'Mix Amount')

	def draw_buttons(self, context, layout):
		layout.prop(self, 'variant')

		si = self.inputs.keys()
		so = self.outputs.keys()
		if self.variant == 'color':
			if not 'Color 1' in si:
				self.inputs.new('luxrender_TC_tex1_socket', 'Color 1')
				self.inputs.new('luxrender_TC_tex2_socket', 'Color 2')
			if 'Float 1' in si:
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			if 'IOR 1' in si:
				self.inputs.remove(self.inputs['IOR 1'])
				self.inputs.remove(self.inputs['IOR 2'])

			if not 'Color' in so:
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])
			if 'Fresnel' in so:
				self.outputs.remove(self.outputs['Fresnel'])
		
		if self.variant == 'float':
			if not 'Float 1' in si:
				self.inputs.new('luxrender_TF_tex1_socket', 'Float 1')
				self.inputs.new('luxrender_TF_tex2_socket', 'Float 2')
			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if 'IOR 1' in si:
				self.inputs.remove(self.inputs['IOR 1'])
				self.inputs.remove(self.inputs['IOR 2'])

			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
			if 'Fresnel' in so:
				self.outputs.remove(self.outputs['Fresnel'])
		
		if self.variant == 'fresnel':
			if not 'IOR 1' in si:
				self.inputs.new('luxrender_TFR_tex1_socket', 'IOR 1')
				self.inputs.new('luxrender_TFR_tex2_socket', 'IOR 2')

			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if 'Float 1' in si:
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			
			if not 'Fresnel' in so:
				self.outputs.new('luxrender_fresnel_socket', 'Fresnel')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])

	def export_texture(self, make_texture):
		mix_params = ParamSet()
		mix_params.update( get_socket_paramsets(self.inputs, make_texture) )
		
		return make_texture(self.variant, 'mix', self.name, mix_params)

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
				self.inputs.new('luxrender_TC_tex1_socket', 'Color 1')
				self.inputs.new('luxrender_TC_tex2_socket', 'Color 2')
			if 'Float 1' in si:
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			if not 'Color' in so:
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Float 1' in si:
				self.inputs.new('luxrender_TF_tex1_socket', 'Float 1')
				self.inputs.new('luxrender_TF_tex2_socket', 'Float 2')
			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])

	def export_texture(self, make_texture):
		scale_params = ParamSet()
		scale_params.update( get_socket_paramsets(self.inputs, make_texture) )
		
		return make_texture(self.variant, 'scale', self.name, scale_params)

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
				self.inputs.new('luxrender_TC_tex1_socket', 'Color 1')
				self.inputs.new('luxrender_TC_tex2_socket', 'Color 2')
			if 'Float 1' in si:
				self.inputs.remove(self.inputs['Float 1'])
				self.inputs.remove(self.inputs['Float 2'])
			if not 'Color' in so:
				self.outputs.new('NodeSocketColor', 'Color')
			if 'Float' in so:
				self.outputs.remove(self.outputs['Float'])
		if self.variant == 'float':
			if not 'Float 1' in si:
				self.inputs.new('luxrender_TF_tex1_socket', 'Float 1')
				self.inputs.new('luxrender_TF_tex2_socket', 'Float 2')
			if 'Color 1' in si:
				self.inputs.remove(self.inputs['Color 1'])
				self.inputs.remove(self.inputs['Color 2'])
			if not 'Float' in so:
				self.outputs.new('NodeSocketFloat', 'Float')
			if 'Color' in so:
				self.outputs.remove(self.outputs['Color'])
	
	def export_texture(self, make_texture):
		subtract_params = ParamSet()
		subtract_params.update( get_socket_paramsets(self.inputs, make_texture) )
		
		return make_texture(self.variant, 'subtract', self.name, subtract_params)
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_uv(luxrender_texture_node):
	'''UV texture node'''
	bl_idname = 'luxrender_texture_uv_node'
	bl_label = 'UV Test Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.inputs.new('luxrender_transform_socket', '2D Transform')
		
		self.outputs.new('NodeSocketColor', 'Color')

	def export_texture(self, make_texture):
		uvtest_params = ParamSet()

		coord_node = get_linked_node(self.inputs[0])
		if coord_node and check_node_get_paramset(coord_node):
			uvtest_params.update( coord_node.get_paramset() )
		else:
			uvtest_params.add_float('vscale', -1.0)
		
		return make_texture('color', 'uv', self.name, uvtest_params)

#Custom sockets for the mix/add/scale/subtract nodes, in all 3 variants. *sigh*
#First, floats...
@LuxRenderAddon.addon_register_class
class luxrender_TF_tex1_socket(bpy.types.NodeSocket):
	'''Texture 1 socket'''
	bl_idname = 'luxrender_TF_tex1_socket'
	bl_label = 'Texture 1 socket'
	
	tex1 = bpy.props.FloatProperty(name='Value 1', min=0.0, max=10.0)
	
	def draw(self, context, layout, node):
		layout.prop(self, 'tex1', text=self.name)
	
	def draw_color(self, context, node):
		return float_socket_color
	
	def get_paramset(self, make_texture):
		tex_node = get_linked_node(self)
		if tex_node:
			if not check_node_export_texture(tex_node):
				return ParamSet()
			
			tex_name = tex_node.export_texture(make_texture)
			
			tex1_params = ParamSet() \
				.add_texture('tex1', tex_name)
		else:
			tex1_params = ParamSet() \
				.add_float('tex1', self.tex1)
		
		return tex1_params

@LuxRenderAddon.addon_register_class
class luxrender_TF_tex2_socket(bpy.types.NodeSocket):
	'''Texture 2 socket'''
	bl_idname = 'luxrender_TF_tex2_socket'
	bl_label = 'Texture 2 socket'
	
	tex2 = bpy.props.FloatProperty(name='Value 2', min=0.0, max=10.0)
	
	def draw(self, context, layout, node):
		layout.prop(self, 'tex2', text=self.name)
	
	def draw_color(self, context, node):
		return float_socket_color
	
	def get_paramset(self, make_texture):
		tex_node = get_linked_node(self)
		if tex_node:
			if not check_node_export_texture(tex_node):
				return ParamSet()
			
			tex_name = tex_node.export_texture(make_texture)
			
			tex2_params = ParamSet() \
				.add_texture('tex2', tex_name)
		else:
			tex2_params = ParamSet() \
				.add_float('tex2', self.tex2)
		
		return tex2_params

#Now, colors:
@LuxRenderAddon.addon_register_class
class luxrender_TC_tex1_socket(bpy.types.NodeSocket):
	'''Texture 1 socket'''
	bl_idname = 'luxrender_TC_tex1_socket'
	bl_label = 'Texture 1 socket'
	
	tex1 = bpy.props.FloatVectorProperty(name='Color 1', subtype='COLOR', min=0.0, soft_max=1.0)
	
	def draw(self, context, layout, node):
		layout.prop(self, 'tex1', text=self.name)
	
	def draw_color(self, context, node):
		return color_socket_color
	
	def get_paramset(self, make_texture):
		tex_node = get_linked_node(self)
		if tex_node:
			if not check_node_export_texture(tex_node):
				return ParamSet()
			
			tex_name = tex_node.export_texture(make_texture)
			
			tex1_params = ParamSet() \
				.add_texture('tex1', tex_name)
		else:
			tex1_params = ParamSet() \
				.add_color('tex1', self.tex1)
		
		return tex1_params

@LuxRenderAddon.addon_register_class
class luxrender_TC_tex2_socket(bpy.types.NodeSocket):
	'''Texture 2 socket'''
	bl_idname = 'luxrender_TC_tex2_socket'
	bl_label = 'Texture 2 socket'
	
	tex2 = bpy.props.FloatVectorProperty(name='Color 2', subtype='COLOR', min=0.0, soft_max=1.0)
	
	def draw(self, context, layout, node):
		layout.prop(self, 'tex2', text=self.name)
	
	def draw_color(self, context, node):
		return color_socket_color
	
	def get_paramset(self, make_texture):
		tex_node = get_linked_node(self)
		if tex_node:
			if not check_node_export_texture(tex_node):
				return ParamSet()
			
			tex_name = tex_node.export_texture(make_texture)
			
			tex2_params = ParamSet() \
				.add_texture('tex2', tex_name)
		else:
			tex2_params = ParamSet() \
				.add_color('tex2', self.tex2)
		
		return tex2_params

#And fresnel!
@LuxRenderAddon.addon_register_class
class luxrender_TFR_tex1_socket(bpy.types.NodeSocket):
	'''Texture 1 socket'''
	bl_idname = 'luxrender_TFR_tex1_socket'
	bl_label = 'Texture 1 socket'
	
	tex1 = bpy.props.FloatProperty(name='IOR 1', min=1.0, max=25.0, default=1.52)
	
	def draw(self, context, layout, node):
		layout.prop(self, 'tex1', text=self.name)
	
	def draw_color(self, context, node):
		return fresnel_socket_color
	
	def get_paramset(self, make_texture):
		tex_node = get_linked_node(self)
		if tex_node:
			if not check_node_export_texture(tex_node):
				return ParamSet()
			
			tex_name = tex_node.export_texture(make_texture)
			
			tex1_params = ParamSet() \
				.add_texture('tex1', tex_name)
		else:
			tex1_params = ParamSet() \
				.add_float('tex1', self.tex1)
		
		return tex1_params

@LuxRenderAddon.addon_register_class
class luxrender_TFR_tex2_socket(bpy.types.NodeSocket):
	'''Texture 2 socket'''
	bl_idname = 'luxrender_TFR_tex2_socket'
	bl_label = 'Texture 2 socket'
	
	tex2 = bpy.props.FloatProperty(name='IOR 2', min=1.0, max=25.0, default=1.52)
	
	def draw(self, context, layout, node):
		layout.prop(self, 'tex2', text=self.name)
	
	def draw_color(self, context, node):
		return fresnel_socket_color
	
	def get_paramset(self, make_texture):
		tex_node = get_linked_node(self)
		if tex_node:
			if not check_node_export_texture(tex_node):
				return ParamSet()
			
			tex_name = tex_node.export_texture(make_texture)
			
			tex2_params = ParamSet() \
				.add_texture('tex2', tex_name)
		else:
			tex2_params = ParamSet() \
				.add_float('tex2', self.tex2)
		
		return tex2_params


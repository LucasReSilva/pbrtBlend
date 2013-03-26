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
from ..properties import luxrender_node, luxrender_material_node
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

from ..properties.material import * # for now just the big hammer for starting autogenerate sockets

# pull default values for inputs and add alpha value to color tuplet
def get_default(TextureParameter):
	TextureParameter = TextureParameter.default
	return TextureParameter

def add_nodetype(layout, type):
	layout.operator('node.add_node', text=type.bl_label).type = type.bl_rna.identifier

@LuxRenderAddon.addon_register_class
class lux_node_Materials_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_materials"
	bl_label = "Materials"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_material_carpaint_node)
		add_nodetype(layout, bpy.types.luxrender_material_cloth_node)
		add_nodetype(layout, bpy.types.luxrender_material_glass_node)
		add_nodetype(layout, bpy.types.luxrender_material_glass2_node)
		add_nodetype(layout, bpy.types.luxrender_material_glossy_node)
		add_nodetype(layout, bpy.types.luxrender_material_glossycoating_node)
#		add_nodetype(layout, bpy.types.luxrender_material_glossytranslucent_node)
		add_nodetype(layout, bpy.types.luxrender_material_layered_node)
		add_nodetype(layout, bpy.types.luxrender_material_matte_node)
		add_nodetype(layout, bpy.types.luxrender_material_mattetranslucent_node)
		add_nodetype(layout, bpy.types.luxrender_material_metal_node)
		add_nodetype(layout, bpy.types.luxrender_material_metal2_node)
		add_nodetype(layout, bpy.types.luxrender_material_mirror_node)
		add_nodetype(layout, bpy.types.luxrender_material_mix_node)
		add_nodetype(layout, bpy.types.luxrender_material_null_node)
		add_nodetype(layout, bpy.types.luxrender_material_roughglass_node)
#		add_nodetype(layout, bpy.types.luxrender_material_scatter_node)
#		add_nodetype(layout, bpy.types.luxrender_material_shinymetal_node)
#		add_nodetype(layout, bpy.types.luxrender_material_velvet_node)

@LuxRenderAddon.addon_register_class
class lux_node_Outputs_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_outputs"
	bl_label = "Outputs"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_material_output_node)

@LuxRenderAddon.addon_register_class
class lux_node_Lights_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_lights"
	bl_label = "Lights"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_light_area_node)
		
@LuxRenderAddon.addon_register_class
class lux_node_Textures_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_textures"
	bl_label = "Textures"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_texture_blender_clouds_node)
		add_nodetype(layout, bpy.types.luxrender_texture_fbm_node)
		add_nodetype(layout, bpy.types.luxrender_texture_blender_musgrave_node)
		add_nodetype(layout, bpy.types.luxrender_texture_windy_node)
		add_nodetype(layout, bpy.types.luxrender_texture_wrinkled_node)

@LuxRenderAddon.addon_register_class
class lux_node_Spectra_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_spectra"
	bl_label = "Spectra"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_texture_blackbody_node)
		add_nodetype(layout, bpy.types.luxrender_texture_colordepth_node)
		add_nodetype(layout, bpy.types.luxrender_texture_gaussian_node)
		add_nodetype(layout, bpy.types.luxrender_texture_tabulateddata_node)
		
@LuxRenderAddon.addon_register_class
class lux_node_Frensel_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_fresnel"
	bl_label = "Fresnel Data"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_texture_fresnelcolor_node)
		add_nodetype(layout, bpy.types.luxrender_texture_fresnelname_node)

@LuxRenderAddon.addon_register_class
class lux_node_Utilities_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_utilities"
	bl_label = "Utilities"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_texture_harlequin_node)
		add_nodetype(layout, bpy.types.luxrender_texture_uv_node)

@LuxRenderAddon.addon_register_class
class lux_node_Volumes_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_volumes"
	bl_label = "Volumes"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_volume_clear_node)
		add_nodetype(layout, bpy.types.luxrender_volume_homogeneous_node)

@LuxRenderAddon.addon_register_class
class luxrender_mat_node_editor(bpy.types.NodeTree):
	'''LuxRender Material Nodes'''

	bl_idname = 'luxrender_material_nodes'
	bl_label = 'LuxRender Material Nodes'
	bl_icon = 'MATERIAL'
	
	@classmethod
	def poll(cls, context):
		return context.scene.render.engine == 'LUXRENDER_RENDER'
		
	def draw_add_menu(self, context, layout):
		layout.label('LuxRender Node Types')
		layout.menu("Lux_NODE_outputs")
		layout.menu("Lux_NODE_materials")
		layout.menu("Lux_NODE_textures")
		layout.menu("Lux_NODE_spectra")
		layout.menu("Lux_NODE_fresnel")
		layout.menu("Lux_NODE_utilities")
		layout.menu("Lux_NODE_volumes")
		layout.menu("Lux_NODE_lights")


# Material nodes alphabetical
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_carpaint(luxrender_material_node):
	# Description string
	'''Car paint material node'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_material_carpaint_node'
	# Label for nice name display
	bl_label = 'Car Paint Material'
	# Icon identifier
	bl_icon = 'MATERIAL'

	for prop in luxrender_mat_carpaint.properties:
		if prop['attr'].startswith('name'):
			carpaint_items = prop['items']
	
	carpaint_presets = bpy.props.EnumProperty(name='Car Paint Presets', description='Luxrender Carpaint Presets', items=carpaint_items, default='-')
	
	def init(self, context):
		self.inputs.new('luxrender_TC_Kd_socket', 'Diffuse Color')
		self.inputs.new('luxrender_TC_Ks1_socket', 'Specular Color 1')
		self.inputs.new('NodeSocketFloat', 'R1')
		self.inputs.new('NodeSocketFloat', 'M1')
		self.inputs.new('luxrender_TC_Ks2_socket', 'Specular Color 2')
		self.inputs.new('NodeSocketFloat', 'R2')
		self.inputs.new('NodeSocketFloat', 'M2')
		self.inputs.new('luxrender_TC_Ks3_socket', 'Specular Color 3')
		self.inputs.new('NodeSocketFloat', 'R3')
		self.inputs.new('NodeSocketFloat', 'M3')
		self.inputs.new('luxrender_TC_Kd_socket', 'Absorbtion Color')
		self.inputs.new('NodeSocketFloat', 'Absorbtion Depth')
		

		self.outputs.new('NodeSocketShader', 'Surface')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'carpaint_presets')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_cloth(luxrender_material_node):
	'''Cloth material node'''
	bl_idname = 'luxrender_material_cloth_node'
	bl_label = 'Cloth Material'
	bl_icon = 'MATERIAL'
	
	for prop in luxrender_mat_cloth.properties:
		if prop['attr'].startswith('presetname'):
			cloth_items = prop['items']

	fabric_type = bpy.props.EnumProperty(name='Cloth Fabric', description='Luxrender Cloth Fabric', items=cloth_items, default='denim')
	repeat_u = bpy.props.FloatProperty(name='Repeat U', default=100.0)
	repeat_v = bpy.props.FloatProperty(name='Repeat V', default=100.0)

	
	def init(self, context):
		self.inputs.new('luxrender_TC_warp_Kd_socket', 'Warp Diffuse Color')
		self.inputs.new('luxrender_TC_warp_Ks_socket', 'Warp Specular Color')
		self.inputs.new('luxrender_TC_weft_Kd_socket', 'Weft Diffuse Color')
		self.inputs.new('luxrender_TC_weft_Ks_socket', 'Weft Specular Color')

		self.outputs.new('NodeSocketShader', 'Surface')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'fabric_type')
		layout.prop(self, 'repeat_u')
		layout.prop(self, 'repeat_v')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_glass(luxrender_material_node):
	'''Glass material node'''
	bl_idname = 'luxrender_material_glass_node'
	bl_label = 'Glass Material'
	bl_icon = 'MATERIAL'

	arch = bpy.props.BoolProperty(name='Architectural', description='Skips refraction during transmission, propagates alpha and shadow rays', default=False)
	
	def init(self, context):
		self.inputs.new('luxrender_TC_Kt_socket', 'Transmission Color')
		self.inputs.new('luxrender_TC_Kr_socket', 'Reflection Color')
		self.inputs.new('NodeSocketFloat', 'IOR')
		self.inputs.new('NodeSocketFloat', 'Cauchy B')
		self.inputs.new('NodeSocketFloat', 'Film IOR')
		self.inputs.new('NodeSocketFloat', 'Film Thickness (nm)')

		self.outputs.new('NodeSocketShader', 'Surface')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'arch')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_glass2(luxrender_material_node):
	'''Glass2 material node'''
	bl_idname = 'luxrender_material_glass2_node'
	bl_label = 'Glass2 Material'
	bl_icon = 'MATERIAL'

	arch = bpy.props.BoolProperty(name='Architectural', description='Skips refraction during transmission, propagates alpha and shadow rays', default=False)
	dispersion = bpy.props.BoolProperty(name='Dispersion', description='Enables chromatic dispersion, volume should have a sufficient data for this', default=False)
	
	def init(self, context):
		self.outputs.new('NodeSocketShader', 'Surface')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'arch')
		layout.prop(self, 'dispersion')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_glossy(luxrender_material_node):
	'''Glossy material node'''
	bl_idname = 'luxrender_material_glossy_node'
	bl_label = 'Glossy Material'
	bl_icon = 'MATERIAL'

	multibounce = bpy.props.BoolProperty(name='Multibounce', description='Enable surface layer multibounce', default=False)
	
	def init(self, context):
		self.inputs.new('luxrender_TC_Kd_socket', 'Diffuse Color')
		self.inputs.new('NodeSocketFloat', 'Sigma')
		self.inputs.new('luxrender_TC_Ks_socket', 'Specular Color')
		self.inputs.new('luxrender_TC_Ka_socket', 'Absorption Color')
		self.inputs.new('NodeSocketFloat', 'Absorption Depth')
		self.inputs.new('NodeSocketFloat', 'U-Roughness')
		self.inputs[5].default_value =get_default(TF_uroughness)
		self.inputs.new('NodeSocketFloat', 'V-Roughness')
		self.inputs[6].default_value = get_default(TF_vroughness)

		self.outputs.new('NodeSocketShader', 'Surface')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'multibounce')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_glossycoating(luxrender_material_node):
	'''Glossy Coating material node'''
	bl_idname = 'luxrender_material_glossycoating_node'
	bl_label = 'Glossy Coating Material'
	bl_icon = 'MATERIAL'

	multibounce = bpy.props.BoolProperty(name='Multibounce', description='Enable surface layer multibounce', default=False)
	
	def init(self, context):
		self.inputs.new('NodeSocketShader', 'Base Material')
		self.inputs.new('luxrender_TC_Ks_socket', 'Specular Color')
		self.inputs.new('luxrender_TC_Ka_socket', 'Absorption Color')
		self.inputs.new('NodeSocketFloat', 'Absorption Depth')
		self.inputs.new('NodeSocketFloat', 'U-Roughness')
		self.inputs[4].default_value = get_default(TF_uroughness)
		self.inputs.new('NodeSocketFloat', 'V-Roughness')
		self.inputs[5].default_value = get_default(TF_vroughness)

		self.outputs.new('NodeSocketShader', 'Surface')
		
	def draw_buttons(self, context, layout):
		layout.prop(self, 'multibounce')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_layered(luxrender_material_node):
	'''Layered material node'''
	bl_idname = 'luxrender_material_layered_node'
	bl_label = 'Layered Material'
	bl_icon = 'MATERIAL'

	def init(self, context):
		self.inputs.new('NodeSocketShader', 'Material 1')
		self.inputs.new('NodeSocketFloat', 'Opacity 1')
		self.inputs.new('NodeSocketShader', 'Material 2')
		self.inputs.new('NodeSocketFloat', 'Opacity 2')
		self.inputs.new('NodeSocketShader', 'Material 3')
		self.inputs.new('NodeSocketFloat', 'Opacity 3')
		self.inputs.new('NodeSocketShader', 'Material 4')
		self.inputs.new('NodeSocketFloat', 'Opacity 4')

		
		self.outputs.new('NodeSocketShader', 'Surface')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_matte(luxrender_material_node):
	'''Matte material node'''
	bl_idname = 'luxrender_material_matte_node'
	bl_label = 'Matte Material'
	bl_icon = 'MATERIAL'

	def init(self, context):
		self.inputs.new('luxrender_TC_Kd_socket', 'Diffuse Color')
		self.inputs.new('NodeSocketFloat', 'Sigma')

		self.outputs.new('NodeSocketShader', 'Surface')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_mattetranslucent(luxrender_material_node):
	'''Matte material node'''
	bl_idname = 'luxrender_material_mattetranslucent_node'
	bl_label = 'Matte Translucent Material'
	bl_icon = 'MATERIAL'
	
	def init(self, context):
		self.inputs.new('NodeSocketBool', 'Energy Conserving')
		self.inputs.new('luxrender_TC_Kr_socket', 'Refection Color')
		self.inputs.new('luxrender_TC_Kt_socket', 'Transmission Color')
		self.inputs.new('NodeSocketFloat', 'Sigma')
		
		self.outputs.new('NodeSocketShader', 'Surface')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_metal(luxrender_material_node):
	'''Metal material node'''
	bl_idname = 'luxrender_material_metal_node'
	bl_label = 'Metal Material'
	bl_icon = 'MATERIAL'
	
#	for prop in luxrender_mat_metal.properties:
#		print("-------------", prop['type'], prop['attr']) # all properties material has
	
	for prop in luxrender_mat_metal.properties:
		if prop['attr'].startswith('name'):
			metal_presets = prop['items']
	
	metal_preset = bpy.props.EnumProperty(name='Preset', description='Luxrender Metal Preset', items=metal_presets, default='aluminium')
	
	use_anisotropy = bpy.props.BoolProperty(name='Anisotropic Roughness', description='Anisotropic roughness', default=False)
# 	use_exponent = bpy.props.BoolProperty(name='Use Exponent', description='Use exponent', default=False)
	metal_nkfile = bpy.props.StringProperty(name='Nk File', description='Nk file path', subtype='FILE_PATH')
		
	def init(self, context):
		self.inputs.new('NodeSocketFloat', 'U-Roughness')
		self.inputs[0].default_value = get_default(TF_uroughness)
		self.inputs.new('NodeSocketFloat', 'V-Roughness')
		self.inputs[1].default_value = get_default(TF_vroughness)
# 		self.inputs.new('NodeSocketFloat', 'U-Exponent')
# 		self.inputs.new('NodeSocketFloat', 'V-Exponent')

		
		self.outputs.new('NodeSocketShader', 'Surface')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, 'metal_preset')
		if self.metal_preset == 'nk':
			layout.prop(self, 'metal_nkfile')
		layout.prop(self, 'use_anisotropy')
# 		layout.prop(self, 'use_exponent')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_metal2(luxrender_material_node):
	'''Metal2 material node'''
	bl_idname = 'luxrender_material_metal2_node'
	bl_label = 'Metal2 Material'
	bl_icon = 'MATERIAL'
	
	for prop in luxrender_mat_metal2.properties:
		if prop['attr'].startswith('metaltype'):
			metal2_types = prop['items']
	
	for prop in luxrender_mat_metal2.properties:
		if prop['attr'].startswith('preset'):
			metal2_presets = prop['items']

	metal2_type = bpy.props.EnumProperty(name='Type', description='Luxrender Metal2 Type', items=metal2_types, default='preset')
	metal2_preset = bpy.props.EnumProperty(name='Preset', description='Luxrender Metal2 Preset', items=metal2_presets, default='aluminium')
	metal2_nkfile = bpy.props.StringProperty(name='Nk File', description='Nk file path', subtype='FILE_PATH')
	
	use_anisotropy = bpy.props.BoolProperty(name='Anisotropic Roughness', description='Anisotropic Roughness', default=False)
#	use_exponent = bpy.props.BoolProperty(name='Use Exponent', description='Anisotropic Roughness', default=False)
	
	def init(self, context):
		self.inputs.new('NodeSocketFloat', 'U-Roughness')
		self.inputs[0].default_value = get_default(TF_uroughness)
		self.inputs.new('NodeSocketFloat', 'V-Roughness')
		self.inputs[1].default_value = get_default(TF_vroughness)
#		self.inputs.new('NodeSocketFloat', 'U-Exponent')
#		self.inputs.new('NodeSocketFloat', 'V-Exponent')
		
		
		self.outputs.new('NodeSocketShader', 'Surface')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, 'metal2_type')
		if self.metal2_type == 'preset':
			layout.prop(self, 'metal2_preset')
		if self.metal2_type == 'nk':
			layout.prop(self, 'metal2_nkfile')
		layout.prop(self, 'use_anisotropy')
#		layout.prop(self, 'use_exponent')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_mirror(luxrender_material_node):
	'''Mirror material node'''
	bl_idname = 'luxrender_material_mirror_node'
	bl_label = 'Mirror Material'
	bl_icon = 'MATERIAL'

	
	def init(self, context):
		self.inputs.new('luxrender_TC_Kr_socket', 'Reflection Color')
		self.inputs.new('NodeSocketFloat', 'Film IOR')
		self.inputs.new('NodeSocketFloat', 'Film Thickness (nm)')

		self.outputs.new('NodeSocketShader', 'Surface')
		
	#This node is only for the Lux node-tree
	@classmethod	
	def poll(cls, tree):
		return tree.bl_idname == 'luxrender_material_nodes'


@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_mix(luxrender_material_node):
	'''Mix material node'''
	bl_idname = 'luxrender_material_mix_node'
	bl_label = 'Mix Material'
	bl_icon = 'MATERIAL'

	def init(self, context):
		self.inputs.new('NodeSocketFloat', 'Mix Amount')
		self.inputs.new('NodeSocketShader', 'Material 1')
		self.inputs.new('NodeSocketShader', 'Material 2')
		
		self.outputs.new('NodeSocketShader', 'Surface')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_null(luxrender_material_node):
	'''Null material node'''
	bl_idname = 'luxrender_material_null_node'
	bl_label = 'Null Material'
	bl_icon = 'MATERIAL'

	def init(self, context):
		self.outputs.new('NodeSocketShader', 'Surface')
		
#Volume and area light nodes

@LuxRenderAddon.addon_register_class
class luxrender_material_type_node_roughglass(luxrender_material_node):
	'''Rough Glass material node'''
	bl_idname = 'luxrender_material_roughglass_node'
	bl_label = 'Rough Glass Material'
	bl_icon = 'MATERIAL'
	
	def init(self, context):
		self.inputs.new('luxrender_TC_Kt_socket', 'Transmission Color')
		self.inputs.new('luxrender_TC_Kr_socket', 'Reflection Color')
		self.inputs.new('NodeSocketFloat', 'IOR')
		self.inputs.new('NodeSocketFloat', 'Cauchy B')
		self.inputs.new('NodeSocketFloat', 'U-Roughness')
		self.inputs[4].default_value = get_default(TF_uroughness)
		self.inputs.new('NodeSocketFloat', 'V-Roughness')
		self.inputs[5].default_value = get_default(TF_vroughness)


		self.outputs.new('NodeSocketShader', 'Surface')

@LuxRenderAddon.addon_register_class
class luxrender_volume_type_node_clear(luxrender_material_node):
	'''Clear volume node'''
	bl_idname = 'luxrender_volume_clear_node'
	bl_label = 'Clear Volume'
	bl_icon = 'MATERIAL'

	def init(self, context):
		self.inputs.new('luxrender_fresnel_socket', 'IOR')
		self.inputs.new('NodeSocketColor', 'Absorption Color')
		self.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)

		self.outputs.new('NodeSocketShader', 'Volume')
		
@LuxRenderAddon.addon_register_class
class luxrender_volume_type_node_homogeneous(luxrender_material_node):
	'''Homogeneous volume node'''
	bl_idname = 'luxrender_volume_homogeneous_node'
	bl_label = 'Homogeneous Volume'
	bl_icon = 'MATERIAL'

	def init(self, context):
		self.inputs.new('luxrender_fresnel_socket', 'IOR')
		self.inputs.new('luxrender_TC_Ka_socket', 'Absorption Color')
		self.inputs.new('NodeSocketColor', 'Scattering Color')
		self.inputs[2].default_value = (0.0, 0.0, 0.0, 1.0)
		self.inputs.new('NodeSocketColor', 'Asymmetry')
		
		self.outputs.new('NodeSocketShader', 'Volume')
		
@LuxRenderAddon.addon_register_class
class luxrender_light_area_node(luxrender_material_node):
	'''A custom node'''
	bl_idname = 'luxrender_light_area_node'
	bl_label = 'Area Light'
	bl_icon = 'LAMP'

	gain = bpy.props.FloatProperty(name='Gain', default=1.0)

	def init(self, context):
		self.inputs.new('NodeSocketColor', 'Light Color')
		self.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
		
		self.outputs.new('NodeSocketShader', 'Emission')
	
	def draw_buttons(self, context, layout):
		layout.prop(self, 'gain')
		
@LuxRenderAddon.addon_register_class
class luxrender_material_output_node(luxrender_node):
	'''A custom node'''
	bl_idname = 'luxrender_material_output_node'
	bl_label = 'Material Output'
	bl_icon = 'MATERIAL'
	
	def init(self, context):
		self.inputs.new('NodeSocketShader', 'Surface')
		self.inputs.new('NodeSocketShader', 'Interior Volume')
		self.inputs.new('NodeSocketShader', 'Exterior Volume')
		self.inputs.new('NodeSocketShader', 'Emission')
		
# Custom socket types
		
@LuxRenderAddon.addon_register_class
class luxrender_fresnel_socket(bpy.types.NodeSocket):
	# Description string
	'''Fresnel texture I/O socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_fresnel_socket'
	# Label for nice name display
	bl_label = 'IOR socket'
	
	
	fresnel = bpy.props.FloatProperty(name='IOR', description='Optical dataset', default=1.52)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'fresnel', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.33, 0.6, 0.85, 1.0)

#bpy.props.FloatVectorProperty(name="", description="", default=(0.0, 0.0, 0.0), min=sys.float_info.min, max=sys.float_info.max, soft_min=sys.float_info.min, soft_max=sys.float_info.max, step=3, precision=2, options={'ANIMATABLE'}, subtype='NONE', size=3, update=None, get=None, set=None)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Ka_socket(bpy.types.NodeSocket):
	# Description string
	'''Absorbtion Color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Ka_socket'
	# Label for nice name display
	bl_label = 'Absorbtion Color socket'
	
	color = bpy.props.FloatVectorProperty(name='Absorbtion Color', description='Absorbtion Color', default=get_default(TC_Ka), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Kd_socket(bpy.types.NodeSocket):
	# Description string
	'''Diffuse Color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Kd_socket'
	# Label for nice name display
	bl_label = 'Diffuse Color socket'
	
	color = bpy.props.FloatVectorProperty(name='Diffuse Color', description='Diffuse Color', default=get_default(TC_Kd), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Kr_socket(bpy.types.NodeSocket):
	# Description string
	'''Reflection color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Kr_socket'
	# Label for nice name display
	bl_label = 'Reflection Color socket'
	
	color = bpy.props.FloatVectorProperty(name='Reflection Color', description='Reflection Color', default=get_default(TC_Kr), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks_socket(bpy.types.NodeSocket):
	# Description string
	'''Specular color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Ks_socket'
	# Label for nice name display
	bl_label = 'Specular Color socket'
	
	color = bpy.props.FloatVectorProperty(name='Specular Color', description='Specular Color', default=get_default(TC_Ks), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks1_socket(bpy.types.NodeSocket):
	# Description string
	'''Specular color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Ks1_socket'
	# Label for nice name display
	bl_label = 'Specular Color 1 socket'
	
	color = bpy.props.FloatVectorProperty(name='Specular Color 1', description='Specular Color 1', default=get_default(TC_Ks1), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks2_socket(bpy.types.NodeSocket):
	# Description string
	'''Specular color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Ks2_socket'
	# Label for nice name display
	bl_label = 'Specular Color 2 socket'
	
	color = bpy.props.FloatVectorProperty(name='Specular Color 2', description='Specular Color 2', default=get_default(TC_Ks2), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Ks3_socket(bpy.types.NodeSocket):
	# Description string
	'''Specular color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Ks3_socket'
	# Label for nice name display
	bl_label = 'Specular Color 3 socket'
	
	color = bpy.props.FloatVectorProperty(name='Specular Color 3', description='Specular Color 3', default=get_default(TC_Ks3), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_Kt_socket(bpy.types.NodeSocket):
	# Description string
	'''Transmission Color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_Kt_socket'
	# Label for nice name display
	bl_label = 'Transmission Color socket'
	
	color = bpy.props.FloatVectorProperty(name='Transmission Color', description='Transmission Color', default=get_default(TC_Kt), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_warp_Kd_socket(bpy.types.NodeSocket):
	# Description string
	'''Warp Diffuse Color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_warp_Kd_socket'
	# Label for nice name display
	bl_label = 'Warp Diffuse socket'
	
	color = bpy.props.FloatVectorProperty(name='Warp Diffuse Color', description='Warp Diffuse Color', default=get_default(TC_warp_Kd), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_warp_Ks_socket(bpy.types.NodeSocket):
	# Description string
	'''Warp Diffuse Color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_warp_Ks_socket'
	# Label for nice name display
	bl_label = 'Warp Specular socket'
	
	color = bpy.props.FloatVectorProperty(name='Warp Specular Color', description='Warp Specular Color', default=get_default(TC_warp_Ks), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_weft_Kd_socket(bpy.types.NodeSocket):
	# Description string
	'''Weft Diffuse Color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_weft_Kd_socket'
	# Label for nice name display
	bl_label = 'Weft Diffuse socket'
	
	color = bpy.props.FloatVectorProperty(name='Weft Diffuse Color', description='Weft Diffuse Color', default=get_default(TC_weft_Kd), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)

@LuxRenderAddon.addon_register_class
class luxrender_TC_weft_Ks_socket(bpy.types.NodeSocket):
	# Description string
	'''Weft Specular Color socket'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_TC_weft_Ks_socket'
	# Label for nice name display
	bl_label = 'Weft Specular socket'
	
	color = bpy.props.FloatVectorProperty(name='Weft Specular Color', description='Weft Specular Color', default=get_default(TC_weft_Ks), subtype='COLOR', min=0.0, max=1.0)
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, 'color', text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (0.9, 0.9, 0.0, 1.0)



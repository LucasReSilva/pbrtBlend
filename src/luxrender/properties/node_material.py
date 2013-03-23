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


def add_nodetype(layout, type):
	layout.operator("node.add_node", text=type.bl_label).type = type.bl_rna.identifier

@LuxRenderAddon.addon_register_class
class luxrender_mat_node_editor(bpy.types.NodeTree):
	'''Experiment in making a node editor for Lux'''

	bl_idname = 'luxrender_material_nodes'
	bl_label = 'LuxRender Material Nodes'
	bl_icon = 'MATERIAL'
	
	@classmethod
	def poll(cls, context):
		return context.scene.render.engine == 'LUXRENDER_RENDER'
		
	def draw_add_menu(self, context, layout):
		layout.label("LuxRender Node Types")
		add_nodetype(layout, bpy.types.luxrender_material_carpaint_node)
		add_nodetype(layout, bpy.types.luxrender_material_cloth_node)
#		add_nodetype(layout, bpy.types.luxrender_material_glass_node)
#		add_nodetype(layout, bpy.types.luxrender_material_glass2_node)
#		add_nodetype(layout, bpy.types.luxrender_material_glossy_node)
#		add_nodetype(layout, bpy.types.luxrender_material_glossycoating_node)
#		add_nodetype(layout, bpy.types.luxrender_material_glossytranslucent_node)
#		add_nodetype(layout, bpy.types.luxrender_material_glossytranslucent_node)
		add_nodetype(layout, bpy.types.luxrender_material_matte_node)
#		add_nodetype(layout, bpy.types.luxrender_material_mattetranslucent_node)
#		add_nodetype(layout, bpy.types.luxrender_material_metal_node)
#		add_nodetype(layout, bpy.types.luxrender_material_metal2_node)
#		add_nodetype(layout, bpy.types.luxrender_material_mirror_node)
#		add_nodetype(layout, bpy.types.luxrender_material_mix_node)
#		add_nodetype(layout, bpy.types.luxrender_material_null_node)
#		add_nodetype(layout, bpy.types.luxrender_material_roughglass_node)
#		add_nodetype(layout, bpy.types.luxrender_material_scatter_node)
#		add_nodetype(layout, bpy.types.luxrender_material_shinymetal_node)
#		add_nodetype(layout, bpy.types.luxrender_material_velvet_node)

		add_nodetype(layout, bpy.types.luxrender_material_output_node)

# Material nodes alphabetical
@LuxRenderAddon.addon_register_class
class luxrender_material_type_node(bpy.types.Node):
	# Description string
	'''A custom node'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_material_carpaint_node'
	# Label for nice name display
	bl_label = 'LuxRender Carpaint Material'
	# Icon identifier
	bl_icon = 'MATERIAL'
	
	def init(self, context):
		self.inputs.new('luxrender_material_carpaint_presets_socket', "Carpaint Presets")
		self.inputs.new('NodeSocketFloat', "Absorbtion Depth")
		self.inputs.new('NodeSocketColor', "Absorbtion")
		self.inputs.new('NodeSocketColor', "Diffuse Color")
		self.inputs.new('NodeSocketColor', "Specular Color 1")
		self.inputs.new('NodeSocketColor', "Specular Color 2")
		self.inputs.new('NodeSocketColor', "Specular Color 3")

		self.outputs.new('NodeSocketShader', "Surface")

@LuxRenderAddon.addon_register_class
class luxrender_material_type_node(bpy.types.Node):
	# Description string
	'''A custom node'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_material_cloth_node'
	# Label for nice name display
	bl_label = 'LuxRender Cloth Material'
	# Icon identifier
	bl_icon = 'MATERIAL'
	
	def init(self, context):
		self.inputs.new('luxrender_material_fabric_socket', "Cloth Fabric")
		self.inputs.new('NodeSocketColor', "Warp Diffuse Color")
		self.inputs.new('NodeSocketColor', "Warp Specular Color")
		self.inputs.new('NodeSocketColor', "Weft Diffuse Color")
		self.inputs.new('NodeSocketColor', "Weft Specular Color")
		self.inputs.new('NodeSocketFloat', "Repeat U")
		self.inputs.new('NodeSocketFloat', "Repeat V")

		self.outputs.new('NodeSocketShader', "Surface")

@LuxRenderAddon.addon_register_class
class luxrender_material_type_node(bpy.types.Node):
	# Description string
	'''A custom node'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_material_matte_node'
	# Label for nice name display
	bl_label = 'LuxRender Matte Material'
	# Icon identifier
	bl_icon = 'MATERIAL'

	def init(self, context):
		self.inputs.new('NodeSocketColor', "Diffuse Color")
		self.inputs.new('NodeSocketFloat', "Sigma")

		self.outputs.new('NodeSocketShader', "Surface")

@LuxRenderAddon.addon_register_class
class luxrender_material_output_node(bpy.types.Node):
	# Description string
	'''A custom node'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_material_output_node'
	# Label for nice name display
	bl_label = 'LuxRender Material Output'
	# Icon identifier
	bl_icon = 'MATERIAL'
	
	def init(self, context):
		self.inputs.new('NodeSocketShader', "Surface")
		self.inputs.new('NodeSocketShader', "Interior")
		self.inputs.new('NodeSocketShader', "Exterior")
		self.inputs.new('NodeSocketShader', "Emission")

# Custom socket types

@LuxRenderAddon.addon_register_class
class luxrender_material_cloth_fabric_socket(bpy.types.NodeSocket):
	# Description string
	'''Custom node socket type'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_material_fabric_socket'
	# Label for nice name display
	bl_label = 'Cloth Fabric Node Socket'

	cloth_items = [
		('denim', 'Denim', 'Denim'),
		('silk_charmeuse', 'Silk Charmeuse', 'Silk charmeuse'),
		('cotton_twill', 'Cotton Twill', 'Cotton twill'),
		('wool_gabardine', 'Wool Gabardine', 'Wool Gabardine'),
		('polyester_lining_cloth', 'Polyester Lining Cloth', 'Polyester lining cloth'),
		('silk_shantung', 'Silk Shantung', 'Silk shantung'),
		]

	myEnumProperty = bpy.props.EnumProperty(name="Cloth Fabric", description="Luxrender Cloth Fabric", items=cloth_items, default='denim')

	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, "myEnumProperty", text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (1.0, 0.4, 0.216, 0.5)

@LuxRenderAddon.addon_register_class
class luxrender_material_carpaint_preset_socket(bpy.types.NodeSocket):
	# Description string
	'''Custom node socket type'''
	# Optional identifier string. If not explicitly defined, the python class name is used.
	bl_idname = 'luxrender_material_carpaint_presets_socket'
	# Label for nice name display
	bl_label = 'Carpaint Presets Node Socket'
	
	carpaint_items = [
		('-', 'Manual settings', '-'),
		('2k acrylack', '2k Acrylack', '2k acrylack'),
		('blue', 'Blue', 'blue'),
		('blue matte', 'Blue Matte', 'blue matte'),
		('bmw339', 'BMW 339', 'bmw339'),
		('ford f8', 'Ford F8', 'ford f8'),
		('opel titan', 'Opel Titan', 'opel titan'),
		('polaris silber', 'Polaris Silber', 'polaris silber'),
		('white', 'White', 'white'),
		]
	
	myEnumProperty = bpy.props.EnumProperty(name="Carpaint Presets", description="Luxrender Carpaint Presets", items=carpaint_items, default='-')
	
	# Optional function for drawing the socket input value
	def draw(self, context, layout, node):
		layout.prop(self, "myEnumProperty", text=self.name)
	
	# Socket color
	def draw_color(self, context, node):
		return (1.0, 0.4, 0.216, 0.5)

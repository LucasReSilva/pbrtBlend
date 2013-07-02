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

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom

from .. import LuxRenderAddon
from ..properties import (luxrender_node, luxrender_material_node, get_linked_node, check_node_export_material, check_node_export_texture, check_node_get_paramset, ExportedVolumes)

from ..properties.texture import (
	import_paramset_to_blender_texture, shorten_name, refresh_preview
)
from ..export import ParamSet, process_filepath_data
from ..export.materials import (
	MaterialCounter, TextureCounter, ExportedMaterials, ExportedTextures, get_texture_from_scene
)

from ..outputs import LuxManager, LuxLog

from ..properties.node_sockets import *

def add_nodetype(layout, type):
	layout.operator('node.add_node', text=type.bl_label).type = type.bl_rna.identifier

#Create the submenus for the add-node menu
@LuxRenderAddon.addon_register_class
class lux_node_Materials_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_material"
	bl_label = "Material"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_material_carpaint_node)
		add_nodetype(layout, bpy.types.luxrender_material_cloth_node)
		add_nodetype(layout, bpy.types.luxrender_material_glass_node)
		add_nodetype(layout, bpy.types.luxrender_material_glass2_node)
		add_nodetype(layout, bpy.types.luxrender_material_glossy_node)
		add_nodetype(layout, bpy.types.luxrender_material_glossycoating_node)
		add_nodetype(layout, bpy.types.luxrender_material_glossytranslucent_node)
		add_nodetype(layout, bpy.types.luxrender_material_matte_node)
		add_nodetype(layout, bpy.types.luxrender_material_mattetranslucent_node)
		add_nodetype(layout, bpy.types.luxrender_material_metal_node)
		add_nodetype(layout, bpy.types.luxrender_material_metal2_node)
		add_nodetype(layout, bpy.types.luxrender_material_mirror_node)
		add_nodetype(layout, bpy.types.luxrender_material_roughglass_node)
		add_nodetype(layout, bpy.types.luxrender_material_scatter_node)
		add_nodetype(layout, bpy.types.luxrender_material_velvet_node)
		add_nodetype(layout, bpy.types.luxrender_material_null_node)
		add_nodetype(layout, bpy.types.luxrender_material_mix_node)
		add_nodetype(layout, bpy.types.luxrender_material_doubleside_node)
		add_nodetype(layout, bpy.types.luxrender_material_layered_node)

@LuxRenderAddon.addon_register_class
class lux_node_Inputs_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_input"
	bl_label = "Input"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_2d_coordinates_node)
		add_nodetype(layout, bpy.types.luxrender_3d_coordinates_node)
		add_nodetype(layout, bpy.types.luxrender_texture_blackbody_node)
		add_nodetype(layout, bpy.types.luxrender_texture_gaussian_node)
		add_nodetype(layout, bpy.types.luxrender_texture_glossyexponent_node)
		add_nodetype(layout, bpy.types.luxrender_texture_tabulateddata_node)
		add_nodetype(layout, bpy.types.luxrender_texture_constant_node) #Drawn as "Value", to match similar compositor/cycles node
		add_nodetype(layout, bpy.types.luxrender_texture_hitpointcolor_node) #These are drawn in the menu under the name "Vertex color/mask"
		add_nodetype(layout, bpy.types.luxrender_texture_hitpointgrey_node)
#		add_nodetype(layout, bpy.types.luxrender_texture_hitpointalpha_node)


@LuxRenderAddon.addon_register_class
class lux_node_Outputs_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_output"
	bl_label = "Output"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_material_output_node)

@LuxRenderAddon.addon_register_class
class lux_node_Lights_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_light"
	bl_label = "Light"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_light_area_node)
		
@LuxRenderAddon.addon_register_class
class lux_node_Textures_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_texture"
	bl_label = "Texture"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_texture_blender_blend_node)
		add_nodetype(layout, bpy.types.luxrender_texture_brick_node)
		add_nodetype(layout, bpy.types.luxrender_texture_blender_clouds_node)
		add_nodetype(layout, bpy.types.luxrender_texture_type_node_vol_cloud_node)
		add_nodetype(layout, bpy.types.luxrender_texture_blender_distortednoise_node)
		add_nodetype(layout, bpy.types.luxrender_texture_type_node_vol_exponential_node)
		add_nodetype(layout, bpy.types.luxrender_texture_fbm_node)
		add_nodetype(layout, bpy.types.luxrender_texture_harlequin_node)
		add_nodetype(layout, bpy.types.luxrender_texture_image_map_node)
		add_nodetype(layout, bpy.types.luxrender_texture_blender_musgrave_node)
		add_nodetype(layout, bpy.types.luxrender_texture_normal_map_node)
		add_nodetype(layout, bpy.types.luxrender_texture_windy_node)
		add_nodetype(layout, bpy.types.luxrender_texture_wrinkled_node)
		add_nodetype(layout, bpy.types.luxrender_texture_uv_node)
		add_nodetype(layout, bpy.types.luxrender_texture_blender_voronoi_node)
		
@LuxRenderAddon.addon_register_class
class lux_node_Fresnel_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_fresnel"
	bl_label = "Fresnel Data"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_texture_cauchy_node)
		add_nodetype(layout, bpy.types.luxrender_texture_fresnelcolor_node)
		add_nodetype(layout, bpy.types.luxrender_texture_fresnelname_node)
		add_nodetype(layout, bpy.types.luxrender_texture_sellmeier_node)

@LuxRenderAddon.addon_register_class
class lux_node_Utilities_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_converter"
	bl_label = "Converter"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_texture_add_node)
		add_nodetype(layout, bpy.types.luxrender_texture_bump_map_node)
		add_nodetype(layout, bpy.types.luxrender_texture_colordepth_node)
		add_nodetype(layout, bpy.types.luxrender_texture_mix_node)
		add_nodetype(layout, bpy.types.luxrender_texture_scale_node)
		add_nodetype(layout, bpy.types.luxrender_texture_subtract_node)

@LuxRenderAddon.addon_register_class
class lux_node_Volumes_Menu(bpy.types.Menu):
	bl_idname = "Lux_NODE_volume"
	bl_label = "Volume"
	
	def draw(self, context):
		layout = self.layout
		add_nodetype(layout, bpy.types.luxrender_volume_clear_node)
		add_nodetype(layout, bpy.types.luxrender_volume_homogeneous_node)
		add_nodetype(layout, bpy.types.luxrender_volume_heterogeneous_node)

@LuxRenderAddon.addon_register_class
class luxrender_mat_node_editor(bpy.types.NodeTree):
	'''LuxRender Material Nodes'''

	bl_idname = 'luxrender_material_nodes'
	bl_label = 'LuxRender Material Nodes'
	bl_icon = 'MATERIAL'
	
	@classmethod
	def poll(cls, context):
		return context.scene.render.engine == 'LUXRENDER_RENDER'
	
	#This function will set the current node tree to the one belonging to the active material
	@classmethod
	def get_from_context(cls, context):
		ob = context.active_object
		if ob and ob.type not in {'LAMP', 'CAMERA'}:
			ma = ob.active_material
			if ma != None:
				nt_name = ma.luxrender_material.nodetree
				if nt_name != '':
					return bpy.data.node_groups[ma.luxrender_material.nodetree], ma, ma
		# Uncomment if/when we make lamp nodes
		#	elif ob and ob.type == 'LAMP':
		#		la = ob.data
		#		nt_name = la.luxrender_lamp.nodetree
		#		if nt_name != '':
		#			return bpy.data.node_groups[la.luxrender_lamp.nodetree], la, la
		return (None, None, None)

	def draw_add_menu(self, context):
		if context.space_data.tree_type == 'luxrender_material_nodes':
			layout = self.layout
			layout.menu("Lux_NODE_input")
			layout.menu("Lux_NODE_output")
			layout.menu("Lux_NODE_material")
			layout.menu("Lux_NODE_texture")
			layout.menu("Lux_NODE_volume")
			layout.menu("Lux_NODE_light")
			layout.menu("Lux_NODE_fresnel")
			layout.menu("Lux_NODE_converter")

	
	# This block updates the preview, when socket links change
	def update(self):
		self.refresh = True
	
	def acknowledge_connection(self, context):
		while self.refresh == True:
			self.refresh = False
			break
	
	refresh = bpy.props.BoolProperty(name='Links Changed', default=False, update=acknowledge_connection)

#Embryonic node-category support. Doesn't actually do anything yet.
class luxrender_node_category(NodeCategory):
	@classmethod
	def poll(cls, context):
		return context.space_data.tree_type == 'luxrender_material_nodes'

luxrender_node_catagories = [
	luxrender_node_category("LUX_INPUT", "Input", items = [
	NodeItem("luxrender_2d_coordinates_node"),
	NodeItem("luxrender_3d_coordinates_node"),
	NodeItem("luxrender_texture_blackbody_node"),
	#	NodeItem("NodeGroupInput", poll=group_input_output_item_poll), ...maybe...
	]),
	]
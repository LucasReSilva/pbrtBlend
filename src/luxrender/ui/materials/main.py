# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
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
#
import bpy

from ... import LuxRenderAddon
from ...ui.materials import luxrender_material_base

@LuxRenderAddon.addon_register_class
class ui_luxrender_material_utils(luxrender_material_base):
	bl_label	= 'LuxRender Materials Utils'
	def draw(self, context):
		row = self.layout.row(align=True)
		row.menu("LUXRENDER_MT_presets_material", text=bpy.types.LUXRENDER_MT_presets_material.bl_label)
		row.operator("luxrender.preset_material_add", text="", icon="ZOOMIN")
		row.operator("luxrender.preset_material_add", text="", icon="ZOOMOUT").remove_active = True
		
		row = self.layout.row(align=True)
		row.operator("luxrender.convert_all_materials", icon='WORLD_DATA')
		
		row = self.layout.row(align=True)
		row.operator("luxrender.convert_material", icon='MATERIAL_DATA')
		
		row = self.layout.row(align=True)
		row.operator("luxrender.copy_mat_color", icon='COLOR')
		
		row = self.layout.row(align=True)
		row.operator("luxrender.material_reset", icon='SOLID')

@LuxRenderAddon.addon_register_class
class ui_luxrender_material(luxrender_material_base):
	'''
	Material Editor UI Panel
	'''
	
	bl_label	= 'LuxRender Materials'
	
	display_property_groups = [
		( ('material',), 'luxrender_material' )
	]
	
	def draw(self, context):
		cl = self.layout.column(align=True)
		cl.menu('MATERIAL_MT_luxrender_type', text=context.material.luxrender_material.type_label)
		super().draw(context)

@LuxRenderAddon.addon_register_class
class ui_luxrender_material_emission(luxrender_material_base):
	'''
	Material Emission Settings
	'''
	
	bl_label = 'LuxRender Emission'
	bl_options = 'DEFAULT_CLOSED'
	
	display_property_groups = [
		( ('material',), 'luxrender_emission' )
	]
	
	def draw_header(self, context):
		self.layout.prop(context.material.luxrender_emission, "use_emission", text="")

@LuxRenderAddon.addon_register_class
class ui_luxrender_material_transparency(luxrender_material_base):
	'''
	Material Transparency Settings
	'''
	
	bl_label = 'LuxRender Alpha Transparency'
	bl_options = 'DEFAULT_CLOSED'
	
	display_property_groups = [
		( ('material',), 'luxrender_transparency' )
	]
	
	# only textures with Kd (or similar) for now
	#LUX_COMPAT = {'carpaint', 'glass', 'glossy', 'glossy_lossy', 'mattetranslucent', 'glossytranslucent', 'scatter', 'matte', 'mirror', 'velvet'}
	
	def draw_header(self, context):
		self.layout.prop(context.material.luxrender_transparency, "transparent", text="")
	
	@classmethod
	def poll(cls, context):
		if not hasattr(context.material, 'luxrender_transparency'):
			return False
		#return super().poll(context) and context.material.luxrender_material.type in cls.LUX_COMPAT
		return super().poll(context) and context.material.luxrender_material.type != 'null'

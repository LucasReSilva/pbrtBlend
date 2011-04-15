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
from ...operators.lrmdb_lib import lrmdb_client

@LuxRenderAddon.addon_register_class
class ui_luxrender_material_utils(luxrender_material_base):
	bl_label	= 'LuxRender Materials Utils'
	def draw(self, context):
		row = self.layout.row(align=True)
		row.operator("luxrender.load_material", icon="DISK_DRIVE")
		row.operator("luxrender.save_material", icon="DISK_DRIVE").filename =\
			'%s.lbm2' % bpy.path.clean_name(context.material.name)
		
		if lrmdb_client.loggedin:
			row = self.layout.row(align=True)
			row.operator("luxrender.lrmdb_upload", icon="FILE_PARENT")
		
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
		row = self.layout.row(align=True)
		row.label("Material type")
		row.menu('MATERIAL_MT_luxrender_type', text=context.material.luxrender_material.type_label)
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

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

from properties_world import WorldButtonsPanel
from extensions_framework.ui import property_group_renderer

from .. import LuxRenderAddon

class world_panel(WorldButtonsPanel, property_group_renderer):
	COMPAT_ENGINES = {LuxRenderAddon.BL_IDNAME}

@LuxRenderAddon.addon_register_class
class world(world_panel):
	'''
	LuxRender World Settings
	'''
	
	bl_label = 'LuxRender World Settings'
	
	display_property_groups = [
		( ('scene',), 'luxrender_world' )
	]

@LuxRenderAddon.addon_register_class
class volumes(world_panel):
	'''
	Interior/Exterior Volumes Settings
	'''
	
	bl_label = 'LuxRender Volumes'
	
	display_property_groups = [
		( ('scene',), 'luxrender_volumes' )
	]
	
	def draw_ior_menu(self, context):
		"""
		This is a draw callback from property_group_renderer, due
		to ef_callback item in luxrender_volume_data.properties
		"""
		
		vi = context.scene.luxrender_volumes.volumes_index
		lv = context.scene.luxrender_volumes.volumes[vi]
		
		if lv.fresnel_fresnelvalue == lv.fresnel_presetvalue:
			menu_text = lv.fresnel_presetstring
		else:
			menu_text = '-- Choose preset --'
		
		cl=self.layout.column(align=True)
		cl.menu('LUXRENDER_MT_ior_presets', text=menu_text)
	
	# overridden in order to draw the selected luxrender_volume_data property group
	def draw(self, context):
		super().draw(context)
		
		if context.world:
			row = self.layout.row(align=True)
			row.menu("LUXRENDER_MT_presets_volume", text=bpy.types.LUXRENDER_MT_presets_volume.bl_label)
			row.operator("luxrender.preset_volume_add", text="", icon="ZOOMIN")
			row.operator("luxrender.preset_volume_add", text="", icon="ZOOMOUT").remove_active = True
			
			if len(context.scene.luxrender_volumes.volumes) > 0:
				current_vol_ind = context.scene.luxrender_volumes.volumes_index
				current_vol = context.scene.luxrender_volumes.volumes[current_vol_ind]
				# 'name' is not a member of current_vol.properties,
				# so we draw it explicitly
				self.layout.prop(
					current_vol, 'name'
				)
				# Here we draw the currently selected luxrender_volumes_data property group
				for control in current_vol.controls:
					self.draw_column(
						control,
						self.layout,
						current_vol,
						context,
						property_group = current_vol
					)
		else:
			self.layout.label('No active World available!')

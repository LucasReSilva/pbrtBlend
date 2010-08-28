# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
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
# Blender API
import bpy
from properties_material import MaterialButtonsPanel

from ef.ui import property_group_renderer

class _lux_material_base(MaterialButtonsPanel, property_group_renderer):
	COMPAT_ENGINES = {'luxrender'}

class material_editor(_lux_material_base, bpy.types.Panel):
	'''
	Material Editor UI Panel
	'''
	
	bl_label = 'LuxRender Materials'
	
	display_property_groups = [
		( ('material',), 'luxrender_material' )
	]

class material_emission(_lux_material_base, bpy.types.Panel):
	'''
	Material Emission Settings
	'''
	
	bl_label = 'LuxRender Material Emission'
	
	display_property_groups = [
		( ('material',), 'luxrender_emission' )
	]

class material_volumes(_lux_material_base, bpy.types.Panel):
	bl_label = 'LuxRender Material Volumes'
	
	display_property_groups = [
		( ('scene',), 'luxrender_volumes' )
	]
	
	# overridden in order to draw the selected luxrender_volume_data property group
	def draw(self, context):
		super().draw(context)
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
					current_vol,
					property_group = current_vol
				)

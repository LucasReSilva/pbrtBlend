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

class volumes(WorldButtonsPanel, property_group_renderer, bpy.types.Panel):
	'''
	Interior/Exterior Volumes Settings
	'''
	COMPAT_ENGINES = {'luxrender'}
	bl_label = 'LuxRender Volumes'
	
	display_property_groups = [
		( ('scene',), 'luxrender_volumes' )
	]
	
	# overridden in order to draw the selected luxrender_volume_data property group
	def draw(self, context):
		super().draw(context)
		# Since the volume data searches for textures in the active object, first
		# make sure that an object is selected and that it has a material assigned
		# TODO: can we search the global bpy.data for all textures and not require a selection ?
		if context.active_object and context.active_object.type == 'MESH':
			if context.active_object.active_material:
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
							context.active_object.active_material,
							property_group = current_vol
						)
			else:
				self.layout.label('Assign a material to the selected object')
		else:
			self.layout.label('Select a MESH object')

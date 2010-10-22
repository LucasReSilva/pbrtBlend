# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Daniel Genrich
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
from properties_data_lamp import DataButtonsPanel 

from addon_framework.ui import property_group_renderer

narrowui = 180

class lamps(DataButtonsPanel, property_group_renderer, bpy.types.Panel):
	bl_label = 'LuxRender Lamps'
	COMPAT_ENGINES = {'luxrender'}
	
	display_property_groups = [
		( ('lamp',), 'luxrender_lamp' )
	]
	
	# Overridden to draw some of blender's lamp controls
	def draw(self, context):
		if context.lamp is not None:
			layout = self.layout
			
			lamp = context.lamp
			wide_ui = context.region.width > narrowui
			
			if wide_ui:
				layout.prop(lamp, "type", expand=True)
			else:
				layout.prop(lamp, "type", text="")
			
			# Show only certain controls for Blender's lamp types
			if context.lamp.type not in ['POINT', 'SUN', 'SPOT', 'HEMI', 'AREA']:
				context.lamp.luxrender_lamp.type = 'UNSUPPORTED'
				layout.label(text="Lamp type not supported by LuxRender.")
			else:
				context.lamp.luxrender_lamp.type = context.lamp.type
				
				split = layout.split()
				
				# TODO: check which properties are supported by which light type
				col = split.column()
				#sub = col.column()
				
				# color is handled by Lux's L ColorTexture
				#sub.prop(lamp, "color", text="")
				layout.prop(lamp, "energy", text="Gain")
				
				# SPOT LAMP: Blender Properties
				if lamp.type == 'SPOT':
					wide_ui = context.region.width > narrowui
					
					if wide_ui:
						#col = split.column()
						col=layout.row()
					else:
						col=layout.column()
					col.prop(lamp, "spot_size", text="Size")
					col.prop(lamp, "spot_blend", text="Blend", slider=True)
				
				# AREA LAMP: Blender Properties
				elif lamp.type == 'AREA':
					
					if wide_ui:
						#col = split.column()
						col=layout.row()
					else:
						col=layout.column()
					col.row().prop(lamp, "shape", expand=True)
					
					sub = col.column(align=True)
					if (lamp.shape == 'SQUARE'):
						sub.prop(lamp, "size")
					elif (lamp.shape == 'RECTANGLE'):
						sub.prop(lamp, "size", text="Size X")
						sub.prop(lamp, "size_y", text="Size Y")
				elif wide_ui:
					col = split.column()
				
				super().draw(context) # draw the display_property_groups

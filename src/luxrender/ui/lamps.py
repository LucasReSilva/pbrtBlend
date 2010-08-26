# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
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

# EF API
from ef.ui import property_group_renderer
from ef.ef import init_properties

from luxrender.properties.lamp import luxrender_lamp

narrowui = 180

class lamps(DataButtonsPanel, property_group_renderer, bpy.types.Panel):
	bl_label = 'LuxRender Lamps'
	COMPAT_ENGINES = {'luxrender'}
	
	display_property_groups = [
		'luxrender_lamp',
	]
	
	object_property_groups = [
		luxrender_lamp,
	]
	
	@classmethod
	def property_reload(cls):
		for lamp in bpy.data.lamps:
			cls.property_create(lamp)
	
	@classmethod
	def property_create(cls, lamp):
		for property_group in cls.object_property_groups:
			if not hasattr(lamp, property_group.__name__):
				init_properties(lamp, [{
					'type': 'pointer',
					'attr': property_group.__name__,
					'ptype': property_group,
					'name': property_group.__name__,
					'description': property_group.__name__
				}], cache=False)
				init_properties(property_group, property_group.properties, cache=False)
	
	# Overridden to provide data storage in the lamp, not the scene
	def draw(self, context):
		if context.lamp is not None:
			layout = self.layout
			lamps.property_create(context.lamp)
			
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
				
				# LuxRender properties
				for property_group_name in self.display_property_groups:
					property_group = getattr(context.lamp, property_group_name)
					for p in property_group.controls:
						self.draw_column(p, self.layout, context.lamp, supercontext=context, property_group=property_group)


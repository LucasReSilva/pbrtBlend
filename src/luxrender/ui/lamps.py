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
from ef.ui import described_layout
from ef.ef import ef
from ef.validate import Logic_Operator as LO 

# Lux API
import luxrender.properties.lamp

narrowui = 180

class lamps(DataButtonsPanel, described_layout):
	bl_label = 'LuxRender Lamps'
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender.properties.lamp.luxrender_lamp

	# prevent creating luxrender_material property group in Scene
	property_group_non_global = True

	@staticmethod
	def property_reload():
		for lamp in bpy.data.lamps:
			lamps.property_create(lamp)
	
	@staticmethod
	def property_create(lamp):
		if not hasattr(lamp, lamps.property_group.__name__):
			ef.init_properties(lamp, [{
				'type': 'pointer',
				'attr': lamps.property_group.__name__,
				'ptype': lamps.property_group,
				'name': lamps.property_group.__name__,
				'description': lamps.property_group.__name__
			}], cache=False)
			ef.init_properties(lamps.property_group, lamps.properties, cache=False)
	
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
				sub = col.column()
				sub.prop(lamp, "color", text="")
				sub.prop(lamp, "energy", text="Gain")

				# SPOT LAMP: Blender Properties
				if lamp.type == 'SPOT':
					wide_ui = context.region.width > narrowui

					if wide_ui:
						col = split.column()
					col.prop(lamp, "spot_size", text="Size")
					col.prop(lamp, "spot_blend", text="Blend", slider=True)
				
				# AREA LAMP: Blender Properties
				elif lamp.type == 'AREA':

					if wide_ui:
						col = split.column()
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
				for p in self.controls:
					self.draw_column(p, self.layout, context.lamp, supercontext=context)
	
	# luxrender properties
	controls = [
		'importance', 'lightgroup',
		['power','efficacy'],
		'turbidity', 'sunsky_type',
		'infinite_map',
		'mapping_type',
	]
	
	visibility = {
		'power':			{ 'type': 'AREA'},
		'efficacy':			{ 'type': 'AREA'},
		
		'turbidity':		{ 'type': 'SUN' },
		'sunsky_type':		{ 'type': 'SUN' },
		
		'infinite_map':		{ 'type': 'HEMI' },
		'mapping_type':		{ 'type': 'HEMI', 'infinite_map': LO({'!=': ''}) },
	}
	
	properties = [
		{
			# hidden value for visibility control
			'type': 'string',
			'attr': 'type',
			'default': 'UNSUPPORTED',
		},
		{
			'type': 'string',
			'attr': 'lightgroup',
			'name': 'Light Group',
			'description': 'Name of group to put this light in',
			'default': 'default'
		},
		{
			'type': 'float',
			'attr': 'power',
			'name': 'Power',
			'default': 100.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		},   
		{
			'type': 'float',
			'attr': 'efficacy',
			'name': 'Efficacy',
			'default': 17.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		},
		{
			'type': 'float',
			'attr': 'importance',
			'name': 'Importance',
			'description': 'Light source importance',
			'default': 0.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e3,
			'soft_max': 1e3,
		},
		
		# Sun
		{
			'type': 'float',
			'attr': 'turbidity',
			'name': 'turbidity',
			'default': 2.0,
			'min': 0.7,
			'soft_min': 0.7,
			'max': 35.0,
			'soft_max': 35.0,
		},
		{
			'type': 'enum',
			'attr': 'sunsky_type',
			'name': 'Sky Type',
			'default': 'sunsky',
			'items': [
				('sunsky', 'Sun & Sky', 'sunsky'),
				('sun', 'Sun Only', 'sun'),
				#('sky', 'Sky Only', 'sky'),	# sky only doesn't work
			]
		},
		
		# HEMI / INFINITE
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'infinite_map',
			'name': 'HDRI Map',
			'description': 'HDR image to use for lighting',
			'default': ''
		},
		{
			'type': 'enum',
			'attr': 'mapping_type',
			'name': 'Map Type',
			'default': 'latlong',
			'items': [
				('latlong', 'Lat Long', 'latlong'),
				('angular', 'Angular', 'angular'),
				('vcross', 'Vert Cross', 'vcross')
			]
		},
	]


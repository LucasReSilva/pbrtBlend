# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Genscher
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
from math import degrees

import bpy, mathutils

from luxrender.module.file_api import Files
from luxrender.export import matrix_to_list
from luxrender.export import ParamSet

from luxrender.properties import dbo

def attr_light(l, name, group, type, params, transform=None):
	'''
	l				pylux.Context
	name			string
	type			string
	params			dict
	transform		None or list
	
	This method outputs a lightSource of the given name and
	type to context l. The lightSource will be wrapped in a
	transformBegin...transformEnd block if a transform is
	given, otherwise it will appear in an attributeBegin...
	attributeEnd block.
	
	Returns			None
	'''
	
	if transform is not None:
		l.transformBegin(comment=name, file=Files.MAIN)
		l.transform(transform)
	else:
		l.attributeBegin(comment=name, file=Files.MAIN)
	
	dbo('LIGHT', (type, params))
	l.lightGroup(group)
	l.lightSource(type, params)
	
	if transform is not None:
		l.transformEnd()
	else:
		l.attributeEnd()

def lights(l, scene):
	'''
	l				pylux.Context
	scene			bpy.types.scene
	
	Iterate over the given scene's light sources,
	and export the compatible ones to the context l.
	
	Returns Boolean indicating if any light sources
	were exported.
	'''
	
	sel = scene.objects
	have_light = False

	for ob in sel:
		
		if ob.type != 'LAMP':
			continue

		light = ob.data
		
		# Params common to all light types
		light_params = ParamSet() \
			.add_float('gain', light.energy) \
			.add_float('importance', light.luxrender_lamp.importance)
		
		if light.type == 'SUN':
			invmatrix = mathutils.Matrix(ob.matrix).invert()
			light_params.add_vector('sundir', (invmatrix[0][2], invmatrix[1][2], invmatrix[2][2]))
			light_params.add_float('turbidity', light.luxrender_lamp.turbidity)
			# nsamples
			# relsize (sun only)
			# [a-e]const (sky only)
			attr_light(l, ob.name, light.luxrender_lamp.lightgroup, light.luxrender_lamp.sunsky_type, light_params)
			have_light = True
		
		if light.type == 'SPOT':
			coneangle = degrees(light.spot_size) * 0.5
			conedeltaangle = degrees(light.spot_size * 0.5 * light.spot_blend)
			light_params.add_color('L', list(light.color))
			light_params.add_point('from', (0,0,0))
			light_params.add_point('to', (0,0,-1))
			light_params.add_float('coneangle', coneangle)
			light_params.add_float('conedeltaangle', conedeltaangle)
			attr_light(l, ob.name, light.luxrender_lamp.lightgroup, 'spot', light_params, transform=matrix_to_list(ob.matrix))
			have_light = True

		if light.type == 'POINT':
			light_params.add_color('L', list(light.color))
			light_params.add_point('from', (0,0,0)) # (0,0,0) is correct since there is an active Transform
			attr_light(l, ob.name, light.luxrender_lamp.lightgroup, 'point', light_params, transform=matrix_to_list(ob.matrix))
			have_light = True
			
		if light.type == 'HEMI':
			if light.luxrender_lamp.infinite_map != '':
				light_params.add_string('mapname', light.luxrender_lamp.infinite_map)
				light_params.add_string('mapping', light.luxrender_lamp.mapping_type)
			else:
				# TODO: check if users want L multiplied to HDRI maps
				light_params.add_color('L', list(light.color))
			# nsamples
			# gamma
			attr_light(l, ob.name, light.luxrender_lamp.lightgroup, 'infinite', light_params, transform=matrix_to_list(ob.matrix))
			have_light = True
		
		if light.type == 'AREA':
			light_params.add_color('L', list(light.color))
			light_params.add_float('power', light.luxrender_lamp.power)
			light_params.add_float('efficacy', light.luxrender_lamp.efficacy)
			# nsamples
			l.attributeBegin(ob.name, file=Files.MAIN)
			l.transform(matrix_to_list(ob.matrix))
			l.lightGroup(light.luxrender_lamp.lightgroup)
			l.arealightSource('area', light_params)

			areax = light.size

			if light.shape == 'SQUARE':
				areay = areax
			elif light.shape == 'RECTANGLE':
				areay = light.size_y
			else:
				areay = areax # not supported yet

			points = [-areax/2, areay/2, 0.0, areax/2, areay/2, 0.0, areax/2, -areay/2, 0.0, -areax/2, -areay/2, 0.0]
			shape_params = ParamSet() \
				.add_integer('indices', [0, 1, 2, 0, 2, 3]) \
				.add_point('P', points)
			l.shape('trianglemesh', shape_params)
			l.attributeEnd()

			have_light = True

	return have_light
		

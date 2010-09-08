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

from ef.util import util as efutil

from luxrender.outputs.file_api import Files
from luxrender.properties import dbo
from luxrender.export import ParamSet, get_worldscale, matrix_to_list
from luxrender.export.materials import add_texture_parameter

def attr_light(lux_context, name, group, type, params, transform=None):
	'''
	lux_context		pylux.Context
	name			string
	type			string
	params			dict
	transform		None or list
	
	This method outputs a lightSource of the given name and
	type to context lux_context. The lightSource will be
	wrapped in a transformBegin...transformEnd block if
	a transform is given, otherwise it will appear in an
	attributeBegin...attributeEnd block.
	
	Returns			None
	'''
	
	if transform is not None:
		lux_context.transformBegin(comment=name, file=Files.MAIN)
		lux_context.transform(transform)
	else:
		lux_context.attributeBegin(comment=name, file=Files.MAIN)
	
	dbo('LIGHT', (type, params))
	lux_context.lightGroup(group, [])
	lux_context.lightSource(type, params)
	
	if transform is not None:
		lux_context.transformEnd()
	else:
		lux_context.attributeEnd()

def exportLights(lux_context, ob, matrix):
	light = ob.data
		
	# Params common to all light types
	
	light_params = ParamSet() \
		.add_float('gain', light.energy) \
		.add_float('importance', light.luxrender_lamp.importance)
	
	if light.type == 'SUN':
		invmatrix = mathutils.Matrix(matrix).invert()
		light_params.add_vector('sundir', (invmatrix[0][2], invmatrix[1][2], invmatrix[2][2]))
		light_params.add_float('turbidity', light.luxrender_lamp.turbidity)
		# nsamples
		# relsize (sun only)
		# [a-e]const (sky only)
		attr_light(lux_context, ob.name, light.luxrender_lamp.lightgroup, light.luxrender_lamp.sunsky_type, light_params)
		return True
	
	# all lights apart from sun + sky have "color L"
	light_params.update( add_texture_parameter(lux_context, 'L', 'color', light.luxrender_lamp) )
	
	if light.type == 'SPOT':
		coneangle = degrees(light.spot_size) * 0.5
		conedeltaangle = degrees(light.spot_size * 0.5 * light.spot_blend)
		light_params.add_point('from', (0,0,0))
		light_params.add_point('to', (0,0,-1))
		light_params.add_float('coneangle', coneangle)
		light_params.add_float('conedeltaangle', conedeltaangle)
		attr_light(lux_context, ob.name, light.luxrender_lamp.lightgroup, 'spot', light_params, transform=matrix_to_list(matrix, apply_worldscale=True))
		return True

	if light.type == 'POINT':
		light_params.add_point('from', (0,0,0)) # (0,0,0) is correct since there is an active Transform
		attr_light(lux_context, ob.name, light.luxrender_lamp.lightgroup, 'point', light_params, transform=matrix_to_list(matrix, apply_worldscale=True))
		return True
		
	if light.type == 'HEMI':
		if light.luxrender_lamp.infinite_map != '':
			if lux_context.API_TYPE == 'FILE':
				# export relative file path
				light_params.add_string('mapname', efutil.path_relative_to_export(light.luxrender_lamp.infinite_map) )
			else:
				light_params.add_string('mapname', light.luxrender_lamp.infinite_map)
			light_params.add_string('mapping', light.luxrender_lamp.mapping_type)
		# nsamples
		# gamma
		attr_light(lux_context, ob.name, light.luxrender_lamp.lightgroup, 'infinite', light_params, transform=matrix_to_list(matrix, apply_worldscale=True))
		return True
	
	if light.type == 'AREA':
		light_params.add_float('power', light.luxrender_lamp.power)
		light_params.add_float('efficacy', light.luxrender_lamp.efficacy)
		
		# overwrite gain with a gain scaled by ws^2 to account for change in lamp area
		light_params.add_float('gain', light.energy * (get_worldscale(as_scalematrix=False)**2))
		# nsamples
		lux_context.attributeBegin(ob.name, file=Files.MAIN)
		lux_context.transform(matrix_to_list(matrix, apply_worldscale=True))
		lux_context.lightGroup(light.luxrender_lamp.lightgroup, [])
		lux_context.areaLightSource('area', light_params)

		areax = light.size

		if light.shape == 'SQUARE':
			areay = areax
		elif light.shape == 'RECTANGLE':
			areay = light.size_y
		else:
			areay = areax # not supported yet

		points = [-areax/2.0, areay/2.0, 0.0, areax/2.0, areay/2.0, 0.0, areax/2.0, -areay/2.0, 0.0, -areax/2.0, -areay/2.0, 0.0]
		shape_params = ParamSet() \
			.add_integer('indices', [0, 1, 2, 0, 2, 3]) \
			.add_point('P', points)
		lux_context.shape('trianglemesh', shape_params)
		lux_context.attributeEnd()
		return True

	return False

#-------------------------------------------------
# lights(lux_context, scene)
# MAIN export function
#-------------------------------------------------
def lights(lux_context, scene):
	'''
	lux_context		pylux.Context
	scene			bpy.types.scene
	
	Iterate over the given scene's light sources,
	and export the compatible ones to the context lux_context.
	
	Returns Boolean indicating if any light sources
	were exported.
	'''
	
	sel = scene.objects
	have_light = False
	
	for ob in sel:
		
		if not ob.is_visible(scene) or ob.hide_render:
			continue
		
		# skip dupli (child) objects when they are not lamps
		if (ob.parent and ob.parent.is_duplicator) and ob.type != 'LAMP':
			continue

		# we have to check for duplis before the "LAMP" ceck 
		# to support a mesh/object which got lamp as dupli object
		if ob.is_duplicator and ob.dupli_type in ('GROUP', 'VERTS', 'FACES'):
			# create dupli objects
			ob.create_dupli_list(scene)

			for dupli_ob in ob.dupli_list:
				if dupli_ob.object.type != 'LAMP':
					continue
				have_light |= exportLights(lux_context, dupli_ob.object, dupli_ob.matrix_world)

			# free object dupli list again. Warning: all dupli objects are INVALID now!
			if ob.dupli_list: 
				ob.free_dupli_list()
		else:
			if ob.type == 'LAMP':
				have_light |= exportLights(lux_context, ob, ob.matrix_world)
		
		if ob.type == 'MESH':
			# now check for emissive materials on ob
			for im in ob.material_slots:
				if hasattr(im.material, 'luxrender_emission'):
					have_light |= im.material.luxrender_emission.use_emission
			for m in ob.data.materials:
				if hasattr(m, 'luxrender_emission'):
					have_light |= m.luxrender_emission.use_emission 
	
	return have_light


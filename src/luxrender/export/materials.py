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
import random

from . import ParamSet
from ..ui import material_property_map, FloatTexture, ColorTexture

class ExportedMaterials(object):
	# Static class variables
	material_names = []
	material_psets = []
	exported_material_names = []
	
	@staticmethod
	def clear():
		ExportedMaterials.material_names = []
		ExportedMaterials.material_psets = []
		ExportedMaterials.exported_material_names = []
		
	@staticmethod
	def makeNamedMaterial(name, paramset):
		ExportedMaterials.material_names.append(name)
		ExportedMaterials.material_psets.append(paramset)
		
	@staticmethod
	def calculate_dependencies():
		'''
		TODO: iterate over materials, detect texture dependencies
		and re-order texture export lists so that deps are satisfied
		TODO: for extra marks, detect and cure cyclic-deps 
		'''
		pass
	
	@staticmethod
	def export_new_named(lux_context):
		for n, p in zip(ExportedMaterials.material_names, ExportedMaterials.material_psets):
			if n not in ExportedMaterials.exported_material_names:
				lux_context.makeNamedMaterial(n, p)
				ExportedMaterials.exported_material_names.append(n)
	

def materials(lux_context, ob):
	if lux_context.API_TYPE == 'FILE':
		materials_file(lux_context, ob)
	elif lux_context.API_TYPE == 'PURE':
		materials_direct(lux_context, ob)

def materials_direct(lux_context, ob):
	for m in ob.data.materials:
		if hasattr(m, 'luxrender_material'):
			material_params = luxrender_material_params(m)
			lux_context.material('matte', material_params)

def materials_file(lux_context, ob):
	lux_context.namedMaterial(ob.active_material.name)
	for m in ob.data.materials:
		if hasattr(m, 'luxrender_material') and m.name not in ExportedMaterials.material_names:
			material_params = luxrender_material_params(m, add_type=True)
			ExportedMaterials.makeNamedMaterial(m.name, material_params)
	
	ExportedMaterials.export_new_named(lux_context)

def add_float_texture(lux_prop_name, lux_mat):
	params = ParamSet()
	
	if getattr(lux_mat, '%s_usetexture'%lux_prop_name):
		# TODO: find and export the named texture
		params.add_texture(
			lux_prop_name,
			getattr(lux_mat, '%s_texturename'%lux_prop_name)
		)
	else:
		params.add_float(
			lux_prop_name,
			getattr(lux_mat, '%s_floatvalue'%lux_prop_name)
		)
	
	return params

def add_color_texture(lux_prop_name, lux_mat):
	params = ParamSet()
	
	if getattr(lux_mat, '%s_usetexture'%lux_prop_name):
		# TODO: find and export the named texture
		params.add_texture(
			lux_prop_name,
			getattr(lux_mat, '%s_texturename'%lux_prop_name)
		)
	else:
		params.add_color(
			lux_prop_name,
			[float(i) for i in getattr(lux_mat, '%s_color'%lux_prop_name)]
		)
	
	return params

def luxrender_material_params(mat, add_type=False):
	print('mat %s'%mat.name)
	lux_mat = mat.luxrender_material
	mp = ParamSet()
	lux_mat_type = lux_mat.material
	if add_type:
		mp.add_string('type', lux_mat_type)
		
	mpm = material_property_map()
	for lux_prop_name in [lp for lp in dir(lux_mat) if lp in mpm.keys()]:
		if lux_mat_type in mpm[lux_prop_name]:
			lux_prop = getattr(lux_mat, lux_prop_name)
			if lux_prop == 'lux_float_texture':
				mp.update(add_float_texture(lux_prop_name, lux_mat))
			elif lux_prop == 'lux_color_texture':
				mp.update(add_color_texture(lux_prop_name, lux_mat))
			# TODO: these basic types should cover everything for now ?
			elif type(lux_prop) is float:
				mp.add_float(lux_prop_name, lux_prop)
			elif type(lux_prop) is str:
				mp.add_string(lux_prop_name, lux_prop)
			elif type(lux_prop) is bool:
				mp.add_bool(lux_prop_name, lux_prop)
			elif type(lux_prop) is int:
				mp.add_integer(lux_prop_name, lux_prop)
	
	return mp
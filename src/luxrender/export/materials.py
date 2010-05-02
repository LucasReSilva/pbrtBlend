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

import bpy

from ef.validate import Visibility

from . import ParamSet
from ..module import LuxLog
from ..properties.util import material_property_map

def write_lxm(l, scene):
	'''
	l			pylux.Context
	scene		bpy.types.scene
	
	Iterate over the given scene's objects, and export materials
	of visible ones to the lux Conext l
	
	Returns		None
	'''
	
	vis_layers = scene.layers
	
	sel = scene.objects
	total_objects = len(sel)
	rpcs = []
	ipc = 0.0
	for ob in sel:
		ipc += 1.0
		
		if ob.type in ('LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE', 'LATTICE'):
			continue
		
		# Check layers
		visible = False
		for layer_index, o_layer in enumerate(ob.layers):
			visible = visible or (o_layer and vis_layers[layer_index])
		
		if not visible:
			continue
		
		materials_file(l, ob)

class ExportedTextures(object):
	# static class variables
	texture_names = []	# Name
	texture_types = []	# Float|Color 
	texture_texts = []	# Texture plugin name
	texture_psets = []	# ParamSets
	exported_texture_names = []
	
	@staticmethod
	def clear():
		ExportedTextures.texture_names = []
		ExportedTextures.texture_types = [] 
		ExportedTextures.texture_texts = []
		ExportedTextures.texture_psets = []
		ExportedTextures.exported_texture_names = []
		
	@staticmethod
	def texture(name, type, texture, params):
		if name not in ExportedTextures.exported_texture_names:
			ExportedTextures.texture_names.append(name)
			ExportedTextures.texture_types.append(type)
			ExportedTextures.texture_texts.append(texture)
			ExportedTextures.texture_psets.append(params)
	
	@staticmethod
	def calculate_dependencies():
		pass
	
	@staticmethod
	def export_new(lux_context):
		for n, ty, tx, p in zip(
				ExportedTextures.texture_names,
				ExportedTextures.texture_types, 
				ExportedTextures.texture_texts,
				ExportedTextures.texture_psets
			):
			if n not in ExportedTextures.exported_texture_names:
				ExportedTextures.calculate_dependencies()
				lux_context.texture(n, ty, tx, p)
				ExportedTextures.exported_texture_names.append(n)

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
		if name not in ExportedMaterials.exported_material_names:
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
				ExportedMaterials.calculate_dependencies()
				lux_context.makeNamedMaterial(n, p)
				ExportedMaterials.exported_material_names.append(n)

def export_object_material(lux_context, ob):
	if lux_context.API_TYPE == 'FILE':
		lux_context.namedMaterial(ob.active_material.name)
	elif lux_context.API_TYPE == 'PURE':
		materials_direct(lux_context, ob)

def materials_direct(lux_context, ob):
	for m in ob.data.materials:
		if hasattr(m, 'luxrender_material'):
			material_params = luxrender_material_params(lux_context, m)
			lux_context.material('matte', material_params)

def materials_file(lux_context, ob):
	for m in ob.data.materials:
		if hasattr(m, 'luxrender_material') and m.name not in ExportedMaterials.material_names:
			material_params = luxrender_material_params(lux_context, m, add_type=True)
			ExportedMaterials.makeNamedMaterial(m.name, material_params)
	
	ExportedMaterials.export_new_named(lux_context)

def add_float_texture(lux_context, lux_prop_name, lux_mattex, mattex):
	params = ParamSet()
	
	if getattr(lux_mattex, '%s_usetexture'%lux_prop_name):
		texture_name = getattr(lux_mattex, '%s_texturename'%lux_prop_name)
		if texture_name != '':
			if texture_name in bpy.data.textures and bpy.data.textures[texture_name].luxrender_texture.variant == 'FLOAT':
				params.add_texture(
					texture_property_translate(lux_prop_name),
					texture_name
				)
				luxrender_texture_params('float', lux_context, bpy.data.textures[texture_name])
				ExportedTextures.export_new(lux_context)
		elif lux_prop_name != 'bumpmap':
			LuxLog('WARNING: Unassigned float texture slot %s -> %s' % (mattex.name, texture_property_translate(lux_prop_name)))
	else:
		params.add_float(
			lux_prop_name,
			float(getattr(lux_mattex, '%s_floatvalue'%lux_prop_name))
		)
	
	return params

def add_color_texture(lux_context, lux_prop_name, lux_mattex, mattex):
	params = ParamSet()
	
	if getattr(lux_mattex, '%s_usetexture'%lux_prop_name):
		texture_name = getattr(lux_mattex, '%s_texturename'%lux_prop_name)
		if texture_name != '':
			if texture_name in bpy.data.textures and bpy.data.textures[texture_name].luxrender_texture.variant == 'COLOR':
				params.add_texture(
					texture_property_translate(lux_prop_name),
					texture_name
				)
				luxrender_texture_params('color', lux_context, bpy.data.textures[texture_name])
				ExportedTextures.export_new(lux_context)
		elif lux_prop_name != 'bumpmap':
			LuxLog('WARNING: Unassigned color texture slot %s -> %s' % (mattex.name, texture_property_translate(lux_prop_name)))
	else:
		params.add_color(
			lux_prop_name,
			[float(i) for i in getattr(lux_mattex, '%s_color'%lux_prop_name)]
		)
	
	return params

def luxrender_texture_params(tex_type, lux_context, tex):
	# TODO: detect luxrender/blender texture, convert if necessary
	
	tp = ParamSet()
	
	if hasattr(tex, 'luxrender_texture'):
		lux_tex = tex.luxrender_texture
		
		# TODO
		
		#ExportedTextures.texture(tex.name, tex_type, lux_tex.texture, tp)

def luxrender_material_params(lux_context, mat, add_type=False):
	#print('mat %s'%mat.name)
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
				mp.update(add_float_texture(lux_context, lux_prop_name, lux_mat, mat))
			elif lux_prop == 'lux_color_texture':
				mp.update(add_color_texture(lux_context, lux_prop_name, lux_mat, mat))
			# TODO: these basic types should cover everything for now ?
			elif type(lux_prop) is float:
				mp.add_float(lux_prop_name, lux_prop)
			elif type(lux_prop) is str:
				mp.add_string(lux_prop_name, lux_prop)
			elif type(lux_prop) is bool:
				mp.add_bool(lux_prop_name, lux_prop)
			elif type(lux_prop) is int:
				mp.add_integer(lux_prop_name, lux_prop)
			elif type(lux_prop).__name__ == 'bpy_prop_array':
				mp.add_vector(lux_prop_name, lux_prop)
	
	return mp

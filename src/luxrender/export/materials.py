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
import bpy

from luxrender.export import ParamSet
from luxrender.outputs import LuxLog
from luxrender.properties import material_property_map

def write_lxm(lux_context, scene):
	'''
	lux_context			pylux.Context
	scene				bpy.types.scene
	
	Iterate over the given scene's objects, and export materials
	of visible ones to the lux Context lux_context
	
	Returns				None
	'''
	
	vis_layers = scene.layers
	
	for ob in scene.objects:
		
		if ob.type in ('LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE', 'LATTICE'):
			continue
		
		# Check layers
		visible = False
		for layer_index, o_layer in enumerate(ob.layers):
			visible = visible or (o_layer and vis_layers[layer_index])
		
		if not visible:
			continue
		
		materials_file(lux_context, ob)

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
		TODO: detect and cure cyclic-deps 
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
	if ob.active_material is not None:
		if lux_context.API_TYPE == 'FILE':
			lux_context.namedMaterial(ob.active_material.name)
		elif lux_context.API_TYPE == 'PURE':
			mat = ob.active_material
			mat.luxrender_material.export(lux_context, mat, mode='direct')
	#else:
	#	LuxLog('WARNING: Object "%s" has no material assigned' % ob.name)

def get_instance_materials(ob):
	obmats = []
	# Grab materials attached to object instances ...
	for ms in ob.material_slots:
		obmats.append(ms.material)
	# ... and to the object's mesh data
	for m in ob.data.materials:
		obmats.append(m)
	
	# when exporting in direct mode, per instance materials will take precedence
	# over the base mesh's material definition.
	return obmats
	
def materials_direct(lux_context, ob):
	for m in get_instance_materials(ob):
		if hasattr(m, 'luxrender_material'):
			lux_context.material( *luxrender_material_params(lux_context, m) )
			break	# just use the first material found

def materials_file(lux_context, ob):
	for m in get_instance_materials(ob):
		if hasattr(m, 'luxrender_material') and m.name not in ExportedMaterials.material_names:
			mat_type, material_params = luxrender_material_params(lux_context, m, add_type=True)
			ExportedMaterials.makeNamedMaterial(m.name, material_params)
	
	ExportedMaterials.export_new_named(lux_context)

def convert_texture(texture):
	
	# Lux only supports blender's textures in float variant
	variant = 'float'
	paramset = ParamSet()
	lux_tex_name = 'blender_%s' % texture.type.lower()
	
	if texture.type == 'BLEND':
		progression_map = {
			'LINEAR':			'lin',
			'QUADRATIC':		'quad',
			'EASING':			'ease',
			'DIAGONAL':			'diag',
			'SPHERICAL':		'sphere',
			'QUADRATIC_SPHERE':	'halo',
			'RADIAL':			'radial',
		}
		paramset.add_bool('flipxy', texture.use_flip_axis) \
				.add_string('type', progression_map[texture.progression])
	
	if texture.type == 'CLOUDS':
		paramset.add_string('noisetype', texture.noise_type.lower() ) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('noisesize', texture.noise_size) \
				.add_integer('noisedepth', texture.noise_depth) \
				.add_float('nabla', texture.nabla)
	
	if texture.type == 'DISTORTED_NOISE':
		lux_tex_name = 'blender_distortednoise'
		paramset.add_string('type', texture.noise_distortion.lower()) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('distamount', texture.distortion) \
				.add_float('noisesize', texture.noise_size) \
				.add_float('nabla', texture.nabla)
	
	if texture.type == 'MAGIC':
		paramset.add_integer('noisedepth', texture.noise_depth) \
				.add_float('turbulence', texture.turbulence)
	
	if texture.type == 'MARBLE':
		paramset.add_string('type', texture.stype.lower() ) \
				.add_string('noisetype', texture.noise_type.lower() ) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_string('noisebasis2', texture.noisebasis2.lower() ) \
				.add_float('noisesize', texture.noise_size) \
				.add_float('turbulence', texture.turbulence) \
				.add_integer('noisedepth', texture.noise_depth) \
				.add_float('nabla', texture.nabla)
	
	if texture.type == 'MUSGRAVE':
		paramset.add_string('type', texture.musgrave_type.lower() ) \
				.add_float('h', texture.highest_dimension) \
				.add_float('lacu', texture.lacunarity) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('noisesize', texture.noise_size) \
				.add_float('octs', texture.octaves) \
				.add_float('nabla', texture.nabla)
	
	# NOISE shows no params ?
	
	if texture.type == 'STUCCI':
		paramset.add_string('type', texture.musgrave_type.lower() ) \
				.add_string('noisetype', texture.noise_type.lower() ) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('noisesize', texture.noise_size) \
				.add_float('turbulence', texture.turbulence)
	
	if texture.type == 'VORONOI':
		distancem_map = {
			'DISTANCE': 'actual_distance',
			'DISTANCE_SQUARED': 'distance_squared',
			'MANHATTAN': 'manhattan',
			'CHEBYCHEV': 'chebychev',
			'MINKOVSKY_HALF': 'minkovsky_half',
			'MINKOVSKY_FOUR': 'minkovsky_four',
			'MINKOVSKY': 'minkovsky'
		}
		paramset.add_string('distmetric', distancem_map[texture.distance_metric]) \
				.add_float('minkowsky_exp', texture.minkovsky_exponent) \
				.add_float('noisesize', texture.noise_size) \
				.add_float('nabla', texture.nabla) \
				.add_float('w1', texture.weight_1) \
				.add_float('w2', texture.weight_2) \
				.add_float('w3', texture.weight_3) \
				.add_float('w4', texture.weight_4)
	
	if texture.type == 'WOOD':
		paramset.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_string('noisebasis2', texture.noisebasis2.lower() ) \
				.add_float('noisesize', texture.noise_size) \
				.add_string('noisetype', texture.noise_type.lower() ) \
				.add_float('turbulence', texture.turbulence) \
				.add_string('type', texture.musgrave_type.lower() ) \
				.add_float('nabla', texture.nabla)
	
	paramset.update( texture.luxrender_texture.transform.get_paramset() )
	
	return variant, lux_tex_name, paramset

def RGC(value):
	if bpy.context.scene.luxrender_engine.rgc:
		gamma = bpy.context.scene.camera.data.luxrender_colorspace.gamma
	else:
		gamma = 1.0
	
	ncol = value**(1/gamma)
	
	if bpy.context.scene.luxrender_engine.colclamp:
		ncol = ncol * 0.9
		if ncol > 0.9:
			ncol = 0.9
		if ncol < 0.0:
			ncol = 0.0
	return ncol

def value_transform_passthrough(val):
	return val

def add_texture_parameter(lux_context, lux_prop_name, variant, lux_mattex, value_transform=value_transform_passthrough):
	'''
	lux_context				pylux.Context - like object
	lux_prop_name			LuxRender material/texture parameter name
	variant					Required variant: 'float' or 'color' or 'fresnel'
	lux_mattex				luxrender_material or luxrender_texture IDPropertyGroup FOR THE CONTAINING MATERIAL/TEXTURE
	
	Either insert a float parameter or a float texture reference, depending on setup
	
	Returns					ParamSet
	'''
	params = ParamSet()
	
	if hasattr(lux_mattex, '%s_use%stexture' % (lux_prop_name, variant)):
		if getattr(lux_mattex, '%s_use%stexture' % (lux_prop_name, variant)):
			texture_name = getattr(lux_mattex, '%s_%stexturename' % (lux_prop_name, variant))
			if texture_name != '':
				if texture_name in bpy.data.textures:
					texture = bpy.data.textures[texture_name]
					if texture.luxrender_texture.type != 'BLENDER':
						tex_luxrender_texture = texture.luxrender_texture
						lux_tex_variant, paramset = tex_luxrender_texture.get_paramset()
						if lux_tex_variant == variant:
							ExportedTextures.texture(texture_name, variant, tex_luxrender_texture.type, paramset)
						else:
							LuxLog('WARNING: Texture %s is wrong variant; needed %s, got %s' % (lux_prop_name, variant, lux_tex_variant))
					else:
						lux_tex_variant, lux_tex_name, paramset = convert_texture(texture)
						if lux_tex_variant == variant:
							ExportedTextures.texture(texture_name, lux_tex_variant, lux_tex_name, paramset)
						else:
							LuxLog('WARNING: Texture %s is wrong variant; needed %s, got %s' % (lux_prop_name, variant, lux_tex_variant))
					
					if hasattr(lux_mattex, '%s_multiplyfloat' % lux_prop_name) and getattr(lux_mattex, '%s_multiplyfloat' % lux_prop_name):
						ExportedTextures.texture(
							texture_name + '_scaled',
							variant,
							'scale',
							ParamSet() \
								.add_float('tex1', float(getattr(lux_mattex, '%s_floatvalue' % lux_prop_name))) \
								.add_texture('tex2', texture_name)
						)
						texture_name += '_scaled'
					
					ExportedTextures.export_new(lux_context)
					
					params.add_texture(
						lux_prop_name,
						texture_name
					)
					
			elif lux_prop_name != 'bumpmap':
				LuxLog('WARNING: Unassigned %s texture slot %s' % (variant, lux_prop_name))
		else:
			if variant == 'float':
				fval = float(getattr(lux_mattex, '%s_floatvalue' % lux_prop_name))
				if not (getattr(lux_mattex, '%s_ignorezero' % lux_prop_name) and fval==0.0):
					params.add_float(
						lux_prop_name,
						fval
					)
			elif variant == 'color':
				use_rgc = getattr(lux_mattex, '%s_usecolorrgc' % lux_prop_name)
				if use_rgc:
					params.add_color(
						lux_prop_name,
						[RGC(value_transform(i)) for i in getattr(lux_mattex, '%s_color' % lux_prop_name)]
					)
				else:
					params.add_color(
						lux_prop_name,
						[float(value_transform(i)) for i in getattr(lux_mattex, '%s_color' % lux_prop_name)]
					)
			elif variant == 'fresnel':
				# TODO
				pass
	else:
		LuxLog('WARNING: Texture %s is unsupported variant; needed %s' % (lux_prop_name, variant))
	
	return params

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
				mp.update(add_texture_parameter(lux_context, lux_prop_name, 'float', lux_mat))
			elif lux_prop == 'lux_color_texture':
				mp.update(add_texture_parameter(lux_context, lux_prop_name, 'color', lux_mat))
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
	
	return lux_mat_type, mp

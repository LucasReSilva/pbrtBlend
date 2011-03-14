# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
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
import os

import bpy

from extensions_framework import util as efutil

from ..export import ParamSet
from ..outputs import LuxLog, LuxManager

# TODO: convert this into ExportCache instance
class ExportedTextures(object):
	# static class variables
	texture_names = []	# Name
	texture_types = []	# Float|Color 
	texture_texts = []	# Texture plugin name
	texture_psets = []	# ParamSets
	exported_texture_names = []
	scalers_count = 0
	
	@staticmethod
	def clear():
		ExportedTextures.texture_names = []
		ExportedTextures.texture_types = [] 
		ExportedTextures.texture_texts = []
		ExportedTextures.texture_psets = []
		ExportedTextures.exported_texture_names = []
		ExportedTextures.scalers_count = 0
	
	@staticmethod
	def next_scale_value():
		ExportedTextures.scalers_count+=1
		return ExportedTextures.scalers_count
	
	@staticmethod
	def texture(lux_context, name, type, texture, params):
		if lux_context.API_TYPE == 'PURE':
			lux_context.texture(name, type, texture, params)
			return
		
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
			if lux_context.API_TYPE!='PURE' and n not in ExportedTextures.exported_texture_names:
				ExportedTextures.calculate_dependencies()
				lux_context.texture(n, ty, tx, p)
				ExportedTextures.exported_texture_names.append(n)

# TODO: convert this into ExportCache instance
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
	def makeNamedMaterial(lux_context, name, paramset):
		if lux_context.API_TYPE == 'PURE':
			lux_context.makeNamedMaterial(name, paramset)
			return
		
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
			if lux_context.API_TYPE!='PURE' and n not in ExportedMaterials.exported_material_names:
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
	if hasattr(ob, 'material_slots'):
		for ms in ob.material_slots:
			obmats.append(ms.material)
	# ... and to the object's mesh data
	if hasattr(ob.data, 'materials'):
		for m in ob.data.materials:
			obmats.append(m)
	
	# per instance materials will take precedence
	# over the base mesh's material definition.
	return obmats

def get_material_volume_defs(m):
	return m.luxrender_material.Interior_volume, m.luxrender_material.Exterior_volume

def convert_texture(scene, texture):
	
	# Lux only supports blender's textures in float variant
	variant = 'float'
	paramset = ParamSet()
	lux_tex_name = 'blender_%s' % texture.type.lower()
	
	mapping_type = '3D'
	
	if texture.type == 'BLEND':
		progression_map = {
			'LINEAR':			'lin',
			'QUADRATIC':			'quad',
			'EASING':			'ease',
			'DIAGONAL':			'diag',
			'SPHERICAL':			'sphere',
			'QUADRATIC_SPHERE':		'halo',
			'RADIAL':			'radial',
		}
		paramset.add_bool('flipxy', texture.use_flip_axis) \
				.add_string('type', progression_map[texture.progression])
	
	if texture.type == 'CLOUDS':
		paramset.add_string('noisetype', texture.noise_type.lower() ) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('noisesize', texture.noise_scale) \
				.add_integer('noisedepth', texture.noise_depth)# \
				#.add_float('nabla', texture.nabla)
	
	if texture.type == 'DISTORTED_NOISE':
		lux_tex_name = 'blender_distortednoise'
		paramset.add_string('type', texture.noise_distortion.lower()) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('distamount', texture.distortion) \
				.add_float('noisesize', texture.noise_scale) \
				.add_float('nabla', texture.nabla)
	
	if texture.type == 'MAGIC':
		paramset.add_integer('noisedepth', texture.noise_depth) \
				.add_float('turbulence', texture.turbulence)
	
	if texture.type == 'MARBLE':
		paramset.add_string('type', texture.marble_type.lower() ) \
				.add_string('noisetype', texture.noise_type.lower() ) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_string('noisebasis2', texture.noisebasis_2.lower() ) \
				.add_float('noisesize', texture.noise_scale) \
				.add_float('turbulence', texture.turbulence) \
				.add_integer('noisedepth', texture.noise_depth)# \
				#.add_float('nabla', texture.nabla)
	
	if texture.type == 'MUSGRAVE':
		paramset.add_string('type', texture.musgrave_type.lower() ) \
				.add_float('h', texture.dimension_max) \
				.add_float('lacu', texture.lacunarity) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('noisesize', texture.noise_scale) \
				.add_float('octs', texture.octaves)# \
				#.add_float('nabla', texture.nabla)
	
	# NOISE shows no params ?
	
	if texture.type == 'STUCCI':
		paramset.add_string('type', texture.stucci_type.lower() ) \
				.add_string('noisetype', texture.noise_type.lower() ) \
				.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_float('noisesize', texture.noise_scale) \
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
				.add_float('minkovsky_exp', texture.minkovsky_exponent) \
				.add_float('noisesize', texture.noise_scale) \
				.add_float('nabla', texture.nabla) \
				.add_float('w1', texture.weight_1) \
				.add_float('w2', texture.weight_2) \
				.add_float('w3', texture.weight_3) \
				.add_float('w4', texture.weight_4)
	
	if texture.type == 'WOOD':
		paramset.add_string('noisebasis', texture.noise_basis.lower() ) \
				.add_string('noisebasis2', texture.noisebasis_2.lower() ) \
				.add_float('noisesize', texture.noise_scale) \
				.add_string('noisetype', texture.noise_type.lower() ) \
				.add_float('turbulence', texture.turbulence) \
				.add_string('type', texture.wood_type.lower() )# \
				#.add_float('nabla', texture.nabla)
	
	# Translate Blender Image/movie into lux tex
	if texture.type == 'IMAGE' and texture.image and texture.image.source in ['GENERATED', 'FILE']:
		if texture.image.source == 'GENERATED':
			tex_image = 'luxblend_baked_image_%s.png' % bpy.path.clean_name(texture.name)
			texture.image.save_render(tex_image, scene)
		
		if texture.image.source == 'FILE':
			if texture.library is not None:
				f_path = efutil.filesystem_path(bpy.path.abspath( texture.image.filepath, texture.library.filepath))
			else:
				f_path = efutil.filesystem_path(texture.image.filepath)
			if not os.path.exists(f_path):
				raise Exception('Image referenced in blender texture %s doesn\'t exist: %s' % (texture.name, f_path))
			tex_image = efutil.path_relative_to_export(f_path)
		
		lux_tex_name = 'imagemap'
		variant = 'color'
		paramset.add_string('filename', tex_image)
		paramset.add_float('gamma', 2.2)
		mapping_type = '2D'
	
	
	if mapping_type == '3D':
		paramset.update( texture.luxrender_texture.luxrender_tex_transform.get_paramset(scene) )
	else:
		paramset.update( texture.luxrender_texture.luxrender_tex_mapping.get_paramset(scene) )
	
	return variant, lux_tex_name, paramset

def value_transform_passthrough(val):
	return val

def get_texture_from_scene(scene, tex_name):
	
	for tex_slot in scene.world.texture_slots:
		if tex_slot != None and tex_slot.texture != None and tex_slot.texture.name == tex_name:
			return tex_slot.texture
	for obj in scene.objects:
		for mat_slot in obj.material_slots:
			if mat_slot != None and mat_slot.material != None:
				for tex_slot in mat_slot.material.texture_slots:
					if tex_slot != None and tex_slot.texture != None and tex_slot.texture.name == tex_name:
						return tex_slot.texture
		if obj.type == 'LAMP':
			for tex_slot in obj.data.texture_slots:
				if tex_slot != None and tex_slot.texture != None and tex_slot.texture.name == tex_name:
					return tex_slot.texture
	
	# Last but not least, look in global bpy.data
	if tex_name in bpy.data.textures:
		return bpy.data.textures[tex_name]
	
	LuxLog('Failed to find Texture "%s" in Scene "%s"' % (tex_name, scene.name))
	return False

def add_texture_parameter(lux_context, lux_prop_name, variant, property_group, value_transform_function=None):
	'''
	lux_context				pylux.Context - like object
	lux_prop_name			LuxRender material/texture parameter name
	variant					Required variant: 'float' or 'color' or 'fresnel'
	property_group			luxrender_material or luxrender_texture IDPropertyGroup FOR THE CONTAINING MATERIAL/TEXTURE
	
	Either insert a float parameter or a float texture reference, depending on setup
	
	Returns					ParamSet
	'''
	params = ParamSet()
	
	if hasattr(property_group, '%s_use%stexture' % (lux_prop_name, variant)):
		
		export_param_name = getattr(property_group, lux_prop_name)
		
		if value_transform_function == None:
			value_transform_function = value_transform_passthrough
		
		if getattr(property_group, '%s_use%stexture' % (lux_prop_name, variant)):
			texture_name = getattr(property_group, '%s_%stexturename' % (lux_prop_name, variant))
			if texture_name != '':
				texture = get_texture_from_scene(LuxManager.CurrentScene, texture_name)
				
				if texture != False:
					if texture.luxrender_texture.type != 'BLENDER':
						tex_luxrender_texture = texture.luxrender_texture
						lux_tex_variant, paramset = tex_luxrender_texture.get_paramset(LuxManager.CurrentScene, texture)
						if lux_tex_variant == variant:
							ExportedTextures.texture(lux_context, texture_name, variant, tex_luxrender_texture.type, paramset)
						else:
							LuxLog('WARNING: Texture %s is wrong variant; needed %s, got %s' % (lux_prop_name, variant, lux_tex_variant))
					else:
						lux_tex_variant, lux_tex_name, paramset = convert_texture(LuxManager.CurrentScene, texture)
						if lux_tex_variant == variant:
							ExportedTextures.texture(lux_context, texture_name, lux_tex_variant, lux_tex_name, paramset)
						else:
							LuxLog('WARNING: Texture %s is wrong variant; needed %s, got %s' % (lux_prop_name, variant, lux_tex_variant))
					
					if hasattr(property_group, '%s_multiplyfloat' % lux_prop_name) and getattr(property_group, '%s_multiplyfloat' % lux_prop_name):
						sv = ExportedTextures.next_scale_value()
						ExportedTextures.texture(
							lux_context,
							'%s_scaled_%i' % (texture_name, sv),
							variant,
							'scale',
							ParamSet() \
								.add_float('tex1', float(getattr(property_group, '%s_floatvalue' % lux_prop_name))) \
								.add_texture('tex2', texture_name)
						)
						texture_name += '_scaled_%i' % sv
					
					if hasattr(property_group, '%s_multiplycolor' % lux_prop_name) and getattr(property_group, '%s_multiplycolor' % lux_prop_name):
						sv = ExportedTextures.next_scale_value()
						ExportedTextures.texture(
							lux_context,
							'%s_scaled_%i' % (texture_name, sv),
							variant,
							'scale',
							ParamSet() \
								.add_color(
									'tex1',
									[float(value_transform_function(i)) for i in getattr(property_group, '%s_color' % lux_prop_name)]
								) \
								.add_texture('tex2', texture_name)
						)
						texture_name += '_scaled_%i' % sv
					
					ExportedTextures.export_new(lux_context)
					
					params.add_texture(
						export_param_name,
						texture_name
					)
					
			elif export_param_name not in ['bumpmap', 'displacementmap']:
				LuxLog('WARNING: Unassigned %s texture slot %s' % (variant, export_param_name))
		else:
			if variant == 'float':
				fval = float(getattr(property_group, '%s_floatvalue' % lux_prop_name))
				if not (getattr(property_group, '%s_ignorezero' % lux_prop_name) and fval==0.0):
					params.add_float(
						export_param_name,
						fval
					)
			elif variant == 'color':
				params.add_color(
					export_param_name,
					[float(value_transform_function(i)) for i in getattr(property_group, '%s_color' % lux_prop_name)]
				)
			elif variant == 'fresnel':
				fval = float(getattr(property_group, '%s_fresnelvalue' % lux_prop_name))
				params.add_float(
					export_param_name,
					fval
				)
	else:
		LuxLog('WARNING: Texture %s is unsupported variant; needed %s' % (lux_prop_name, variant))
	
	return params

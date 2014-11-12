# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli
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
import bpy, os
from ..extensions_framework import util as efutil
from symbol import except_clause
import math
import mathutils

from .. import pyluxcore
from ..outputs import LuxManager, LuxLog
from ..outputs.luxcore_api import ToValidLuxCoreName
from ..export import get_worldscale
from ..export.materials import get_texture_from_scene

class BlenderSceneConverter(object):
	
	scalers_count = 0
	# Amount of output channels (AOVs)
	outputCounter = 0
	material_id_mask_counter = 0
	by_material_id_counter = 0
	
	@staticmethod
	def next_scale_value():
		BlenderSceneConverter.scalers_count+=1
		return BlenderSceneConverter.scalers_count
	
	@staticmethod
	def clear():
		BlenderSceneConverter.scalers_count = 0
	
	def __init__(self, blScene):
		LuxManager.SetCurrentScene(blScene)

		self.blScene = blScene
		self.lcScene = pyluxcore.Scene()
		self.scnProps = pyluxcore.Properties()
		self.cfgProps = pyluxcore.Properties()
		
		self.materialsCache = set()
		self.texturesCache = set()
	
	def createChannelOutputString(self, channelName, id = -1):
		'''
		Creates a config string for LuxCore AOV output
		'''
		
		# the OpenCL engines only support 1 MATERIAL_ID_MASK and 1 BY_MATERIAL_ID channel
		engine = self.blScene.luxcore_enginesettings.renderengine_type
		if engine in ['BIASPATHOCL', 'PATHOCL']:
			if channelName == 'MATERIAL_ID_MASK':
				if self.material_id_mask_counter == 0:
					self.material_id_mask_counter += 1
				else:
					# don't create the output channel
					return 
				
			elif channelName == 'BY_MATERIAL_ID':
				if self.by_material_id_counter == 0:
					self.by_material_id_counter += 1
				else:
					# don't create the output channel
					return 
		
		self.outputCounter += 1
		
		# list of channels that don't use a HDR format
		LDR_channels = ['RGB_TONEMAPPED', 'RGBA_TONEMAPPED', 'ALPHA', 'MATERIAL_ID', 'DIRECT_SHADOW_MASK', 'INDIRECT_SHADOW_MASK', 'MATERIAL_ID_MASK', 'BY_MATERIAL_ID']
		
		# channel type (e.g. "film.outputs.1.type")
		outputStringType = 'film.outputs.' + str(self.outputCounter) + '.type'
		self.cfgProps.Set(pyluxcore.Property(outputStringType, [channelName]))
		
		# output filename (e.g. "film.outputs.1.filename")
		suffix = ('.png' if (channelName in LDR_channels) else '.exr')
		outputStringFilename = 'film.outputs.' + str(self.outputCounter) + '.filename'
		self.cfgProps.Set(pyluxcore.Property(outputStringFilename, [channelName + suffix]))
		
		# output id
		if id != -1:
			outputStringId = 'film.outputs.' + str(self.outputCounter) + '.id'
			self.cfgProps.Set(pyluxcore.Property(outputStringId, [id]))
	
	def ConvertObjectGeometry(self, obj):
		try:
			mesh_definitions = []

			if obj.hide_render:
				return mesh_definitions

			mesh = obj.to_mesh(self.blScene, True, 'RENDER')
			if mesh is None:
				LuxLog('Cannot create render/export object: %s' % obj.name)
				return mesh_definitions

			mesh.transform(obj.matrix_world)
			mesh.update(calc_tessface = True)

			# Collate faces by mat index
			ffaces_mats = {}
			mesh_faces = mesh.tessfaces
			for f in mesh_faces:
				mi = f.material_index
				if mi not in ffaces_mats.keys():
					ffaces_mats[mi] = []
				ffaces_mats[mi].append(f)
			material_indices = ffaces_mats.keys()

			number_of_mats = len(mesh.materials)
			if number_of_mats > 0:
				iterator_range = range(number_of_mats)
			else:
				iterator_range = [0]

			for i in iterator_range:
				try:
					if i not in material_indices:
						continue

					mesh_name = '%s-%s_m%03d' % (obj.data.name, self.blScene.name, i)

					uv_textures = mesh.tessface_uv_textures
					if len(uv_textures) > 0:
						if uv_textures.active and uv_textures.active.data:
							uv_layer = uv_textures.active.data
					else:
						uv_layer = None

					# Export data
					points = []
					normals = []
					uvs = []
					face_vert_indices = []		# List of face vert indices

					# Caches
					vert_vno_indices = {}		# Mapping of vert index to exported vert index for verts with vert normals
					vert_use_vno = set()		# Set of vert indices that use vert normals

					vert_index = 0				# Exported vert index
					for face in ffaces_mats[i]:
						fvi = []
						for j, vertex in enumerate(face.vertices):
							v = mesh.vertices[vertex]

							if face.use_smooth:
								if uv_layer:
									vert_data = (v.co[:], v.normal[:], uv_layer[face.index].uv[j][:])
								else:
									vert_data = (v.co[:], v.normal[:], tuple())

								if vert_data not in vert_use_vno:
									vert_use_vno.add(vert_data)

									points.append(vert_data[0])
									normals.append(vert_data[1])
									uvs.append(vert_data[2])

									vert_vno_indices[vert_data] = vert_index
									fvi.append(vert_index)

									vert_index += 1
								else:
									fvi.append(vert_vno_indices[vert_data])

							else:
								# all face-vert-co-no are unique, we cannot
								# cache them
								points.append(v.co[:])
								normals.append(face.normal[:])
								if uv_layer:
									uvs.append(uv_layer[face.index].uv[j][:])

								fvi.append(vert_index)

								vert_index += 1

						# For Lux, we need to triangulate quad faces
						face_vert_indices.append(tuple(fvi[0:3]))
						if len(fvi) == 4:
							face_vert_indices.append((fvi[0], fvi[2], fvi[3]))

					del vert_vno_indices
					del vert_use_vno

					# Define a new mesh
					lcObjName = ToValidLuxCoreName(mesh_name)
					self.lcScene.DefineMesh('Mesh-' + lcObjName, points, face_vert_indices, normals, uvs if uv_layer else None, None, None)				
					mesh_definitions.append((lcObjName, i))

				except Exception as err:
					LuxLog('Mesh export failed, skipping this mesh:\n%s' % err)

			del ffaces_mats
			bpy.data.meshes.remove(mesh)

			return mesh_definitions;

		except Exception as err:
			LuxLog('Object export failed, skipping this object:\n%s' % err)
			return []

	def ConvertMapping(self, prefix, texture):
		# Note 2DMapping is used for: bilerp, checkerboard(dimension == 2), dots, imagemap, normalmap, uv, uvmask
		# Blender - image
		luxMapping = getattr(texture.luxrender_texture, 'luxrender_tex_mapping')
		
		if luxMapping.type == 'uv':
			self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.type', ['uvmapping2d']))
			self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.uvscale', [luxMapping.uscale, luxMapping.vscale * - 1.0]))
			if luxMapping.center_map ==  False:
				self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.uvdelta', [luxMapping.udelta, luxMapping.vdelta + 1.0]))
			else:
				self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.uvdelta', [
					luxMapping.udelta + 0.5 * (1.0 - luxMapping.uscale), luxMapping.vdelta * - 1.0 + 1.0 - (0.5 * (1.0 - luxMapping.vscale))]))
		else:
			raise Exception('Unsupported mapping for texture: ' + texture.name)

	def ConvertTransform(self, prefix, texture):
	# Note 3DMapping is used for: brick, checkerboard(dimension == 3), cloud', densitygrid, exponential, fbm', marble', windy, wrinkled
	# BLENDER - CLOUDS,DISTORTED_NOISE,MAGIC,MARBLE, MUSGRAVE,STUCCI,VORONOI, WOOD
		luxTransform = getattr(texture.luxrender_texture, 'luxrender_tex_transform')

		if luxTransform.coordinates == 'uv':
			self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.type', ['uvmapping3d']))
		elif luxTransform.coordinates == 'global':
			self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.type', ['globalmapping3d']))
		else:
			raise Exception('Unsupported mapping for texture: ' + texture.name)

		luxTranslate = getattr(texture.luxrender_texture.luxrender_tex_transform, 'translate')
		luxScale = getattr(texture.luxrender_texture.luxrender_tex_transform, 'scale')
		luxRotate = getattr(texture.luxrender_texture.luxrender_tex_transform, 'rotate')

		# create a location matrix
		tex_loc = mathutils.Matrix.Translation((luxTranslate))
		
		# create an identitiy matrix
		tex_sca0 = mathutils.Matrix.Scale((luxScale[0]), 4)
		tex_sca1 = mathutils.Matrix.Scale((luxScale[1]), 4)
		tex_sca2 = mathutils.Matrix.Scale((luxScale[2]), 4)
		tex_sca = tex_sca0 * tex_sca1 * tex_sca2

		# create a rotation matrix
		tex_rot0 = mathutils.Matrix.Rotation(math.radians(luxRotate[0]), 4, 'X')
		tex_rot1 = mathutils.Matrix.Rotation(math.radians(luxRotate[1]), 4, 'Y')
		tex_rot2 = mathutils.Matrix.Rotation(math.radians(luxRotate[2]), 4, 'Z')
		tex_rot = tex_rot0 * tex_rot1 * tex_rot2
		
		# combine transformations
		tex_out = tex_loc * tex_sca * tex_rot
		
		str_matrix = [tex_out[0][0], tex_out[0][1], tex_out[0][2], tex_out[0][3],
					  tex_out[1][0], tex_out[1][1], tex_out[1][2], tex_out[1][3],
					  tex_out[2][0], tex_out[2][1], tex_out[2][2], tex_out[2][3],
					  tex_out[3][0], tex_out[3][1], tex_out[3][2], tex_out[3][3]]

		f_matrix = []
		for item in str_matrix:
			f_matrix.append(item)

		self.scnProps.Set(pyluxcore.Property(prefix + '.mapping.transformation', f_matrix))

	def ConvertTexture(self, texture):
		texType = texture.luxrender_texture.type
		
		props = pyluxcore.Properties()
		
		if texType == 'BLENDER':
			texName = ToValidLuxCoreName(texture.name)
			bl_texType = getattr(texture, 'type')

			prefix = 'scene.textures.' + texName
			####################################################################
			# BLEND
			####################################################################
			if bl_texType == 'BLEND':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_blend']))
				props.Set(pyluxcore.Property(prefix + '.progressiontype', ''.join(str(i).lower() for i in getattr(texture, 'progression'))))
				props.Set(pyluxcore.Property(prefix + '.direction', ''.join(str(i).lower() for i in getattr(texture, 'use_flip_axis'))))
			####################################################################
			# CLOUDS
			####################################################################
			elif bl_texType == 'CLOUDS':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_clouds']))
				props.Set(pyluxcore.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
				props.Set(pyluxcore.Property(prefix + '.noisebasis', ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
				props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
				props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
			####################################################################
			# Distorted Noise
			####################################################################
			elif bl_texType == 'DISTORTED_NOISE':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_distortednoise']))
				props.Set(pyluxcore.Property(prefix + '.noise_distortion', ''.join(str(i).lower() for i in getattr(texture, 'noise_distortion'))))
				props.Set(pyluxcore.Property(prefix + '.noisebasis', ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
				props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
				props.Set(pyluxcore.Property(prefix + '.distortion', [float(texture.distortion)]))
			####################################################################
			# MAGIC
			####################################################################
			elif bl_texType == 'MAGIC':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_magic']))
				props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
				props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
			####################################################################
			# MARBLE
			####################################################################
			elif bl_texType == 'MARBLE':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_marble']))
				props.Set(pyluxcore.Property(prefix + '.marbletype', ''.join(str(i).lower() for i in getattr(texture, 'marble_type'))))
				props.Set(pyluxcore.Property(prefix + '.noisebasis', ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
				props.Set(pyluxcore.Property(prefix + '.noisebasis2', ''.join(str(i).lower() for i in getattr(texture, 'noise_basis_2'))))
				props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
				props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
				props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
				props.Set(pyluxcore.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
			####################################################################
			# MUSGRAVE
			####################################################################
			elif bl_texType == 'MUSGRAVE':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_musgrave']))
				props.Set(pyluxcore.Property(prefix + '.musgravetype', ''.join(str(i).lower() for i in getattr(texture, 'musgrave_type'))))
				props.Set(pyluxcore.Property(prefix + '.noisebasis', ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
				props.Set(pyluxcore.Property(prefix + '.dimension', [float(texture.dimension_max)]))
				props.Set(pyluxcore.Property(prefix + '.intensity', [float(texture.noise_intensity)]))
				props.Set(pyluxcore.Property(prefix + '.lacunarity', [float(texture.lacunarity)]))
				props.Set(pyluxcore.Property(prefix + '.offset', [float(texture.offset)]))
				props.Set(pyluxcore.Property(prefix + '.gain', [float(texture.gain)]))
				props.Set(pyluxcore.Property(prefix + '.octaves', [float(texture.octaves)]))
				props.Set(pyluxcore.Property(prefix + '.dimension', [float(texture.noise_scale)]))
				props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
#				props.Set(pyluxcore.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type')))) # not in blender !
			####################################################################
			# NOISE
			####################################################################
			elif bl_texType == 'NOISE':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_noise']))
				props.Set(pyluxcore.Property(prefix + '.noisedepth', [float(texture.noise_depth)]))
			####################################################################
			# STUCCI
			####################################################################
			elif bl_texType == 'STUCCI':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_stucci']))
				props.Set(pyluxcore.Property(prefix + '.stuccitype', ''.join(str(i).lower() for i in getattr(texture, 'stucci_type'))))
				props.Set(pyluxcore.Property(prefix + '.noisebasis', ''.join(str(i).lower() for i in getattr(texture, 'noise_basis'))))
				props.Set(pyluxcore.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
				props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
				props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
			####################################################################
			# WOOD
			####################################################################
			elif bl_texType == 'WOOD':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_wood']))
				props.Set(pyluxcore.Property(prefix + '.woodtype', ''.join(str(i).lower() for i in getattr(texture, 'wood_type'))))
				props.Set(pyluxcore.Property(prefix + '.noisebasis2', ''.join(str(i).lower() for i in getattr(texture, 'noise_basis_2'))))
				props.Set(pyluxcore.Property(prefix + '.noisetype', ''.join(str(i).lower() for i in getattr(texture, 'noise_type'))))
				props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
				props.Set(pyluxcore.Property(prefix + '.turbulence', [float(texture.turbulence)]))
			####################################################################
			# VORONOI
			####################################################################
			elif bl_texType == 'VORONOI':
				props.Set(pyluxcore.Property(prefix + '.type', ['blender_voronoi']))
				props.Set(pyluxcore.Property(prefix + '.dismetric', ''.join(str(i).lower() for i in getattr(texture, 'distance_metric'))))
#				props.Set(pyluxcore.Property(prefix + '.colormode', ''.join(str(i).lower() for i in getattr(texture, 'color_mode')))) # not yet in luxcore
				props.Set(pyluxcore.Property(prefix + '.intensity', [float(texture.noise_intensity)]))
				props.Set(pyluxcore.Property(prefix + '.exponent', [float(texture.minkovsky_exponent)]))
				props.Set(pyluxcore.Property(prefix + '.w1', [float(texture.weight_1)]))
				props.Set(pyluxcore.Property(prefix + '.w2', [float(texture.weight_2)]))
				props.Set(pyluxcore.Property(prefix + '.w3', [float(texture.weight_3)]))
				props.Set(pyluxcore.Property(prefix + '.w4', [float(texture.weight_4)]))
				props.Set(pyluxcore.Property(prefix + '.noisesize', [float(texture.noise_scale)]))
			####################################################################
			# IMAGE/MOVIE/SEQUENCE
			####################################################################
			elif bl_texType == 'IMAGE' and texture.image and texture.image.source in ['GENERATED', 'FILE', 'SEQUENCE']:
				extract_path = os.path.join(
											efutil.scene_filename(),
											bpy.path.clean_name(self.blScene.name),
											'%05d' % self.blScene.frame_current
											)
											
				if texture.image.source == 'GENERATED':
					tex_image = 'luxblend_baked_image_%s.%s' % (bpy.path.clean_name(texture.name), self.blScene.render.image_settings.file_format)
					tex_image = os.path.join(extract_path, tex_image)
					texture.image.save_render(tex_image, self.blScene)
				
				if texture.image.source == 'FILE':
					if texture.image.packed_file:
						tex_image = 'luxblend_extracted_image_%s.%s' % (bpy.path.clean_name(texture.name), self.blScene.render.image_settings.file_format)
						tex_image = os.path.join(extract_path, tex_image)
						texture.image.save_render(tex_image, self.blScene)
					else:
						if texture.library is not None:
							f_path = efutil.filesystem_path(bpy.path.abspath( texture.image.filepath, texture.library.filepath))
						else:
							f_path = efutil.filesystem_path(texture.image.filepath)
						if not os.path.exists(f_path):
							raise Exception('Image referenced in blender texture %s doesn\'t exist: %s' % (texture.name, f_path))
						tex_image = efutil.filesystem_path(f_path)

				if texture.image.source == 'SEQUENCE':
					if texture.image.packed_file:
						tex_image = 'luxblend_extracted_image_%s.%s' % (bpy.path.clean_name(texture.name), self.blScene.render.image_settings.file_format)
						tex_image = os.path.join(extract_path, tex_image)
						texture.image.save_render(tex_image, self.blScene)
					else:
						# sequence params from blender
						sequence = bpy.data.textures[(texture.name).replace('.001', '')].image_user # remove tex_preview extension to avoid error
						seqframes = sequence.frame_duration
						seqoffset = sequence.frame_offset
						seqstartframe = sequence.frame_start # the global frame at which the imagesequence starts
						seqcyclic = sequence.use_cyclic
						currentframe = self.blScene.frame_current
						
						if texture.library is not None:
							f_path = efutil.filesystem_path(bpy.path.abspath( texture.image.filepath, texture.library.filepath))
						else:
							f_path = efutil.filesystem_path(texture.image.filepath)
						
						if currentframe < seqstartframe:
							fnumber = 1 + seqoffset
						else:
							fnumber = currentframe - (seqstartframe-1) + seqoffset
						
						if fnumber > seqframes:
							if seqcyclic == False:
								fnumber = seqframes
							else:
								fnumber = (currentframe - (seqstartframe-1)) % seqframes
								if fnumber == 0:
									fnumber = seqframes
					
						import re
						def get_seq_filename(number, f_path):
							m = re.findall(r'(\d+)', f_path)
							if len(m) == 0:
								return "ERR: Can't find pattern"
							
							rightmost_number = m[len(m)-1]
							seq_length = len(rightmost_number)
							
							nstr = "%i" %number
							new_seq_number = nstr.zfill(seq_length)
							
							return f_path.replace(rightmost_number, new_seq_number)
						
						f_path = get_seq_filename(fnumber, f_path)

						if not os.path.exists(f_path):
							raise Exception('Image referenced in blender texture %s doesn\'t exist: %s' % (texture.name, f_path))
						tex_image = efutil.filesystem_path(f_path)

				props.Set(pyluxcore.Property(prefix + '.file', [tex_image]))
				self.ConvertMapping(prefix, texture)
			####################################################################
			# Pararameters shared by all blender textures
			####################################################################
			props.Set(pyluxcore.Property(prefix + '.bright', [float(texture.intensity)]))
			props.Set(pyluxcore.Property(prefix + '.contrast', [float(texture.contrast)]))
			if bl_texType != 'IMAGE':
				self.ConvertTransform(prefix, texture)

			self.texturesCache.add(texName)
			return texName

		if texType != 'BLENDER':
			texName = ToValidLuxCoreName(texture.name)
			luxTex = getattr(texture.luxrender_texture, 'luxrender_tex_' + texType)

			prefix = 'scene.textures.' + texName
			####################################################################
			# Imagemap
			####################################################################
			if texType == 'imagemap':
				props.Set(pyluxcore.Property(prefix + '.file', [luxTex.filename]))
				props.Set(pyluxcore.Property(prefix + '.gamma', [float(luxTex.gamma)]))
				props.Set(pyluxcore.Property(prefix + '.gain', [float(luxTex.gain)]))
				self.ConvertMapping(prefix, texture)
			####################################################################
			# Normalmap
			####################################################################
			elif texType == 'normalmap':
				props.Set(pyluxcore.Property(prefix + '.file', [luxTex.filename]))
				self.ConvertMapping(prefix, texture)
			####################################################################
			# Marble
			####################################################################
			elif texType == 'marble':
				props.Set(pyluxcore.Property(prefix + '.octaves', [float(luxTex.octaves)]))
				props.Set(pyluxcore.Property(prefix + '.roughness', [float(luxTex.roughness)]))
				props.Set(pyluxcore.Property(prefix + '.scale', [float(luxTex.scale)]))
				props.Set(pyluxcore.Property(prefix + '.variation', [float(luxTex.variation)]))
				self.ConvertTransform(prefix, texture)
			####################################################################
			# Mix
			####################################################################
			elif texType == 'mix':
				props.Set(pyluxcore.Property(prefix + '.amount', self.ConvertMaterialChannel(luxTex, 'amount', 'float')))
				props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
				if luxTex.variant == 'color':
					props.Set(pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'color')))
					props.Set(pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'color')))
				elif luxTex.variant == 'float':
					props.Set(pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'float')))
					props.Set(pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'float')))
				elif luxTex.variant == 'fresnel':
					props.Set(pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'fresnel')))
					props.Set(pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'fresnel')))
			####################################################################
			# Scale
			####################################################################
			elif texType == 'scale':
				props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
				if luxTex.variant == 'color':
					props.Set(pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'color')))
					props.Set(pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'color')))
				elif luxTex.variant == 'float':
					props.Set(pyluxcore.Property(prefix + '.texture1', self.ConvertMaterialChannel(luxTex, 'tex1', 'float')))
					props.Set(pyluxcore.Property(prefix + '.texture2', self.ConvertMaterialChannel(luxTex, 'tex2', 'float')))
			####################################################################
			# Brick
			####################################################################
			elif texType == 'brick':
				props.Set(pyluxcore.Property(prefix + '.variant', [(luxTex.variant)]))
				props.Set(pyluxcore.Property(prefix + '.brickbond', [(luxTex.brickbond)]))
				
				if texture.luxrender_texture.luxrender_tex_brick.brickbond in ('running', 'flemish'):
					props.Set(pyluxcore.Property(prefix + '.brickrun', [float(luxTex.brickrun)]))
				
				props.Set(pyluxcore.Property(prefix + '.mortarsize', [float(luxTex.mortarsize)]))
				props.Set(pyluxcore.Property(prefix + '.brickwidth', [float(luxTex.brickwidth)]))
				props.Set(pyluxcore.Property(prefix + '.brickdepth', [float(luxTex.brickdepth)]))
				props.Set(pyluxcore.Property(prefix + '.brickheight', [float(luxTex.brickheight)]))
					
				if luxTex.variant == 'color':
					props.Set(pyluxcore.Property(prefix + '.bricktex', self.ConvertMaterialChannel(luxTex, 'bricktex', 'color')))
					props.Set(pyluxcore.Property(prefix + '.brickmodtex', self.ConvertMaterialChannel(luxTex, 'brickmodtex', 'color')))
					props.Set(pyluxcore.Property(prefix + '.mortartex', self.ConvertMaterialChannel(luxTex, 'mortartex', 'color')))
				else:
					props.Set(pyluxcore.Property(prefix + '.bricktex', self.ConvertMaterialChannel(luxTex, 'bricktex', 'float')))
					props.Set(pyluxcore.Property(prefix + '.brickmodtex', self.ConvertMaterialChannel(luxTex, 'brickmodtex', 'float')))
					props.Set(pyluxcore.Property(prefix + '.mortartex', self.ConvertMaterialChannel(luxTex, 'mortartex', 'float')))
				self.ConvertTransform(prefix, texture)
			else:
			####################################################################
			# Fallback to exception
			####################################################################
				raise Exception('Unknown type ' + texType + 'for texture: ' + texture.name)

			if texType != 'normalmap':
				props.Set(pyluxcore.Property(prefix + '.type', self.ConvertTexType(luxTex, texType)))

			self.scnProps.Set(props)
			self.texturesCache.add(texName)
			return texName
		
		raise Exception('Unknown texture type: ' + texture.name)

	def ConvertTexType(self, luxTex, texType):
		return texType

	def ConvertMaterialChannel(self, luxMaterial, materialChannel, variant):
		if getattr(luxMaterial, materialChannel + '_use' + variant + 'texture'):
			texName = getattr(luxMaterial, '%s_%stexturename' % (materialChannel, variant))
			is_multiplied = getattr(luxMaterial, '%s_multiply%s' % (materialChannel, variant))
			validTexName = ToValidLuxCoreName(texName)
			# Check if it is an already defined texture, but texture with different multipliers must not stop here
			if validTexName in self.texturesCache and not is_multiplied:
				return validTexName
			LuxLog('Texture: ' + texName)
			
			texture = get_texture_from_scene(self.blScene, texName)
			if texture != False:
				if hasattr(luxMaterial, '%s_multiplycolor' % materialChannel) and is_multiplied:
					texName = self.ConvertTexture(texture)
					sv = BlenderSceneConverter.next_scale_value()
					sctexName = '%s_scaled_%i' % (texName, sv)
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.type', ['scale']))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture1', ' '.join(str(i) for i in (getattr(luxMaterial, materialChannel + '_color')))))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture2', ['%s'% texName]))
					return sctexName

				elif hasattr(luxMaterial, '%s_multiplyfloat' % materialChannel) and is_multiplied:
					texName = self.ConvertTexture(texture)
					sv = BlenderSceneConverter.next_scale_value()
					sctexName = '%s_scaled_%i' % (texName, sv)
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.type', ['scale']))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture1', float(getattr(luxMaterial, '%s_floatvalue' % materialChannel))))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture2', ['%s'% texName]))
					return sctexName
				elif hasattr(luxMaterial, '%s_multiplyfresnel' % materialChannel) and is_multiplied:
					texName = self.ConvertTexture(texture)
					sv = BlenderSceneConverter.next_scale_value()
					sctexName = '%s_scaled_%i' % (texName, sv)
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.type', ['scale']))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture1', float(getattr(luxMaterial, '%s_fresnelvalue' % materialChannel))))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture2', ['%s'% texName]))
					return sctexName
				
				else:
					return self.ConvertTexture(texture)
		else:
			if variant == 'float':
				return str(getattr(luxMaterial, materialChannel + '_floatvalue'))
			elif variant == 'color':
				return ' '.join(str(i) for i in getattr(luxMaterial, materialChannel + '_color'))
			elif variant == 'fresnel':
				return str(getattr(luxMaterial, materialChannel + '_fresnelvalue'))

		raise Exception('Unknown texture in channel' + materialChannel + ' for material ' + material.luxrender_material.type)
				
	def ConvertCommonChannel(self, luxMap, material, type):
		if getattr(material.luxrender_material, type +'_usefloattexture'):
			is_multiplied = getattr(material.luxrender_material, '%s_multiplyfloat' % type)
			texName = getattr(material.luxrender_material, '%s_floattexturename' % (type))
			validTexName = ToValidLuxCoreName(texName)
			# Check if it is an already defined texture, but texture with different multipliers must not stop here
			if validTexName in self.texturesCache and not is_multiplied:
				return validTexName
			LuxLog('Texture: ' + texName)
			
			texture = get_texture_from_scene(self.blScene, texName)
			if texture != False:

				if hasattr(material.luxrender_material, '%s_multiplyfloat' % type) and is_multiplied:
					texName = self.ConvertTexture(texture)
					sv = BlenderSceneConverter.next_scale_value()
					sctexName = '%s_scaled_%i' % (texName, sv)
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.type', ['scale']))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture1', float(getattr(material.luxrender_material, '%s_floatvalue' % type))))
					self.scnProps.Set(pyluxcore.Property('scene.textures.' + sctexName + '.texture2', ['%s'% texName]))
					return sctexName
				else:
					return self.ConvertTexture(texture)

	def ConvertMaterial(self, material, materials):
		try:
			if material is None:
				return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

			matIsTransparent = False
			if material.type in ['glass', 'glass2', 'null']:
				matIsTransparent == True

			if self.blScene.luxrender_testing.clay_render and matIsTransparent == False:
				return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

			matName = ToValidLuxCoreName(material.name)
			# Check if it is an already defined material
			if matName in self.materialsCache:
				return matName
			LuxLog('Material: ' + material.name)

			matType = material.luxrender_material.type
			luxMat = getattr(material.luxrender_material, 'luxrender_mat_' + matType)
			
			props = pyluxcore.Properties()
			
			prefix = 'scene.materials.' + matName
			####################################################################
			# Matte and Roughmatte
			####################################################################
			if matType == 'matte':
				sigma = self.ConvertMaterialChannel(luxMat, 'sigma', 'float')
				if sigma == '0.0':
					props.Set(pyluxcore.Property(prefix + '.type', ['matte']))
					props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
				else:
					props.Set(pyluxcore.Property(prefix + '.type', ['roughmatte']))
					props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
					props.Set(pyluxcore.Property(prefix + '.sigma', self.ConvertMaterialChannel(luxMat, 'sigma', 'float')))
			####################################################################
			# Mattetranslucent
			####################################################################
			elif matType == 'mattetranslucent':
				props.Set(pyluxcore.Property(prefix + '.type', ['mattetranslucent']))
				props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
				props.Set(pyluxcore.Property(prefix + '.kt', self.ConvertMaterialChannel(luxMat, 'Kt', 'color')))
				props.Set(pyluxcore.Property(prefix + '.sigma', self.ConvertMaterialChannel(luxMat, 'sigma', 'float')))
			####################################################################
			# Metal2
			####################################################################
			elif matType == 'metal2':
				props.Set(pyluxcore.Property(prefix + '.type', ['metal2']))
				m2_type = material.luxrender_material.luxrender_mat_metal2.metaltype
				if m2_type == 'preset':
					props.Set(pyluxcore.Property(prefix + '.preset', material.luxrender_material.luxrender_mat_metal2.preset))
				elif m2_type == 'fresnelcolor':
					props.Set(pyluxcore.Property(prefix + '.n', 'fn_dummy_tex'))
					props.Set(pyluxcore.Property(prefix + '.k', 'fk_dummy_tex'))
					props.Set(pyluxcore.Property('scene.textures.fn_dummy_tex.type', 'fresnelapproxn'))
					props.Set(pyluxcore.Property('scene.textures.fn_dummy_tex.texture', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
					props.Set(pyluxcore.Property('scene.textures.fk_dummy_tex.type', 'fresnelapproxk'))
					props.Set(pyluxcore.Property('scene.textures.fk_dummy_tex.texture', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
				#TODO: nk_data and fresneltex
				else:
					LuxLog('WARNING: Not yet supported metal2 type: %s' % m2_type)

				props.Set(pyluxcore.Property(prefix + '.uroughness', self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))
				props.Set(pyluxcore.Property(prefix + '.vroughness', self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))
			####################################################################
			# Mirror
			####################################################################
			elif matType == 'mirror':
				props.Set(pyluxcore.Property(prefix + '.type', ['mirror']))
				props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
			####################################################################
			# Glossy
			####################################################################
			elif matType == 'glossy':
				props.Set(pyluxcore.Property(prefix + '.type', ['glossy2']))
				props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
				if material.luxrender_material.luxrender_mat_glossy.useior:
					props.Set(pyluxcore.Property(prefix + '.index', self.ConvertMaterialChannel(luxMat, 'index', 'float')))
				else:
					props.Set(pyluxcore.Property(prefix + '.ks', self.ConvertMaterialChannel(luxMat, 'Ks', 'color')))
				
				props.Set(pyluxcore.Property(prefix + '.ka', self.ConvertMaterialChannel(luxMat, 'Ka', 'color')))
				props.Set(pyluxcore.Property(prefix + '.multibounce', material.luxrender_material.luxrender_mat_glossy.multibounce))
				props.Set(pyluxcore.Property(prefix + '.sigma', self.ConvertMaterialChannel(luxMat, 'sigma', 'float')))
				props.Set(pyluxcore.Property(prefix + '.d', self.ConvertMaterialChannel(luxMat, 'd', 'float')))
				props.Set(pyluxcore.Property(prefix + '.uroughness', self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))
				props.Set(pyluxcore.Property(prefix + '.vroughness', self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))
			####################################################################
			# Glass
			####################################################################
			elif matType == 'glass':
				if material.luxrender_material.luxrender_mat_glass.architectural == False:
					props.Set(pyluxcore.Property(prefix + '.type', ['glass']))
				else:
					props.Set(pyluxcore.Property(prefix + '.type', ['archglass']))
				
				props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
				props.Set(pyluxcore.Property(prefix + '.kt', self.ConvertMaterialChannel(luxMat, 'Kt', 'color')))
				props.Set(pyluxcore.Property(prefix + '.cauchyb', self.ConvertMaterialChannel(luxMat, 'cauchyb', 'float')))
				props.Set(pyluxcore.Property(prefix + '.film', self.ConvertMaterialChannel(luxMat, 'film', 'float')))
				props.Set(pyluxcore.Property(prefix + '.interiorior', self.ConvertMaterialChannel(luxMat, 'index', 'float')))
				props.Set(pyluxcore.Property(prefix + '.filmindex', self.ConvertMaterialChannel(luxMat, 'filmindex', 'float')))
			####################################################################
			# Roughlass
			####################################################################
			elif matType == 'roughglass':
				props.Set(pyluxcore.Property(prefix + '.type', ['roughglass']))
				props.Set(pyluxcore.Property(prefix + '.kr', self.ConvertMaterialChannel(luxMat, 'Kr', 'color')))
				props.Set(pyluxcore.Property(prefix + '.kt', self.ConvertMaterialChannel(luxMat, 'Kt', 'color')))
				props.Set(pyluxcore.Property(prefix + '.cauchyb', self.ConvertMaterialChannel(luxMat, 'cauchyb', 'float')))
				props.Set(pyluxcore.Property(prefix + '.interiorior', self.ConvertMaterialChannel(luxMat, 'index', 'float')))
				props.Set(pyluxcore.Property(prefix + '.uroughness', self.ConvertMaterialChannel(luxMat, 'uroughness', 'float')))
				props.Set(pyluxcore.Property(prefix + '.vroughness', self.ConvertMaterialChannel(luxMat, 'vroughness', 'float')))
			####################################################################
			# Cloth
			####################################################################
			elif matType == 'cloth':
				props.Set(pyluxcore.Property(prefix + '.type', ['cloth']))
				props.Set(pyluxcore.Property(prefix + '.preset', material.luxrender_material.luxrender_mat_cloth.presetname))
				props.Set(pyluxcore.Property(prefix + '.warp_kd', self.ConvertMaterialChannel(luxMat, 'warp_Kd', 'color')))
				props.Set(pyluxcore.Property(prefix + '.warp_ks', self.ConvertMaterialChannel(luxMat, 'warp_Ks', 'color')))
				props.Set(pyluxcore.Property(prefix + '.weft_kd', self.ConvertMaterialChannel(luxMat, 'weft_Kd', 'color')))
				props.Set(pyluxcore.Property(prefix + '.weft_ks', self.ConvertMaterialChannel(luxMat, 'weft_Ks', 'color')))
				props.Set(pyluxcore.Property(prefix + '.repeat_u', material.luxrender_material.luxrender_mat_cloth.repeat_u ))
				props.Set(pyluxcore.Property(prefix + '.repeat_v', material.luxrender_material.luxrender_mat_cloth.repeat_v ))
			####################################################################
			# Carpaint
			####################################################################
			elif matType == 'carpaint':
				props.Set(pyluxcore.Property(prefix + '.type', ['carpaint']))
				props.Set(pyluxcore.Property(prefix + '.preset', material.luxrender_material.luxrender_mat_carpaint.name))
				props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
				props.Set(pyluxcore.Property(prefix + '.ka', self.ConvertMaterialChannel(luxMat, 'Ka', 'color')))
				props.Set(pyluxcore.Property(prefix + '.ks1', self.ConvertMaterialChannel(luxMat, 'Ks1', 'color')))
				props.Set(pyluxcore.Property(prefix + '.ks2', self.ConvertMaterialChannel(luxMat, 'Ks2', 'color')))
				props.Set(pyluxcore.Property(prefix + '.ks3', self.ConvertMaterialChannel(luxMat, 'Ks3', 'color')))
				props.Set(pyluxcore.Property(prefix + '.d', self.ConvertMaterialChannel(luxMat, 'd', 'float')))
				props.Set(pyluxcore.Property(prefix + '.m1', material.luxrender_material.luxrender_mat_carpaint.M1_floatvalue))
				props.Set(pyluxcore.Property(prefix + '.m2', material.luxrender_material.luxrender_mat_carpaint.M2_floatvalue))
				props.Set(pyluxcore.Property(prefix + '.m3', material.luxrender_material.luxrender_mat_carpaint.M3_floatvalue))
				props.Set(pyluxcore.Property(prefix + '.r1', material.luxrender_material.luxrender_mat_carpaint.R1_floatvalue))
				props.Set(pyluxcore.Property(prefix + '.r2', material.luxrender_material.luxrender_mat_carpaint.R2_floatvalue))
				props.Set(pyluxcore.Property(prefix + '.r3', material.luxrender_material.luxrender_mat_carpaint.R3_floatvalue))
			####################################################################
			# Velvet
			####################################################################
			elif matType == 'velvet':
				props.Set(pyluxcore.Property(prefix + '.type', ['velvet']))
				props.Set(pyluxcore.Property(prefix + '.kd', self.ConvertMaterialChannel(luxMat, 'Kd', 'color')))
				props.Set(pyluxcore.Property(prefix + '.thickness', material.luxrender_material.luxrender_mat_velvet.thickness))
				props.Set(pyluxcore.Property(prefix + '.p1', material.luxrender_material.luxrender_mat_velvet.p1))
				props.Set(pyluxcore.Property(prefix + '.p2', material.luxrender_material.luxrender_mat_velvet.p2))
				props.Set(pyluxcore.Property(prefix + '.p3', material.luxrender_material.luxrender_mat_velvet.p3))
			####################################################################
			# Null
			####################################################################
			elif matType == 'null':
				props.Set(pyluxcore.Property(prefix + '.type', ['null']))
			####################################################################
			# Mix
			####################################################################
			elif matType == 'mix':
				if material.luxrender_material.luxrender_mat_mix.namedmaterial1_material == '' or material.luxrender_material.luxrender_mat_mix.namedmaterial2_material =='':
					return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'
				else:
					try:
						mat1 = materials[material.luxrender_material.luxrender_mat_mix.namedmaterial1_material].material
						mat1Name = self.ConvertMaterial(mat1, materials)
						mat2 = materials[material.luxrender_material.luxrender_mat_mix.namedmaterial2_material].material
						mat2Name = self.ConvertMaterial(mat2, materials)

						props.Set(pyluxcore.Property(prefix + '.type', ['mix']))
						props.Set(pyluxcore.Property(prefix + '.material1', mat1Name))
						props.Set(pyluxcore.Property(prefix + '.material2', mat2Name))
						props.Set(pyluxcore.Property(prefix + '.amount', self.ConvertMaterialChannel(luxMat, 'amount', 'float')))
					except:
						LuxLog('WARNING: unable to convert mix material: %s' % material.name)
						return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'
			####################################################################
			# Fallback
			####################################################################
			else:
				return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

			# Common material settings
			if material.luxrender_material.bumpmap_usefloattexture:
				luxMap = material.luxrender_material.bumpmap_floattexturename
				props.Set(pyluxcore.Property(prefix + '.bumptex', self.ConvertCommonChannel(luxMap, material, 'bumpmap')))
			
			if material.luxrender_material.normalmap_usefloattexture:
				luxMap = material.luxrender_material.normalmap_floattexturename
				props.Set(pyluxcore.Property(prefix + '.normaltex', self.ConvertCommonChannel(luxMap, material, 'normalmap')))


			# LuxCore specific material settings
			if material.luxcore_material.id != -1:
				props.Set(pyluxcore.Property(prefix + '.id', [material.luxcore_material.id]))
				if material.luxcore_material.create_MATERIAL_ID_MASK:
					self.createChannelOutputString('MATERIAL_ID_MASK', material.luxcore_material.id)
				if material.luxcore_material.create_BY_MATERIAL_ID:
					self.createChannelOutputString('BY_MATERIAL_ID', material.luxcore_material.id)
				
			if material.luxcore_material.emission_id != -1:
				props.Set(pyluxcore.Property(prefix + '.emission.id', [material.luxcore_material.light_id]))
			
			props.Set(pyluxcore.Property(prefix + '.samples', [material.luxcore_material.samples]))
			props.Set(pyluxcore.Property(prefix + '.emission.samples', [material.luxcore_material.emission_samples]))
			props.Set(pyluxcore.Property(prefix + '.bumpsamplingdistance', [material.luxcore_material.bumpsamplingdistance]))
			
			props.Set(pyluxcore.Property(prefix + '.visibility.indirect.diffuse.enable', material.luxcore_material.visibility_indirect_diffuse_enable))
			props.Set(pyluxcore.Property(prefix + '.visibility.indirect.glossy.enable', material.luxcore_material.visibility_indirect_glossy_enable))
			props.Set(pyluxcore.Property(prefix + '.visibility.indirect.specular.enable', material.luxcore_material.visibility_indirect_specular_enable))
			
			# LuxRender emission
			if material.luxrender_emission.use_emission:
				emit_enabled = self.blScene.luxrender_lightgroups.is_enabled(material.luxrender_emission.lightgroup)
				emit_enabled &= (material.luxrender_emission.L_color.v * material.luxrender_emission.gain) > 0.0
				if emit_enabled:
					props.Set(pyluxcore.Property(prefix + '.emission',
						self.ConvertMaterialChannel(material.luxrender_emission, 'L', 'color')))
					props.Set(pyluxcore.Property(prefix + '.emission.gain', [
						material.luxrender_emission.gain, material.luxrender_emission.gain, material.luxrender_emission.gain]))
					props.Set(pyluxcore.Property(prefix + '.emission.power', material.luxrender_emission.power))
					props.Set(pyluxcore.Property(prefix + '.emission.efficency', material.luxrender_emission.efficacy))
					
			self.scnProps.Set(props)
			self.materialsCache.add(matName)
			return matName
		except Exception as err:
			LuxLog('Material export failed, skipping material: %s\n%s' % (material.name, err))
			import traceback
			traceback.print_exc()
			return 'LUXBLEND_LUXCORE_CLAY_MATERIAL'

	def ConvertObject(self, obj):
		########################################################################
		# Convert the object geometry
		########################################################################

		meshDefinitions = []
		meshDefinitions.extend(self.ConvertObjectGeometry(obj))

		for meshDefinition in meshDefinitions:
			objName = meshDefinition[0]
			objMatIndex = meshDefinition[1]

			####################################################################
			# Convert the (main) material
			####################################################################
			
			try:
				objMat = obj.material_slots[objMatIndex].material
			except IndexError:
				objMat = None
				LuxLog('WARNING: material slot %d on object "%s" is unassigned!' % (objMatIndex + 1, obj.name))
			
			objMatName = self.ConvertMaterial(objMat, obj.material_slots)

			####################################################################
			# Create the mesh
			####################################################################
			
			self.scnProps.Set(pyluxcore.Property('scene.objects.' + objName + '.material', [objMatName]))
			self.scnProps.Set(pyluxcore.Property('scene.objects.' + objName + '.ply', ['Mesh-' + objName]))

	def ConvertCamera(self, imageWidth = None, imageHeight = None):
		blCamera = self.blScene.camera
		blCameraData = blCamera.data
		luxCamera = blCameraData.luxrender_camera

		if (not imageWidth is None) and (not imageHeight is None):
			xr = imageWidth
			yr = imageHeight
		else:
			xr, yr = luxCamera.luxrender_film.resolution(self.blScene)

		lookat = luxCamera.lookAt(blCamera)
		orig = list(lookat[0:3])
		target = list(lookat[3:6])
		up = list(lookat[6:9])
		self.scnProps.Set(pyluxcore.Property('scene.camera.lookat.orig', orig))
		self.scnProps.Set(pyluxcore.Property('scene.camera.lookat.target', target))
		self.scnProps.Set(pyluxcore.Property('scene.camera.up', up))

		if blCameraData.type == 'PERSP' and luxCamera.type == 'perspective':
			self.scnProps.Set(pyluxcore.Property('scene.camera.fieldofview', [math.degrees(blCameraData.angle)]))
		
		self.scnProps.Set(pyluxcore.Property("scene.camera.screenwindow", luxCamera.screenwindow(xr, yr, self.blScene, blCameraData)));
		
		if luxCamera.use_dof:
			# Do not world-scale this, it is already in meters !
			self.scnProps.Set(pyluxcore.Property("scene.camera.lensradius", (blCameraData.lens / 1000.0) / (2.0 * luxCamera.fstop)));
		
		ws = get_worldscale(as_scalematrix = False)
		
		if luxCamera.use_dof:
			if blCameraData.dof_object is not None:
				self.scnProps.Set(pyluxcore.Property("scene.camera.focaldistance", ws * ((blCamera.location - blCameraData.dof_object.location).length)));
			elif blCameraData.dof_distance > 0:
				self.scnProps.Set(pyluxcore.Property("scene.camera.focaldistance"), ws * blCameraData.dof_distance);
			
		if luxCamera.use_clipping:
			self.scnProps.Set(pyluxcore.Property("scene.camera.cliphither", ws * blCameraData.clip_start));
			self.scnProps.Set(pyluxcore.Property("scene.camera.clipyon", ws * blCameraData.clip_end));

	def ConvertEngineSettings(self):
		engine = self.blScene.luxcore_enginesettings.renderengine_type
		if len(engine) == 0:
			engine = 'PATHCPU'
		self.cfgProps.Set(pyluxcore.Property('renderengine.type', [engine]))
		
		if engine == 'BIASPATHCPU' or engine == 'BIASPATHOCL':
			self.cfgProps.Set(pyluxcore.Property('tile.size', [self.blScene.luxcore_enginesettings.tile_size]))
			self.cfgProps.Set(pyluxcore.Property('tile.multipass.enable', [self.blScene.luxcore_enginesettings.tile_multipass_enable]))
			self.cfgProps.Set(pyluxcore.Property('tile.multipass.convergencetest.threshold', [self.blScene.luxcore_enginesettings.tile_multipass_convergencetest_threshold]))
			self.cfgProps.Set(pyluxcore.Property('tile.multipass.convergencetest.threshold.reduction', [self.blScene.luxcore_enginesettings.tile_multipass_convergencetest_threshold_reduction]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.aa.size', [self.blScene.luxcore_enginesettings.biaspath_sampling_aa_size]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.diffuse.size', [self.blScene.luxcore_enginesettings.biaspath_sampling_diffuse_size]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.glossy.size', [self.blScene.luxcore_enginesettings.biaspath_sampling_glossy_size]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.sampling.specular.size', [self.blScene.luxcore_enginesettings.biaspath_sampling_specular_size]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.total', [self.blScene.luxcore_enginesettings.biaspath_pathdepth_total]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.diffuse', [self.blScene.luxcore_enginesettings.biaspath_pathdepth_diffuse]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.glossy', [self.blScene.luxcore_enginesettings.biaspath_pathdepth_glossy]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.pathdepth.specular', [self.blScene.luxcore_enginesettings.biaspath_pathdepth_specular]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.clamping.radiance.maxvalue', [self.blScene.luxcore_enginesettings.biaspath_clamping_radiance_maxvalue]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.clamping.pdf.value', [self.blScene.luxcore_enginesettings.biaspath_clamping_pdf_value]))
			self.cfgProps.Set(pyluxcore.Property('biaspath.lights.samplingstrategy.type', [self.blScene.luxcore_enginesettings.biaspath_lights_samplingstrategy_type]))
		
		# CPU settings
		if (self.blScene.luxcore_enginesettings.native_threads_count > 0):
			self.cfgProps.Set(pyluxcore.Property('native.threads.count', [self.blScene.luxcore_enginesettings.native_threads_count]))
		
		# OpenCL settings
		if len(self.blScene.luxcore_enginesettings.luxcore_opencl_devices) > 0:
			dev_string = ''
			for dev_index in range(len(self.blScene.luxcore_enginesettings.luxcore_opencl_devices)):
				dev = self.blScene.luxcore_enginesettings.luxcore_opencl_devices[dev_index]
				dev_string += '1' if dev.opencl_device_enabled else '0'

			self.cfgProps.Set(pyluxcore.Property('opencl.devices.select', [dev_string]))
		
		# Accelerator settings
		self.cfgProps.Set(pyluxcore.Property('accelerator.instances.enable', [False]))
		
	def Convert(self, imageWidth = None, imageHeight = None):
		########################################################################
		# Convert camera definition
		########################################################################

		self.ConvertCamera(imageWidth = imageWidth, imageHeight = imageHeight)

		########################################################################
		# Add a sky definition
		########################################################################

		self.scnProps.Set(pyluxcore.Property('scene.lights.sunlight.type', ['sun']))
		self.scnProps.Set(pyluxcore.Property('scene.lights.sunlight.gain', [1.0, 1.0, 1.0]))
		self.scnProps.Set(pyluxcore.Property('scene.lights.sunlight.dir', [0.166974, -0.59908, 0.783085]))
		self.scnProps.Set(pyluxcore.Property('scene.lights.skylight.type', ['sky']))
		self.scnProps.Set(pyluxcore.Property('scene.lights.skylight.gain', [1.0, 1.0, 1.0]))
		self.scnProps.Set(pyluxcore.Property('scene.lights.skylight.dir', [0.166974, -0.59908, 0.783085]))

		########################################################################
		# Add dummy material
		########################################################################

		self.scnProps.Set(pyluxcore.Property('scene.materials.LUXBLEND_LUXCORE_CLAY_MATERIAL.type', ['matte']))
		self.scnProps.Set(pyluxcore.Property('scene.materials.LUXBLEND_LUXCORE_CLAY_MATERIAL.kd', '0.7 0.7 0.7'))

		########################################################################
		# Convert all objects
		########################################################################

		for obj in self.blScene.objects:
			LuxLog('Object: %s' % obj.name)
			self.ConvertObject(obj)

		# Debug information
		LuxLog('Scene Properties:')
		LuxLog(str(self.scnProps))

		self.lcScene.Parse(self.scnProps)

		########################################################################
		# Create the configuration
		########################################################################

		self.ConvertEngineSettings()

		# Film
		if (not imageWidth is None) and (not imageHeight is None):
			filmWidth = imageWidth
			filmHeight = imageHeight
		else:
			filmWidth, filmHeight = self.blScene.camera.data.luxrender_camera.luxrender_film.resolution(self.blScene)

		self.cfgProps.Set(pyluxcore.Property('film.width', [filmWidth]))
		self.cfgProps.Set(pyluxcore.Property('film.height', [filmHeight]))

		# Image Pipeline
		self.cfgProps.Set(pyluxcore.Property('film.imagepipeline.0.type', ['TONEMAP_AUTOLINEAR']))
		self.cfgProps.Set(pyluxcore.Property('film.imagepipeline.1.type', ['GAMMA_CORRECTION']))
		self.cfgProps.Set(pyluxcore.Property('film.imagepipeline.1.value', [2.2]))
#		self.cfgProps.Set(pyluxcore.Property('film.alphachannel.enable', ['1']))
		
		# Configure AOV output
		channels = self.blScene.luxrender_channels
		
		if channels.RGB:
			self.createChannelOutputString('RGB')
		if channels.RGBA:
			self.createChannelOutputString('RGBA')
		if channels.RGB_TONEMAPPED:
			self.createChannelOutputString('RGB_TONEMAPPED')
		if channels.RGBA_TONEMAPPED:
			self.createChannelOutputString('RGBA_TONEMAPPED')
		if channels.ALPHA:
			self.createChannelOutputString('ALPHA')
		if channels.DEPTH:
			self.createChannelOutputString('DEPTH')
		if channels.POSITION:
			self.createChannelOutputString('POSITION')
		if channels.GEOMETRY_NORMAL:
			self.createChannelOutputString('GEOMETRY_NORMAL')
		if channels.SHADING_NORMAL:
			self.createChannelOutputString('SHADING_NORMAL')
		if channels.MATERIAL_ID:
			self.createChannelOutputString('MATERIAL_ID')
		if channels.DIRECT_DIFFUSE:
			self.createChannelOutputString('DIRECT_DIFFUSE')
		if channels.DIRECT_GLOSSY:
			self.createChannelOutputString('DIRECT_GLOSSY')
		if channels.EMISSION:
			self.createChannelOutputString('EMISSION')
		if channels.INDIRECT_DIFFUSE:
			self.createChannelOutputString('INDIRECT_DIFFUSE')
		if channels.INDIRECT_GLOSSY:
			self.createChannelOutputString('INDIRECT_GLOSSY')
		if channels.INDIRECT_SPECULAR:
			self.createChannelOutputString('INDIRECT_SPECULAR')
		if channels.DIRECT_SHADOW_MASK:
			self.createChannelOutputString('DIRECT_SHADOW_MASK')
		if channels.INDIRECT_SHADOW_MASK:
			self.createChannelOutputString('INDIRECT_SHADOW_MASK')
		if channels.UV:
			self.createChannelOutputString('UV')
		if channels.RAYCOUNT:
			self.createChannelOutputString('RAYCOUNT')
		
		# Pixel Filter
		self.cfgProps.Set(pyluxcore.Property('film.filter.type', ['MITCHELL_SS']))

		# Sampler
		self.cfgProps.Set(pyluxcore.Property('sampler.type', ['RANDOM']))

		# Debug information
		LuxLog('RenderConfig Properties:')
		LuxLog(str(self.cfgProps))

		self.lcConfig = pyluxcore.RenderConfig(self.cfgProps, self.lcScene)
		BlenderSceneConverter.clear() # for scalers_count etc.

		return self.lcConfig

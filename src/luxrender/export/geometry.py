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
import os, struct, math

import bpy, mathutils, math
from bpy.app.handlers import persistent

from extensions_framework import util as efutil

from ..outputs import LuxLog
from ..outputs.file_api import Files
from ..export import ParamSet, ExportProgressThread, ExportCache, object_anim_matrices
from ..export import matrix_to_list
from ..export import fix_matrix_order
from ..export.materials import get_material_volume_defs
from ..export import LuxManager
from ..export import is_obj_visible

class InvalidGeometryException(Exception):
	pass

class UnexportableObjectException(Exception):
	pass

class MeshExportProgressThread(ExportProgressThread):
	message = 'Exporting meshes: %i%%'

class DupliExportProgressThread(ExportProgressThread):
	message = '...  %i%% ...'

class GeometryExporter(object):
	
	# for partial mesh export
	KnownExportedObjects = set()
	KnownModifiedObjects = set()
	NewExportedObjects = set()
	
	def __init__(self, lux_context, visibility_scene):
		self.lux_context = lux_context
		self.visibility_scene = visibility_scene
		
		self.ExportedMeshes = ExportCache('ExportedMeshes')
		self.ExportedObjects = ExportCache('ExportedObjects')
		self.ExportedPLYs = ExportCache('ExportedPLYs')
		self.AnimationDataCache = ExportCache('AnimationData')
		self.ExportedObjectsDuplis = ExportCache('ExportedObjectsDuplis')
		
		# start fresh
		GeometryExporter.NewExportedObjects = set()
		
		self.objects_used_as_duplis = set()
		
		self.have_emitting_object = False
		self.exporting_duplis = False
		
		self.callbacks = {
			'duplis': {
				'FACES': self.handler_Duplis_GENERIC,
				'GROUP': self.handler_Duplis_GENERIC,
				'VERTS': self.handler_Duplis_GENERIC,
			},
			'particles': {
				'OBJECT': self.handler_Duplis_GENERIC,
				'GROUP': self.handler_Duplis_GENERIC,
				'PATH': self.handler_Duplis_PATH,
			},
			'objects': {
				'MESH': self.handler_MESH,
				'SURFACE': self.handler_MESH,
				'CURVE': self.handler_MESH,
				'FONT': self.handler_MESH,
				'META': self.handler_MESH
			}
		}
		
		self.valid_duplis_callbacks = self.callbacks['duplis'].keys()
		self.valid_particles_callbacks = self.callbacks['particles'].keys()
		self.valid_objects_callbacks = self.callbacks['objects'].keys()
	
	def buildMesh(self, obj):
		"""
		Decide which mesh format to output, if any, since the given object
		may be an external PLY proxy.
		"""
		
		# Using a cache on object massively speeds up dupli instance export
		obj_cache_key = (self.geometry_scene, obj)
		if self.ExportedObjects.have(obj_cache_key): return self.ExportedObjects.get(obj_cache_key)
		
		mesh_definitions = []
		
		export_original = True
		# mesh data name first for portal reasons
		ext_mesh_name = '%s_%s_ext' % (obj.data.name, self.geometry_scene.name)
		if obj.luxrender_object.append_proxy:
			if obj.luxrender_object.hide_proxy_mesh:
				export_original = False
			
			if self.allow_instancing(obj) and self.ExportedMeshes.have(ext_mesh_name):
				mesh_definitions.append( self.ExportedMeshes.get(ext_mesh_name) )
			else:
				ext_params = ParamSet()
				if obj.luxrender_object.proxy_type in {'plymesh', 'stlmesh'}:
					ext_params.add_string('filename', efutil.path_relative_to_export(obj.luxrender_object.external_mesh))
					ext_params.add_bool('smooth', obj.luxrender_object.use_smoothing)
				if obj.luxrender_object.proxy_type in {'sphere', 'cylinder', 'cone', 'disk', 'paraboloid'}:
					ext_params.add_float('radius', obj.luxrender_object.radius)
					ext_params.add_float('phimax', obj.luxrender_object.phimax*(180/math.pi))
				if obj.luxrender_object.proxy_type in {'cylinder', 'paraboloid'}:
					ext_params.add_float('zmax', obj.luxrender_object.zmax)
				if obj.luxrender_object.proxy_type == 'cylinder':
					ext_params.add_float('zmin', obj.luxrender_object.zmin)
				
				mesh_definition = (ext_mesh_name, obj.active_material.name, obj.luxrender_object.proxy_type, ext_params)
				mesh_definitions.append( mesh_definition )
				
				# Only export objectBegin..objectEnd and cache this mesh_definition if we plan to use instancing
				if self.allow_instancing(obj):
					self.exportShapeDefinition(obj, mesh_definition)
					self.ExportedMeshes.add(ext_mesh_name, mesh_definition)
		
		if export_original:
			# Choose the mesh export type, if set, or use the default
			mesh_type = obj.data.luxrender_mesh.mesh_type
			# If the rendering is INT and not writing to disk, we must use native mesh format
			internal_nofiles = self.visibility_scene.luxrender_engine.export_type=='INT' and not self.visibility_scene.luxrender_engine.write_files
			global_type = 'native' if internal_nofiles else self.visibility_scene.luxrender_engine.mesh_type
			if mesh_type == 'native' or (mesh_type == 'global' and global_type == 'native'):
				mesh_definitions.extend( self.buildNativeMesh(obj) )
			if mesh_type == 'binary_ply' or (mesh_type == 'global' and global_type == 'binary_ply'):
				mesh_definitions.extend( self.buildBinaryPLYMesh(obj) )
		
		self.ExportedObjects.add(obj_cache_key, mesh_definitions)
		return mesh_definitions
	
	def buildBinaryPLYMesh(self, obj):
		"""
		Convert supported blender objects into a MESH, and then split into parts
		according to vertex material assignment, and construct a mesh_name and
		ParamSet for each part which will become a LuxRender PLYShape statement
		wrapped within objectBegin..objectEnd or placed in an
		attributeBegin..attributeEnd scope, depending if instancing is allowed.
		The actual geometry will be dumped to a binary ply file.
		"""
		try:
			mesh_definitions = []
			mesh = obj.to_mesh(self.geometry_scene, True, 'RENDER')
			if mesh is None:
				raise UnexportableObjectException('Cannot create render/export mesh')
			
			# collate faces by mat index
			ffaces_mats = {}
			mesh_faces = mesh.tessfaces if bpy.app.version > (2, 62, 1 ) else mesh.faces # bmesh
			for f in mesh_faces:
				mi = f.material_index
				if mi not in ffaces_mats.keys(): ffaces_mats[mi] = []
				ffaces_mats[mi].append( f )
			material_indices = ffaces_mats.keys()
			
			number_of_mats = len(mesh.materials)
			if number_of_mats > 0:
				iterator_range = range(number_of_mats)
			else:
				iterator_range = [0]
			
			for i in iterator_range:
				try:
					if i not in material_indices: continue
					
					# If this mesh/mat combo has already been processed, get it from the cache
					mesh_cache_key = (self.geometry_scene, obj.data, i)
					if self.allow_instancing(obj) and self.ExportedMeshes.have(mesh_cache_key):
						mesh_definitions.append( self.ExportedMeshes.get(mesh_cache_key) )
						continue
					
					# Put PLY files in frame-numbered subfolders to avoid
					# clobbering when rendering animations
					sc_fr = '%s/%s/%s/%05d' % (efutil.export_path, efutil.scene_filename(), bpy.path.clean_name(self.geometry_scene.name), self.visibility_scene.frame_current)
					if not os.path.exists( sc_fr ):
						os.makedirs(sc_fr)
					
					def make_plyfilename():
						ply_serial = self.ExportedPLYs.serial(mesh_cache_key)
						mesh_name = '%s_%04d_m%03d' % (obj.data.name, ply_serial, i)
						ply_filename = '%s.ply' % bpy.path.clean_name(mesh_name)
						ply_path = '/'.join([sc_fr, ply_filename])
						return mesh_name, ply_path
					
					mesh_name, ply_path = make_plyfilename()
					
					# Ensure that all PLY files have unique names
					while self.ExportedPLYs.have(ply_path):
						mesh_name, ply_path = make_plyfilename()
					
					self.ExportedPLYs.add(ply_path, None)
					
					# skip writing the PLY file if the box is checked
					skip_exporting = obj in self.KnownExportedObjects and not obj in self.KnownModifiedObjects
					if not os.path.exists(ply_path) or not (self.visibility_scene.luxrender_engine.partial_ply and skip_exporting):
						
						GeometryExporter.NewExportedObjects.add(obj)
						
						uv_textures = mesh.tessface_uv_textures if bpy.app.version > (2, 62, 0 ) else mesh.uv_textures # bmesh
						if len(uv_textures) > 0:
							if mesh.uv_textures.active and uv_textures.active.data:
								uv_layer = uv_textures.active.data
						else:
							uv_layer = None
						
						# Here we work out exactly which vert+normal combinations
						# we need to export. This is done first, and the export
						# combinations cached before writing to file because the
						# number of verts needed needs to be written in the header
						# and that number is not known before this is done.
						
						# Export data
						co_no_uv_cache = []
						face_vert_indices = {}		# mapping of face index to list of exported vert indices for that face
						
						# Caches
						vert_vno_indices = {}		# mapping of vert index to exported vert index for verts with vert normals
						vert_use_vno = set()		# Set of vert indices that use vert normals
						
						vert_index = 0				# exported vert index
						for face in ffaces_mats[i]:
							fvi = []
							for j, vertex in enumerate(face.vertices):
								v = mesh.vertices[vertex]
								
								if face.use_smooth:
									
									if uv_layer:
										vert_data = (v.co[:], v.normal[:], uv_layer[face.index].uv[j][:])
									else:
										vert_data = (v.co[:], v.normal[:])
									
									if vert_data not in vert_use_vno:
										vert_use_vno.add( vert_data )
										
										co_no_uv_cache.append( vert_data )
										
										vert_vno_indices[vert_data] = vert_index
										fvi.append(vert_index)
										
										vert_index += 1
									else:
										fvi.append(vert_vno_indices[vert_data])
									
								else:
									
									if uv_layer:
										vert_data = (v.co[:], face.normal[:], uv_layer[face.index].uv[j][:])
									else:
										vert_data = (v.co[:], face.normal[:])
									
									# All face-vert-co-no are unique, we cannot
									# cache them
									co_no_uv_cache.append( vert_data )
									
									fvi.append(vert_index)
									
									vert_index += 1
							
							face_vert_indices[face.index] = fvi
						
						del vert_vno_indices
						del vert_use_vno
						
						with open(ply_path, 'wb') as ply:
							ply.write(b'ply\n')
							ply.write(b'format binary_little_endian 1.0\n')
							ply.write(b'comment Created by LuxBlend 2.6 exporter for LuxRender - www.luxrender.net\n')
							
							# vert_index == the number of actual verts needed
							ply.write( ('element vertex %d\n' % vert_index).encode() )
							ply.write(b'property float x\n')
							ply.write(b'property float y\n')
							ply.write(b'property float z\n')
							
							ply.write(b'property float nx\n')
							ply.write(b'property float ny\n')
							ply.write(b'property float nz\n')
							
							if uv_layer:
								ply.write(b'property float s\n')
								ply.write(b'property float t\n')
							
							ply.write( ('element face %d\n' % len(ffaces_mats[i])).encode() )
							ply.write(b'property list uchar uint vertex_indices\n')
							
							ply.write(b'end_header\n')
							
							# dump cached co/no/uv
							if uv_layer:
								for co,no,uv in co_no_uv_cache:
									ply.write( struct.pack('<3f', *co) )
									ply.write( struct.pack('<3f', *no) )
									ply.write( struct.pack('<2f', *uv) )
							else:
								for co,no in co_no_uv_cache:
									ply.write( struct.pack('<3f', *co) )
									ply.write( struct.pack('<3f', *no) )
							
							# dump face vert indices
							for face in ffaces_mats[i]:
								lfvi = len(face_vert_indices[face.index])
								ply.write( struct.pack('<B', lfvi) )
								ply.write( struct.pack('<%dI'%lfvi, *face_vert_indices[face.index]) )
							
							del co_no_uv_cache
							del face_vert_indices
						
						LuxLog('Binary PLY file written: %s' % (ply_path))
					else:
						LuxLog('Skipping already exported PLY: %s' % mesh_name)
					
					# Export the shape definition to LXO
					shape_params = ParamSet().add_string(
						'filename',
						efutil.path_relative_to_export(ply_path)
					)
					
					# Add subdiv etc options
					shape_params.update( obj.data.luxrender_mesh.get_paramset() )
					
					mesh_definition = (
						mesh_name,
						i,
						'plymesh',
						shape_params
					)
					mesh_definitions.append( mesh_definition )
					
					# Only export objectBegin..objectEnd and cache this mesh_definition if we plan to use instancing
					if self.allow_instancing(obj):
						self.exportShapeDefinition(obj, mesh_definition)
						self.ExportedMeshes.add(mesh_cache_key, mesh_definition)
				
				except InvalidGeometryException as err:
					LuxLog('Mesh export failed, skipping this mesh: %s' % err)
			
			del ffaces_mats
			bpy.data.meshes.remove(mesh)
			
		except UnexportableObjectException as err:
			LuxLog('Object export failed, skipping this object: %s' % err)
		
		return mesh_definitions
	
	def buildNativeMesh(self, obj):
		"""
		Convert supported blender objects into a MESH, and then split into parts
		according to vertex material assignment, and construct a mesh_name and
		ParamSet for each part which will become a LuxRender Shape statement
		wrapped within objectBegin..objectEnd or placed in an
		attributeBegin..attributeEnd scope, depending if instancing is allowed.
		"""
		
		try:
			mesh_definitions = []
			mesh = obj.to_mesh(self.geometry_scene, True, 'RENDER')
			if mesh is None:
				raise UnexportableObjectException('Cannot create render/export mesh')
			
			# collate faces by mat index
			ffaces_mats = {}
			mesh_faces = mesh.tessfaces if bpy.app.version > (2, 62, 1 ) else mesh.faces # bmesh
			for f in mesh_faces:
				mi = f.material_index
				if mi not in ffaces_mats.keys(): ffaces_mats[mi] = []
				ffaces_mats[mi].append( f )
			material_indices = ffaces_mats.keys()
			
			number_of_mats = len(mesh.materials)
			if number_of_mats > 0:
				iterator_range = range(number_of_mats)
			else:
				iterator_range = [0]
			
			for i in iterator_range:
				try:
					if i not in material_indices: continue
					
					# If this mesh/mat-index combo has already been processed, get it from the cache
					mesh_cache_key = (self.geometry_scene, obj.data, i)
					if self.allow_instancing(obj) and self.ExportedMeshes.have(mesh_cache_key):
						mesh_definitions.append( self.ExportedMeshes.get(mesh_cache_key) )
						continue
					
					# mesh_name must start with mesh data name to match with portals
					mesh_name = '%s-%s_m%03d' % (obj.data.name, self.geometry_scene.name, i)
					
					if self.visibility_scene.luxrender_testing.object_analysis: print(' -> NativeMesh:')
					if self.visibility_scene.luxrender_testing.object_analysis: print('  -> Material index: %d' % i)
					if self.visibility_scene.luxrender_testing.object_analysis: print('  -> derived mesh name: %s' % mesh_name)
					
					uv_textures = mesh.tessface_uv_textures if bpy.app.version > (2, 62, 0 ) else mesh.uv_textures # bmesh
					if len(uv_textures) > 0:
						if uv_textures.active and uv_textures.active.data:
							uv_layer = uv_textures.active.data
					else:
						uv_layer = None
					
					# Export data
					points = []
					normals = []
					uvs = []
					ntris = 0
					face_vert_indices = []		# list of face vert indices
					
					# Caches
					vert_vno_indices = {}		# mapping of vert index to exported vert index for verts with vert normals
					vert_use_vno = set()		# Set of vert indices that use vert normals
					
					vert_index = 0				# exported vert index
					for face in ffaces_mats[i]:
						fvi = []
						for j, vertex in enumerate(face.vertices):
							v = mesh.vertices[vertex]
							
							if face.use_smooth:
								
								if uv_layer:
									vert_data = (v.co[:], v.normal[:], uv_layer[face.index].uv[j][:] )
								else:
									vert_data = (v.co[:], v.normal[:], tuple() )
								
								if vert_data not in vert_use_vno:
									vert_use_vno.add(vert_data)
									
									points.extend( vert_data[0] )
									normals.extend( vert_data[1] )
									uvs.extend( vert_data[2] )
									
									vert_vno_indices[vert_data] = vert_index
									fvi.append(vert_index)
									
									vert_index += 1
								else:
									fvi.append(vert_vno_indices[vert_data])
								
							else:
								# all face-vert-co-no are unique, we cannot
								# cache them
								points.extend( v.co[:] )
								normals.extend( face.normal[:] )
								if uv_layer: uvs.extend( uv_layer[face.index].uv[j][:] )
								
								fvi.append(vert_index)
								
								vert_index += 1
						
						# For Lux, we need to triangulate quad faces
						face_vert_indices.extend( fvi[0:3] )
						ntris += 3
						if len(fvi) == 4:
							face_vert_indices.extend([ fvi[0], fvi[2], fvi[3] ])
							ntris += 3
					
					del vert_vno_indices
					del vert_use_vno
					
					# build shape ParamSet
					shape_params = ParamSet()
					
					if self.lux_context.API_TYPE == 'PURE':
						# ntris isn't really the number of tris!!
						shape_params.add_integer('ntris', ntris)
						shape_params.add_integer('nvertices', vert_index)
					
					shape_params.add_integer('triindices', face_vert_indices)
					shape_params.add_point('P', points)
					shape_params.add_normal('N', normals)
					
					if uv_layer:
						shape_params.add_float('uv', uvs)
					
					# Add other properties from LuxRender Mesh panel
					shape_params.update( obj.data.luxrender_mesh.get_paramset() )
					
					mesh_definition = (
						mesh_name,
						i,
						'mesh',
						shape_params
					)
					mesh_definitions.append( mesh_definition )
					
					# Only export objectBegin..objectEnd and cache this mesh_definition if we plan to use instancing
					if self.allow_instancing(obj):
						self.exportShapeDefinition(obj, mesh_definition)
						self.ExportedMeshes.add(mesh_cache_key, mesh_definition)
				
				except InvalidGeometryException as err:
					LuxLog('Mesh export failed, skipping this mesh: %s' % err)
			
			del ffaces_mats
			bpy.data.meshes.remove(mesh)
			
		except UnexportableObjectException as err:
			LuxLog('Object export failed, skipping this object: %s' % err)
		
		return mesh_definitions
	
	is_preview = False
	
	def allow_instancing(self, obj):
		# Some situations require full geometry export
		if self.visibility_scene.luxrender_rendermode.renderer == 'hybrid':
			return False
		
		# Portals are always instances
		if obj.type == 'MESH' and obj.data.luxrender_mesh.portal:
			return True
		
		if obj.type == 'MESH' and obj.data.luxrender_mesh.instancing_mode != 'auto':
			return obj.data.luxrender_mesh.instancing_mode == 'always'
		
		# If the object is animated, for motion blur we need instances
		if self.is_object_animated(obj)[0]:
			return True
		
		# If the mesh is only used once, instancing is a waste of memory
		# However, duplis don't increase the users count, so we cout those separately
		if (not ((obj.parent and obj.parent.is_duplicator) or obj in self.objects_used_as_duplis)) and obj.data.users == 1:
			return False
		
		# Only allow instancing for duplis and particles in non-hybrid mode, or
		# for normal objects if the object has certain modifiers applied against
		# the same shared base mesh.
		if hasattr(obj, 'modifiers') and len(obj.modifiers) > 0 and obj.data.users > 1:
			instance = False
			for mod in obj.modifiers:
				# Allow non-deforming modifiers
				instance |= mod.type in ('COLLISION','PARTICLE_INSTANCE','PARTICLE_SYSTEM','SMOKE')
			return instance
		else:
			return not self.is_preview
	
	def exportShapeDefinition(self, obj, mesh_definition):
		"""
		If the mesh is valid and instancing is allowed for this object, export
		an objectBegin..objectEnd block containing the Shape definition.
		"""
		
		me_name = mesh_definition[0]
		me_shape_type, me_shape_params = mesh_definition[2:4]
		
		if len(me_shape_params) == 0: return
		
		# Shape is the only thing to go into the ObjectBegin..ObjectEnd definition
		# Everything else is set on a per-instance basis
		self.lux_context.objectBegin(me_name)
		
		# We need the transform in the object definition if this is a portal, since
		# an objectInstance won't be exported for it.
		if obj.type == 'MESH' and obj.data.luxrender_mesh.portal:
			self.lux_context.transform( matrix_to_list(obj.matrix_world, apply_worldscale=True) )
		me_shape_params.add_string('name', obj.name)
		self.lux_context.shape(me_shape_type, me_shape_params)
		self.lux_context.objectEnd()
		
		LuxLog('Mesh definition exported: %s' % me_name)
	
	def is_object_animated(self, obj, matrix=None):
		
		if self.AnimationDataCache.have(obj):
			return self.AnimationDataCache.get(obj)
		
		next_matrices = []
		
		# object motion blur
		is_object_animated = False
		if self.visibility_scene.camera.data.luxrender_camera.usemblur and self.visibility_scene.camera.data.luxrender_camera.objectmblur:
			if matrix is not None and matrix[1] is not None:
				next_matrices = [matrix[1]]
				is_object_animated = True
			else:
				# grab a bunch of fractional-frame fcurve_matrices and export
				# several motionInstances for non-linear motion blur
				STEPS = self.geometry_scene.camera.data.luxrender_camera.motion_blur_samples
				
				# object_anim_matrices returns steps+1 matrices, ie start and end of frame
				# we don't want the start matrix
				next_matrices = object_anim_matrices(self.geometry_scene, obj, STEPS)[1:]
				
				is_object_animated = len(next_matrices) > 0
		
		self.AnimationDataCache.add(obj, (is_object_animated, next_matrices))
		
		return is_object_animated, next_matrices
	
	def exportShapeInstances(self, obj, mesh_definitions, matrix=None, parent=None):
		
		# Don't export instances of portal meshes
		if obj.type == 'MESH' and obj.data.luxrender_mesh.portal: return
		# or empty definitions
		if len(mesh_definitions) < 1: return
		
		self.lux_context.attributeBegin(comment=obj.name, file=Files.GEOM)
		
		is_object_animated, next_matrices = self.is_object_animated(obj, matrix)
		
		# object translation/rotation/scale
		if is_object_animated:
			num_steps = len(next_matrices)
			fsps = float(num_steps) * self.visibility_scene.render.fps / self.visibility_scene.render.fps_base
			step_times = [(i) / fsps for i in range(0, num_steps+1)]
			self.lux_context.motionBegin(step_times)
			# then export first matrix as normal
		
		if matrix is not None:
			self.lux_context.transform( matrix_to_list(matrix[0], apply_worldscale=True) )
		else:
			self.lux_context.transform( matrix_to_list(obj.matrix_world, apply_worldscale=True) )
		
		# export rest of the frames matrices
		if is_object_animated:
			for next_matrix in next_matrices:
				#fni = float(num_instances) * self.visibility_scene.render.fps
				#self.lux_context.motionInstance(me_name, i/fni, (i+1)/fni, '%s_motion_%i' % (obj.name, i))
				#self.lux_context.transformBegin(comment=obj.name)
				#self.lux_context.identity()
				#self.lux_context.transform(matrix_to_list(next_matrix, apply_worldscale=True))
				#self.lux_context.coordinateSystem('%s_motion_%i' % (obj.name, i))
				#self.lux_context.transformEnd()
				self.lux_context.transform(matrix_to_list(next_matrix, apply_worldscale=True))
			self.lux_context.motionEnd()
		
		use_inner_scope = len(mesh_definitions) > 1
		for me_name, me_mat_index, me_shape_type, me_shape_params in mesh_definitions:
			me_shape_params.add_string('name', obj.name)
			if use_inner_scope: self.lux_context.attributeBegin()
			
			if parent != None:
				mat_object = parent
			else:
				mat_object = obj
			
			try:
				ob_mat = mat_object.material_slots[me_mat_index].material
			except IndexError:
				ob_mat = None
				LuxLog('WARNING: material slot %d on object "%s" is unassigned!' %(me_mat_index+1, mat_object.name))
			
			if ob_mat is not None:
				
				# Export material definition && check for emission
				if self.lux_context.API_TYPE == 'FILE':
					self.lux_context.set_output_file(Files.MATS)
					mat_export_result = ob_mat.luxrender_material.export(self.visibility_scene, self.lux_context, ob_mat, mode='indirect')
					self.lux_context.set_output_file(Files.GEOM)
					if not 'CLAY' in mat_export_result:
						self.lux_context.namedMaterial(ob_mat.name)
				elif self.lux_context.API_TYPE == 'PURE':
					mat_export_result = ob_mat.luxrender_material.export(self.visibility_scene, self.lux_context, ob_mat, mode='direct')
				
				object_is_emitter = ob_mat.luxrender_emission.use_emission
				
				if object_is_emitter:
					# Only add the AreaLightSource if this object's emission lightgroup is enabled
					if self.visibility_scene.luxrender_lightgroups.is_enabled(ob_mat.luxrender_emission.lightgroup):
						if not self.visibility_scene.luxrender_lightgroups.ignore:
							self.lux_context.lightGroup(ob_mat.luxrender_emission.lightgroup, [])
						self.lux_context.areaLightSource( *ob_mat.luxrender_emission.api_output(ob_mat) )
					else:
						object_is_emitter = False
				
				int_v, ext_v = get_material_volume_defs(ob_mat)
				if int_v != '':
					self.lux_context.interior(int_v)
				elif self.geometry_scene.luxrender_world.default_interior_volume != '':
					self.lux_context.interior(self.geometry_scene.luxrender_world.default_interior_volume)
				if ext_v != '':
					self.lux_context.exterior(ext_v)
				elif self.geometry_scene.luxrender_world.default_exterior_volume != '':
					self.lux_context.exterior(self.geometry_scene.luxrender_world.default_exterior_volume)
				
			else:
				object_is_emitter = False
			
			self.have_emitting_object |= object_is_emitter
			
			# If the object emits, don't export instance or motioninstance, just the Shape
			if (not self.allow_instancing(mat_object)) or object_is_emitter:
				self.lux_context.shape(me_shape_type, me_shape_params)
			# motionInstance for motion blur
			#elif is_object_animated:
			# handled by ordinary object instance
			# ordinary mesh instance
			else:
				self.lux_context.objectInstance(me_name)
			
			if use_inner_scope: self.lux_context.attributeEnd()
		
		self.lux_context.attributeEnd()
	
	def BSpline(self, points, dimension, degree, u):
		controlpoints = []
		def Basispolynom(controlpoints, i, u, degree):
			if degree == 0:
				temp = 0
				if (controlpoints[i] <= u) and (u < controlpoints[i+1]): temp = 1
			else:
				N0 = Basispolynom(controlpoints,i,u,degree-1)
				N1 = Basispolynom(controlpoints,i+1,u,degree-1)
				
				if N0 == 0: 
					sum1 = 0
				else:
					sum1 = (u-controlpoints[i])/(controlpoints[i+degree] - controlpoints[i])*N0
				if N1 == 0: 
					sum2 = 0
				else:
					sum2 = (controlpoints[i+1+degree]-u)/(controlpoints[i+1+degree] - controlpoints[i+1])*N1
				
				temp = sum1 + sum2
			return temp
		
		for i in range(len(points)+degree+1):
			if i <= degree:
				controlpoints.append(0)
			elif i >= len(points):
				controlpoints.append(len(points)-degree)
			else:
				controlpoints.append(i - degree)
		
		if dimension == 2: temp = mathutils.Vector((0.0,0.0))
		elif dimension == 3:temp = mathutils.Vector((0.0,0.0,0.0))
		
		for i in range(len(points)):
			temp = temp + Basispolynom(controlpoints, i, u, degree)*points[i]
		return temp
	
	def handler_Duplis_PATH(self, obj, *args, **kwargs):
		if not 'particle_system' in kwargs.keys():
			LuxLog('ERROR: handler_Duplis_PATH called without particle_system')
			return
		
		psys = kwargs['particle_system']
		
		if not psys.settings.type == 'HAIR':
			LuxLog('ERROR: handler_Duplis_PATH can only handle Hair particle systems ("%s")' % psys.name)
			return
			
		for mod in obj.modifiers:
			if mod.type == 'PARTICLE_SYSTEM' and mod.show_render == False:
				return
		
		# This should force the strand/junction objects to be instanced
		self.objects_used_as_duplis.add(obj)
		
		LuxLog('Exporting Hair system "%s"...' % psys.name)
		
		size = psys.settings.particle_size / 2.0 / 1000.0 # XXX divide by 2 twice ? Also throw in /1000.0 to scale down to millimeters
		hair_Junction = (
			(
				'HAIR_Junction_%s'%psys.name,
				psys.settings.material - 1,
				'sphere',
				ParamSet().add_float('radius', size/2.0)
			),
		)
		hair_Strand = (
			(
				'HAIR_Strand_%s'%psys.name,
				psys.settings.material - 1,
				'cylinder',
				ParamSet() \
					.add_float('radius', size/2.0) \
					.add_float('zmin', 0.0) \
					.add_float('zmax', 1.0)
			),
		)
		
		for sn, si, st, sp in hair_Junction:
			self.lux_context.objectBegin(sn)
			self.lux_context.shape(st, sp)
			self.lux_context.objectEnd()
		
		for sn, si, st, sp in hair_Strand:
			self.lux_context.objectBegin(sn)
			self.lux_context.shape(st, sp)
			self.lux_context.objectEnd()
		
		det = DupliExportProgressThread()
		det.start(len(psys.particles))
		
		for particle in psys.particles:
			if not (particle.is_exist and particle.is_visible): continue
			
			det.exported_objects += 1
			
			points = []
			for j in range(len(particle.hair_keys)):
				points.append(particle.hair_keys[j].co)
			if psys.settings.use_hair_bspline:
				temp = []
				degree = 2
				dimension = 3
				for i in range(math.trunc(math.pow(2,psys.settings.render_step))):
					if i > 0:
						u = i*(len(points)- degree)/math.trunc(math.pow(2,psys.settings.render_step)-1)-0.0000000000001
					else:
						u = i*(len(points)- degree)/math.trunc(math.pow(2,psys.settings.render_step)-1)
					temp.append(self.BSpline(points, dimension, degree, u))
				points = temp
			
			for j in range(len(points)-1):
				# transpose SB so we can extract columns
				# TODO - change when matrix.col is available
				SB = obj.matrix_basis.transposed().to_3x3()
				SB = fix_matrix_order(SB) # matrix indexing hack
				v1 = points[j+1] - points[j]
				v2 = SB[2].cross(v1)
				v3 = v1.cross(v2)
				v2.normalize()
				v3.normalize()
				if any(v.length_squared == 0 for v in (v1, v2, v3)):
					M = SB
				else:
					# v1, v2, v3 are the new columns
					# set as rows, transpose later
					M = mathutils.Matrix( (v3,v2,v1) )
					M = fix_matrix_order(M) # matrix indexing hack
				M = M.transposed().to_4x4()
				
				Mtrans = mathutils.Matrix.Translation(points[j])
				matrix = obj.matrix_world * Mtrans * M
				
				self.exportShapeInstances(
					obj,
					hair_Strand,
					matrix=[matrix,None]
				)
				matrix = obj.matrix_world * Mtrans
				
				self.exportShapeInstances(
					obj,
					hair_Junction,
					matrix=[matrix,None]
				)
		
		det.stop()
		det.join()
		
		LuxLog('... done, exported %s hairs' % det.exported_objects)
	
	def handler_Duplis_GENERIC(self, obj, *args, **kwargs):
		try:
			LuxLog('Exporting Duplis...')
			
			if self.ExportedObjectsDuplis.have(obj):
				LuxLog('... duplis already exported for object %s' % obj)
				return
			
			self.ExportedObjectsDuplis.add(obj, True)
			
			obj.dupli_list_create(self.visibility_scene)
			if not obj.dupli_list:
				raise Exception('cannot create dupli list for object %s' % obj.name)
			
			# Create our own DupliOb list to work around incorrect layers
			# attribute when inside create_dupli_list()..free_dupli_list()
			duplis = []
			for dupli_ob in obj.dupli_list:
				if dupli_ob.object.type not in ['MESH', 'SURFACE', 'FONT', 'CURVE']: #metaballs are omitted from this function intentionally. Adding them causes recursion when building the ball. (add 'META' to this if you actually want that bug, it makes for some fun glitch art with particles)
					continue
				#if not dupli_ob.object.is_visible(self.visibility_scene) or dupli_ob.object.hide_render:
				if not is_obj_visible(self.visibility_scene, dupli_ob.object, is_dupli=True):
					continue
				
				self.objects_used_as_duplis.add(dupli_ob.object)
				duplis.append(
					(
						dupli_ob.object,
						dupli_ob.matrix.copy()
					)
				)
			
			obj.dupli_list_clear()
			
			det = DupliExportProgressThread()
			det.start(len(duplis))
			
			self.exporting_duplis = True
			
			# dupli object, dupli matrix
			for do, dm in duplis:
				
				det.exported_objects += 1
				
				# Check for group layer visibility, if the object is in a group
				gviz = len(do.users_group) == 0
				for grp in do.users_group:
					gviz |= True in [a&b for a,b in zip(do.layers, grp.layers)]
				if not gviz:
					continue
				
				self.exportShapeInstances(
					obj,
					self.buildMesh(do),
					matrix=[dm,None],
					parent=do
				)
			
			del duplis
			
			self.exporting_duplis = False
			
			det.stop()
			det.join()
			
			LuxLog('... done, exported %s duplis' % det.exported_objects)
			
		except Exception as err:
			LuxLog('Error with handler_Duplis_GENERIC and object %s: %s' % (obj, err))
	
	def handler_MESH(self, obj, *args, **kwargs):
		if self.visibility_scene.luxrender_testing.object_analysis: print(' -> handler_MESH: %s' % obj)
		
		if 'matrix' in kwargs.keys():
			self.exportShapeInstances(
				obj,
				self.buildMesh(obj),
				matrix=kwargs['matrix']
			)
		else:
			self.exportShapeInstances(
				obj,
				self.buildMesh(obj)
			)
	
	def iterateScene(self, geometry_scene):
		self.geometry_scene = geometry_scene
		self.have_emitting_object = False
		
		progress_thread = MeshExportProgressThread()
		tot_objects = len(geometry_scene.objects)
		progress_thread.start(tot_objects)
		
		export_originals = {}
		
		for obj in geometry_scene.objects:
			progress_thread.exported_objects += 1
			
			if self.visibility_scene.luxrender_testing.object_analysis: print('Analysing object %s : %s' % (obj, obj.type))
			
			try:
				# Export only objects which are enabled for render (in the outliner) and visible on a render layer
				if not is_obj_visible(self.visibility_scene, obj):
					raise UnexportableObjectException(' -> not visible')
				
				if obj.parent and obj.parent.is_duplicator:
					raise UnexportableObjectException(' -> parent is duplicator')
				
				for mod in obj.modifiers:
					if mod.name == 'Smoke':
						if mod.smoke_type == 'DOMAIN':
							raise UnexportableObjectException(' -> Smoke domain')
				
				number_psystems = len(obj.particle_systems)
				
				if obj.is_duplicator and number_psystems < 1:
					if self.visibility_scene.luxrender_testing.object_analysis: print(' -> is duplicator without particle systems')
					if obj.dupli_type in self.valid_duplis_callbacks:
						self.callbacks['duplis'][obj.dupli_type](obj)
					elif self.visibility_scene.luxrender_testing.object_analysis: print(' -> Unsupported Dupli type: %s' % obj.dupli_type)
				
				# Some dupli types should hide the original
				if obj.is_duplicator and obj.dupli_type in ('VERTS', 'FACES', 'GROUP'):
					export_originals[obj] = False
				else:
					export_originals[obj] = True
				
				if number_psystems > 0:
					export_originals[obj] = False
					if self.visibility_scene.luxrender_testing.object_analysis: print(' -> has %i particle systems' % number_psystems)
					for psys in obj.particle_systems:
						export_originals[obj] = export_originals[obj] or psys.settings.use_render_emitter
						if psys.settings.render_type in self.valid_particles_callbacks:
							self.callbacks['particles'][psys.settings.render_type](obj, particle_system=psys)
						elif self.visibility_scene.luxrender_testing.object_analysis: print(' -> Unsupported Particle system type: %s' % psys.settings.render_type)
			
			except UnexportableObjectException as err:
				if self.visibility_scene.luxrender_testing.object_analysis: print(' -> Unexportable object: %s : %s : %s' % (obj, obj.type, err))
		
		export_originals_keys = export_originals.keys()
		
		for obj in geometry_scene.objects:
			try:
				if obj not in export_originals_keys: continue
				
				if not export_originals[obj]:
					raise UnexportableObjectException('export_original_object=False')
				
				if not obj.type in self.valid_objects_callbacks:
					raise UnexportableObjectException('Unsupported object type')
				
				self.callbacks['objects'][obj.type](obj)
			
			except UnexportableObjectException as err:
				if self.visibility_scene.luxrender_testing.object_analysis: print(' -> Unexportable object: %s : %s : %s' % (obj, obj.type, err))
		
		progress_thread.stop()
		progress_thread.join()
		
		self.objects_used_as_duplis.clear()
		
		# update known exported objects for partial export
		GeometryExporter.KnownModifiedObjects -= GeometryExporter.NewExportedObjects
		GeometryExporter.KnownExportedObjects |= GeometryExporter.NewExportedObjects
		GeometryExporter.NewExportedObjects = set()
		
		return self.have_emitting_object



# Update handlers

@persistent
def lux_scene_update(context):
	if bpy.data.objects.is_updated:
		for ob in bpy.data.objects:
			if ob == None:
				continue
			#if ob.is_updated_data:
			#	print('updated_data', ob.name)
			#if ob.data.is_updated:
			#	print('updated', ob.name)
			
			# only flag as updated if either modifiers or 
			# mesh data is updated
			if ob.is_updated_data or (ob.data != None and ob.data.is_updated):
				GeometryExporter.KnownModifiedObjects.add(ob)

@persistent
def lux_scene_load(context):
	# clear known list on scene load
	GeometryExporter.KnownExportedObjects = set()

if hasattr(bpy.app, 'handlers') and hasattr(bpy.app.handlers, 'scene_update_post'):
	bpy.app.handlers.scene_update_post.append(lux_scene_update)
	bpy.app.handlers.load_post.append(lux_scene_load)
	LuxLog('Installed scene post-update handler')

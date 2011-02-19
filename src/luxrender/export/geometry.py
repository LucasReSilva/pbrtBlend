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
import os, struct
OBJECT_ANALYSIS = os.getenv('LB25_OBJECT_ANALYSIS', False)

import bpy

from extensions_framework import util as efutil

from ..outputs import LuxLog
from ..outputs.file_api import Files
from ..export import ParamSet, ExportProgressThread, ExportCache, object_anim_matrix
from ..export import matrix_to_list
from ..export.materials import get_material_volume_defs

def time_export(func):
	if not OBJECT_ANALYSIS: return func
	
	import time
	def _wrap(*args, **kwargs):
		start = time.time()
		result = func(*args, **kwargs)
		end = time.time()
		print('Calling %s took %0.4f seconds' % (func, (end-start)))
		return result
	return _wrap

class InvalidGeometryException(Exception):
	pass

class UnexportableObjectException(Exception):
	pass

class MeshExportProgressThread(ExportProgressThread):
	message = 'Exporting meshes: %i%%'

class DupliExportProgressThread(ExportProgressThread):
	message = '...  %i%% ...'

class GeometryExporter(object):
	
#	lux_context = None
#	scene = None
#	
#	ExportedMeshes = None
#	ExportedObjects = None
#	ExportedPLYs = None
#	
#	callbacks = {}
#	valid_duplis_callbacks = []
#	valid_particles_callbacks = []
#	valid_objects_callbacks = []
#	
#	have_emitting_object = False
#	
#	exporting_duplis = False
	
	def __init__(self, lux_context, scene):
		self.lux_context = lux_context
		self.scene = scene
		
		self.ExportedMeshes = ExportCache('ExportedMeshes')
		self.ExportedObjects = ExportCache('ExportedObjects')
		self.ExportedPLYs = ExportCache('ExportedPLYs')
		
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
				#'PATH': handler_Duplis_PATH,
			},
			'objects': {
				'MESH': self.handler_MESH,
				'SURFACE': self.handler_MESH,
				'FONT': self.handler_MESH
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
		if self.ExportedObjects.have(obj): return self.ExportedObjects.get(obj)
		
		mesh_definitions = []
		
		export_original = True
		ply_mesh_name = '%s_ply' % obj.data.name
		if obj.luxrender_object.append_external_mesh:
			if obj.luxrender_object.hide_proxy_mesh:
				export_original = False
			
			if self.allow_instancing(obj) and self.ExportedMeshes.have(ply_mesh_name):
				mesh_definitions.append( self.ExportedMeshes.get(ply_mesh_name) )
			else:
				ply_params = ParamSet()
				ply_params.add_string('filename', efutil.path_relative_to_export(obj.luxrender_object.external_mesh))
				ply_params.add_bool('smooth', obj.luxrender_object.use_smoothing)
				
				mesh_definition = (ply_mesh_name, obj.active_material, 'plymesh', ply_params)
				mesh_definitions.append( mesh_definition )
				
				# Only export objectBegin..objectEnd and cache this mesh_definition if we plan to use instancing
				if self.allow_instancing(obj):
					self.exportShapeDefinition(obj, mesh_definition)
					self.ExportedMeshes.add(ply_mesh_name, mesh_definition)
		
		if export_original:
			# Choose the mesh export type, if set, or use the default
			mesh_type = obj.data.luxrender_mesh.mesh_type
			# If the rendering is INT and not writing to disk, we must use native mesh format
			internal_nofiles = self.scene.luxrender_engine.export_type=='INT' and not self.scene.luxrender_engine.write_files
			global_type = 'native' if internal_nofiles else self.scene.luxrender_engine.mesh_type
			if mesh_type == 'native' or (mesh_type == 'global' and global_type == 'native'):
				mesh_definitions.extend( self.buildNativeMesh(obj) )
			if mesh_type == 'binary_ply' or (mesh_type == 'global' and global_type == 'binary_ply'):
				mesh_definitions.extend( self.buildBinaryPLYMesh(obj) )
		
		self.ExportedObjects.add(obj, mesh_definitions)
		return mesh_definitions
	
	@time_export
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
			mesh = obj.create_mesh(self.scene, True, 'RENDER')
			if mesh is None:
				raise UnexportableObjectException('Cannot create render/export mesh')
			
			# collate faces by mat index
			ffaces_mats = {}
			for f in mesh.faces:
				mi = f.material_index
				if mi not in ffaces_mats.keys(): ffaces_mats[mi] = []
				ffaces_mats[mi].append( f )
			
			number_of_mats = len(mesh.materials)
			if number_of_mats > 0:
				iterator_range = range(number_of_mats)
			else:
				iterator_range = [0]
			
			for i in iterator_range:
				try:
					if i not in ffaces_mats.keys(): continue
					
					mesh_name = ('%s_m%03d' % (obj.data.name, i)).replace(' ','_')
					
					# If this mesh/mat combo has already been processed, get it from the cache
					if self.allow_instancing(obj) and self.ExportedMeshes.have(mesh_name):
						mesh_definitions.append( self.ExportedMeshes.get(mesh_name) )
						continue
					
					# Put PLY files in frame-numbered subfolders to avoid
					# clobbering when rendering animations
					sc_fr = '%05d' % self.scene.frame_current
					if not os.path.exists( os.path.join(os.getcwd(), sc_fr) ):
						os.mkdir(sc_fr)
					
					ply_filename = '/'.join([sc_fr, bpy.path.clean_name(mesh_name) + '.%04d.ply'%self.ExportedPLYs.serial(mesh_name)])
					
					# Ensure that all PLY files have unique names
					while self.ExportedPLYs.have(ply_filename):
						ply_filename = '/'.join([sc_fr, bpy.path.clean_name(mesh_name) + '.%04d.ply'%self.ExportedPLYs.serial(mesh_name)])
					
					self.ExportedPLYs.add(ply_filename, None)
					
					# skip writing the PLY file if the box is checked
					if not (os.path.exists(ply_filename) and self.scene.luxrender_engine.partial_ply):
						if len(mesh.uv_textures) > 0:
							if mesh.uv_textures.active and mesh.uv_textures.active.data:
								uv_layer = mesh.uv_textures.active.data
						else:
							uv_layer = None
						
						# Here we work out exactly which vert+normal combinations
						# we need to export. This is done first, and the export
						# combinations cached before writing to file because the
						# number of verts needed needs to be written in the header
						# and that number is not known before this is done.
						
						# Export data
						co_no_cache = []
						uv_cache = []
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
									
									if vertex not in vert_use_vno:
										vert_use_vno.add(vertex)
										
										co_no_cache.append( (v.co, v.normal) )
										if uv_layer:
											uv_cache.append( uv_layer[face.index].uv[j] )
										
										vert_vno_indices[vertex] = vert_index
										fvi.append(vert_index)
										
										vert_index += 1
									else:
										fvi.append(vert_vno_indices[vertex])
									
								else:
									# All face-vert-co-no are unique, we cannot
									# cache them
									co_no_cache.append( (v.co, face.normal) )
									if uv_layer:
										uv_cache.append( uv_layer[face.index].uv[j] )
									
									fvi.append(vert_index)
									
									vert_index += 1
							
							face_vert_indices[face.index] = fvi
						
						del vert_vno_indices
						del vert_use_vno
						
						with open(ply_filename, 'wb') as ply:
							ply.write(b'ply\n')
							ply.write(b'format binary_little_endian 1.0\n')
							ply.write(b'comment Created by LuxBlend 2.5 exporter for LuxRender - www.luxrender.net\n')
							
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
								for j, (co,no) in enumerate(co_no_cache):
									ply.write( struct.pack('<3f', *co) )
									ply.write( struct.pack('<3f', *no) )
									ply.write( struct.pack('<2f', *uv_cache[j] ) )
							else:
								for co,no in co_no_cache:
									ply.write( struct.pack('<3f', *co) )
									ply.write( struct.pack('<3f', *no) )
							
							# dump face vert indices
							for face in ffaces_mats[i]:
								lfvi = len(face_vert_indices[face.index])
								ply.write( struct.pack('<B', lfvi) )
								ply.write( struct.pack('<%dI'%lfvi, *face_vert_indices[face.index]) )
							
							del co_no_cache
							del uv_cache
							del face_vert_indices
						
						LuxLog('Binary PLY file written: %s/%s' % (os.getcwd(),ply_filename))
					
					# Export the shape definition to LXO
					shape_params = ParamSet().add_string(
						'filename',
						ply_filename
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
						self.ExportedMeshes.add(mesh_name, mesh_definition)
					
					#LuxLog('Binary PLY Mesh Exported: %s' % mesh_name)
				
				except InvalidGeometryException as err:
					LuxLog('Mesh export failed, skipping this mesh: %s' % err)
			
			del ffaces_mats
			
		except UnexportableObjectException as err:
			LuxLog('Object export failed, skipping this object: %s' % err)
		
		return mesh_definitions
	
	@time_export
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
			mesh = obj.create_mesh(self.scene, True, 'RENDER')
			if mesh is None:
				raise UnexportableObjectException('Cannot create render/export mesh')
			
			# collate faces by mat index
			ffaces_mats = {}
			for f in mesh.faces:
				mi = f.material_index
				if mi not in ffaces_mats.keys(): ffaces_mats[mi] = []
				ffaces_mats[mi].append( f )
			
			number_of_mats = len(mesh.materials)
			if number_of_mats > 0:
				iterator_range = range(number_of_mats)
			else:
				iterator_range = [0]
			
			for i in iterator_range:
				try:
					if i not in ffaces_mats.keys(): continue
					
					mesh_name = ('%s_%03d' % (obj.data.name, i)).replace(' ','_')
					
					# If this mesh/mat-index combo has already been processed, get it from the cache
					if self.allow_instancing(obj) and self.ExportedMeshes.have(mesh_name):
						mesh_definitions.append( self.ExportedMeshes.get(mesh_name) )
						continue
					
					if OBJECT_ANALYSIS: print(' -> NativeMesh:')
					if OBJECT_ANALYSIS: print('  -> Material index: %d' % i)
					if OBJECT_ANALYSIS: print('  -> derived mesh name: %s' % mesh_name)
					
					
					if len(mesh.uv_textures) > 0:
						if mesh.uv_textures.active and mesh.uv_textures.active.data:
							uv_layer = mesh.uv_textures.active.data
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
								
								if vertex not in vert_use_vno:
									vert_use_vno.add(vertex)
									
									points.extend(v.co)
									normals.extend(v.normal)
									if uv_layer:
										uvs.extend( uv_layer[face.index].uv[j] )
									
									vert_vno_indices[vertex] = vert_index
									fvi.append(vert_index)
									
									vert_index += 1
								else:
									fvi.append(vert_vno_indices[vertex])
								
							else:
								# all face-vert-co-no are unique, we cannot
								# cache them
								points.extend(v.co)
								normals.extend(face.normal)
								if uv_layer:
									uvs.extend( uv_layer[face.index].uv[j] )
								
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
					
					#print(' %s num points: %i' % (obj.name, len(points)))
					#print(' %s num normals: %i' % (obj.name, len(normals)))
					#print(' %s num idxs: %i' % (obj.name, len(indices)))
					
					# build shape ParamSet
					shape_params = ParamSet()
					
					if self.lux_context.API_TYPE == 'PURE':
						# ntris isn't really the number of tris!!
						shape_params.add_integer('ntris', ntris)
						shape_params.add_integer('nvertices', vert_index)
					
					#print('-> Add indices to paramset')
					shape_params.add_integer('triindices', face_vert_indices)
					#print('-> Add verts to paramset')
					shape_params.add_point('P', points)
					#print('-> Add normals to paramset')
					shape_params.add_normal('N', normals)
					
					if uv_layer:
						#print(' %s num uvs: %i' % (obj.name, len(uvs)))
						#print('-> Add UVs to paramset')
						shape_params.add_float('uv', uvs)
					
					#print(' %s ntris: %i' % (obj.name, ntris))
					#print(' %s nvertices: %i' % (obj.name, nvertices))
					
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
						self.ExportedMeshes.add(mesh_name, mesh_definition)
					
					#LuxLog('LuxRender Mesh Exported: %s' % mesh_name)
					
				except InvalidGeometryException as err:
					LuxLog('Mesh export failed, skipping this mesh: %s' % err)
			
			del ffaces_mats
			
		except UnexportableObjectException as err:
			LuxLog('Object export failed, skipping this object: %s' % err)
		
		return mesh_definitions
	
	def allow_instancing(self, obj):
		# Some situations require full geometry export
		if self.scene.luxrender_engine.renderer == 'hybrid':
			return False
		
		# If the mesh is only used once, instancing is a waste of memory
		# ERROR: this can break dupli export if the dupli'd mesh is exported
		# before the duplicator
		#if (not self.exporting_duplis) and obj.data.users == 1:
		#	return False
		
		# Only allow instancing for duplis and particles in non-hybrid mode, or
		# for normal objects if the object has certain modifiers applied against
		# the same shared base mesh.
		if hasattr(obj, 'modifiers') and len(obj.modifiers) > 0 and obj.data.users > 1:
			#if OBJECT_ANALYSIS: print(' -> Instancing check on %s' % obj)
			instance = False
			for mod in obj.modifiers:
				#if OBJECT_ANALYSIS: print(' -> MODIFIER %s' % mod.type)
				# Allow non-deforming modifiers
				instance |= mod.type in ('COLLISION','PARTICLE_INSTANCE','PARTICLE_SYSTEM','SMOKE')
			#if OBJECT_ANALYSIS: print(' -> INSTANCING == %s'%instance)
			return instance
		else:
			return True
	
	def exportShapeDefinition(self, obj, mesh_definition):
		"""
		If the mesh is valid and instancing is allowed for this object, export
		an objectBegin..objectEnd block containing the Shape definition.
		"""
		
		me_name, me_mat_index, me_shape_type, me_shape_params = mesh_definition
		
		if len(me_shape_params) == 0: return
		
		# Shape is the only thing to go into the ObjectBegin..ObjectEnd definition
		# Everything else is set on a per-instance basis
		self.lux_context.objectBegin(me_name)
		
		# We need the transform in the object definition if this is a portal, since
		# an objectInstance won't be exported for it.
		if obj.type == 'MESH' and obj.data.luxrender_mesh.portal:
			self.lux_context.transform( matrix_to_list(obj.matrix_world, apply_worldscale=True) )
		
		self.lux_context.shape(me_shape_type, me_shape_params)
		self.lux_context.objectEnd()
		
		LuxLog('Mesh definition exported: %s' % me_name)
	
	def exportShapeInstances(self, obj, mesh_definitions, matrix=None, parent=None):
		
		# Don't export instances of portal meshes
		if obj.type == 'MESH' and obj.data.luxrender_mesh.portal: return
		
		self.lux_context.attributeBegin(comment=obj.name, file=Files.GEOM)
		
		# object translation/rotation/scale
		if matrix is not None:
			self.lux_context.transform( matrix_to_list(matrix[0], apply_worldscale=True) )
		else:
			self.lux_context.transform( matrix_to_list(obj.matrix_world, apply_worldscale=True) )
		
		# object motion blur
		is_object_animated = False
		if self.scene.camera.data.luxrender_camera.usemblur and self.scene.camera.data.luxrender_camera.objectmblur:
			if matrix is not None and matrix[1] is not None:
				next_matrices = [matrix[1]]
				is_object_animated = True
			
			else:
				next_matrices = []
				# grab a bunch of fractional-frame fcurve_matrices and export
				# several motionInstances for non-linear motion blur
				STEPS = 1
				for i in range(STEPS,0,-1):
					fcurve_matrix = object_anim_matrix(self.scene, obj, frame_offset=i/float(STEPS))
					if fcurve_matrix == False:
						break
					
					next_matrices.append(fcurve_matrix)
				
				is_object_animated = len(next_matrices) > 0
		
		if is_object_animated:
			for i, next_matrix in enumerate(next_matrices):
				self.lux_context.transformBegin(comment=obj.name)
				self.lux_context.identity()
				self.lux_context.transform(matrix_to_list(next_matrix, apply_worldscale=True))
				self.lux_context.coordinateSystem('%s_motion_%i' % (obj.name, i))
				self.lux_context.transformEnd()
		
		for me_name, me_mat_index, me_shape_type, me_shape_params in mesh_definitions:
			self.lux_context.attributeBegin()
			
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
					object_is_emitter = ob_mat.luxrender_material.export(self.lux_context, ob_mat, mode='indirect')
					self.lux_context.set_output_file(Files.GEOM)
					self.lux_context.namedMaterial(ob_mat.name)
				elif self.lux_context.API_TYPE == 'PURE':
					object_is_emitter = ob_mat.luxrender_material.export(self.lux_context, ob_mat, mode='direct')
				
				if object_is_emitter:
					self.lux_context.lightGroup(ob_mat.luxrender_emission.lightgroup, [])
					self.lux_context.areaLightSource( *ob_mat.luxrender_emission.api_output() )
				
				int_v, ext_v = get_material_volume_defs(ob_mat)
				if int_v != '':
					self.lux_context.interior(int_v)
				elif self.scene.luxrender_world.default_interior_volume != '':
					self.lux_context.interior(self.scene.luxrender_world.default_interior_volume)
				if ext_v != '':
					self.lux_context.exterior(ext_v)
				elif self.scene.luxrender_world.default_exterior_volume != '':
					self.lux_context.exterior(self.scene.luxrender_world.default_exterior_volume)
				
			else:
				object_is_emitter = False
			
			self.have_emitting_object |= object_is_emitter
			
			# If the object emits, don't export instance or motioninstance, just the Shape
			if (not self.allow_instancing(mat_object)) or object_is_emitter:
				self.lux_context.shape(me_shape_type, me_shape_params)
			# motionInstance for motion blur
			elif is_object_animated:
				num_instances = len(next_matrices)
				for i in range(num_instances):
					fni = float(num_instances) * self.scene.render.fps
					self.lux_context.motionInstance(me_name, i/fni, (i+1)/fni, '%s_motion_%i' % (obj.name, i))
			# ordinary mesh instance
			else:
				self.lux_context.objectInstance(me_name)
			
			self.lux_context.attributeEnd()
		
		self.lux_context.attributeEnd()
	
	def handler_Duplis_GENERIC(self, obj, *args, **kwargs):
		try:
			# TODO - this workaround is still needed for file->export operator
			#if 'particle_system' in kwargs.keys():
			#	prev_display_pc = kwargs['particle_system'].settings.draw_percentage
			#	if prev_display_pc < 100:
			#		LuxLog(
			#			'WARNING: Due to a limitation in blender only %s%% of particle system "%s" will be exported. '
			#			'Set the DISPLAY percentage to 100%% before exporting' % (prev_display_pc, kwargs['particle_system'].name)
			#		)
			
			obj.create_dupli_list(self.scene)
			
			if obj.dupli_list:
				LuxLog('Exporting Duplis...')
				
				det = DupliExportProgressThread()
				det.start(len(obj.dupli_list))
				
				self.exporting_duplis = True
				
				for dupli_ob in obj.dupli_list:
					
					det.exported_objects += 1
					
					if not dupli_ob.object.is_visible(self.scene) or dupli_ob.object.hide_render:
						continue
					
					if dupli_ob.object.type not in ['MESH', 'SURFACE', 'FONT']:
						continue
					
					self.exportShapeInstances(
						obj,
						self.buildMesh(dupli_ob.object),
						matrix=[dupli_ob.matrix,None],
						parent=dupli_ob.object
					)
				
				self.exporting_duplis = False
				
				det.stop()
				det.join()
				
				LuxLog('... done, exported %s duplis' % det.exported_objects)
			
			# free object dupli list again. Warning: all dupli objects are INVALID now!
			obj.free_dupli_list()
			
		except SystemError as err:
			LuxLog('Error with handler_Duplis_GENERIC and object %s: %s' % (obj, err))
	
	def handler_MESH(self, obj, *args, **kwargs):
		if OBJECT_ANALYSIS: print(' -> handler_MESH: %s' % obj)
		
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

def iterateScene(lux_context, scene):
	
	geometry_exporter = GeometryExporter(lux_context, scene)
	
	progress_thread = MeshExportProgressThread()
	progress_thread.start(len(scene.objects))
	
	for obj in scene.objects:
		if OBJECT_ANALYSIS: print('Analysing object %s : %s' % (obj, obj.type))
			
		try:
			# Export only objects which are enabled for render (in the outliner) and visible on a render layer
			if not obj.is_visible(scene) or obj.hide_render:
				raise UnexportableObjectException(' -> not visible: %s / %s' % (obj.is_visible(scene), obj.hide_render))
			
			if obj.parent and obj.parent.is_duplicator:
				raise UnexportableObjectException(' -> parent is duplicator')
			
			for mod in obj.modifiers:
				if mod.name == 'Smoke':
					if mod.smoke_type == 'DOMAIN':
						raise UnexportableObjectException(' -> Smoke domain')
			
			number_psystems = len(obj.particle_systems)
			
			if obj.is_duplicator and number_psystems < 1:
				if OBJECT_ANALYSIS: print(' -> is duplicator without particle systems')
				if obj.dupli_type in geometry_exporter.valid_duplis_callbacks:
					geometry_exporter.callbacks['duplis'][obj.dupli_type](obj)
				elif OBJECT_ANALYSIS: print(' -> Unsupported Dupli type: %s' % obj.dupli_type)
			
			# Some dupli types should hide the original
			if obj.is_duplicator and obj.dupli_type in ('VERTS', 'FACES'):
				export_original_object = False
			else:
				export_original_object = True
			
			if number_psystems > 0:
				export_original_object = False
				if OBJECT_ANALYSIS: print(' -> has %i particle systems' % number_psystems)
				for psys in obj.particle_systems:
					export_original_object = export_original_object or psys.settings.use_render_emitter
					if psys.settings.render_type in geometry_exporter.valid_particles_callbacks:
						geometry_exporter.callbacks['particles'][psys.settings.render_type](obj, particle_system=psys)
					elif OBJECT_ANALYSIS: print(' -> Unsupported Particle system type: %s' % psys.settings.render_type)
			
			if not export_original_object:
				raise UnexportableObjectException('export_original_object=False')
			
			if not obj.type in geometry_exporter.valid_objects_callbacks:
				raise UnexportableObjectException('Unsupported object type')
			
			geometry_exporter.callbacks['objects'][obj.type](obj)
		
		except UnexportableObjectException as err:
			if OBJECT_ANALYSIS: print(' -> Unexportable object: %s : %s : %s' % (obj, obj.type, err))
		
		progress_thread.exported_objects += 1
	
	progress_thread.stop()
	progress_thread.join()
	
	# we keep a copy of the mesh_names exported for use as portalInstances when we export the lights
	mesh_names = geometry_exporter.ExportedMeshes.cache_keys.copy()
	
	return mesh_names, geometry_exporter.have_emitting_object

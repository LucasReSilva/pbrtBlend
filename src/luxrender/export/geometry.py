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

from extensions_framework import util as efutil

from luxrender.outputs import LuxLog
from luxrender.outputs.file_api import Files
from luxrender.export import ParamSet, ExportProgressThread, ExportCache, object_anim_matrix
from luxrender.export import matrix_to_list
from luxrender.export.materials import get_material_volume_defs

def time_export(func):
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
	lux_context = None
	scene = None
	
	ExportedMeshes = None
	ExportedObjects = None
	
	callbacks = {}
	valid_duplis_callbacks = []
	valid_particles_callbacks = []
	valid_objects_callbacks = []
	
	have_emitting_object = False
	
	def __init__(self, lux_context, scene):
		self.lux_context = lux_context
		self.scene = scene
		
		self.ExportedMeshes = ExportCache('ExportedMeshes')
		self.ExportedObjects = ExportCache('ExportedObjects')
		
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
			global_type = self.scene.luxrender_engine.mesh_type
			if mesh_type == 'native' or (mesh_type == 'global' and global_type == 'native'):
				mesh_definitions.extend( self.buildNativeMesh(obj) )
			if mesh_type == 'binary_ply' or (mesh_type == 'global' and global_type == 'binary_ply'):
				mesh_definitions.extend( self.buildBinaryPLYMesh(obj) )
		
		self.ExportedObjects.add(obj, mesh_definitions)
		return mesh_definitions
	
	#@time_export
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
			
			# Cache vert positions because me.vertices access is very slow
			#print('-> Cache vert pos and normals')
			verts_co_no = [tuple(v.co)+tuple(v.normal) for v in mesh.vertices]
			
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
					
					# If this mesh/mat combo has already been processed, get it from the cache
					if self.allow_instancing(obj) and self.ExportedMeshes.have(mesh_name):
						mesh_definitions.append( self.ExportedMeshes.get(mesh_name) )
						continue
					
					ply_filename = '%s.ply' % mesh_name
					# Binary PLY mesh translation goes in here
					with open(ply_filename, 'wb') as ply:
						
						ply.write(b'ply\n')
						ply.write(b'format binary_little_endian 1.0\n')
						ply.write(b'comment Created by LuxBlend 2.5 exporter for LuxRender - www.luxrender.net\n')
						
						total_verts = 0
						for face in ffaces_mats[i]:
							total_verts += len(face.vertices)
						
						ply.write( ('element vertex %d\n' % total_verts).encode() )
						ply.write(b'property float x\n')
						ply.write(b'property float y\n')
						ply.write(b'property float z\n')
						
						ply.write(b'property float nx\n')
						ply.write(b'property float ny\n')
						ply.write(b'property float nz\n')
						
						if len(mesh.uv_textures) > 0:
							if mesh.uv_textures.active and mesh.uv_textures.active.data:
								uv_layer = mesh.uv_textures.active.data
						else:
							uv_layer = None
						
						if uv_layer:
							ply.write(b'property float s\n')
							ply.write(b'property float t\n')
						
						ply.write( ('element face %d\n' % len(ffaces_mats[i])).encode() )
						ply.write(b'property list uchar uint vertex_indices\n')
						
						ply.write(b'end_header\n')
						
						# dump vertices and normals and uvs if present
						for face in ffaces_mats[i]:
							for j, vertex in enumerate(face.vertices):
								if face.use_smooth:
									ply.write( struct.pack('<6f', *verts_co_no[vertex]) )
								else:
									ply.write( struct.pack('<3f', *verts_co_no[vertex][:3]) )
									ply.write( struct.pack('<3f', *face.normal) )
								if uv_layer:
									uv = uv_layer[face.index].uv[j]
									ply.write( struct.pack('<2f', *uv ) )
						
						index = 0
						# dump face vert indices
						for face in ffaces_mats[i]:
							num_verts = len(face.vertices)
							ply.write( struct.pack('<B', num_verts) )
							for j in range(num_verts):
								ply.write( struct.pack('<I',index+j) )
							index += num_verts
					
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
					
					LuxLog('Binary PLY Mesh Exported: %s' % mesh_name)
					
				except InvalidGeometryException as err:
					LuxLog('Mesh export failed, skipping this mesh: %s' % err)
		
		except UnexportableObjectException as err:
			LuxLog('Object export failed, skipping this object: %s' % err)
		
		return mesh_definitions
	
	#@time_export
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
			
			# Cache vert positions because me.vertices access is very slow
			#print('-> Cache vert pos and normals')
			verts_co_no = [tuple(v.co)+tuple(v.normal) for v in mesh.vertices]
			
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
					
					# face indices
					index = 0
					indices = []
					ntris = 0
					#print('-> Collect face indices')
					for face in ffaces_mats[i]:
						indices.append(index)
						indices.append(index+1)
						indices.append(index+2)
						ntris += 3
						if (len(face.vertices)==4):
							indices.append(index)
							indices.append(index+2)
							indices.append(index+3)
							ntris += 3
						index += len(face.vertices)
					
					if ntris == 0:
						raise InvalidGeometryException('Mesh has no tris')
					
					# vertex positions
					points = []
					#print('-> Collect vert positions')
					nvertices = 0
					for face in ffaces_mats[i]:
						for vertex in face.vertices:
							v = verts_co_no[vertex][:3]
							nvertices += 1
							for co in v:
								points.append(co)
					
					if nvertices == 0:
						raise InvalidGeometryException('Mesh has no verts')
					
					# vertex normals
					#print('-> Collect mert normals')
					normals = []
					for face in ffaces_mats[i]:
						normal = face.normal
						for vertex in face.vertices:
							if face.use_smooth:
								normal = verts_co_no[vertex][3:]
							for no in normal:
								normals.append(no)
					
					# uv coordinates
					#print('-> Collect UV layers')
					
					if len(mesh.uv_textures) > 0:
						if mesh.uv_textures.active and mesh.uv_textures.active.data:
							uv_layer = mesh.uv_textures.active.data
					else:
						uv_layer = None
					
					if uv_layer:
						uvs = []
						try:
							for face in ffaces_mats[i]:
								for uv in uv_layer[face.index].uv:
									for uv_coord in uv:
										uvs.append(uv_coord)
						
						except IndexError:
							LuxLog('ERROR: Incomplete UV map for %s, skipping UV export' % obj)
							uv_layer = None
					
					#print(' %s num points: %i' % (obj.name, len(points)))
					#print(' %s num normals: %i' % (obj.name, len(normals)))
					#print(' %s num idxs: %i' % (obj.name, len(indices)))
					
					# build shape ParamSet
					shape_params = ParamSet()
					
					if self.lux_context.API_TYPE == 'PURE':
						# ntris isn't really the number of tris!!
						shape_params.add_integer('ntris', ntris)
						shape_params.add_integer('nvertices', nvertices)
					
					#print('-> Add indices to paramset')
					shape_params.add_integer('triindices', indices)
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
					
					LuxLog('LuxRender Mesh Exported: %s' % mesh_name)
					
				except InvalidGeometryException as err:
					LuxLog('Mesh export failed, skipping this mesh: %s' % err)
		
		except UnexportableObjectException as err:
			LuxLog('Object export failed, skipping this object: %s' % err)
		
		return mesh_definitions
	
	def allow_instancing(self, obj):
		# Some situations require full geometry export
		if self.scene.luxrender_engine.renderer == 'hybrid':
			return False
		
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
	
	def exportShapeInstances(self, obj, mesh_definitions, matrix=None):
		
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
			
			ob_mat = obj.material_slots[me_mat_index].material
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
			if (not self.allow_instancing(obj)) or object_is_emitter:
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
		dupli_object_names = set()
		
		try:
			# ridiculous work-around for exporting every particle
			if 'particle_system' in kwargs.keys():
				prev_display_pc = kwargs['particle_system'].settings.draw_percentage
				if prev_display_pc < 100:
					LuxLog(
						'WARNING: Due to a limitation in blender only %s%% of particle system "%s" will be exported. '
						'Set the DISPLAY percentage to 100%% before exporting' % (prev_display_pc, kwargs['particle_system'].name)
					)
				# The rest of this workaround is disabled due to RNA write restriction
#				kwargs['particle_system'].settings.draw_percentage = 100
#				obj.tag = True
#				self.scene.update()
			
			obj.create_dupli_list(self.scene)
			
			if obj.dupli_list:
				LuxLog('Exporting Duplis...')
				
				det = DupliExportProgressThread()
				det.start(len(obj.dupli_list))
				
				for dupli_ob in obj.dupli_list:
					if dupli_ob.object.type not in  ['MESH', 'SURFACE', 'FONT']:
						continue
					
					self.exportShapeInstances(
						obj,
						self.buildMesh(dupli_ob.object),
						matrix=[dupli_ob.matrix,None]
					)
					
					dupli_object_names.add( dupli_ob.object.name )
					
					det.exported_objects += 1
				
				det.stop()
				det.join()
				
				LuxLog('... done, exported %s duplis' % det.exported_objects)
			
			# free object dupli list again. Warning: all dupli objects are INVALID now!
			obj.free_dupli_list()
			
#			if 'particle_system' in kwargs.keys():
#				kwargs['particle_system'].settings.draw_percentage = prev_display_pc
#				obj.tag = True
#				self.scene.update()
			
		except SystemError as err:
			LuxLog('Error with handler_Duplis_GENERIC and object %s: %s' % (obj, err))
		
		return dupli_object_names
	
	#def handler_Duplis_PATH(lux_context, scene, obj, *args, **kwargs):
	#	if not 'particle_system' in kwargs.keys(): return
	#	
	#	import mathutils
	#	
	#	cyl = ParamSet()\
	#			.add_float('radius', 0.0005) \
	#			.add_float('zmin', 0.0) \
	#			.add_float('zmax', 1.0)
	#	
	#	strand = ('%s_hair'%obj.name, obj.active_material, 'cylinder', cyl)
	#	
	#	exportShapeDefinition(lux_context, obj, strand)
	#	
	#	scale_z = mathutils.Vector([0.0, 0.0, 1.0])
	#	
	#	for particle in kwargs['particle_system'].particles:
	#		for i in range(len(particle.hair)-1):
	#			segment_length = (particle.hair[i].co - particle.hair[i+1].co).length
	#			segment_matrix = mathutils.Matrix.Translation( particle.hair[i].co_hair_space + particle.location )
	#			segment_matrix *= mathutils.Matrix.Scale(segment_length, 4, scale_z)
	#			segment_matrix *= particle.rotation.to_matrix().resize_4x4()
	#			
	#			exportShapeInstances(lux_context, scene, obj, [strand], matrix=[segment_matrix,None])
	
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
	

# TODO: allow swapping out geometry_exporter for some other handler
# in order to make this function re-usable for other scene elements ?
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
			
			number_psystems = len(obj.particle_systems)
			
			if obj.is_duplicator and number_psystems < 1:
				if OBJECT_ANALYSIS: print(' -> is duplicator without particle systems')
				if obj.dupli_type in geometry_exporter.valid_duplis_callbacks:
					geometry_exporter.callbacks['duplis'][obj.dupli_type](obj)
				elif OBJECT_ANALYSIS: print(' -> Unsupported Dupli type: %s' % obj.dupli_type)
			
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

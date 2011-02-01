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
import os
OBJECT_ANALYSIS = os.getenv('LB25_OBJECT_ANALYSIS', False)

from extensions_framework import util as efutil

from luxrender.outputs import LuxLog
from luxrender.outputs.file_api import Files
from luxrender.export import ParamSet, LuxManager
from luxrender.export import matrix_to_list

class InvalidGeometryException(Exception):
	pass

class UnexportableObjectException(Exception):
	pass

def buildNativeMesh(lux_context, scene, obj):
	"""
	Convert supported blender objects into a MESH, and then split into parts
	according to vertex material assignment, and construct a mesh_name and
	ParamSet for each part which will become a LuxRender Shape statement
	wrapped within objectBegin..objectEnd or placed in an
	attributeBegin..attributeEnd scope, depending if instancing is allowed.
	"""
	
	# Using a cache on object massively speeds up dupli instance export
	if lux_context.ExportedObjects.have(obj): return lux_context.ExportedObjects.get(obj)
	
	mesh_definitions = []
	
	ply_mesh_name = '%s_ply' % obj.data.name
	if obj.luxrender_object.append_external_mesh:
		if allow_instancing(lux_context, obj) and lux_context.ExportedMeshes.have(ply_mesh_name):
			mesh_definitions.append( lux_context.ExportedMeshes.get(ply_mesh_name) )
		else:
			ply_params = ParamSet()
			ply_params.add_string('filename', efutil.path_relative_to_export(obj.luxrender_object.external_mesh))
			ply_params.add_bool('smooth', obj.luxrender_object.use_smoothing)
			
			mesh_definition = (ply_mesh_name, obj.active_material, 'plymesh', ply_params)
			mesh_definitions.append( mesh_definition )
			
			# Only export objectBegin..objectEnd and cache this mesh_definition if we plan to use instancing
			if allow_instancing(lux_context, obj):
				exportMeshDefinition(lux_context, mesh_definition)
				lux_context.ExportedMeshes.add(ply_mesh_name, mesh_definition)
	
	try:
		#(not a) or (a and not b) == not (a and b)
		if not (obj.luxrender_object.append_external_mesh and obj.luxrender_object.hide_proxy_mesh):
			mesh = obj.create_mesh(scene, True, 'RENDER')
			if mesh is None:
				raise UnexportableObjectException('Cannot create render/export mesh')
			
			# Cache vert positions because me.vertices access is very slow
			#print('-> Cache vert pos and normals')
			verts_co_no = [tuple(v.co)+tuple(v.normal) for v in mesh.vertices]
			
			# collate faces and face verts by mat index
			faces_verts_mats = {}
			ffaces_mats = {}
			for f in mesh.faces:
				mi = f.material_index
				if mi not in faces_verts_mats.keys(): faces_verts_mats[mi] = []
				faces_verts_mats[mi].append( f.vertices )
				if mi not in ffaces_mats.keys(): ffaces_mats[mi] = []
				ffaces_mats[mi].append( f )
			
			number_of_mats = len(mesh.materials)
			if number_of_mats > 0:
				iterator_range = range(number_of_mats)
			else:
				iterator_range = [0]
			
			for i in iterator_range:
				try:
					if i not in faces_verts_mats.keys(): continue
					if i not in ffaces_mats.keys(): continue
					
					try:
						mesh_mat = mesh.materials[i]
					except IndexError:
						mesh_mat = None
					
					if mesh_mat is not None:
						mesh_name = ('%s_%s' % (obj.data.name, mesh_mat.name)).replace(' ','_')
					else:
						mesh_name = obj.data.name.replace(' ','_')
					
					# If this mesh/mat combo has already been processed, get it from the cache
					if allow_instancing(lux_context, obj) and lux_context.ExportedMeshes.have(mesh_name):
						mesh_definitions.append( lux_context.ExportedMeshes.get(mesh_name) )
						continue
					
					if OBJECT_ANALYSIS: print(' -> NativeMesh:')
					if OBJECT_ANALYSIS: print('  -> Material: %s' % mesh_mat)
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
						for fi, uv in enumerate(uv_layer):
							# TODO: The following line is iffy
							if fi in range(len(faces_verts_mats[i])) and len(faces_verts_mats[i][fi]) == 4:
								face_uvs = uv.uv1, uv.uv2, uv.uv3, uv.uv4
							else:
								face_uvs = uv.uv1, uv.uv2, uv.uv3
							for uv in face_uvs:
								for single_uv in uv:
									uvs.append(single_uv)
					
					#print(' %s num points: %i' % (obj.name, len(points)))
					#print(' %s num normals: %i' % (obj.name, len(normals)))
					#print(' %s num idxs: %i' % (obj.name, len(indices)))
					
					# build shape ParamSet
					shape_params = ParamSet()
					
					if lux_context.API_TYPE == 'PURE':
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
						mesh_mat,
						obj.data.luxrender_mesh.get_shape_type(),
						shape_params
					)
					mesh_definitions.append( mesh_definition )
					
					# Only export objectBegin..objectEnd and cache this mesh_definition if we plan to use instancing
					if allow_instancing(lux_context, obj):
						exportMeshDefinition(lux_context, mesh_definition)
						lux_context.ExportedMeshes.add(mesh_name, mesh_definition)
					
					LuxLog('Mesh Exported: %s' % mesh_name)
					
				except InvalidGeometryException as err:
					LuxLog('Mesh export failed, skipping this mesh: %s' % err)
		
		lux_context.ExportedObjects.add(obj, mesh_definitions)
	
	except UnexportableObjectException as err:
		LuxLog('Object export failed, skipping this object: %s' % err)
	
	return mesh_definitions

def allow_instancing(lux_context, obj=None):
	# Some situations require full geometry export
	if LuxManager.CurrentScene.luxrender_engine.renderer == 'hybrid':
		return False
	
	# Only allow instancing for duplis and particles in non-hybrid mode, or
	# for normal objects if the object has certain modifiers applied against
	# the same shared base mesh.
	if obj is not None and hasattr(obj, 'modifiers') and len(obj.modifiers) > 0 and obj.data.users > 1:
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

def exportMeshDefinition(lux_context, mesh_definition):
	"""
	If the mesh is valid and instancing is allowed for this object, export
	an objectBegin..objectEnd block containing the Shape definition.
	"""
	
	me_name, me_mat, me_shape_type, me_shape_params = mesh_definition
	
	if len(me_shape_params) == 0: return
	#if not allow_instancing(lux_context): return
	
	# Shape is the only thing to go into the ObjectBegin..ObjectEnd definition
	# Everything else is set on a per-instance basis
	lux_context.objectBegin(me_name)
	lux_context.shape(me_shape_type, me_shape_params)
	lux_context.objectEnd()

def get_material_volume_defs(m):
	return m.luxrender_material.Interior_volume, m.luxrender_material.Exterior_volume

def exportMeshInstances(lux_context, obj, mesh_definitions, matrix=None):
	scene = LuxManager.CurrentScene
	
	lux_context.attributeBegin(comment=obj.name, file=Files.GEOM)
	
	# object translation/rotation/scale
	if matrix is not None:
		lux_context.transform( matrix_to_list(matrix[0], apply_worldscale=True) )
	else:
		lux_context.transform( matrix_to_list(obj.matrix_world, apply_worldscale=True) )
	
	# object motion blur
	is_object_animated = False
	if scene.camera.data.luxrender_camera.usemblur and scene.camera.data.luxrender_camera.objectmblur:
		if matrix is not None and matrix[1] is not None:
			m1 = matrix[1]
			is_object_animated = True
		else:
			scene.frame_set(scene.frame_current + 1)
			m1 = obj.matrix_world.copy()
			scene.frame_set(scene.frame_current - 1)
			scene.update()
			is_object_animated =  m1 != obj.matrix_world
	
	if is_object_animated:
		lux_context.transformBegin(comment=obj.name, file=Files.GEOM)
		lux_context.identity()
		lux_context.transform(matrix_to_list(m1, apply_worldscale=True))
		lux_context.coordinateSystem('%s' % obj.name + '_motion')
		lux_context.transformEnd()
	
	for me_name, me_mat, me_shape_type, me_shape_params in mesh_definitions:
		lux_context.attributeBegin()
		
		if me_mat is not None:
			
			# Check for emission and volume data
			object_is_emitter = hasattr(me_mat, 'luxrender_emission') and me_mat.luxrender_emission.use_emission
			if object_is_emitter:
				lux_context.lightGroup(me_mat.luxrender_emission.lightgroup, [])
				lux_context.areaLightSource( *me_mat.luxrender_emission.api_output() )
			
			if hasattr(me_mat, 'luxrender_material'):
				int_v, ext_v = get_material_volume_defs(me_mat)
				if int_v != '':
					lux_context.interior(int_v)
				elif scene.luxrender_world.default_interior_volume != '':
					lux_context.interior(scene.luxrender_world.default_interior_volume)
				if ext_v != '':
					lux_context.exterior(ext_v)
				elif scene.luxrender_world.default_exterior_volume != '':
					lux_context.exterior(scene.luxrender_world.default_exterior_volume)
			
			if lux_context.API_TYPE == 'FILE':
				lux_context.namedMaterial(me_mat.name)
			elif lux_context.API_TYPE == 'PURE':
				me_mat.luxrender_material.export(lux_context, me_mat, mode='direct')
		
		else:
			object_is_emitter = False
		
		instance = allow_instancing(lux_context, obj)
		
		#if OBJECT_ANALYSIS: print(' -> instance? %s' % instance)
		#if OBJECT_ANALYSIS: print(' -> emitter?  %s' % object_is_emitter)
		#if OBJECT_ANALYSIS: print(' -> animated? %s' % is_object_animated)
		
		# If the object emits, don't export instance or motioninstance, just the Shape
		if (not instance) or object_is_emitter:
			lux_context.shape(me_shape_type, me_shape_params)
		# motionInstance for motion blur
		elif is_object_animated:
			lux_context.motionInstance(me_name, 0.0, 1.0, obj.name + '_motion')
		# ordinary mesh instance
		else:
			lux_context.objectInstance(me_name)
		
		lux_context.attributeEnd()
	
	lux_context.attributeEnd()

class ExportProgressThread(efutil.TimerThread):
	message = '%i%%'
	KICK_PERIOD = 0.2
	total_objects = 0
	exported_objects = 0
	last_update = 0
	def start(self, number_of_meshes):
		self.total_objects = number_of_meshes
		self.exported_objects = 0
		self.last_update = 0
		super().start()
	def kick(self):
		if self.exported_objects != self.last_update:
			self.last_update = self.exported_objects
			pc = int(100 * self.exported_objects/self.total_objects)
			LuxLog(self.message % pc)

class MeshExportProgressThread(ExportProgressThread):
	message = 'Exporting meshes: %i%%'

class DupliExportProgressThread(ExportProgressThread):
	message = '...  %i%% ...'

class ExportCache(object):
	
	name = 'Cache'
	cache_keys = set()
	cache_items = {}
	
	def __init__(self, name):
		self.name = name
		self.cache_keys = set()
		self.cache_items = {}
	
	def have(self, ck):
		return ck in self.cache_keys
	
	def add(self, ck, ci):
		self.cache_keys.add(ck)
		self.cache_items[ck] = ci
		
	def get(self, ck):
		if self.have(ck):
			return self.cache_items[ck]
		else:
			raise InvalidGeometryException('Item %s not found in %s!' % (ck, self.name))

def handler_Duplis_GENERIC(lux_context, scene, obj, *args, **kwargs):
	dupli_object_names = set()
	
	try:
		# ridiculous work-around for exporting every particle
		if 'particle_system' in kwargs.keys():
			prev_display_pc = kwargs['particle_system'].settings.draw_percentage
			kwargs['particle_system'].settings.draw_percentage = 100
			obj.tag = True
			scene.update()
		
		obj.create_dupli_list(scene)
		
		if obj.dupli_list:
			LuxLog('Exporting Duplis...')
			
			det = DupliExportProgressThread()
			det.start(len(obj.dupli_list))
			
			for dupli_ob in obj.dupli_list:
				if dupli_ob.object.type not in  ['MESH', 'SURFACE', 'FONT']:
					continue
				
				exportMeshInstances(
					lux_context,
					obj,
					buildNativeMesh(lux_context, scene, dupli_ob.object),
					matrix=[dupli_ob.matrix,None]
				)
				
				dupli_object_names.add( dupli_ob.object.name )
				
				det.exported_objects += 1
			
			det.stop()
			det.join()
			
			LuxLog('... done, exported %s duplis' % len(obj.dupli_list))
		
		# free object dupli list again. Warning: all dupli objects are INVALID now!
		obj.free_dupli_list()
		
		if 'particle_system' in kwargs.keys():
			kwargs['particle_system'].settings.draw_percentage = prev_display_pc
			obj.tag = True
			scene.update()
		
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
#	exportMeshDefinition(lux_context, strand)
#	
#	scale_z = mathutils.Vector([0.0, 0.0, 1.0])
#	
#	for particle in kwargs['particle_system'].particles:
#		for i in range(len(particle.hair)-1):
#			segment_length = (particle.hair[i].co - particle.hair[i+1].co).length
#			segment_matrix = mathutils.Matrix.Translation( particle.hair[i].co_hair_space + particle.location )
#			segment_matrix *= mathutils.Matrix.Scale(segment_length, 4, scale_z)
#			segment_matrix *= particle.rotation.to_matrix().resize4x4()
#			
#			exportMeshInstances(lux_context, obj, [strand], matrix=[segment_matrix,None])

def handler_MESH(lux_context, scene, obj, *args, **kwargs):
	if OBJECT_ANALYSIS: print(' -> handler_MESH: %s' % obj)
	
	exportMeshInstances(
		lux_context,
		obj,
		buildNativeMesh(lux_context, scene, obj)
	)

callbacks = {
	'duplis': {
		'FACES': handler_Duplis_GENERIC,
		'GROUP': handler_Duplis_GENERIC,
		'VERTS': handler_Duplis_GENERIC,
	},
	'particles': {
		'OBJECT': handler_Duplis_GENERIC,
		'GROUP': handler_Duplis_GENERIC,
		#'PATH': handler_Duplis_PATH,
	},
	'objects': {
		'MESH': handler_MESH,
		'SURFACE': handler_MESH,
		'FONT': handler_MESH
	}
}

def iterateScene(lux_context, scene):
	lux_context.ExportedMeshes = ExportCache('ExportedMeshes')
	lux_context.ExportedObjects = ExportCache('ExportedObjects')
	
	valid_duplis_callbacks = callbacks['duplis'].keys()
	valid_particles_callbacks = callbacks['particles'].keys()
	valid_objects_callbacks = callbacks['objects'].keys()
	
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
				if obj.dupli_type in valid_duplis_callbacks:
					callbacks['duplis'][obj.dupli_type](lux_context, scene, obj)
				elif OBJECT_ANALYSIS: print(' -> Unsupported Dupli type: %s' % obj.dupli_type)
			
			export_original_object = True
			
			if number_psystems > 0:
				export_original_object = False
				if OBJECT_ANALYSIS: print(' -> has %i particle systems' % number_psystems)
				for psys in obj.particle_systems:
					export_original_object = export_original_object or psys.settings.use_render_emitter
					if psys.settings.render_type in valid_particles_callbacks:
						callbacks['particles'][psys.settings.render_type](lux_context, scene, obj, particle_system=psys)
					elif OBJECT_ANALYSIS: print(' -> Unsupported Particle system type: %s' % psys.settings.render_type)
			
			if not export_original_object:
				raise UnexportableObjectException('export_original_object=False')
			
			if not obj.type in valid_objects_callbacks:
				raise UnexportableObjectException('Unsupported object type')
			
			callbacks['objects'][obj.type](lux_context, scene, obj)
		
		except UnexportableObjectException as err:
			if OBJECT_ANALYSIS: print(' -> Unexportable object: %s : %s : %s' % (obj, obj.type, err))
		
		progress_thread.exported_objects += 1
	
	progress_thread.stop()
	progress_thread.join()
	
	# we keep a copy of the mesh_names exported for use as portalInstances
	# when we export the lights
	mesh_names = lux_context.ExportedMeshes.cache_keys
	
	del lux_context.ExportedMeshes
	del lux_context.ExportedObjects
	
	return mesh_names

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
import bpy, mathutils

from extensions_framework import util as efutil

from luxrender.outputs import LuxLog
from luxrender.outputs.file_api import Files
from luxrender.export import ParamSet, LuxManager
from luxrender.export import matrix_to_list
from luxrender.export.materials import add_texture_parameter

OBJECT_ANALYSIS = True

class InvalidGeometryException(Exception):
	pass

def buildNativeMesh(lux_context, object):
	"""
	Split up a blender MESH into parts according to vertex material assignment,
	and construct a mesh_name and ParamSet for each part which will become a
	LuxRender Shape statement wrapped within objectBegin..objectEnd or placed
	in an attributeBegin..attributeEnd scope.
	"""
	
	scene = LuxManager.CurrentScene
	mesh = object.create_mesh(scene, True, 'RENDER')
	if mesh is None:
		raise InvalidGeometryException('Cannot create render/export mesh')
	
	mesh_definitions = []
	
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
	
	for i in range(len(mesh.materials)):
		
		if mesh.materials[i] is None: continue
		if i not in faces_verts_mats.keys(): continue
		if i not in ffaces_mats.keys(): continue
		
		mesh_name = ('%s_%s' % (object.data.name, mesh.materials[i].name)).replace(' ','_')
		
		if ExportedMeshes.have(mesh_name):
			mesh_definitions.append( ExportedMeshes.get(mesh_name) )
			continue
		
		if OBJECT_ANALYSIS: print(' -> NativeMesh:')
		if OBJECT_ANALYSIS: print('  -> Material: %s' % mesh.materials[i])
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
			raise InvalidGeometryException()
		
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
			raise InvalidGeometryException()
		
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
		
		#print(' %s num points: %i' % (ob.name, len(points)))
		#print(' %s num normals: %i' % (ob.name, len(normals)))
		#print(' %s num idxs: %i' % (ob.name, len(indices)))
		
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
			#print(' %s num uvs: %i' % (ob.name, len(uvs)))
			#print('-> Add UVs to paramset')
			shape_params.add_float('uv', uvs)
		
		#print(' %s ntris: %i' % (ob.name, ntris))
		#print(' %s nvertices: %i' % (ob.name, nvertices))
		
		# Add other properties from LuxRender Mesh panel
		shape_params.update( object.data.luxrender_mesh.get_paramset() )
		
		mesh_definition = (
			mesh_name,
			mesh.materials[i],
			object.data.luxrender_mesh.get_shape_type(),
			shape_params
		)
		mesh_definitions.append( mesh_definition )
		exportMeshDefinition(lux_context, mesh_definition)
		ExportedMeshes.add(mesh_name, mesh_definition)
	
	return mesh_definitions

def exportMeshDefinition(lux_context, mesh_definition):
	"""
	If the mesh is valid and instancing is allowed for this object, export
	an objectBegin..objectEnd block containing the Shape definition.
	"""
	
	me_name, me_mat, me_shape_type, me_shape_params = mesh_definition
	
	if len(me_shape_params) == 0: return
	if not allow_instancing(): return
	
	LuxLog('Mesh Exported: %s' % me_name)
	
	# Shape is the only thing to go into the ObjectBegin..ObjectEnd definition
	# Everything else is set on a per-instance basis
	lux_context.objectBegin(me_name)
	lux_context.shape(me_shape_type, me_shape_params)
	lux_context.objectEnd()

def allow_instancing():
	# Some situations require full geometry export
	if LuxManager.CurrentScene.luxrender_engine.renderer == 'hybrid':
		return False
	
	# Only allow instancing for duplis and particles in non-hybrid mode
	return True

def get_material_volume_defs(m):
	return m.luxrender_material.Interior_volume, m.luxrender_material.Exterior_volume

def exportMeshInstance(lux_context, ob, mesh_definition, matrix=None):
	scene = LuxManager.CurrentScene
	
	me_name, me_mat, me_shape_type, me_shape_params = mesh_definition
	
	lux_context.attributeBegin(comment=me_name, file=Files.GEOM)
	
	# object translation/rotation/scale
	if matrix is not None:
		lux_context.transform( matrix_to_list(matrix, apply_worldscale=True) )
	else:
		lux_context.transform( matrix_to_list(ob.matrix_world, apply_worldscale=True) )
	
	# Check for emission and volume data
	object_is_emitter = hasattr(ob, 'luxrender_emission') and ob.luxrender_emission.use_emission
	if object_is_emitter:
		lux_context.lightGroup(ob.luxrender_emission.lightgroup, [])
		arealightsource_params = ParamSet() \
				.add_float('gain', ob.luxrender_emission.gain) \
				.add_float('power', ob.luxrender_emission.power) \
				.add_float('efficacy', ob.luxrender_emission.efficacy)
		arealightsource_params.update( add_texture_parameter(lux_context, 'L', 'color', ob.luxrender_emission) )
		lux_context.areaLightSource('area', arealightsource_params)
	
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
	
	# object motion blur
	is_object_animated = False
	if scene.camera.data.luxrender_camera.usemblur and scene.camera.data.luxrender_camera.objectmblur:
		scene.frame_set(scene.frame_current + 1)
		if matrix is not None:
			m1 = matrix.copy()
		else:
			m1 = object.matrix_world.copy()
		scene.frame_set(scene.frame_current - 1)
		scene.update()
		if matrix is not None:
			is_object_animated =  m1 != matrix
		else:
			is_object_animated =  m1 != object.matrix_world
	
	# If the object emits, don't export instance or motioninstance, just the Shape
	if (not allow_instancing()) or object_is_emitter:
		lux_context.shape(me_shape_type, me_shape_params)
	# motionInstance for motion blur
	elif is_object_animated:
		lux_context.transformBegin(comment=me_name, file=Files.GEOM)
		lux_context.identity()
		lux_context.transform(matrix_to_list(m1, apply_worldscale=True))
		lux_context.coordinateSystem('%s' % me_name + '_motion')
		lux_context.transformEnd()
		lux_context.motionInstance(me_name, 0.0, 1.0, me_name + '_motion')
	# ordinary mesh instance
	else:
		lux_context.objectInstance(me_name)
	
	lux_context.attributeEnd()

class MeshExportProgressThread(efutil.TimerThread):
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
			LuxLog('LuxRender: Parsing meshes %i%%' % pc)
			bpy.ops.ef.msg(
				msg_type='INFO',
				msg_text='LuxRender: Parsing meshes %i%%' % pc
			)

class ExportedMeshes(object):
	mesh_names = set()
	mesh_definitions = {}
	
	@classmethod
	def reset(cls):
		cls.mesh_names = set()
		cls.mesh_definitions = {}
	
	@classmethod
	def have(cls, mesh_name):
		return mesh_name in cls.mesh_names
	
	@classmethod
	def add(cls, mesh_name, mesh_definition):
		cls.mesh_names.add(mesh_name)
		cls.mesh_definitions[mesh_name] = mesh_definition
		
	@classmethod
	def get(cls, mesh_name):
		if cls.have(mesh_name):
			return cls.mesh_definitions[mesh_name]
		else:
			raise InvalidGeometryException('Mesh definition not found in cache!')

def handler_Duplis_GENERIC(lux_context, scene, object):
	object.create_dupli_list(scene)
	
	for dupli_ob in object.dupli_list:
		if dupli_ob.object.type != 'MESH':
			continue
		
		if OBJECT_ANALYSIS: print('  -> exporting dupli mesh(s) for %s' % object.name )
		dupli_meshes = buildNativeMesh(lux_context, dupli_ob.object)
	
		if OBJECT_ANALYSIS: print('  -> exporting dupli instance(s) for %s' % object.name )
		for mesh_definition in dupli_meshes:
			exportMeshInstance(lux_context, object, mesh_definition, matrix=dupli_ob.matrix)
	
	# free object dupli list again. Warning: all dupli objects are INVALID now!
	if OBJECT_ANALYSIS: print(' -> parsed %i dupli objects' % len(object.dupli_list))
	if object.dupli_list: 
		object.free_dupli_list()

def handler_Duplis_GROUP(lux_context, scene, object):
	if OBJECT_ANALYSIS: print(' -> handler_Duplis_GROUP: %s' % object)
	handler_Duplis_GENERIC(lux_context, scene, object)

def handler_Duplis_VERTS(lux_context, scene, object):
	if OBJECT_ANALYSIS: print(' -> handler_Duplis_VERTS: %s' % object)
	handler_Duplis_GENERIC(lux_context, scene, object)

#def handler_Particles_OBJECT(lux_context, scene, object):
#	if OBJECT_ANALYSIS: print(' -> handler_Particles_OBJECT: %s' % object)
#	particle_object = psys_settings.dupli_object
#					
#	mesh_names = []
#	
#	# Scan meshes first
#	for particle in psys.particles:
#		if particle.is_visible and (particle.alive_state in allowed_particle_states):
#			if allow_instancing(dupli=True) and (particle_object.data.name not in meshes_exported):
#				mesh_names = exportMesh(lux_context, particle_object, scale=[particle.size]*3, log=False)
#				meshes_exported.add(particle_object.data.name)
#	
#	# Export instances second
#	for particle in psys.particles:
#		if particle.is_visible and (particle.alive_state in allowed_particle_states):
#			particle_matrix = mathutils.Matrix.Translation( particle.location )
#			particle_matrix *= particle.rotation.to_matrix().to_4x4()
#			#particle_matrix *= mathutils.Matrix.Scale(particle.size, 4)
#			exportInstance(lux_context, particle_object, particle_matrix, dupli=True, append_objects=mesh_names)
#			del particle_matrix

def handler_MESH(lux_context, scene, object):
	if OBJECT_ANALYSIS: print(' -> handler_MESH: %s' % object)
	
	# TODO: add in PLY proxy switch
#	if ob.luxrender_object.append_external_mesh:
#		lux_context.objectBegin(ob.name)
#		ply_params = ParamSet()
#		ply_params.add_string('filename', efutil.path_relative_to_export(ob.luxrender_object.external_mesh))
#		ply_params.add_bool('smooth', ob.luxrender_object.use_smoothing)
#		lux_context.shape('plymesh', ply_params)
#		lux_context.objectEnd()
#		append_objects.append( (ob.name, ob.active_material, None) )
		
	split_meshes = buildNativeMesh(lux_context, object)
	for mesh_definition in split_meshes:
		exportMeshInstance(lux_context, object, mesh_definition)

def iterateScene(lux_context, scene):
	ExportedMeshes.reset()
	
	callbacks = {
		'duplis': {
			'GROUP': handler_Duplis_GROUP,
			'VERTS': handler_Duplis_VERTS,
		},
		'particles': {
			#'OBJECT': handler_Particles_OBJECT,
		},
		'objects': {
			'MESH': handler_MESH
		}
	}
	
	valid_duplis_callbacks = callbacks['duplis'].keys()
	valid_particles_callbacks = callbacks['particles'].keys()
	valid_objects_callbacks = callbacks['objects'].keys()
	
	progress_thread = MeshExportProgressThread()
	progress_thread.start(len(scene.objects))
	
	for object in scene.objects:
		if OBJECT_ANALYSIS: print('Analysing object %s : %s' % (object, object.type))
		
		# Export only objects which are enabled for render (in the outliner) and visible on a render layer
		if not object.is_visible(scene) or object.hide_render:
			if OBJECT_ANALYSIS: print(' -> not visible: %s / %s' % (object.is_visible(scene), object.hide_render))
			continue
		
		if object.parent and object.parent.is_duplicator:
			if OBJECT_ANALYSIS: print(' -> parent is duplicator')
			continue
		
		number_psystems = len(object.particle_systems)
		
		if object.is_duplicator and number_psystems < 1:
			if OBJECT_ANALYSIS: print(' -> is duplicator without particle systems')
			if object.dupli_type in valid_duplis_callbacks:
				callbacks['duplis'][object.dupli_type](lux_context, scene, object)
			elif OBJECT_ANALYSIS:
				print(' -> Unsupported Dupli type: %s' % object.dupli_type)
		
		render_particle_emitter = True
		if number_psystems > 0:
			if OBJECT_ANALYSIS: print(' -> has %i particle systems' % number_psystems)
			for psys in object.particle_systems:
				render_particle_emitter &= psys.settings.use_render_emitter
				if psys.settings.render_type in valid_particles_callbacks:
					callbacks['particles'][psys.settings.render_type](lux_context, scene, object)
				elif OBJECT_ANALYSIS:
					print(' -> Unsupported Particle system type: %s' % object.dupli_type)
		
		export_bare_object = True
		export_bare_object &= (not object.is_duplicator or object.dupli_type == 'DUPLIFRAMES')
		export_bare_object &= render_particle_emitter
		# the last check (object.names not in dupli_names) requires splitting this loop into two pieces
		
		if export_bare_object and object.type in valid_objects_callbacks:
			callbacks['objects'][object.type](lux_context, scene, object)
		elif OBJECT_ANALYSIS:
			print(' -> Unexportable object: %s : %s' % (object, object.type))
			
		progress_thread.exported_objects += 1
	
	progress_thread.stop()
	progress_thread.join()

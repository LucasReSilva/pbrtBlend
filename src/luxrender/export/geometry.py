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
from luxrender.export import ParamSet
from luxrender.export import matrix_to_list
from luxrender.export.materials import export_object_material, get_instance_materials, add_texture_parameter


class InvalidGeometryException(Exception):
	pass

#-------------------------------------------------
# getMeshType(mesh)
# returns type of mesh as string to use depending on thresholds
#-------------------------------------------------
def getMeshType(mesh):
	
	params = ParamSet()
	dstr = 'trianglemesh'

	# check if subdivision is used
	if mesh.luxrender_mesh.subdiv == True:
		dstr = 'loopsubdiv'
		params.add_integer('nlevels', mesh.luxrender_mesh.sublevels)
		params.add_bool('dmnormalsmooth', mesh.luxrender_mesh.nsmooth)
		params.add_bool('dmsharpboundary', mesh.luxrender_mesh.sharpbound)
	
	return dstr,params

def exportNativeMesh(scene, mesh, lux_context):
	#print('-> Cache face verts')
	faces_verts = [f.vertices for f in mesh.faces]
	#print('-> Cache faces')
	ffaces = [f for f in mesh.faces]
	#faces_normals = [tuple(f.normal) for f in me.faces]
	#verts_normals = [tuple(v.normal) for v in me.vertices]
	
	# Cache vert positions because me.vertices access is very slow
	#print('-> Cache vert pos and normals')
	verts_co_no = [tuple(v.co)+tuple(v.normal) for v in mesh.vertices]
	
	
	# face indices
	index = 0
	indices = []
	ntris = 0
	#print('-> Collect face indices')
	for face in ffaces:
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
	for face in ffaces:
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
	for face in ffaces:
		normal = face.normal
		for vertex in face.vertices:
			if face.use_smooth:
				normal = verts_co_no[vertex][3:]
			for no in normal:
				normals.append(no)
	
	# uv coordinates
	#print('-> Collect UV layers')
	try:
		uv_layer = mesh.uv_textures.active.data
	except:
		uv_layer = None
		
	if uv_layer:
		uvs = []
		for fi, uv in enumerate(uv_layer):
			if len(faces_verts[fi]) == 4:
				face_uvs = uv.uv1, uv.uv2, uv.uv3, uv.uv4
			else:
				face_uvs = uv.uv1, uv.uv2, uv.uv3
			for uv in face_uvs:
				for single_uv in uv:
					uvs.append(single_uv)
	
	#print(' %s num points: %i' % (ob.name, len(points)))
	#print(' %s num normals: %i' % (ob.name, len(normals)))
	#print(' %s num idxs: %i' % (ob.name, len(indices)))
	
	# export shape
	shape_type, shape_params = getMeshType(mesh)
	
	if lux_context.API_TYPE == 'PURE':
		# ntris isn't really the number of tris!!
		shape_params.add_integer('ntris', ntris)
		shape_params.add_integer('nvertices', nvertices)
	
	#print('-> Add indices to paramset')
	shape_params.add_integer('indices', indices)
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
	
	return shape_type, shape_params

def exportPlyMesh(scene, mesh, lux_context):
	ply_filename = efutil.export_path + '_' + bpy.path.clean_name(mesh.name) + '.ply'
	
	# TODO: find out how to set the context object
	# bpy.context.object = ob
	bpy.ops.export.ply(
		filepath = ply_filename,
		use_modifiers = True,
		use_normals = True,
		use_uv_coords = True,
		use_colors = False
	)
	
	ply_params = ParamSet()
	ply_params.add_string('filename', efutil.path_relative_to_export(ply_filename))
	ply_params.add_bool('smooth', mesh.use_auto_smooth)
	
	return 'plymesh', ply_params

#-------------------------------------------------
# export_mesh(lux_context, scene, object, matrix)
# create mesh from object and export it to file
#-------------------------------------------------
def exportMesh(lux_context, scene, ob, object_begin_end=True, scale=None, log=True, transformed=False):
	
	if log: LuxLog('Mesh Export: %s' % ob.data.name)
	
	#print('-> Create render mesh')
	mesh = ob.create_mesh(scene, True, 'RENDER')
	if mesh is None:
		return
	
	# Shape is the only thing to go into the ObjectBegin..ObjectEnd definition
	# Everything else is set on a per-instance basis
	if object_begin_end: lux_context.objectBegin(ob.data.name)
	
	if scale is not None: lux_context.scale(*scale)
	
	if transformed: lux_context.transform( matrix_to_list(ob.matrix_world, apply_worldscale=True) )
	
	try:
		if scene.luxrender_engine.mesh_type == 'native':
			shape_type, shape_params = exportNativeMesh(scene, mesh, lux_context)
		elif scene.luxrender_engine.mesh_type == 'ply':
			shape_type, shape_params = exportPlyMesh(scene, mesh, lux_context)
		
		#print('-> Create shape')
		lux_context.shape(shape_type, shape_params)
		#print('-> Mesh done')
	except InvalidGeometryException:
		pass
	
	if object_begin_end: lux_context.objectEnd()
	
	#print('-> Remove render mesh')
	bpy.data.meshes.remove(mesh)

def allow_instancing(scene):
	# Some situations require full geometry export
	allow_instancing = True
	
	if scene.luxrender_engine.renderer == 'hybrid':
		allow_instancing = False
		
	return allow_instancing

def exportInstance(lux_context, scene, ob, matrix):
	lux_context.attributeBegin(comment=ob.name, file=Files.GEOM)
	
	# object translation/rotation/scale 
	lux_context.transform( matrix_to_list(matrix, apply_worldscale=True) )
	
	# Export either NamedMaterial stmt or the full material
	# definition depending on the output type
	export_object_material(scene, lux_context, ob)
	
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
	
	object_has_volume = False
	for m in get_instance_materials(ob):
		# just export the first volume interior/exterior
		if hasattr(m, 'luxrender_material') and m.luxrender_material.type in ['glass2'] and not object_has_volume:
			lux_context.interior(m.luxrender_material.luxrender_mat_glass2.Interior_volume)
			lux_context.exterior(m.luxrender_material.luxrender_mat_glass2.Exterior_volume)
			object_has_volume = True
	
	# object motion blur
	is_object_animated = False
	if scene.camera.data.luxrender_camera.usemblur and scene.camera.data.luxrender_camera.objectmblur:
		scene.frame_set(scene.frame_current + 1)
		m1 = matrix.copy()
		scene.frame_set(scene.frame_current - 1)
		scene.update()
		if m1 != matrix:
			is_object_animated = True
	
	# If the object emits, don't export instance or motioninstance
	if (not allow_instancing(scene)) or object_is_emitter:
		exportMesh(lux_context, scene, ob, object_begin_end=False, log=False)
	# special case for motion blur since the mesh is already exported before the attribute
	elif is_object_animated:
		lux_context.transformBegin(comment=ob.name, file=Files.GEOM)
		lux_context.identity()
		lux_context.transform(matrix_to_list(m1, apply_worldscale=True))
		lux_context.coordinateSystem('%s' % ob.data.name + '_motion')
		lux_context.transformEnd()
		lux_context.motionInstance(ob.data.name, 0.0, 1.0, ob.data.name + '_motion')

	else:
		lux_context.objectInstance(ob.data.name)
	
	lux_context.attributeEnd()

class MeshExportProgressThread(efutil.TimerThread):
	KICK_PERIOD = 1
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
			#render_engine.update_stats('', 'LuxRender: Parsing meshes %i%%' % pc)
			bpy.ops.ef.msg(
				msg_type='INFO',
				msg_text='LuxRender: Parsing meshes %i%%' % pc
			)

#-------------------------------------------------
# write_lxo(render_engine, lux_context, scene)
# MAIN export function
#-------------------------------------------------
def write_lxo(render_engine, lux_context, scene):
	'''
	lux_context		pylux.Context
	scene			bpy.types.scene
	
	Iterate over the given scene's objects,
	and export the compatible ones to the context lux_context.
	
	Returns		None
	'''
	
	sel = scene.objects
	total_objects = len(sel)

	# browse all scene objects for "mesh-convertible" ones
	# First round: check for duplis
	duplis = []
	meshes_exported = set()
	
	for ob in sel:
		if ob.type in ('LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE', 'LATTICE'):
			continue
		
		# Export only objects which are enabled for render (in the outliner) and visible on a render layer
		if not ob.is_visible(scene) or ob.hide_render:
			continue
		
		if ob.parent and ob.parent.is_duplicator:
			continue

		if ob.is_duplicator and len(ob.particle_systems) < 1:
			# create dupli objects
			ob.create_dupli_list(scene)

			for dupli_ob in ob.dupli_list:
				if dupli_ob.object.type != 'MESH':
					continue
				if allow_instancing(scene) and (dupli_ob.object.data.name not in meshes_exported):
					exportMesh(lux_context, scene, dupli_ob.object)
					meshes_exported.add(dupli_ob.object.data.name)
				
				exportInstance(lux_context, scene, dupli_ob.object, dupli_ob.object.matrix_world)
				
				if dupli_ob.object.name not in duplis:
					duplis.append(dupli_ob.object.name)
			
			# free object dupli list again. Warning: all dupli objects are INVALID now!
			if ob.dupli_list: 
				ob.free_dupli_list()
		
		for psys in ob.particle_systems:
			psys_settings = psys.settings
			allowed_particle_states = {'ALIVE'}
			if psys_settings.render_type == 'OBJECT':
				scene.update()
				particle_object = psys_settings.dupli_object
				for mat in get_instance_materials(particle_object):
					mat.luxrender_material.export(scene, lux_context, mat, mode='indirect')
				for particle in psys.particles:
					if particle.is_visible and (particle.alive_state in allowed_particle_states):
						if allow_instancing(scene) and (particle_object.data.name not in meshes_exported):
							exportMesh(lux_context, scene, particle_object, scale=[particle.size]*3, log=False)
							meshes_exported.add(particle_object.data.name)
						particle_matrix = mathutils.Matrix.Translation( particle.location )
						particle_matrix *= particle.rotation.to_matrix().to_4x4()
						#particle_matrix *= mathutils.Matrix.Scale(particle.size, 4)
						exportInstance(lux_context, scene, particle_object, particle_matrix)
						del particle_matrix

	# browse all scene objects for "mesh-convertible" ones
	# skip duplicated objects here
	
	progress_thread = MeshExportProgressThread()
	progress_thread.start(total_objects)
	
	for ob in sel:
		if ob.type != 'MESH':
			continue
		
		# Export only objects which are enabled for render (in the outliner) and visible on a render layer
		if not ob.is_visible(scene) or ob.hide_render:
			continue
		
		if ob.parent and ob.parent.is_duplicator:
			continue

		# special case for objects with particle system: check if emitter should be rendered
		if len(ob.particle_systems) > 0:
			render_emitter = False
		else:
			render_emitter = True
		for psys in ob.particle_systems:
			render_emitter |= psys.settings.use_render_emitter

		# dupli object render rule copied from convertblender.c (blender internal render)
		if (not ob.is_duplicator or ob.dupli_type == 'DUPLIFRAMES') and render_emitter and (ob.name not in duplis):
			# Export mesh definition once
			if allow_instancing(scene) and (ob.data.name not in meshes_exported):
				exportMesh(lux_context, scene, ob, transformed=ob.data.luxrender_mesh.portal)
				meshes_exported.add(ob.data.name)
			
			# Export object instance
			if not ob.data.luxrender_mesh.portal:
				exportInstance(lux_context, scene, ob, ob.matrix_world)

		progress_thread.exported_objects += 1
	
	progress_thread.stop()
	progress_thread.join()

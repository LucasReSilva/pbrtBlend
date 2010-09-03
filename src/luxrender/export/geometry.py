# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
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
import bpy
# from mathutils import Matrix

from luxrender.outputs import LuxLog
from luxrender.outputs.file_api import Files
from luxrender.export import ParamSet
from luxrender.export import matrix_to_list
from luxrender.export.materials import export_object_material, get_instance_materials, add_texture_parameter

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

def exportGeometry(ob, me, lux_context, smoothing_enabled):
	
	LuxLog('Mesh Export: %s' % ob.name)
	faces_verts = [f.vertices for f in me.faces]
	ffaces = [f for f in me.faces]
	#faces_normals = [tuple(f.normal) for f in me.faces]
	#verts_normals = [tuple(v.normal) for v in me.vertices]
	
	# face indices
	index = 0
	indices = []
	ntris = 0
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
		
	# vertex positions
	points = []
	nvertices = 0
	for face in ffaces:
		for vertex in face.vertices:
			v = me.vertices[vertex]
			nvertices += 1
			for co in v.co:
				points.append(co)
				
	# vertex normals
	normals = []
	for face in ffaces:
		normal = face.normal
		for vertex in face.vertices:
			if (smoothing_enabled and face.use_smooth):
				v = me.vertices[vertex]
				normal = v.normal
			for no in normal:
				normals.append(no)
				
	# uv coordinates
	try:
		uv_layer = me.uv_textures.active.data
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
	shape_type, shape_params = getMeshType(ob.data)
	
	if lux_context.API_TYPE == 'PURE':
		# ntris isn't really the number of tris!!
		shape_params.add_integer('ntris', ntris)
		shape_params.add_integer('nvertices', nvertices)
	
	shape_params.add_integer('indices', indices)
	shape_params.add_point('P', points)
	shape_params.add_normal('N', normals)
	
	if uv_layer:
		#print(' %s num uvs: %i' % (ob.name, len(uvs)))
		shape_params.add_float('uv', uvs)
	
	#print(' %s ntris: %i' % (ob.name, ntris))
	#print(' %s nvertices: %i' % (ob.name, nvertices))
	
	if ob.data.luxrender_mesh.portal:
		lux_context.portalShape(shape_type, shape_params)
	else:
		lux_context.shape(shape_type, shape_params)

#-------------------------------------------------
# export_mesh(lux_context, scene, object, matrix)
# create mesh from object and export it to file
#-------------------------------------------------
def exportMesh(lux_context, scene, ob, smoothing_enabled, object_begin_end=True):
	me = ob.create_mesh(scene, True, 'RENDER')
		
	if not me:
		return
	
	# Shape is the only thing to go into the ObjectBegin..ObjectEnd definition
	# Everything else is set on a per-instance basis
	if object_begin_end: lux_context.objectBegin(ob.data.name)
	exportGeometry(ob, me, lux_context, smoothing_enabled)
	if object_begin_end: lux_context.objectEnd()
	
	bpy.data.meshes.remove(me)

def exportInstance(lux_context, scene, ob, matrix, smoothing_enabled=True):
	lux_context.attributeBegin(comment=ob.name, file=Files.GEOM)
	# object translation/rotation/scale 
	lux_context.transform( matrix_to_list(matrix, scene=scene, apply_worldscale=True) )
	
	# Export either NamedMaterial stmt or the full material
	# definition depending on the output type
	export_object_material(scene, lux_context, ob)
	
	# Check for emission material assignment and volume data
	object_is_emitter = False
	object_has_volume = False
	for m in get_instance_materials(ob):
		# just export the first emitting material
		if not object_is_emitter:
			if hasattr(m, 'luxrender_emission') and m.luxrender_emission.use_emission:
				lux_context.lightGroup(m.luxrender_emission.lightgroup, [])
				arealightsource_params = ParamSet() \
						.add_float('gain', m.luxrender_emission.gain) \
						.add_float('power', m.luxrender_emission.power) \
						.add_float('efficacy', m.luxrender_emission.efficacy)
				arealightsource_params.update( add_texture_parameter(lux_context, 'L', 'color', m.luxrender_emission) )
				lux_context.areaLightSource('area', arealightsource_params)
				object_is_emitter = True
		# just export the first volume interior/exterior
		if hasattr(m, 'luxrender_material') and m.luxrender_material.type in ['glass2'] and not object_has_volume:
			lux_context.interior(m.luxrender_material.Interior_volume)
			lux_context.exterior(m.luxrender_material.Exterior_volume)
			object_has_volume = True
	
	# object motion blur
	is_object_animated = False
	if scene.camera.data.luxrender_camera.usemblur and scene.camera.data.luxrender_camera.objectmblur:
		scene.set_frame(scene.frame_current + 1)
		m1 = matrix.copy()
		scene.set_frame(scene.frame_current - 1)
		if m1 != matrix:
			is_object_animated = True
	
	# If the object emits, don't export instance or motioninstance
	if object_is_emitter:
		exportMesh(lux_context, scene, ob, smoothing_enabled, object_begin_end=False)
	# special case for motion blur since the mesh is already exported before the attribute
	elif is_object_animated:
		lux_context.transformBegin(comment=ob.name, file=Files.GEOM)
		lux_context.identity()
		lux_context.transform(matrix_to_list(m1, scene=scene, apply_worldscale=True))
		lux_context.coordinateSystem('%s' % ob.data.name + '_motion')
		lux_context.transformEnd()
		lux_context.motionInstance(ob.data.name, 0.0, 1.0, ob.data.name + '_motion')

	else:
		lux_context.objectInstance(ob.data.name)
	
	lux_context.attributeEnd()

#-------------------------------------------------
# write_lxo(render_engine, lux_context, scene, smoothing_enabled=True)
# MAIN export function
#-------------------------------------------------
def write_lxo(render_engine, lux_context, scene, smoothing_enabled=True):
	'''
	lux_context		pylux.Context
	scene			bpy.types.scene
	
	Iterate over the given scene's objects,
	and export the compatible ones to the context lux_context.
	
	Returns		None
	'''

	rpcs = []
	ipc = 0.0

	vis_layers = scene.layers
	
	sel = scene.objects
	total_objects = len(sel)

	# browse all scene objects for "mesh-convertible" ones
	# First round: check for duplis
	duplis = []
	meshes_exported = set()
	
	for ob in sel:
		if ob.type in ('LAMP', 'CAMERA', 'EMPTY', 'META', 'ARMATURE', 'LATTICE'):
			continue
		
		# Check layers
		visible = False
		for layer_index, o_layer in enumerate(ob.layers):
			visible = visible or (o_layer and vis_layers[layer_index])
		
		# Export only objects which are enabled for render (in the outliner) and visible on a render layer
		if not visible or ob.hide_render:
			continue
		
		if ob.parent and ob.parent.is_duplicator:
			continue

		if ob.is_duplicator:
			# create dupli objects
			ob.create_dupli_list(scene)

			for dupli_ob in ob.dupli_list:
				if dupli_ob.object.type != 'MESH':
					continue
				if not dupli_ob.object.data.name in meshes_exported:
					exportMesh(lux_context, scene, dupli_ob.object, smoothing_enabled)
					meshes_exported.add(dupli_ob.object.data.name)
				
				exportInstance(lux_context, scene, dupli_ob.object, dupli_ob.object.matrix_world, smoothing_enabled)
				
				if dupli_ob.object.name not in duplis:
					duplis.append(dupli_ob.object.name)
			
			# free object dupli list again. Warning: all dupli objects are INVALID now!
			if ob.dupli_list: 
				ob.free_dupli_list()

	# browse all scene objects for "mesh-convertible" ones
	# skip duplicated objects here
	
	for ob in sel:
		if ob.type != 'MESH':
			continue
		
		# Check layers
		visible = False
		for layer_index, o_layer in enumerate(ob.layers):
			visible = visible or (o_layer and vis_layers[layer_index])
		
		# Export only objects which are enabled for render (in the outliner) and visible on a render layer
		if not visible or ob.hide_render:
			continue
		
		if ob.parent and ob.parent.is_duplicator:
			continue

		# special case for objects with particle system: check if emitter should be rendered
		if len(ob.particle_systems) > 0:
			render_emitter = False
		else:
			render_emitter = True
		for psys in ob.particle_systems:
			render_emitter |= psys.settings.emitter

		# dupli object render rule copied from convertblender.c (blender internal render)		
		if (not ob.is_duplicator or ob.dupli_type == 'DUPLIFRAMES') and render_emitter and (ob.name not in duplis):
			# Export mesh definition once
			if not ob.data.name in meshes_exported:
				exportMesh(lux_context, scene, ob, smoothing_enabled)
				meshes_exported.add(ob.data.name)
			
			# Export object instance
			exportInstance(lux_context, scene, ob, ob.matrix_world, smoothing_enabled)

		# exported another object
		ipc += 1.0

		# TODO: this probably isn't very efficient for large scenes
		pc = int(100 * ipc/total_objects)
		if pc not in rpcs:
			rpcs.append(pc)
			#render_engine.update_stats('', 'LuxRender: Parsing meshes %i%%' % pc)
			bpy.ops.ef.msg(
				msg_type='INFO',
				msg_text='LuxRender: Parsing meshes %i%%' % pc
			)

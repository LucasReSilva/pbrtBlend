# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
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
# System Libs
import os

# Blender Libs
import bpy

# ExporterFramework Libs
from ef.ef import init_properties
from ef.util import util as efutil

# LuxRender Libs
from luxrender.outputs import LuxManager as LM

from luxrender.export import get_worldscale
from luxrender.export import film		as export_film
from luxrender.export import lights		as export_lights
from luxrender.export import materials	as export_materials
from luxrender.export import geometry	as export_geometry
from luxrender.outputs.file_api			import Files

class LUXRENDER_OT_volume_add(bpy.types.Operator):
	'''Add a new material volume definition to the scene'''
	
	bl_idname = "luxrender.volume_add"
	bl_label = "Add LuxRender Volume"
	
	new_volume_name = bpy.props.StringProperty(default='New Volume')
	
	def invoke(self, context, event):
		v = context.scene.luxrender_volumes.volumes
		v.add()
		new_vol = v[len(v)-1]
		new_vol.name = self.properties.new_volume_name
		# TODO: this init_properties should be executed
		# elsewhere, once, on the luxrender_volume_data type,
		# not on individual instances
		init_properties(new_vol, new_vol.properties)
		return {'FINISHED'}
	
class LUXRENDER_OT_volume_remove(bpy.types.Operator):
	'''Remove the selected material volume definition'''
	
	bl_idname = "luxrender.volume_remove"
	bl_label = "Remove LuxRender Volume"
	
	def invoke(self, context, event):
		w = context.scene.luxrender_volumes
		w.volumes.remove( w.volumes_index )
		w.volumes_index = len(w.volumes)-1
		return {'FINISHED'}

class EXPORT_OT_luxrender(bpy.types.Operator):
	bl_idname = 'export.luxrender'
	bl_label = 'Export LuxRender Scene (.lxs)'
	
	filename		= bpy.props.StringProperty(name='IGS filename')
	directory		= bpy.props.StringProperty(name='IGS directory')
	
	api_type		= bpy.props.StringProperty(options={'HIDDEN'}, default='FILE')	# Export target ['FILE','API',...]
	write_files		= bpy.props.BoolProperty(options={'HIDDEN'}, default=True)		# Write any files ?
	write_all_files	= bpy.props.BoolProperty(options={'HIDDEN'}, default=True)		# Force writing all files, don't obey UI settings
	
	def export_init(self, scene):
		
		# force scene update to current rendering frame
		scene.set_frame(scene.frame_current)
		
		if scene.luxrender_engine.threads_auto:
			try:
				import multiprocessing
				threads = multiprocessing.cpu_count()
			except:
				# TODO: when might this fail?
				threads = 4
		else:
			threads = scene.luxrender_engine.threads
		
		# Set up the rendering context
		self.report({'INFO'}, 'Creating LuxRender context')
		LuxManager = LM(
			scene.name,
			api_type = self.properties.api_type,
			threads = threads
		)
		LM.SetActive(LuxManager)
		
		lux_context = LuxManager.lux_context
		
		if self.properties.api_type == 'FILE':
			
			if self.properties.write_all_files:
				LXS = True
				LXM = True
				LXO = True
			else:
				LXS = scene.luxrender_engine.write_lxs
				LXM = scene.luxrender_engine.write_lxm
				LXO = scene.luxrender_engine.write_lxo
			
			if not os.access( self.properties.directory, os.W_OK):
				self.report({'ERROR'}, 'Output path "%s" is not writable' % self.properties.directory)
				return False
			
			if self.properties.filename.endswith('.lxs'):
				self.properties.filename = self.properties.filename[:-4]
			
			lxs_filename = os.path.join(
				self.properties.directory,
				self.properties.filename
			)
			
			efutil.export_path = lxs_filename
			
			if LXS or LXM or LXO:
				lux_context.set_filename(
					lxs_filename,
					LXS = LXS, 
					LXM = LXM,
					LXO = LXO
				)
			else:
				self.report({'ERROR'}, 'Nothing to do! Select at least one of LXM/LXS/LXO')
				return False
		else:
			# Set export path so that relative paths in export work correctly
			efutil.export_path = scene.render.filepath
		
		return lux_context
	
	def invoke(self, context, event):
		wm = context.manager
		wm.add_fileselect(self)
		return {'RUNNING_MODAL'}
	
	def execute(self, context):
		scene = context.scene
		lux_context = self.export_init(scene)
		if lux_context == False:
			return {'CANCELLED'}
		
		export_materials.ExportedMaterials.clear()
		export_materials.ExportedTextures.clear()
		
		self.report({'INFO'}, 'Exporting render settings')
		if (self.properties.api_type in ['API', 'LUXFIRE_CLIENT'] and not self.properties.write_files) or (self.properties.write_files and scene.luxrender_engine.write_lxs):
			# Set up render engine parameters
			lux_context.sampler(			*scene.luxrender_sampler.api_output()		)
			lux_context.accelerator(		*scene.luxrender_accelerator.api_output()	)
			lux_context.surfaceIntegrator(	*scene.luxrender_integrator.api_output()	)
			lux_context.volumeIntegrator(	*scene.luxrender_volume.api_output()		)
			lux_context.pixelFilter(		*scene.luxrender_filter.api_output()		)
			
			# Set up camera, view and film
			is_cam_animated = False
			if scene.camera.data.luxrender_camera.usemblur and scene.camera.data.luxrender_camera.cammblur:
				scene.set_frame(scene.frame_current + 1)
				m1 = scene.camera.matrix_world.copy()
				scene.set_frame(scene.frame_current - 1)
				if m1 != scene.camera.matrix_world:
					lux_context.transformBegin(file=Files.MAIN)
					ws = get_worldscale(scene=scene)
					matrix *= ws
					ws = get_worldscale(scene=scene, as_scalematrix=False)
					matrix[3][0] *= ws
					matrix[3][1] *= ws
					matrix[3][2] *= ws
					pos = m1[3]
					forwards = -m1[2]
					target = (pos + forwards)
					up = m1[1]
					transform = (pos[0], pos[1], pos[2], target[0], target[1], target[2], up[0], up[1], up[2])
					lux_context.lookAt( *transform )
					lux_context.coordinateSystem('CameraEndTransform')
					lux_context.transformEnd()
					is_cam_animated = True
			lux_context.lookAt(	*export_film.lookAt(scene)	)
			lux_context.camera(	*scene.camera.data.luxrender_camera.api_output(scene, is_cam_animated)	)
			lux_context.film(	*export_film.film(scene)	)
			
			lux_context.worldBegin()
			
			# Light source iteration and export goes here.
			if self.properties.api_type == 'FILE':
				lux_context.set_output_file(Files.MAIN)
			
			self.report({'INFO'}, 'Exporting lights')
			if export_lights.lights(lux_context, scene) == False:
				self.report({'ERROR'}, 'No lights in scene!')
				return {'CANCELLED'}
		
		if (self.properties.api_type in ['API', 'LUXFIRE_CLIENT'] and not self.properties.write_files) or (self.properties.write_files and scene.luxrender_engine.write_lxm):
			if self.properties.api_type == 'FILE':
				lux_context.set_output_file(Files.MATS)
			
			self.report({'INFO'}, 'Exporting materials')
			export_materials.write_lxm(lux_context, scene)
			
		self.report({'INFO'}, 'Exporting volume data')
		for volume in scene.luxrender_volumes.volumes:
			lux_context.makeNamedVolume( volume.name, *export_materials.luxrender_volume_params(lux_context, volume) )
		
		self.report({'INFO'}, 'Exporting geometry')
		if (self.properties.api_type in ['API', 'LUXFIRE_CLIENT'] and not self.properties.write_files) or (self.properties.write_files and scene.luxrender_engine.write_lxo):
			if self.properties.api_type == 'FILE':
				lux_context.set_output_file(Files.GEOM)
			export_geometry.write_lxo(self, lux_context, scene, smoothing_enabled=True)
		
		if self.properties.write_all_files:
			lux_context.worldEnd()
		
		self.report({'INFO'}, 'Export finished')
		return {'FINISHED'}

menu_func = lambda self, context: self.layout.operator("export.luxrender", text="Export LuxRender Scene...")
bpy.types.INFO_MT_file_export.append(menu_func)
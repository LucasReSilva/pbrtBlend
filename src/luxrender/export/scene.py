# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
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

# Extensions_Framework Libs
from extensions_framework import util as efutil

# LuxRender libs
from luxrender.export 			import get_worldscale
from luxrender.export			import lights		as export_lights
from luxrender.export			import materials	as export_materials
from luxrender.export			import geometry		as export_geometry
from luxrender.outputs			import LuxManager, LuxLog
from luxrender.outputs.file_api	import Files
from luxrender.outputs.pure_api	import LUXRENDER_VERSION

class SceneExporterProperties(object):
	"""
	Mimics the properties member conatined within EXPORT_OT_LuxRender operator
	"""
	
	filename		= ''
	directory		= ''
	api_type		= ''
	write_files		= True
	write_all_files	= True

class SceneExporter(object):
	
	scene = None
	properties = SceneExporterProperties()
	
	def set_properties(self, properties):
		self.properties = properties
		return self
	
	def set_scene(self, scene):
		self.scene = scene
		return self
	
	def set_report(self, report):
		self.report = report
		return self
	
	def report(self, type, message):
		LuxLog('%s: %s' % ('|'.join([('%s'%i).upper() for i in type]), message))
	
	def export(self):
		scene = self.scene
		
		if scene is None:
			self.report({'ERROR'}, 'Scene is not valid for export to %s'%self.properties.filename)
			return {'CANCELLED'}
		
		# Force scene update; NB, scene.update() doesn't work
		scene.frame_set( scene.frame_current )
		
		# Set up the rendering context
		self.report({'INFO'}, 'Creating LuxRender context')
		created_lux_manager = False
		if LuxManager.ActiveManager is None:
			LM = LuxManager(
				scene.name,
				api_type = self.properties.api_type,
			)
			LuxManager.SetActive(LM)
			created_lux_manager = True
		
		LuxManager.ActiveManager.SetCurrentScene(scene)
		lux_context = LuxManager.ActiveManager.lux_context
		
		if self.properties.filename.endswith('.lxs'):
			self.properties.filename = self.properties.filename[:-4]
		
		lxs_filename = '/'.join([
			self.properties.directory,
			self.properties.filename
		])
		
		efutil.export_path = lxs_filename
		#print('(3) export_path is %s' % efutil.export_path)
		
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
				return {'CANCELLED'}
			
			if LXS or LXM or LXO:
				lux_context.set_filename(
					lxs_filename,
					LXS = LXS, 
					LXM = LXM,
					LXO = LXO
				)
			else:
				self.report({'ERROR'}, 'Nothing to do! Select at least one of LXM/LXS/LXO')
				return {'CANCELLED'}
		
		if lux_context == False:
			self.report({'ERROR'}, 'Lux context is not valid for export to %s'%self.properties.filename)
			return {'CANCELLED'}
		
		export_materials.ExportedMaterials.clear()
		export_materials.ExportedTextures.clear()
		
		if (self.properties.api_type in ['API', 'LUXFIRE_CLIENT'] and not self.properties.write_files) or (self.properties.write_files and scene.luxrender_engine.write_lxs):
			self.report({'INFO'}, 'Exporting render settings')
			# Set up render engine parameters
			if LUXRENDER_VERSION >= '0.8':
				lux_context.renderer(		*scene.luxrender_engine.api_output()							)
			lux_context.sampler(			*scene.luxrender_sampler.api_output()							)
			lux_context.accelerator(		*scene.luxrender_accelerator.api_output()						)
			lux_context.surfaceIntegrator(	*scene.luxrender_integrator.api_output(scene.luxrender_engine)	)
			lux_context.volumeIntegrator(	*scene.luxrender_volumeintegrator.api_output()					)
			lux_context.pixelFilter(		*scene.luxrender_filter.api_output()							)
			
			# Set up camera, view and film
			is_cam_animated = False
			if scene.camera.data.luxrender_camera.usemblur and scene.camera.data.luxrender_camera.cammblur:
				scene.frame_set(scene.frame_current + 1)
				m1 = scene.camera.matrix_world.copy()
				scene.frame_set(scene.frame_current - 1)
				scene.update()
				if m1 != scene.camera.matrix_world:
					lux_context.transformBegin(file=Files.MAIN)
					ws = get_worldscale()
					m1 *= ws
					ws = get_worldscale(as_scalematrix=False)
					m1[3][0] *= ws
					m1[3][1] *= ws
					m1[3][2] *= ws
					pos = m1[3]
					forwards = -m1[2]
					target = (pos + forwards)
					up = m1[1]
					transform = (pos[0], pos[1], pos[2], target[0], target[1], target[2], up[0], up[1], up[2])
					lux_context.lookAt( *transform )
					lux_context.coordinateSystem('CameraEndTransform')
					lux_context.transformEnd()
					is_cam_animated = True
			lux_context.lookAt(	*scene.camera.data.luxrender_camera.lookAt(scene.camera) )
			lux_context.camera(	*scene.camera.data.luxrender_camera.api_output(scene, is_cam_animated)	)
			lux_context.film(	*scene.camera.data.luxrender_camera.luxrender_film.api_output()	)
			
			lux_context.worldBegin()
			
			# Light source iteration and export goes here.
			if self.properties.api_type == 'FILE':
				lux_context.set_output_file(Files.MAIN)
		
		self.report({'INFO'}, 'Exporting volume data')
		for volume in scene.luxrender_volumes.volumes:
			lux_context.makeNamedVolume( volume.name, *volume.api_output(lux_context) )
		
		mesh_names = set()
		
		if (self.properties.api_type in ['API', 'LUXFIRE_CLIENT'] and not self.properties.write_files) or (self.properties.write_files and scene.luxrender_engine.write_lxo):
			self.report({'INFO'}, 'Exporting geometry')
			if self.properties.api_type == 'FILE':
				lux_context.set_output_file(Files.GEOM)
			#export_geometry.write_lxo(lux_context)
			mesh_names, emitting_mats = export_geometry.iterateScene(lux_context, scene)
		
		# Make sure lamp textures go back into main file, not geom file
		if self.properties.api_type in ['FILE']:
			lux_context.set_output_file(Files.MAIN)
		
		if (self.properties.api_type in ['API', 'LUXFIRE_CLIENT'] and not self.properties.write_files) or (self.properties.write_files and scene.luxrender_engine.write_lxs):
			self.report({'INFO'}, 'Exporting lights')
			if export_lights.lights(lux_context, mesh_names) == False and not emitting_mats:
				self.report({'ERROR'}, 'No lights in scene!')
				return {'CANCELLED'}
		
		# Default 'Camera' Exterior
		if scene.camera.data.luxrender_camera.Exterior_volume != '':
			lux_context.exterior(scene.camera.data.luxrender_camera.Exterior_volume)
		elif scene.luxrender_world.default_exterior_volume != '':
			lux_context.exterior(scene.luxrender_world.default_exterior_volume)
		
		if self.properties.write_all_files:
			lux_context.worldEnd()
		
		if created_lux_manager:
			LM.reset()
		
		self.report({'INFO'}, 'Export finished')
		return {'FINISHED'}

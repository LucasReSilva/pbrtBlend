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

# Extensions_Framework Libs
from extensions_framework import util as efutil

# LuxRender libs
from ..export 			import get_worldscale, object_anim_matrix
from ..export			import lights		as export_lights
from ..export			import materials	as export_materials
from ..export			import geometry		as export_geometry
from ..export			import volumes		as export_volumes
from ..outputs			import LuxManager, LuxLog
from ..outputs.file_api	import Files
from ..outputs.pure_api	import LUXRENDER_VERSION

class SceneExporterProperties(object):
	"""
	Mimics the properties member contained within EXPORT_OT_LuxRender operator
	"""
	
	filename		= ''
	directory		= ''
	api_type		= ''
	write_files		= True
	write_all_files	= True

class SceneExporter(object):
	
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
		
		try:
			if scene is None:
				raise Exception('Scene is not valid for export to %s'%self.properties.filename)
			
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
			
			if self.properties.api_type == 'FILE':
				
				if self.properties.write_all_files:
					LXV = True
				else:
					LXV = scene.luxrender_engine.write_lxv
				
				if not os.access( self.properties.directory, os.W_OK):
					raise Exception('Output path "%s" is not writable' % self.properties.directory)
				
				lux_context.set_filename(
					scene,
					lxs_filename,
					LXV = LXV
				)
			
			if lux_context == False:
				raise Exception('Lux context is not valid for export to %s'%self.properties.filename)
			
			export_materials.ExportedMaterials.clear()
			export_materials.ExportedTextures.clear()
			
			# Pretty sure this conditional is useless
			#if (self.properties.api_type in ['API'] and not self.properties.write_files) or (self.properties.write_files):
			self.report({'INFO'}, 'Exporting render settings')
			
			if self.properties.api_type == 'FILE':
				lux_context.set_output_file(Files.MAIN)
			
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
				
				next_matrix = object_anim_matrix(scene, scene.camera, ignore_scale=True)
				
				if next_matrix != False:
					lux_context.transformBegin(file=Files.MAIN)
					
					ws = get_worldscale()
					next_matrix *= ws
					ws = get_worldscale(as_scalematrix=False)
					next_matrix[3][0] *= ws
					next_matrix[3][1] *= ws
					next_matrix[3][2] *= ws
					
					pos = next_matrix[3]
					forwards = -next_matrix[2]
					target = (pos + forwards)
					up = next_matrix[1]
					lux_context.lookAt( * pos[:3] + target[:3] + up[:3] )
					lux_context.coordinateSystem('CameraEndTransform')
					lux_context.transformEnd()
					is_cam_animated = True
					
			lux_context.lookAt(	*scene.camera.data.luxrender_camera.lookAt(scene.camera) )
			lux_context.camera(	*scene.camera.data.luxrender_camera.api_output(scene, is_cam_animated)	)
			lux_context.film(	*scene.camera.data.luxrender_camera.luxrender_film.api_output()	)
			
			lux_context.worldBegin()
			
			lights_in_export = False
			
			# Find linked 'background_set' scenes
			geom_scenes = [scene]
			s=scene
			while s.background_set != None:
				s = s.background_set
				geom_scenes.append(s)
			
			GE = export_geometry.GeometryExporter(lux_context, scene)
			# Pretty sure this conditional is useless
			#if (self.properties.api_type in ['API'] and not self.properties.write_files) or (self.properties.write_files):
			if scene.luxrender_engine.write_lxv:
				if self.properties.api_type == 'FILE':
					lux_context.set_output_file(Files.VOLM)
				export_volumes.export_smoke(lux_context, scene)
			
			# Make sure lamp textures go back into main file, not geom file
			if self.properties.api_type in ['FILE']:
				lux_context.set_output_file(Files.MAIN)
			
			# Export all data in linked 'background_set' scenes
			for geom_scene in geom_scenes:
				if len(geom_scene.luxrender_volumes.volumes) > 0:
					self.report({'INFO'}, 'Exporting volume data')
					if self.properties.api_type == 'FILE':
						lux_context.set_output_file(Files.MATS)
					for volume in geom_scene.luxrender_volumes.volumes:
						lux_context.makeNamedVolume( volume.name, *volume.api_output(lux_context) )
				
				# Pretty sure this conditional is useless
				#if (self.properties.api_type in ['API'] and not self.properties.write_files) or (self.properties.write_files):
				self.report({'INFO'}, 'Exporting geometry')
				if self.properties.api_type == 'FILE':
					lux_context.set_output_file(Files.GEOM)
				lights_in_export |= GE.iterateScene(geom_scene)
			
			for geom_scene in geom_scenes:
				# Make sure lamp textures go back into main file, not geom file
				if self.properties.api_type in ['FILE']:
					lux_context.set_output_file(Files.MAIN)
				
				# Pretty sure this conditional is useless
				#if (self.properties.api_type in ['API'] and not self.properties.write_files) or (self.properties.write_files):
				self.report({'INFO'}, 'Exporting lights')
				lights_in_export |= export_lights.lights(lux_context, geom_scene, scene, GE.ExportedMeshes)
			
			if lights_in_export == False:
				raise Exception('No lights in exported data!')
			
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
		
		except Exception as err:
			self.report({'ERROR'}, 'Export aborted: %s' % err)
			# raise err
			return {'CANCELLED'}

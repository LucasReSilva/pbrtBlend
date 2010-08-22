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
# System libs
import os, time, threading, subprocess, sys

# Blender libs
import bpy
from mathutils import Matrix

# Framework libs
from ef.ef import ef
from ef.engine import engine_base
from ef.util import util as efutil

# Exporter libs
from ..module import LuxManager as LM
from ..module import LuxLog

from ..ui import render_panels	as ui_render_panels
from ..ui import camera			as ui_camera
from ..ui import lamps			as ui_lamps
from ..ui import meshes			as ui_meshes
from ..ui import world			as ui_world
from ..ui import materials		as ui_materials
from ..ui.textures import main	as texture_main
from ..ui.textures import		bilerp, blackbody, brick, checkerboard, dots, \
								equalenergy, fbm, gaussian, harlequin, imagemap, \
								lampspectrum, mapping, marble, mix, scale, \
								transform, uv, windy, wrinkled

from ..export import get_worldscale
from ..export import film		as export_film
from ..export import lights		as export_lights
from ..export import materials	as export_materials
from ..export import geometry	as export_geometry
from ..module.file_api			import Files

from ..operators import			EXPORT_OT_luxrender, LUXRENDER_OT_volume_add, LUXRENDER_OT_volume_remove

# Add standard Blender Interface elements
import properties_render
properties_render.RENDER_PT_render.COMPAT_ENGINES.add('luxrender')
properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('luxrender')
properties_render.RENDER_PT_output.COMPAT_ENGINES.add('luxrender')
del properties_render

import properties_material
properties_material.MATERIAL_PT_context_material.COMPAT_ENGINES.add('luxrender')
properties_material.MATERIAL_PT_preview.COMPAT_ENGINES.add('luxrender')
del properties_material

import properties_data_lamp
properties_data_lamp.DATA_PT_context_lamp.COMPAT_ENGINES.add('luxrender')
# properties_data_lamp.DATA_PT_area.COMPAT_ENGINES.add('luxrender')
del properties_data_lamp

@classmethod
def blender_texture_poll(cls, context):
	tex = context.texture
	return	tex and \
			((tex.type == cls.tex_type and not tex.use_nodes) and (context.scene.render.engine in cls.COMPAT_ENGINES)) and \
			tex.luxrender_texture.type == 'BLENDER'

import properties_texture
properties_texture.TEXTURE_PT_context_texture.COMPAT_ENGINES.add('luxrender')
blender_texture_ui_list = [
	properties_texture.TEXTURE_PT_blend,
	properties_texture.TEXTURE_PT_clouds,
	properties_texture.TEXTURE_PT_distortednoise,
	#properties_texture.TEXTURE_PT_image,
	properties_texture.TEXTURE_PT_magic,
	properties_texture.TEXTURE_PT_marble,
	properties_texture.TEXTURE_PT_musgrave,
	#properties_texture.TEXTURE_PT_noise,
	properties_texture.TEXTURE_PT_stucci,
	properties_texture.TEXTURE_PT_voronoi,
	properties_texture.TEXTURE_PT_wood,
]
for blender_texture_ui in blender_texture_ui_list:
	blender_texture_ui.COMPAT_ENGINES.add('luxrender')
	blender_texture_ui.poll = blender_texture_poll

del properties_texture

# compatible() copied from blender repository (netrender)
def compatible(module):
	module = __import__(module)
	for subclass in module.__dict__.values():
		try:	subclass.COMPAT_ENGINES.add('luxrender')
		except:	pass
	del module

compatible("properties_data_mesh")
compatible("properties_data_camera")

class RENDERENGINE_luxrender(bpy.types.RenderEngine, engine_base):

	'''
	LuxRender Engine Exporter/Integration class
	'''
	
	bl_idname = 'luxrender'
	bl_label = 'LuxRender'
	bl_preview = False # blender's preview scene is inadequate, needs custom rebuild
	
	LuxManager = None
	render_update_timer = None
	output_file = 'default.png'
	
#	# This member is read by the ExporterFramework to set up the property groups for each UI panel
	interfaces = [
		# LuxRender configuration and settings
		ui_render_panels.engine,
		ui_render_panels.sampler,
		ui_render_panels.integrator,
		ui_render_panels.volume,
		ui_render_panels.filter,
		ui_render_panels.accelerator,

		# Custom object data panels
		ui_lamps.lamps,
		ui_meshes.meshes,
		ui_world.world,
		
		# Camera
		ui_camera.camera,
		ui_camera.colorspace,
		ui_camera.tonemapping,
		
		# Materials
		ui_materials.material_editor,
		
		# Textures
		texture_main.ui_panel_main,
		bilerp.ui_panel_bilerp,
		blackbody.ui_panel_blackbody,
		brick.ui_panel_brick,
		checkerboard.ui_panel_checkerboard,
		dots.ui_panel_dots,
		equalenergy.ui_panel_equalenergy,
		fbm.ui_panel_fbm,
		gaussian.ui_panel_gaussian,
		harlequin.ui_panel_harlequin,
		imagemap.ui_panel_imagemap,
		lampspectrum.ui_panel_lampspectrum,
		mapping.ui_panel_mapping,
		marble.ui_panel_marble,
		mix.ui_panel_mix,
		scale.ui_panel_scale,
		transform.ui_panel_transform,
		uv.ui_panel_uv,
		windy.ui_panel_windy,
		wrinkled.ui_panel_wrinkled,
	]
	
	def update_framebuffer(self, xres, yres, fb):
		'''
		xres		int
		yres		int
		fb			list
		
		Update the current RenderResult with the current render image.
		
		This will be called by the LuxFilmDisplay thread started by LuxManager
		
		TODO: perhaps this class itself is a threaded timer ?
		
		Returns None
		'''
		
		#print('fb len: %i' % len(fb))
		#print('fb max: %i' % max(fb))
		#print('fb min: %i' % min(fb))
		
		result = self.begin_result(0,0,xres,yres)
		# TODO: don't read the file whilst it is still being written..
		# ... however file locking in python seems incomplete/non-portable ?
		if os.path.exists(self.output_file):
			lay = result.layers[0]
			# TODO: use the framebuffer direct from pylux when Blender's API supports it
			lay.load_from_file(self.output_file)
		else:
			LuxLog('ERROR: Could not load render result from %s' % self.output_file)
		self.end_result(result)
	
	def render(self, context):
		'''
		scene		bpy.types.scene
		
		Export the given scene to LuxRender.
		Choose from one of several methods depending on what needs to be rendered.
		
		Returns None
		'''
		
		# Force update of all custom properties
		for ui in self.interfaces:
			ui.property_reload()
		
		if context.name == 'preview':
			self.render_preview(context)
		else:
			self.render_scene(context)
		
	def render_init(self, scene, api_type):
		
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
		self.LuxManager = LM(
			scene.name,
			api_type = api_type,
			threads = threads
		)
		LM.SetActive(self.LuxManager)
		
		lux_context = self.LuxManager.lux_context
		
		if api_type == 'FILE':
			
			LXS = scene.luxrender_engine.write_lxs
			LXM = scene.luxrender_engine.write_lxm
			LXO = scene.luxrender_engine.write_lxo
			
			if os.path.isdir(scene.render.filepath):
				output_dir = scene.render.filepath
			else:
				output_dir = os.path.dirname(scene.render.filepath)
			
			if not os.access( output_dir, os.W_OK):
				raise Exception('Output path "%s" is not writable' % output_dir)
			
			lxs_filename = os.path.join(
				output_dir,
				efutil.scene_filename() + '.%s.%05i' % (scene.name, scene.frame_current)
			)
			
			efutil.export_path = lxs_filename
			
			if LXS or LXM or LXO:
				lux_context.set_filename(
					lxs_filename,
					LXS = LXS, 
					LXM = LXM,
					LXO = LXO
				)
				self.output_file = efutil.path_relative_to_export(lxs_filename + '.png')
			else:
				raise Exception('Nothing to do! Select at least one of LXM/LXS/LXO')
		else:
			# Set export path so that relative paths in export work correctly
			efutil.export_path = scene.render.filepath
			self.output_file = efutil.path_relative_to_export(efutil.export_path) + '.png'
		
		# BEGIN!
		self.update_stats('', 'LuxRender: Parsing Scene')
		
		return lux_context
	
	def render_preview(self, scene):
		
		lux_context = self.render_init(scene, 'API')
		
		# Set up render parameters optimised for preview
		from luxrender.export.preview_scene import preview_scene_setup , preview_scene_lights
		preview_scene_setup(scene, lux_context)
		
		# Set up camera, view and film
		lux_context.lookAt( *export_film.lookAt(scene) )
		lux_context.camera( *scene.camera.data.luxrender_camera.api_output(scene, False) )
		
		lux_context.worldBegin()
		preview_scene_lights(lux_context)
		# Light source iteration and export goes here.
#		if export_lights.lights(l, scene) == False:
#			LuxLog('Error - No lights in scene.')
#			return
		
		# No materials as we're using API with no files, export
		# is handled in geometry iteration
		
		# Geometry iteration and export goes here.
		export_geometry.write_lxo(self, lux_context, scene, smoothing_enabled=False)
		
		self.render_start(scene)
	
	def render_scene(self, scene):
		
		if scene.luxrender_engine.export_type == 'INT' and not scene.luxrender_engine.write_files:
			api_type = 'API'
			write_files = scene.luxrender_engine.write_files
		elif scene.luxrender_engine.export_type == 'LFC':
			api_type = 'LUXFIRE_CLIENT'
			write_files = False
		else:
			api_type = 'FILE'
			write_files = True
		
		lux_context = self.render_init(scene, api_type)
		
		if (api_type in ['API', 'LUXFIRE_CLIENT'] and not write_files) or (write_files and scene.luxrender_engine.write_lxs):
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
			export_materials.ExportedTextures.clear()
			if api_type == 'FILE':
				lux_context.set_output_file(Files.MAIN)
			
			if export_lights.lights(lux_context, scene) == False:
				LuxLog('Error - No lights in scene.')
				return
		
		if (api_type in ['API', 'LUXFIRE_CLIENT'] and not write_files) or (write_files and scene.luxrender_engine.write_lxm):
			if api_type == 'FILE':
				lux_context.set_output_file(Files.MATS)
			export_materials.ExportedMaterials.clear()
			export_materials.write_lxm(lux_context, scene)
		
		if (api_type in ['API', 'LUXFIRE_CLIENT'] and not write_files) or (write_files and scene.luxrender_engine.write_lxo):
			if api_type == 'FILE':
				lux_context.set_output_file(Files.GEOM)
			export_geometry.write_lxo(self, lux_context, scene, smoothing_enabled=True)
		
		self.render_start(scene)
		
	def render_start(self, scene):
		# TODO: this will be removed when direct framebuffer
		# access is implemented in Blender
		if os.path.exists(self.output_file):
			# reset output image file and
			os.remove(self.output_file)
		
		internal	= (scene.luxrender_engine.export_type in ['INT', 'LFC'])
		write_files	= scene.luxrender_engine.write_files
		render		= scene.luxrender_engine.render
		
		# Handle various option combinations using simplified variable names !
		if internal:
			if write_files:
				if render:
					start_rendering = True
					parse = True
					worldEnd = False
				else:
					start_rendering = False
					parse = False
					worldEnd = False
			else:
				# will always render
				start_rendering = True
				parse = False
				worldEnd = True
		else:
			# external always writes files
			if render:
				start_rendering = True
				parse = False
				worldEnd = False
			else:
				start_rendering = False
				parse = False
				worldEnd = False
		
		#print('internal %s' % internal)
		#print('write_files %s' % write_files)
		#print('render %s' % render)
		#print('start_rendering %s' % start_rendering)
		#print('parse %s' % parse)
		#print('worldEnd %s' % worldEnd)
		
		# Set path to export path to launch render
		working_path = os.getcwd()
		os.chdir( os.path.dirname(efutil.export_path) )
		
		if self.LuxManager.lux_context.API_TYPE == 'FILE':
			#print('calling pylux.context.worldEnd() (1)')
			self.LuxManager.lux_context.worldEnd()
			if parse:
				# file_api.parse() creates a real pylux context. we must replace
				# LuxManager's context with that one so that the running renderer
				# can be controlled.
				ctx = self.LuxManager.lux_context.parse(self.LuxManager.lux_context.file_names[0], True)
				self.LuxManager.lux_context = ctx
				self.LuxManager.stats_thread.lux_context = ctx
				self.LuxManager.fb_thread.lux_context = ctx
		elif worldEnd:
			#print('calling pylux.context.worldEnd() (2)')
			self.LuxManager.lux_context.worldEnd()
		
		# Begin rendering
		if start_rendering:
			if internal:
				self.LuxManager.start(self)
				self.update_stats('', 'LuxRender: Rendering warmup')
				while self.LuxManager.started:
					self.render_update_timer = threading.Timer(1, self.stats_timer)
					self.render_update_timer.start()
					if self.render_update_timer.isAlive(): self.render_update_timer.join()
			else:
				config_updates = {
					'auto_start': render
				}
				
				luxrender_path = scene.luxrender_engine.exe_path
				if os.path.exists(luxrender_path):
					config_updates['exe_path'] = luxrender_path

				# Get binary from OSX package
				if sys.platform == 'darwin':
					luxrender_path += '/Contents/MacOS/luxrender'
				
				if not os.path.exists(luxrender_path):
					raise
				
				try:
					for k,v in config_updates.items():
						efutil.write_config_value('luxrender', 'defaults', k, v)
				except Exception as err:
					LuxLog('Saving LuxRender config failed: %s' % err)
				
				fn = self.LuxManager.lux_context.file_names[0]
				LuxLog('Launching LuxRender with scene file "%s"' % fn)
				# TODO: add support for luxrender command line options
				subprocess.Popen([luxrender_path + ' %s'%fn], shell=True)
		
		os.chdir(working_path)
	
	def stats_timer(self):
		'''
		Update the displayed rendering statistics and detect end of rendering
		
		Returns None
		'''
		
		self.update_stats('', 'LuxRender: Rendering %s' % self.LuxManager.stats_thread.stats_string)
		if self.test_break() or \
			self.LuxManager.lux_context.statistics('filmIsReady') == 1.0 or \
			self.LuxManager.lux_context.statistics('terminated') == 1.0 or \
			self.LuxManager.lux_context.statistics('enoughSamples') == 1.0:
			self.LuxManager.reset()
			LM.ClearActive()
			self.update_stats('', '')

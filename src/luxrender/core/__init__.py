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
"""Main LuxRender extension class definition"""

# System libs
import os
import multiprocessing
import time
import threading
import subprocess
import sys

# Blender libs
import bpy

# Framework libs
from extensions_framework.engine		import ( engine_base )
from extensions_framework				import ( util as efutil )

# Exporter libs
from luxrender.outputs					import ( LuxManager, LuxFilmDisplay )
from luxrender.outputs					import ( LuxLog )
from luxrender.outputs.pure_api			import ( LUXRENDER_VERSION )

# Exporter Property Groups
from luxrender.properties.accelerator	import ( luxrender_accelerator )
from luxrender.properties.camera 		import ( luxrender_camera,
												 luxrender_colorspace,
												 luxrender_film,
												 luxrender_tonemapping )
from luxrender.properties.engine		import ( luxrender_engine, luxrender_networking )
from luxrender.properties.filter		import ( luxrender_filter )
from luxrender.properties.integrator	import ( luxrender_integrator )
from luxrender.properties.lamp			import ( luxrender_lamp,
												 luxrender_lamp_point,
												 luxrender_lamp_sun,
												 luxrender_lamp_spot,
												 luxrender_lamp_hemi,
												 luxrender_lamp_area )
from luxrender.properties.material		import ( luxrender_material,
												 luxrender_mat_compositing,
												 luxrender_mat_carpaint,
												 luxrender_mat_glass,
												 luxrender_mat_glass2,
												 luxrender_mat_roughglass,
												 luxrender_mat_glossytranslucent,
												 luxrender_mat_glossy,
												 luxrender_mat_glossy_lossy,
												 luxrender_mat_matte,
												 luxrender_mat_mattetranslucent,
												 luxrender_mat_metal,
												 luxrender_mat_scatter,
												 luxrender_mat_shinymetal,
												 luxrender_mat_mirror,
												 luxrender_mat_mix,
												 luxrender_mat_null,
												 luxrender_mat_velvet,
												 luxrender_volume_data,
												 luxrender_volumes )
from luxrender.properties.mesh			import ( luxrender_mesh )
from luxrender.properties.object		import ( luxrender_emission )
from luxrender.properties.texture		import ( luxrender_texture,
												 luxrender_tex_bilerp,
												 luxrender_tex_blackbody,
												 luxrender_tex_brick,
												 luxrender_tex_cauchy,
												 luxrender_tex_constant,
												 luxrender_tex_checkerboard,
												 luxrender_tex_dots,
												 luxrender_tex_equalenergy,
												 luxrender_tex_fbm,
												 luxrender_tex_gaussian,
												 luxrender_tex_harlequin,
												 luxrender_tex_imagemap,
												 luxrender_tex_lampspectrum,
												 luxrender_tex_luxpop,
												 luxrender_tex_mapping,
												 luxrender_tex_marble,
												 luxrender_tex_mix,
												 luxrender_tex_sellmeier,
												 luxrender_tex_scale,
												 luxrender_tex_sopra,
												 luxrender_tex_transform,
												 luxrender_tex_uv,
												 luxrender_tex_windy,
												 luxrender_tex_wrinkled )
from luxrender.properties.sampler		import ( luxrender_sampler )
from luxrender.properties.volume		import ( luxrender_volumeintegrator )

# Exporter Interface Panels
from luxrender.ui						import ( render_panels		as ui_render_panels )
from luxrender.ui						import ( camera				as ui_camera )
from luxrender.ui						import ( image				as ui_image )
from luxrender.ui						import ( lamps				as ui_lamps )
from luxrender.ui						import ( mesh				as ui_mesh )
from luxrender.ui						import ( object				as ui_object )
from luxrender.ui.materials				import ( main				as ui_materials,
												 compositing		as ui_materials_compositing,
												 carpaint			as ui_materials_carpaint,
												 glass				as ui_materials_glass,
												 glass2				as ui_materials_glass2,
												 roughglass			as ui_materials_roughglass,
												 glossytranslucent	as ui_materials_glossytranslucent,
												 glossy_lossy		as ui_materials_glossy_lossy,
												 glossy				as ui_materials_glossy,
												 matte				as ui_materials_matte,
												 mattetranslucent	as ui_materials_mattetranslucent,
												 metal				as ui_materials_metal,
												 mirror				as ui_materials_mirror,
												 mix				as ui_materials_mix,
												 null				as ui_materials_null,
												 scatter			as ui_materials_scatter,
												 shinymetal			as ui_materials_shinymetal,
												 velvet				as ui_materials_velvet,
												 volumes			as ui_materials_volumes )
from luxrender.ui.textures				import ( main				as ui_textures,
												 bilerp				as ui_texture_bilerp,
												 blackbody			as ui_texture_blackbody,
												 brick				as ui_texture_brick,
												 cauchy				as ui_texture_cauchy,
												 constant			as ui_texture_constant,
												 checkerboard		as ui_texture_checkerboard,
												 dots				as ui_texture_dots,
												 equalenergy		as ui_texture_equalenergy,
												 fbm				as ui_texture_fbm,
												 gaussian			as ui_texture_gaussian,
												 harlequin			as ui_texture_harlequin,
												 imagemap			as ui_texture_imagemap,
												 lampspectrum		as ui_texture_lampspectrum,
												 luxpop				as ui_texture_luxpop,
												 marble				as ui_texture_marble,
												 mix				as ui_texture_mix,
												 sellmeier			as ui_texture_sellmeier,
												 scale				as ui_texture_scale,
												 sopra				as ui_texture_sopra,
												 uv					as ui_texture_uv,
												 windy				as ui_texture_windy,
												 wrinkled			as ui_texture_wrinkled,
												 mapping			as ui_texture_mapping,
												 transform			as ui_texture_transform )

# Exporter Operators
from luxrender.operators				import ( EXPORT_OT_luxrender,
												 LUXRENDER_OT_volume_add,
												 LUXRENDER_OT_volume_remove )

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
	show = tex and \
		   ((tex.type == cls.tex_type and not tex.use_nodes) and \
		   (context.scene.render.engine in cls.COMPAT_ENGINES))
	
	if context.scene.render.engine == 'luxrender':
		show = show and tex.luxrender_texture.type == 'BLENDER'
	
	return show

import properties_texture
properties_texture.TEXTURE_PT_context_texture.COMPAT_ENGINES.add('luxrender')
blender_texture_ui_list = [
	properties_texture.TEXTURE_PT_blend,
	properties_texture.TEXTURE_PT_clouds,
	properties_texture.TEXTURE_PT_distortednoise,
	properties_texture.TEXTURE_PT_image,
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
def compatible(mod):
	mod = __import__(mod)
	for subclass in mod.__dict__.values():
		try:
			subclass.COMPAT_ENGINES.add('luxrender')
		except:
			pass
	del mod

compatible("properties_data_mesh")
compatible("properties_data_camera")
compatible("properties_particle")


class RENDERENGINE_luxrender(bpy.types.RenderEngine, engine_base):

	'''
	LuxRender Engine Exporter/Integration class
	'''
	
	bl_idname			= 'luxrender'
	bl_label			= 'LuxRender'
	bl_use_preview		= True
	
	LuxManager			= None
	render_update_timer	= None
	output_dir			= './'
	output_file			= 'default.png'
	
#	# This member is read by the extensions_framework to set up custom property groups
	property_groups = [
		('Scene', luxrender_accelerator),
		('Scene', luxrender_engine),
		('Scene', luxrender_networking),
		('Scene', luxrender_filter),
		('Scene', luxrender_integrator),
		('Scene', luxrender_sampler),
		('Scene', luxrender_volumeintegrator),
		('Scene', luxrender_volumes),
		('Camera', luxrender_camera),
		('luxrender_camera', luxrender_film),
		('luxrender_film', luxrender_colorspace),
		('luxrender_film', luxrender_tonemapping),
		('Lamp', luxrender_lamp),
		('luxrender_lamp', luxrender_lamp_point),
		('luxrender_lamp', luxrender_lamp_sun),
		('luxrender_lamp', luxrender_lamp_spot),
		('luxrender_lamp', luxrender_lamp_hemi),
		('luxrender_lamp', luxrender_lamp_area),
		('Mesh', luxrender_mesh),
		('Material', luxrender_material),
		('luxrender_material', luxrender_mat_compositing),
		('luxrender_material', luxrender_mat_carpaint),
		('luxrender_material', luxrender_mat_glass),
		('luxrender_material', luxrender_mat_glass2),
		('luxrender_material', luxrender_mat_roughglass),
		('luxrender_material', luxrender_mat_glossytranslucent),
		('luxrender_material', luxrender_mat_glossy),
		('luxrender_material', luxrender_mat_glossy_lossy),
		('luxrender_material', luxrender_mat_matte),
		('luxrender_material', luxrender_mat_mattetranslucent),
		('luxrender_material', luxrender_mat_metal),
		('luxrender_material', luxrender_mat_scatter),
		('luxrender_material', luxrender_mat_shinymetal),
		('luxrender_material', luxrender_mat_mirror),
		('luxrender_material', luxrender_mat_mix),
		('luxrender_material', luxrender_mat_null),
		('luxrender_material', luxrender_mat_velvet),
		('Object', luxrender_emission),
		(None, luxrender_volume_data),		# call init_properties, but don't create instance
		('Texture', luxrender_texture),
		('luxrender_texture', luxrender_tex_bilerp),
		('luxrender_texture', luxrender_tex_blackbody),
		('luxrender_texture', luxrender_tex_brick),
		('luxrender_texture', luxrender_tex_cauchy),
		('luxrender_texture', luxrender_tex_constant),
		('luxrender_texture', luxrender_tex_checkerboard),
		('luxrender_texture', luxrender_tex_dots),
		('luxrender_texture', luxrender_tex_equalenergy),
		('luxrender_texture', luxrender_tex_fbm),
		('luxrender_texture', luxrender_tex_gaussian),
		('luxrender_texture', luxrender_tex_harlequin),
		('luxrender_texture', luxrender_tex_imagemap),
		('luxrender_texture', luxrender_tex_lampspectrum),
		('luxrender_texture', luxrender_tex_luxpop),
		('luxrender_texture', luxrender_tex_mapping),
		('luxrender_texture', luxrender_tex_marble),
		('luxrender_texture', luxrender_tex_mix),
		('luxrender_texture', luxrender_tex_sellmeier),
		('luxrender_texture', luxrender_tex_scale),
		('luxrender_texture', luxrender_tex_sopra),
		('luxrender_texture', luxrender_tex_transform),
		('luxrender_texture', luxrender_tex_uv),
		('luxrender_texture', luxrender_tex_windy),
		('luxrender_texture', luxrender_tex_wrinkled),
	]
	
	render_lock = threading.Lock()
	
	def render(self, scene):
		'''
		scene:	bpy.types.Scene
		
		Export the given scene to LuxRender.
		Choose from one of several methods depending on what needs to be rendered.
		
		Returns None
		'''
		
		with self.render_lock:	# just render one thing at a time
			prev_dir = os.getcwd()
			
			if scene is None:
				bpy.ops.ef.msg(msg_type='ERROR', msg_text='Scene to render is not valid')
				return
			
			if scene.name == 'preview':
				self.render_preview(scene)
				return
			
			if scene.render.use_color_management == False:
				LuxLog('WARNING: Colour Management is switched off, render results may look too dark.')
			
			if self.render_scene(scene) == False:
				#bpy.ops.ef.msg(msg_type='ERROR', msg_text='Export failed')
				return
			
			self.render_start(scene)
			os.chdir(prev_dir)
	
	def render_preview(self, scene):
		self.output_dir = efutil.filesystem_path( bpy.app.tempdir )
		
		if self.output_dir[-1] != '/':
			self.output_dir += '/'
		
		efutil.export_path = self.output_dir
		#print('(2) export_path is %s' % efutil.export_path)
		os.chdir( self.output_dir )
		
		from luxrender.outputs.pure_api import PYLUX_AVAILABLE
		if not PYLUX_AVAILABLE:
			self.bl_use_preview = False
			bpy.ops.ef.msg(msg_type='ERROR', msg_text='Material previews require pylux')
			return
		
		from luxrender.export import materials as export_materials
		
		# Iterate through the preview scene, finding objects with materials attached
		objects_mats = {}
		for object in [ob for ob in scene.objects if ob.is_visible(scene) and not ob.hide_render]:
			for mat in export_materials.get_instance_materials(object):
				if mat is not None:
					if not object.name in objects_mats.keys(): objects_mats[object] = []
					objects_mats[object].append(mat)
		
		# find objects that are likely to be the preview objects
		preview_objects = [o for o in objects_mats.keys() if o.name.startswith('preview')]
		if len(preview_objects) < 1:
			return
		
		# find the materials attached to the likely preview object
		likely_materials = objects_mats[preview_objects[0]]
		if len(likely_materials) < 1:
			return
		
		pm = likely_materials[0]
		LuxLog('Rendering material preview: %s' % pm.name)
		
		LM = LuxManager(
			scene.name,
			api_type = 'API',
		)
		LuxManager.SetCurrentScene(scene)
		LuxManager.SetActive(LM)
		
		file_based_preview = False
		
		if file_based_preview:
			# Dump to file in temp dir for debugging
			from luxrender.outputs.file_api import Custom_Context as lxs_writer
			preview_context = lxs_writer(scene.name)
			preview_context.set_filename('luxblend25-preview', LXS=True, LXM=False, LXO=False)
			LM.lux_context = preview_context
		else:
			preview_context = LM.lux_context
		
		try:
			export_materials.ExportedMaterials.clear()
			export_materials.ExportedTextures.clear()
			
			from luxrender.export import preview_scene
			xres, yres = scene.camera.data.luxrender_camera.luxrender_film.resolution()
			xres, yres = int(xres), int(yres)
			
			# Don't render the tiny images
			if xres <= 96:
				raise Exception('Preview image too small (%ix%i)' % (xres,yres))
			
			preview_scene.preview_scene(scene, preview_context, obj=preview_objects[0], mat=pm)
			
			# render !
			preview_context.worldEnd()
			
			if file_based_preview:
				preview_context = preview_context.parse('luxblend25-preview.lxs', True)
				LM.lux_context = preview_context
			
			while not preview_context.statistics('sceneIsReady'):
				time.sleep(0.05)
			
			def is_finished(ctx):
				#future
				#return ctx.getAttribute('renderer', 'state') == ctx.PYLUX.Renderer.State.TERMINATE
				return ctx.statistics('enoughSamples') == 1.0
			
			def interruptible_sleep(sec, increment=0.05):
				sec_elapsed = 0.0
				while not self.test_break() and sec_elapsed<=sec:
					sec_elapsed += increment
					time.sleep(increment)
			
			for i in range(multiprocessing.cpu_count()-2):
				# -2 since 1 thread already created and leave 1 spare
				if is_finished(preview_context):
					break
				preview_context.addThread()
			
			while not is_finished(preview_context):
				if self.test_break():
					raise Exception('Render interrupted')
				
				# progressively update the preview
				time.sleep(0.2) # safety-sleep
				if LUXRENDER_VERSION < '0.8' or preview_context.statistics('samplesPx') > 24:
					interruptible_sleep(1.8) # up to HALTSPP every 2 seconds in sum
					
				LuxLog('Updating preview (%ix%i - %s)' % (xres, yres, preview_context.printableStatistics(False)))
				
				result = self.begin_result(0, 0, xres, yres)
				lay = result.layers[0]
				
				lay.rect, no_z_buffer  = preview_context.blenderCombinedDepthRects()
				
				self.end_result(result)
		except Exception as exc:
			LuxLog('Preview aborted: %s' % exc)
		
		preview_context.exit()
		preview_context.wait()
		preview_context.cleanup()
		
		LM.reset()
	
	def render_scene(self, scene):
		scene_path = efutil.filesystem_path(scene.render.filepath)
		if os.path.isdir(scene_path):
			self.output_dir = scene_path
		else:
			self.output_dir = os.path.dirname( scene_path )
		
		if self.output_dir[-1] != '/':
			self.output_dir += '/'
		
		efutil.export_path = self.output_dir
		#print('(1) export_path is %s' % efutil.export_path)
		os.chdir(self.output_dir)
		
		if scene.luxrender_engine.export_type == 'INT': # and not scene.luxrender_engine.write_files:
			write_files = scene.luxrender_engine.write_files
			if write_files:
				api_type = 'FILE'
			else:
				api_type = 'API'
		elif scene.luxrender_engine.export_type == 'LFC':
			api_type = 'LUXFIRE_CLIENT'
			write_files = False
		else:
			api_type = 'FILE'
			write_files = True
		
		# Pre-allocate the LuxManager so that we can set up the network servers before export
		LM = LuxManager(
			scene.name,
			api_type = api_type,
		)
		LuxManager.SetActive(LM)
		
		if scene.luxrender_engine.export_type == 'INT':
			# Set up networking before export so that we get better server usage
			if scene.luxrender_networking.use_network_servers:
				LM.lux_context.setNetworkServerUpdateInterval( scene.luxrender_networking.serverinterval )
				for server in scene.luxrender_networking.servers.split(','):
					LM.lux_context.addServer(server.strip())
		
		output_filename = efutil.scene_filename() + '.%s.%05i' % (scene.name, scene.frame_current)
		export_result = bpy.ops.export.luxrender(
			directory = self.output_dir,
			filename = output_filename,
			
			api_type = api_type,			# Set export target
			write_files = write_files,		# Use file write decision from above
			write_all_files = False,		# Use UI file write settings
			scene = scene.name,				# Export this named scene
		)
		
		if 'CANCELLED' in export_result:
			return False
		
		if not scene.camera.data.luxrender_camera.luxrender_film.integratedimaging:
			self.output_file = efutil.path_relative_to_export(
				'%s/%s.png' % (self.output_dir, output_filename)
			)
		
		return True
	
	def render_start(self, scene):
		self.LuxManager = LuxManager.ActiveManager
		
		# TODO: this will be removed when direct framebuffer
		# access is implemented in Blender
		if os.path.exists(self.output_file):
			# reset output image file and
			os.remove(self.output_file)
		
		internal	= (scene.luxrender_engine.export_type in ['INT', 'LFC'])
		write_files	= scene.luxrender_engine.write_files and (scene.luxrender_engine.export_type in ['INT', 'EXT'])
		render		= scene.luxrender_engine.render or (scene.luxrender_engine.export_type in ['LFC'])
		
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
		
		if self.LuxManager.lux_context.API_TYPE == 'FILE':
			fn = self.LuxManager.lux_context.file_names[0]
			
			#print('calling pylux.context.worldEnd() (1)')
			self.LuxManager.lux_context.worldEnd()
			if parse:
				# file_api.parse() creates a real pylux context. we must replace
				# LuxManager's context with that one so that the running renderer
				# can be controlled.
				ctx = self.LuxManager.lux_context.parse(fn, True)
				self.LuxManager.lux_context = ctx
				self.LuxManager.stats_thread.LocalStorage['lux_context'] = ctx
				self.LuxManager.fb_thread.LocalStorage['lux_context'] = ctx
		elif worldEnd:
			#print('calling pylux.context.worldEnd() (2)')
			self.LuxManager.lux_context.worldEnd()
		
		# Begin rendering
		if start_rendering:
			bpy.ops.ef.msg(msg_text='Starting LuxRender')
			if internal:
				
				self.update_stats('', 'LuxRender: Rendering warmup')
				self.LuxManager.start()
				
				self.LuxManager.fb_thread.LocalStorage['integratedimaging'] = scene.camera.data.luxrender_camera.luxrender_film.integratedimaging
				
				if scene.camera.data.luxrender_camera.luxrender_film.integratedimaging:
					# Use the GUI update interval
					self.LuxManager.fb_thread.set_kick_period( scene.camera.data.luxrender_camera.luxrender_film.displayinterval )
				else:
					# Update the image from disk only as often as it is written
					self.LuxManager.fb_thread.set_kick_period( scene.camera.data.luxrender_camera.luxrender_film.writeinterval )
				
				# Start the stats and framebuffer threads and add additional threads to Lux renderer
				self.LuxManager.start_worker_threads(self)
				
				if scene.luxrender_engine.threads_auto:
					try:
						thread_count = multiprocessing.cpu_count()
					except:
						# TODO: when might this fail?
						thread_count = 1
				else:
					thread_count = scene.luxrender_engine.threads
				
				# Run rendering with specified number of threads
				for i in range(thread_count - 1):
					self.LuxManager.lux_context.addThread()
				
				while self.LuxManager.started:
					self.render_update_timer = threading.Timer(1, self.stats_timer)
					self.render_update_timer.start()
					if self.render_update_timer.isAlive(): self.render_update_timer.join()
			else:
				config_updates = {
					'auto_start': render
				}
				
				luxrender_path = efutil.filesystem_path( scene.luxrender_engine.install_path )
				if luxrender_path[-1] != '/':
					luxrender_path += '/'
				
				if os.path.isdir(luxrender_path) and os.path.exists(luxrender_path):
					config_updates['install_path'] = luxrender_path
				
				if sys.platform == 'darwin' and scene.luxrender_engine.binary_name == 'luxrender':
					# Get binary from OSX package
					luxrender_path += 'luxrender.app/Contents/MacOS/luxrender'
				elif sys.platform == 'win32':
					luxrender_path += '%s.exe' % scene.luxrender_engine.binary_name
				else:
					luxrender_path += scene.luxrender_engine.binary_name
				
				if not os.path.exists(luxrender_path):
					LuxLog('LuxRender not found at path: %s' % luxrender_path)
					return False
				
				cmd_args = [luxrender_path, fn]
				
				if scene.luxrender_engine.binary_name == 'luxrender':
					# Copy the GUI log to the console
					cmd_args.append('--logconsole')
				
				# Set number of threads for external processes
				if not scene.luxrender_engine.threads_auto:
					cmd_args.append('--threads=%i' % scene.luxrender_engine.threads)
				
				if scene.luxrender_networking.use_network_servers:
					for server in scene.luxrender_networking.servers.split(','):
						cmd_args.append('--useserver')
						cmd_args.append(server.strip())
					
					cmd_args.append('--serverinterval')
					cmd_args.append('%i' % scene.luxrender_networking.serverinterval)
					
					config_updates['servers'] = scene.luxrender_networking.servers
					config_updates['serverinterval'] = '%i' % scene.luxrender_networking.serverinterval
				
				config_updates['use_network_servers'] = scene.luxrender_networking.use_network_servers
				
				# Save changed config items and then launch Lux
				
				try:
					for k, v in config_updates.items():
						efutil.write_config_value('luxrender', 'defaults', k, v)
				except Exception as err:
					LuxLog('WARNING: Saving LuxRender config failed, please set your user scripts dir: %s' % err)
				
				LuxLog('Launching: %s' % cmd_args)
				# LuxLog(' in %s' % self.outout_dir)
				luxrender_process = subprocess.Popen(cmd_args, cwd=self.output_dir)
				framebuffer_thread = LuxFilmDisplay({
					'resolution': scene.camera.data.luxrender_camera.luxrender_film.resolution(),
					'RE': self,
				})
				framebuffer_thread.set_kick_period( scene.camera.data.luxrender_camera.luxrender_film.writeinterval ) 
				framebuffer_thread.start()
				while luxrender_process.poll() == None and not self.test_break():
					self.render_update_timer = threading.Timer(1, self.process_wait_timer)
					self.render_update_timer.start()
					if self.render_update_timer.isAlive(): self.render_update_timer.join()
				
				# If we exit the wait loop (user cancelled) and luxconsole is still running, then send SIGINT
				if luxrender_process.poll() == None and scene.luxrender_engine.binary_name != 'luxrender':
					# Use SIGTERM because that's the only one supported on Windows
					luxrender_process.send_signal(subprocess.signal.SIGTERM)
				
				# Stop updating the render result and load the final image
				framebuffer_thread.stop()
				framebuffer_thread.join()
				framebuffer_thread.kick(render_end=True)
	
	def process_wait_timer(self):
		# Nothing to do here
		pass
	
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
			self.update_stats('', '')

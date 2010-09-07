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
from luxrender.outputs import LuxManager as LM
from luxrender.outputs import LuxLog

# Exporter Property Groups
from luxrender.properties.accelerator	import	luxrender_accelerator
from luxrender.properties.camera 		import	luxrender_camera, \
												luxrender_colorspace, \
												luxrender_tonemapping
from luxrender.properties.engine		import	luxrender_engine
from luxrender.properties.filter		import	luxrender_filter
from luxrender.properties.integrator	import	luxrender_integrator
from luxrender.properties.lamp			import	luxrender_lamp
from luxrender.properties.material		import	luxrender_material, \
												luxrender_emission, \
												luxrender_volume_data, \
												luxrender_volumes, \
												carpaint			as luxrender_material_carpaint, \
												glass				as luxrender_material_glass, \
												glass2				as luxrender_material_glass2, \
												roughglass			as luxrender_material_roughglass, \
												glossy				as luxrender_material_glossy, \
												glossy_lossy		as luxrender_material_glossy_lossy, \
												matte				as luxrender_material_matte, \
												mattetranslucent	as luxrender_material_mattetranslucent, \
												metal				as luxrender_material_metal, \
												shinymetal			as luxrender_material_shinymetal, \
												mirror				as luxrender_material_mirror, \
												mix					as luxrender_material_mix, \
												null				as luxrender_material_null,\
												velvet				as luxrender_material_velvet
from luxrender.properties.mesh			import	luxrender_mesh
from luxrender.properties.texture		import	luxrender_texture, \
												bilerp				as luxrender_texture_bilerp, \
												blackbody			as luxrender_texture_blackbody, \
												brick				as luxrender_texture_brick, \
												cauchy				as luxrender_texture_cauchy, \
												constant			as luxrender_texture_constant, \
												checkerboard		as luxrender_texture_checkerboard, \
												dots				as luxrender_texture_dots, \
												equalenergy			as luxrender_texture_equalenergy, \
												fbm					as luxrender_texture_fbm, \
												gaussian			as luxrender_texture_gaussian, \
												harlequin			as luxrender_texture_harlequin, \
												imagemap			as luxrender_texture_imagemap, \
												lampspectrum		as luxrender_texture_lampspectrum, \
												luxpop				as luxrender_texture_luxpop, \
												mapping				as luxrender_texture_mapping, \
												marble				as luxrender_texture_marble, \
												mix					as luxrender_texture_mix, \
												sellmeier			as luxrender_texture_sellmeier, \
												scale				as luxrender_texture_scale, \
												sopra				as luxrender_texture_sopra, \
												transform			as luxrender_texture_transform, \
												uv					as luxrender_texture_uv, \
												windy				as luxrender_texture_windy, \
												wrinkled			as luxrender_texture_wrinkled
from luxrender.properties.sampler		import	luxrender_sampler
from luxrender.properties.volume		import	luxrender_volumeintegrator

# Exporter Interface Panels
from luxrender.ui						import	render_panels		as ui_render_panels
from luxrender.ui						import	camera				as ui_camera
from luxrender.ui						import	lamps				as ui_lamps
from luxrender.ui						import	meshes				as ui_meshes
from luxrender.ui.materials				import	main				as ui_materials, \
												carpaint			as ui_materials_carpaint, \
												glass				as ui_materials_glass, \
												glass2				as ui_materials_glass2, \
												roughglass			as ui_materials_roughglass, \
												glossy_lossy		as ui_materials_glossy_lossy, \
												glossy				as ui_materials_glossy, \
												matte				as ui_materials_matte, \
												mattetranslucent	as ui_materials_mattetranslucent, \
												metal				as ui_materials_metal, \
												mirror				as ui_materials_mirror, \
												mix					as ui_materials_mix, \
												shinymetal			as ui_materials_shinymetal, \
												velvet				as ui_materials_velvet, \
												emission			as ui_materials_emission, \
												volumes				as ui_materials_volumes
from luxrender.ui.textures				import	main				as ui_textures, \
												bilerp				as ui_texture_bilerp, \
												blackbody			as ui_texture_blackbody, \
												brick				as ui_texture_brick, \
												cauchy				as ui_texture_cauchy, \
												constant			as ui_texture_constant, \
												checkerboard		as ui_texture_checkerboard, \
												dots				as ui_texture_dots, \
												equalenergy			as ui_texture_equalenergy, \
												fbm					as ui_texture_fbm, \
												gaussian			as ui_texture_gaussian, \
												harlequin			as ui_texture_harlequin, \
												imagemap			as ui_texture_imagemap, \
												lampspectrum		as ui_texture_lampspectrum, \
												luxpop				as ui_texture_luxpop, \
												marble				as ui_texture_marble, \
												mix					as ui_texture_mix, \
												sellmeier			as ui_texture_sellmeier, \
												scale				as ui_texture_scale, \
												sopra				as ui_texture_sopra, \
												uv					as ui_texture_uv, \
												windy				as ui_texture_windy, \
												wrinkled			as ui_texture_wrinkled, \
												mapping				as ui_texture_mapping, \
												transform			as ui_texture_transform

# Exporter Operators
from luxrender.operators import		EXPORT_OT_luxrender, LUXRENDER_OT_volume_add, LUXRENDER_OT_volume_remove

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
def compatible(md):
	md = __import__(md)
	for subclass in md.__dict__.values():
		try:	subclass.COMPAT_ENGINES.add('luxrender')
		except:	pass
	del md

compatible("properties_data_mesh")
compatible("properties_data_camera")

class RENDERENGINE_luxrender(bpy.types.RenderEngine, engine_base):

	'''
	LuxRender Engine Exporter/Integration class
	'''
	
	bl_idname			= 'luxrender'
	bl_label			= 'LuxRender'
	bl_preview			= False			# blender's preview scene is inadequate, needs custom rebuild
	
	LuxManager			= None
	render_update_timer	= None
	output_file			= 'default.png'
	
#	# This member is read by the ExporterFramework to set up custom property groups
	property_groups = [
		('Scene', luxrender_accelerator),
		('Scene', luxrender_engine),
		('Scene', luxrender_filter),
		('Scene', luxrender_integrator),
		('Scene', luxrender_sampler),
		('Scene', luxrender_volumeintegrator),
		('Scene', luxrender_volumes),
		('Camera', luxrender_camera),
		('Camera', luxrender_colorspace),
		('Camera', luxrender_tonemapping),
		('Lamp', luxrender_lamp),
		('Mesh', luxrender_mesh),
		('Material', luxrender_emission),
		('Material', luxrender_material),
		('luxrender_material', luxrender_material_carpaint),
		('luxrender_material', luxrender_material_glass),
		('luxrender_material', luxrender_material_glass2),
		('luxrender_material', luxrender_material_roughglass),
		('luxrender_material', luxrender_material_glossy),
		('luxrender_material', luxrender_material_glossy_lossy),
		('luxrender_material', luxrender_material_matte),
		('luxrender_material', luxrender_material_mattetranslucent),
		('luxrender_material', luxrender_material_metal),
		('luxrender_material', luxrender_material_shinymetal),
		('luxrender_material', luxrender_material_mirror),
		('luxrender_material', luxrender_material_mix),
		('luxrender_material', luxrender_material_null),
		('luxrender_material', luxrender_material_velvet),
		(None, luxrender_volume_data),		# call init_properties, but don't create instance
		('Texture', luxrender_texture),
		('luxrender_texture', luxrender_texture_bilerp),
		('luxrender_texture', luxrender_texture_blackbody),
		('luxrender_texture', luxrender_texture_brick),
		('luxrender_texture', luxrender_texture_cauchy),
		('luxrender_texture', luxrender_texture_constant),
		('luxrender_texture', luxrender_texture_checkerboard),
		('luxrender_texture', luxrender_texture_dots),
		('luxrender_texture', luxrender_texture_equalenergy),
		('luxrender_texture', luxrender_texture_fbm),
		('luxrender_texture', luxrender_texture_gaussian),
		('luxrender_texture', luxrender_texture_harlequin),
		('luxrender_texture', luxrender_texture_imagemap),
		('luxrender_texture', luxrender_texture_lampspectrum),
		('luxrender_texture', luxrender_texture_luxpop),
		('luxrender_texture', luxrender_texture_mapping),
		('luxrender_texture', luxrender_texture_marble),
		('luxrender_texture', luxrender_texture_mix),
		('luxrender_texture', luxrender_texture_sellmeier),
		('luxrender_texture', luxrender_texture_scale),
		('luxrender_texture', luxrender_texture_sopra),
		('luxrender_texture', luxrender_texture_transform),
		('luxrender_texture', luxrender_texture_uv),
		('luxrender_texture', luxrender_texture_windy),
		('luxrender_texture', luxrender_texture_wrinkled),
	]
	
	def update_framebuffer(self, xres, yres, fb):
		'''
		xres		int
		yres		int
		fb			list
		
		Update the current RenderResult with the current render image.
		
		This will be called by the LuxFilmDisplay thread started by LuxManager
		
		TODO: move this method into LuxFilmDisplay
		
		Returns None
		'''
		
		result = self.begin_result(0,0,xres,yres)
		# TODO: don't read the file whilst it is still being written..
		# ... however file locking in python seems incomplete/non-portable ?
		if os.path.exists(self.output_file):
			bpy.ops.ef.msg(msg_text='Updating RenderResult')
			lay = result.layers[0]
			# TODO: use the framebuffer direct from pylux when Blender's API supports it
			lay.load_from_file(self.output_file)
		else:
			err_msg = 'ERROR: Could not load render result from %s' % self.output_file
			LuxLog(err_msg)
			bpy.ops.ef.msg(msg_type='ERROR', msg_text=err_msg)
		self.end_result(result)
	
	def render(self, context):
		'''
		context: bpy.types.scene
		
		Export the given scene to LuxRender.
		Choose from one of several methods depending on what needs to be rendered.
		
		Returns None
		'''
		
		if context.name == 'preview':
			export_result = self.render_preview(context)
		else:
			export_result = self.render_scene(context)
			
		if export_result == False:
			return
		
		self.render_start(context)
		
	def render_preview(self, scene):
		raise NotImplementedError()
	
	def render_scene(self, scene):
		
		output_dir = ''
		if scene.luxrender_engine.export_type == 'INT' and not scene.luxrender_engine.write_files:
			api_type = 'API'
			write_files = scene.luxrender_engine.write_files
		elif scene.luxrender_engine.export_type == 'LFC':
			api_type = 'LUXFIRE_CLIENT'
			write_files = False
		else:
			api_type = 'FILE'
			write_files = True
			if os.path.isdir(scene.render.filepath):
				output_dir = scene.render.filepath
			else:
				output_dir = os.path.dirname(scene.render.filepath)
		
		output_filename = efutil.scene_filename() + '.%s.%05i' % (scene.name, scene.frame_current)
		export_result = bpy.ops.export.luxrender(
			directory = output_dir,
			filename = output_filename,
			
			api_type = api_type,			# Set export target
			write_files = write_files,		# Use file write decision from above
			write_all_files = False,		# Use UI file write settings
		)
		
		if 'CANCELLED' in export_result:
			return False
		
		if api_type == 'FILE':
			self.output_file = efutil.path_relative_to_export(
				os.path.join(output_dir, output_filename) + '.png'
			)
		else:
			self.output_file = efutil.path_relative_to_export(efutil.export_path) + '.png'
		
		return True
	
	def render_start(self, scene):
		self.LuxManager = LM.ActiveManager
		
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
				self.LuxManager.stats_thread.LocalStorage['lux_context'] = ctx
				self.LuxManager.fb_thread.LocalStorage['lux_context'] = ctx
		elif worldEnd:
			#print('calling pylux.context.worldEnd() (2)')
			self.LuxManager.lux_context.worldEnd()
		
		# Begin rendering
		if start_rendering:
			bpy.ops.ef.msg(msg_text='Starting LuxRender')
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
					LuxLog('LuxRender not found at path: %s' % luxrender_path)
					return False
				
				try:
					for k,v in config_updates.items():
						efutil.write_config_value('luxrender', 'defaults', k, v)
				except Exception as err:
					LuxLog('Saving LuxRender config failed: %s' % err)
				
				fn = self.LuxManager.lux_context.file_names[0]
				LuxLog('Launching LuxRender with scene file "%s"' % fn)
				# TODO: add support for luxrender command line options
				subprocess.Popen([luxrender_path + ' "%s"'%fn], shell=True)
		
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

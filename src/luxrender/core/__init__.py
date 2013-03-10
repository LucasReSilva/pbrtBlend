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
import bpy, bl_ui

# Framework libs
from extensions_framework import util as efutil

# Exporter libs
from .. import LuxRenderAddon
from ..export import get_output_filename
from ..export.scene import SceneExporter
from ..outputs import LuxManager, LuxFilmDisplay
from ..outputs import LuxLog
from ..outputs.pure_api import LUXRENDER_VERSION

# Exporter Property Groups need to be imported to ensure initialisation
from ..properties import (
	accelerator, camera, engine, filter, integrator, ior_data, lamp, lampspectrum_data,
	material, mesh, object as prop_object, rendermode, sampler, texture, world
)

# Exporter Interface Panels need to be imported to ensure initialisation
from ..ui import (
	render_panels, camera, image, lamps, mesh, object as ui_object, world
)

from ..ui.materials import (
	main as mat_main, compositing, carpaint, cloth, glass, glass2, roughglass, glossytranslucent,
	glossycoating, glossy, layered, matte, mattetranslucent, metal, metal2, mirror, mix as mat_mix, null,
	scatter, shinymetal, velvet
)

from ..ui.textures import (
	main as tex_main, add, band, blender, bilerp, blackbody, brick, cauchy, constant, colordepth,
	checkerboard, dots, equalenergy, fbm, fresnelcolor, fresnelname, gaussian, harlequin, imagemap, imagesampling, normalmap,
	lampspectrum, luxpop, marble, mix as tex_mix, multimix, sellmeier, scale, subtract, sopra, uv,
	uvmask, windy, wrinkled, mapping, tabulateddata, transform
)

# Exporter Operators need to be imported to ensure initialisation
from .. import operators
from ..operators import lrmdb

def _register_elm(elm, required=False):
	try:
		elm.COMPAT_ENGINES.add('LUXRENDER_RENDER')
	except:
		if required:
			LuxLog('Failed to add LuxRender to ' + elm.__name__)

# Add standard Blender Interface elements
_register_elm(bl_ui.properties_render.RENDER_PT_render, required=True)
_register_elm(bl_ui.properties_render.RENDER_PT_dimensions, required=True)
_register_elm(bl_ui.properties_render.RENDER_PT_output, required=True)
_register_elm(bl_ui.properties_render.RENDER_PT_stamp)

_register_elm(bl_ui.properties_scene.SCENE_PT_scene, required=True)
_register_elm(bl_ui.properties_scene.SCENE_PT_audio)
_register_elm(bl_ui.properties_scene.SCENE_PT_physics) #This is the gravity panel
_register_elm(bl_ui.properties_scene.SCENE_PT_keying_sets)
_register_elm(bl_ui.properties_scene.SCENE_PT_keying_set_paths)
_register_elm(bl_ui.properties_scene.SCENE_PT_unit)
_register_elm(bl_ui.properties_scene.SCENE_PT_color_management)

if bpy.app.version > (2, 65, 8):
	_register_elm(bl_ui.properties_scene.SCENE_PT_rigid_body_world)

_register_elm(bl_ui.properties_scene.SCENE_PT_custom_props)

_register_elm(bl_ui.properties_world.WORLD_PT_context_world, required=True)

_register_elm(bl_ui.properties_material.MATERIAL_PT_preview)
_register_elm(bl_ui.properties_texture.TEXTURE_PT_preview)

_register_elm(bl_ui.properties_data_lamp.DATA_PT_context_lamp)

### Some additions to Blender panels for better allocation in context
### use this example for such overrides

# Add a hint to differentiate blender output and lux output
def lux_output_hints(self, context):
	if context.scene.render.engine == 'LUXRENDER_RENDER':
	
		pipe_mode = (context.scene.luxrender_engine.export_type == 'INT' and context.scene.luxrender_engine.write_files == False) #In this mode, we don't use use the regular interval write

		if not (pipe_mode): #in this case, none of these buttons do anything, so don't even bother drawing the label
			col = self.layout.column()
			col.label("LuxRender Output Formats")
		row = self.layout.row()
		if not pipe_mode:
			row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_png", text="PNG")
			if context.scene.camera.data.luxrender_camera.luxrender_film.write_png:
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_png_16bit", text="Use 16bit PNG")
			row = self.layout.row()
			row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_tga", text="TARGA")
			row = self.layout.row()
			row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr", text="OpenEXR")
			if context.scene.camera.data.luxrender_camera.luxrender_film.write_exr:
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr_applyimaging", text="Tonemap EXR")
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr_halftype", text="Use 16bit EXR")
				row = self.layout.row()
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr_compressiontype", text="EXR Compression")
			if context.scene.camera.data.luxrender_camera.luxrender_film.write_tga or context.scene.camera.data.luxrender_camera.luxrender_film.write_exr:
				row = self.layout.row()
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_zbuf", text="Enable Z-Buffer")
				if context.scene.camera.data.luxrender_camera.luxrender_film.write_zbuf:
					row = self.layout.row()
					row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "zbuf_normalization", text="Z-Buffer Normalization")
			row = self.layout.row()
			row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_flm", text="Write FLM")
			if context.scene.camera.data.luxrender_camera.luxrender_film.write_flm:
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "restart_flm", text="Restart FLM")
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_flm_direct", text="Write FLM Directly")
		row = self.layout.row()
	
		if not context.scene.luxrender_engine.integratedimaging or context.scene.luxrender_engine.export_type == 'EXT':
			row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "output_alpha", text="Alpha Channel") # Alpha and coupled premul option for all modes but integrated imaging
		else:
			row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "output_alpha", text="Transparent Background") # Integrated imaging always with premul named according Blender usage
				
		if (context.scene.camera.data.luxrender_camera.luxrender_film.output_alpha):
			if not context.scene.luxrender_engine.integratedimaging or context.scene.luxrender_engine.export_type == 'EXT': # Premul only availyble for non integrated imaging
				row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "premultiply_alpha", text="Premultiply Alpha")
		

_register_elm(bl_ui.properties_render.RENDER_PT_output.append(lux_output_hints))

# Add view buttons for viewcontrol to preview panels
def lux_use_alternate_matview(self, context):

	if context.scene.render.engine == 'LUXRENDER_RENDER':
		row = self.layout.row()
		row.prop(context.scene.luxrender_world, "preview_object_size", text="Size")
		row.prop(context.material.luxrender_material, "preview_zoom", text="Zoom")
		if context.material.preview_render_type == 'FLAT':
			row.prop(context.material.luxrender_material, "mat_preview_flip_xz", text="Flip XZ")

_register_elm(bl_ui.properties_material.MATERIAL_PT_preview.append(lux_use_alternate_matview))

def lux_use_alternate_texview(self, context):

	if context.scene.render.engine == 'LUXRENDER_RENDER':
		row = self.layout.row()
		row.prop(context.scene.luxrender_world, "preview_object_size", text="Size")
		row.prop(context.material.luxrender_material, "preview_zoom", text="Zoom")
		if context.material.preview_render_type == 'FLAT':
			row.prop(context.material.luxrender_material, "mat_preview_flip_xz", text="Flip XZ")

_register_elm(bl_ui.properties_texture.TEXTURE_PT_preview.append(lux_use_alternate_texview))

# Add use_clipping button to lens panel
def lux_use_clipping(self, context):

	if context.scene.render.engine == 'LUXRENDER_RENDER':

		self.layout.split().column().prop(context.camera.luxrender_camera, "use_clipping", text="Export Clipping")

_register_elm(bl_ui.properties_data_camera.DATA_PT_lens.append(lux_use_clipping))

# Add lux dof elements to blender dof panel
def lux_use_dof(self, context):

	if context.scene.render.engine == 'LUXRENDER_RENDER':
		row = self.layout.row()

		row.prop(context.camera.luxrender_camera, "use_dof", text="Use Depth of Field")
		if context.camera.luxrender_camera.use_dof == True:
			row.prop(context.camera.luxrender_camera, "autofocus", text="Auto Focus")

			row = self.layout.row()
			row.prop(context.camera.luxrender_camera, "blades", text="Blades")

			row = self.layout.row(align=True)
			row.prop(context.camera.luxrender_camera, "distribution", text="Distribution")
			row.prop(context.camera.luxrender_camera, "power", text="Power")

_register_elm(bl_ui.properties_data_camera.DATA_PT_camera_dof.append(lux_use_dof))

#Add options by render image/anim buttons
def render_start_options(self, context):

	if context.scene.render.engine == 'LUXRENDER_RENDER':
		col = self.layout.column()
		row = self.layout.row()
		
		col.prop(context.scene.luxrender_engine, "export_type", text="Export type")
		if context.scene.luxrender_engine.export_type == 'EXT':
			col.prop(context.scene.luxrender_engine, "binary_name", text="Render using")
			col.prop(context.scene.luxrender_engine, "install_path", text="Path to LuxRender Installation")
		if context.scene.luxrender_engine.export_type == 'INT':
			row.prop(context.scene.luxrender_engine, "write_files", text="Write to Disk")
			row.prop(context.scene.luxrender_engine, "integratedimaging", text="Integrated Imaging")

_register_elm(bl_ui.properties_render.RENDER_PT_render.append(render_start_options))

@classmethod
def blender_texture_poll(cls, context):
	tex = context.texture
	show = tex and \
		   ((tex.type == cls.tex_type and not tex.use_nodes) and \
		   (context.scene.render.engine in cls.COMPAT_ENGINES))
	
	if context.scene.render.engine == 'LUXRENDER_RENDER':
		show = show and tex.luxrender_texture.type == 'BLENDER'
	
	return show

_register_elm(bl_ui.properties_texture.TEXTURE_PT_context_texture)
blender_texture_ui_list = [
	bl_ui.properties_texture.TEXTURE_PT_blend,
	bl_ui.properties_texture.TEXTURE_PT_clouds,
	bl_ui.properties_texture.TEXTURE_PT_distortednoise,
	bl_ui.properties_texture.TEXTURE_PT_image,
	bl_ui.properties_texture.TEXTURE_PT_magic,
	bl_ui.properties_texture.TEXTURE_PT_marble,
	bl_ui.properties_texture.TEXTURE_PT_musgrave,
	bl_ui.properties_texture.TEXTURE_PT_stucci,
	bl_ui.properties_texture.TEXTURE_PT_voronoi,
	bl_ui.properties_texture.TEXTURE_PT_wood,
	bl_ui.properties_texture.TEXTURE_PT_ocean,
]
for blender_texture_ui in blender_texture_ui_list:
	_register_elm(blender_texture_ui)
	blender_texture_ui.poll = blender_texture_poll

# compatible() copied from blender repository (netrender)
def compatible(mod):
	mod = getattr(bl_ui, mod)
	for subclass in mod.__dict__.values():
		_register_elm(subclass)
	del mod

compatible("properties_data_mesh")
compatible("properties_data_camera")
compatible("properties_particle")
compatible("properties_data_speaker")


@LuxRenderAddon.addon_register_class
class RENDERENGINE_luxrender(bpy.types.RenderEngine):
	'''
	LuxRender Engine Exporter/Integration class
	'''
	
	bl_idname			= 'LUXRENDER_RENDER'
	bl_label			= 'LuxRender'
	bl_use_preview		= True
	
	render_lock = threading.Lock()
	
	def render(self, scene):
		'''
		scene:	bpy.types.Scene
		
		Export the given scene to LuxRender.
		Choose from one of several methods depending on what needs to be rendered.
		
		Returns None
		'''
		
		with RENDERENGINE_luxrender.render_lock:	# just render one thing at a time
			prev_cwd = os.getcwd()
			try:
				self.LuxManager				= None
				self.render_update_timer	= None
				self.output_dir				= efutil.temp_directory()
				self.output_file			= 'default.png'
				
				if scene is None:
					LuxLog('ERROR: Scene to render is not valid')
					return
				
				if scene.name == 'preview':
					self.render_preview(scene)
					return

				if bpy.app.version < (2, 63, 19 ):
					if scene.render.use_color_management == False:
						LuxLog('WARNING: Colour Management is switched off, render results may look too dark.')
				else:
					if scene.display_settings.display_device != "sRGB":
						LuxLog('WARNING: Colour Management not set to sRGB, render results may look too dark.')
				
				api_type, write_files = self.set_export_path(scene)
				
				os.chdir(efutil.export_path)
				
				is_animation = hasattr(self, 'is_animation') and self.is_animation
				make_queue = scene.luxrender_engine.export_type == 'EXT' and scene.luxrender_engine.binary_name == 'luxrender' and write_files
				
				if is_animation and make_queue:
					queue_file = efutil.export_path + '%s.%s.lxq' % (efutil.scene_filename(), bpy.path.clean_name(scene.name))
					
					# Open/reset a queue file
					if scene.frame_current == scene.frame_start:
						open(queue_file, 'w').close()
					
					if hasattr(self, 'update_progress'):
						fr = scene.frame_end - scene.frame_start
						fo = scene.frame_current - scene.frame_start
						self.update_progress(fo/fr)
				
				exported_file = self.export_scene(scene)
				if exported_file == False:
					return	# Export frame failed, abort rendering
				
				if is_animation and make_queue:
					self.LuxManager = LuxManager.GetActive()
					self.LuxManager.lux_context.worldEnd()
					with open(queue_file, 'a') as qf:
						qf.write("%s\n" % exported_file)
					
					if scene.frame_current == scene.frame_end:
						# run the queue
						self.render_queue(scene, queue_file)
				else:
					self.render_start(scene)
			
			except Exception as err:
				LuxLog('%s'%err)
				self.report({'ERROR'}, '%s'%err)
			
			os.chdir(prev_cwd)
	
	def render_preview(self, scene):
		if sys.platform == 'darwin':
			self.output_dir = efutil.filesystem_path( bpy.app.tempdir )
		else:
			self.output_dir = efutil.temp_directory()
		
		if self.output_dir[-1] != '/':
			self.output_dir += '/'
		
		efutil.export_path = self.output_dir
		
		from ..outputs.pure_api import PYLUX_AVAILABLE
		if not PYLUX_AVAILABLE:
			self.bl_use_preview = False
			LuxLog('ERROR: Material previews require pylux')
			return
		
		from ..export import materials as export_materials
		
		# Iterate through the preview scene, finding objects with materials attached
		objects_mats = {}
		for obj in [ob for ob in scene.objects if ob.is_visible(scene) and not ob.hide_render]:
			for mat in export_materials.get_instance_materials(obj):
				if mat is not None:
					if not obj.name in objects_mats.keys(): objects_mats[obj] = []
					objects_mats[obj].append(mat)
		
		PREVIEW_TYPE = None		# 'MATERIAL' or 'TEXTURE'
		
		# find objects that are likely to be the preview objects
		preview_objects = [o for o in objects_mats.keys() if o.name.startswith('preview')]
		if len(preview_objects) > 0:
			PREVIEW_TYPE = 'MATERIAL'
		else:
			preview_objects = [o for o in objects_mats.keys() if o.name.startswith('texture')]
			if len(preview_objects) > 0:
				PREVIEW_TYPE = 'TEXTURE'
		
		if PREVIEW_TYPE == None:
			return
		
		# TODO: scene setup based on PREVIEW_TYPE
		
		# find the materials attached to the likely preview object
		likely_materials = objects_mats[preview_objects[0]]
		if len(likely_materials) < 1:
			print('no preview materials')
			return
		
		pm = likely_materials[0]
		pt = None
		LuxLog('Rendering material preview: %s' % pm.name)

		if PREVIEW_TYPE == 'TEXTURE':
			pt = pm.active_texture		
		
		LM = LuxManager(
			scene.name,
			api_type = 'API',
		)
		LuxManager.SetCurrentScene(scene)
		LuxManager.SetActive(LM)
		
		file_based_preview = False
		
		if file_based_preview:
			# Dump to file in temp dir for debugging
			from ..outputs.file_api import Custom_Context as lxs_writer
			preview_context = lxs_writer(scene.name)
			preview_context.set_filename(scene, 'luxblend25-preview', LXV=False)
			LM.lux_context = preview_context
		else:
			preview_context = LM.lux_context
			preview_context.logVerbosity('quiet')
		
		try:
			export_materials.ExportedMaterials.clear()
			export_materials.ExportedTextures.clear()
			
			from ..export import preview_scene
			xres, yres = scene.camera.data.luxrender_camera.luxrender_film.resolution(scene)
			
			# Don't render the tiny images
			if xres <= 96:
				raise Exception('Skipping material thumbnail update, image too small (%ix%i)' % (xres,yres))
			
			preview_scene.preview_scene(scene, preview_context, obj=preview_objects[0], mat=pm, tex=pt)
			
			# render !
			preview_context.worldEnd()
			
			if file_based_preview:
				preview_context = preview_context.parse('luxblend25-preview.lxs', True)
				LM.lux_context = preview_context
			
			while not preview_context.statistics('sceneIsReady'):
				time.sleep(0.05)
			
			def is_finished(ctx):
				return ctx.getAttribute('film', 'enoughSamples')
			
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
				if self.test_break() or bpy.context.scene.render.engine != 'LUXRENDER_RENDER':
					raise Exception('Render interrupted')
				
				# progressively update the preview
				time.sleep(0.2) # safety-sleep
				
				if preview_context.getAttribute('renderer_statistics', 'samplesPerPixel') > 6:
					if PREVIEW_TYPE == 'TEXTURE':
						interruptible_sleep(0.8) # reduce update to every 1.0 sec until haltthreshold kills the render
					else:
						interruptible_sleep(1.8) # reduce update to every 2.0 sec until haltthreshold kills the render

				preview_context.updateStatisticsWindow()
				LuxLog('Updating preview (%ix%i - %s)' % (xres, yres, preview_context.getAttribute('renderer_statistics_formatted_short', '_recommended_string')))
				
				result = self.begin_result(0, 0, xres, yres)
				lay = result.layers[0]
				
				lay.rect  = preview_context.blenderCombinedDepthRects()[0]
				
				self.end_result(result, 0) if bpy.app.version > (2, 63, 17 ) else self.end_result(result) # cycles tiles adaption
		except Exception as exc:
			LuxLog('Preview aborted: %s' % exc)
		
		preview_context.exit()
		preview_context.wait()
		
		# cleanup() destroys the pylux Context
		preview_context.cleanup()
		
		LM.reset()
	
	def set_export_path(self, scene):
		# replace /tmp/ with the real %temp% folder on Windows
		# OSX also has a special temp location that we should use
		fp = scene.render.filepath
		output_path_split = list(os.path.split(fp))
		if sys.platform in ('win32', 'darwin') and output_path_split[0] == '/tmp':
			output_path_split[0] = efutil.temp_directory()
			fp = '/'.join(output_path_split)
		
		scene_path = efutil.filesystem_path( fp )
		
		if os.path.isdir(scene_path):
			self.output_dir = scene_path
		else:
			self.output_dir = os.path.dirname( scene_path )
		
		if self.output_dir[-1] not in ('/', '\\'):
			self.output_dir += '/'
		
		if scene.luxrender_engine.export_type == 'INT':
			write_files = scene.luxrender_engine.write_files
			if write_files:
				api_type = 'FILE'
			else:
				api_type = 'API'
				if sys.platform == 'darwin':
					self.output_dir = efutil.filesystem_path( bpy.app.tempdir )
				else:
					self.output_dir = efutil.temp_directory()
		
		else:
			api_type = 'FILE'
			write_files = True
		
		efutil.export_path = self.output_dir
		
		return api_type, write_files
	
	def export_scene(self, scene):
		api_type, write_files = self.set_export_path(scene)
		
		# Pre-allocate the LuxManager so that we can set up the network servers before export
		LM = LuxManager(
			scene.name,
			api_type = api_type,
		)
		LuxManager.SetActive(LM)
		
		if scene.luxrender_engine.export_type == 'INT':
			# Set up networking before export so that we get better server usage
			if scene.luxrender_networking.use_network_servers and scene.luxrender_networking.servers != '':
				LM.lux_context.setNetworkServerUpdateInterval( scene.luxrender_networking.serverinterval )
				for server in scene.luxrender_networking.servers.split(','):
					LM.lux_context.addServer(server.strip())
		
		output_filename = get_output_filename(scene)
		
		scene_exporter = SceneExporter()
		scene_exporter.properties.directory = self.output_dir
		scene_exporter.properties.filename = output_filename
		scene_exporter.properties.api_type = api_type			# Set export target
		scene_exporter.properties.write_files = write_files		# Use file write decision from above
		scene_exporter.properties.write_all_files = False		# Use UI file write settings
		scene_exporter.set_scene(scene)
		
		export_result = scene_exporter.export()
		
		if 'CANCELLED' in export_result:
			return False
		
		# Look for an output image to load
		if scene.camera.data.luxrender_camera.luxrender_film.write_png:
			self.output_file = efutil.path_relative_to_export(
				'%s/%s.png' % (self.output_dir, output_filename)
			)
		elif scene.camera.data.luxrender_camera.luxrender_film.write_tga:
			self.output_file = efutil.path_relative_to_export(
				'%s/%s.tga' % (self.output_dir, output_filename)
			)
		elif scene.camera.data.luxrender_camera.luxrender_film.write_exr:
			self.output_file = efutil.path_relative_to_export(
				'%s/%s.exr' % (self.output_dir, output_filename)
			)
		
		return "%s.lxs" % output_filename
	
	def rendering_behaviour(self, scene):
		internal	= (scene.luxrender_engine.export_type in ['INT'])
		write_files	= scene.luxrender_engine.write_files and (scene.luxrender_engine.export_type in ['INT', 'EXT'])
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
		
		return internal, start_rendering, parse, worldEnd
	
	def render_queue(self, scene, queue_file):
		internal, start_rendering, parse, worldEnd = self.rendering_behaviour(scene)
		
		if start_rendering:
			cmd_args = self.get_process_args(scene, start_rendering)
			
			cmd_args.extend(['-L', queue_file])
			
			LuxLog('Launching Queue: %s' % cmd_args)
			# LuxLog(' in %s' % self.outout_dir)
			luxrender_process = subprocess.Popen(cmd_args, cwd=self.output_dir)
	
	def get_process_args(self, scene, start_rendering):
		config_updates = {
			'auto_start': start_rendering
		}
		
		luxrender_path = efutil.filesystem_path( scene.luxrender_engine.install_path )
		if luxrender_path[-1] != '/':
			luxrender_path += '/'
		
		if os.path.isdir(luxrender_path) and os.path.exists(luxrender_path):
			config_updates['install_path'] = luxrender_path
		
		if sys.platform == 'darwin':
			luxrender_path += 'LuxRender.app/Contents/MacOS/%s' % scene.luxrender_engine.binary_name # Get binary from OSX bundle
			if not os.path.exists(luxrender_path):
				LuxLog('LuxRender not found at path: %s' % luxrender_path, ', trying default LuxRender location')
				luxrender_path = '/Applications/LuxRender/LuxRender.app/Contents/MacOS/%s' % scene.luxrender_engine.binary_name # try fallback to default installation path

		elif sys.platform == 'win32':
			luxrender_path += '%s.exe' % scene.luxrender_engine.binary_name
		else:
			luxrender_path += scene.luxrender_engine.binary_name
		
		if not os.path.exists(luxrender_path):
			raise Exception('LuxRender not found at path: %s' % luxrender_path)
		
		cmd_args = [luxrender_path]
		
		# set log verbosity
		if scene.luxrender_engine.log_verbosity != 'default':
			cmd_args.append('--' + scene.luxrender_engine.log_verbosity)
		
		if scene.luxrender_engine.binary_name == 'luxrender':
			# Copy the GUI log to the console
			cmd_args.append('--logconsole')
		
		# Set number of threads for external processes
		if not scene.luxrender_engine.threads_auto:
			cmd_args.append('--threads=%i' % scene.luxrender_engine.threads)
			
		#Set fixed seeds, if enabled
		if scene.luxrender_engine.fixed_seed:
			cmd_args.append('--fixedseed')
		
		if scene.luxrender_networking.use_network_servers and scene.luxrender_networking.servers != '':
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
		
		return cmd_args
	
	def render_start(self, scene):
		self.LuxManager = LuxManager.GetActive()
		
		# Remove previous rendering, to prevent loading old data
		# if the update timer fires before the image is written
		if os.path.exists(self.output_file):
			os.remove(self.output_file)
		
		internal, start_rendering, parse, worldEnd = self.rendering_behaviour(scene)
		
		if self.LuxManager.lux_context.API_TYPE == 'FILE':
			fn = self.LuxManager.lux_context.file_names[0]
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
			self.LuxManager.lux_context.worldEnd()
		
		# Begin rendering
		if start_rendering:
			LuxLog('Starting LuxRender')
			if internal:
				
				self.LuxManager.lux_context.logVerbosity(scene.luxrender_engine.log_verbosity)
				
				self.update_stats('', 'LuxRender: Building %s' % scene.luxrender_accelerator.accelerator)
				self.LuxManager.start()
				
				self.LuxManager.fb_thread.LocalStorage['integratedimaging'] = scene.luxrender_engine.integratedimaging
				
				# Update the image from disk only as often as it is written
				self.LuxManager.fb_thread.set_kick_period( scene.camera.data.luxrender_camera.luxrender_film.internal_updateinterval )
				
				# Start the stats and framebuffer threads and add additional threads to Lux renderer
				self.LuxManager.start_worker_threads(self)
				
				if scene.luxrender_engine.threads_auto:
					try:
						thread_count = multiprocessing.cpu_count()
					except:
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
				cmd_args = self.get_process_args(scene, start_rendering)
				
				cmd_args.append(fn.replace('//','/'))
				
				LuxLog('Launching: %s' % cmd_args)
				# LuxLog(' in %s' % self.outout_dir)
				luxrender_process = subprocess.Popen(cmd_args, cwd=self.output_dir)
				
				if not (scene.luxrender_engine.binary_name == 'luxrender' and not scene.luxrender_engine.monitor_external):
					framebuffer_thread = LuxFilmDisplay({
						'resolution': scene.camera.data.luxrender_camera.luxrender_film.resolution(scene),
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
		
		LC = self.LuxManager.lux_context
		
		self.update_stats('', 'LuxRender: Rendering %s' % self.LuxManager.stats_thread.stats_string)
		
		if hasattr(self, 'update_progress') and LC.getAttribute('renderer_statistics', 'percentComplete') > 0:
			prg = LC.getAttribute('renderer_statistics', 'percentComplete') / 100.0
			self.update_progress(prg)
		
		if self.test_break() or \
			LC.statistics('filmIsReady') == 1.0 or \
			LC.statistics('terminated') == 1.0 or \
			LC.getAttribute('film', 'enoughSamples') == True:
			self.LuxManager.reset()
			self.update_stats('', '')

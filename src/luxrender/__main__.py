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
# System libs
import os, time

# Framework libs
from ef.ef import ef
from ef.engine import engine_base

# Exporter libs
from luxrender.module import LuxManager as LM
import luxrender.ui.materials
import luxrender.ui.textures
import luxrender.ui.render_panels
import luxrender.nodes

# Add standard Blender Interface elements
import properties_render
properties_render.RENDER_PT_render.COMPAT_ENGINES.add('luxrender')
properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('luxrender')
# Don't need file output panel for API
#properties_render.RENDER_PT_output.COMPAT_ENGINES.add('luxrender')
del properties_render

import properties_material
properties_material.MATERIAL_PT_context_material.COMPAT_ENGINES.add('luxrender')
del properties_material

#import properties_texture
#properties_texture.TEXTURE_PT_context_texture.COMPAT_ENGINES.add('luxrender')
#del properties_texture

class luxrender(engine_base):
	bl_label = 'LuxRender'
	
	LuxManager = LM()
		
	interfaces = [
		luxrender.ui.render_panels.engine,
		luxrender.ui.render_panels.sampler,
		luxrender.ui.render_panels.integrator,
		luxrender.ui.render_panels.volume,
		luxrender.ui.render_panels.filter,
		luxrender.ui.render_panels.accelerator,
		
		luxrender.ui.materials.material_editor,
		luxrender.ui.textures.texture_editor,
		
		#luxrender.nodes.test_node
	]
	
	def update_framebuffer(self, xres, yres, fb):
		'''
		this will be called by the LuxFilmDisplay thread started by LuxManager
		
		TODO: perhaps this class itself is a threaded timer ?
		'''
		
		result = self.begin_result(0,0,xres,yres)
		# read default png file
		if os.path.exists('luxout.png'):
			lay = result.layers[0]
			lay.load_from_file('luxout.png')
			#lay.rect = fb
		self.end_result(result)
	
	
	def render(self, scene):
		self.LuxManager.reset()
		self.update_stats('', 'LuxRender: Parsing Scene')
		
		l = self.LuxManager.lux_module
		
		# Set up render engine parameters
		l.sampler(            *scene.luxrender_sampler.api_output()       )
		l.accelerator(        *scene.luxrender_accelerator.api_output()   )
		l.surfaceIntegrator(  *scene.luxrender_integrator.api_output()    )
		l.volumeIntegrator(   *scene.luxrender_volume.api_output()        )
		l.pixelFilter(        *scene.luxrender_filter.api_output()        )
		
		
		# BEGIN TEST CODE
		# In future use some classes to gather parameters into dicts for API calls please ;)
		matrix = scene.camera.matrix
		pos = matrix[3]
		forwards = -matrix[2]
		target = pos + forwards
		up = matrix[1]
		l.lookAt(pos[0], pos[1], pos[2], target[0], target[1], target[2], up[0], up[1], up[2])
		cs = {
			'fov': scene.camera.data.angle,
		}
		l.camera('perspective', list(cs.items()))
		
		fs = {
			# Set resolution
			'xresolution':   int(scene.render.resolution_x * scene.render.resolution_percentage / 100.0),
			'yresolution':   int(scene.render.resolution_y * scene.render.resolution_percentage / 100.0),
			
			# write only default png file
			'write_exr':         False,
			'write_png':         True,
			'write_tga':         False,
			'write_resume_flm':  False,
			'displayinterval':   5,
			'writeinterval':     8,
		}
		l.film('fleximage', list(fs.items()))
		l.worldBegin()
		
		es = {
			'sundir': (0,0,1)
		}
		l.lightSource('sunsky', list(es.items()))
		# END TEST CODE
		
		
		
		# reset output image file and begin rendering
		if os.path.exists('luxout.png'):
			os.remove('luxout.png')
			
		self.LuxManager.start(self)
		self.update_stats('', 'LuxRender: Rendering warmup')
		
		# TODO: replace time.sleep with a threading event
		while self.LuxManager.started:
			time.sleep(1)
			self.update_stats('', 'LuxRender: Rendering %s' % self.LuxManager.stats_thread.stats_string)
			if self.test_break():
				self.LuxManager.reset()
				self.update_stats('', '')

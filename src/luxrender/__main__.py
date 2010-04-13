# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Genscher
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
import os, time, threading

# Framework libs
from ef.ef import ef
from ef.engine import engine_base

# Exporter libs
from luxrender.module import LuxManager as LM
import luxrender.ui.materials
import luxrender.ui.textures
import luxrender.ui.render_panels
#import luxrender.nodes

import luxrender.module.export_geometry     as export_geometry
import luxrender.module.export_camerafilm   as export_camerafilm
import luxrender.module.export_lights       as export_lights
from luxrender.module.file_api import Files


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

import properties_data_lamp
properties_data_lamp.DATA_PT_context_lamp.COMPAT_ENGINES.add('luxrender')
properties_data_lamp.DATA_PT_lamp.COMPAT_ENGINES.add('luxrender')
properties_data_lamp.DATA_PT_sunsky.COMPAT_ENGINES.add('luxrender')
properties_data_lamp.DATA_PT_spot.COMPAT_ENGINES.add('luxrender')
del properties_data_lamp

#import properties_texture
#properties_texture.TEXTURE_PT_context_texture.COMPAT_ENGINES.add('luxrender')
#del properties_texture

class luxrender(engine_base):
    bl_label = 'LuxRender'
    
    LuxManager = None
        
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
    
    render_update_timer = None
    
    def update_framebuffer(self, xres, yres, fb):
        '''
        this will be called by the LuxFilmDisplay thread started by LuxManager
        
        TODO: perhaps this class itself is a threaded timer ?
        '''
        
        #print('fb len: %i' % len(fb))
        #print('fb max: %i' % max(fb))
        #print('fb min: %i' % min(fb))
        
        result = self.begin_result(0,0,xres,yres)
        # read default png file
        if os.path.exists('default.png'):
            lay = result.layers[0]
            lay.load_from_file('default.png')
        self.end_result(result)
    
    def render(self, scene):
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
            'Main render',
            api_type = scene.luxrender_engine.api_type,
            threads = threads
        )
        
        l = self.LuxManager.lux_context
        l.set_filename('default')
        
        self.update_stats('', 'LuxRender: Parsing Scene')
        
        # Set up render engine parameters
        l.sampler(            *scene.luxrender_sampler.api_output()       )
        l.accelerator(        *scene.luxrender_accelerator.api_output()   )
        l.surfaceIntegrator(  *scene.luxrender_integrator.api_output()    )
        l.volumeIntegrator(   *scene.luxrender_volume.api_output()        )
        l.pixelFilter(        *scene.luxrender_filter.api_output()        )
        
        # Set up camera, view and film
        l.lookAt( *export_camerafilm.lookAt(scene) )
        l.camera( *export_camerafilm.camera(scene) )
        l.film(   *export_camerafilm.film(scene)   )
        
        
        l.worldBegin()
        # Light source iteration and export goes here.
        export_lights.lights(l, scene)
        
        # Materials iteration and export goes here.
        
        # Geometry iteration and export goes here.
        export_geometry.write_lxo(l, scene)
        
        # reset output image file and begin rendering
        if os.path.exists('default.png'):
            os.remove('default.png')
            
        self.LuxManager.start(self)
        self.update_stats('', 'LuxRender: Rendering warmup')
        
        while self.LuxManager.started:
            self.render_update_timer = threading.Timer(1, self.stats_timer)
            self.render_update_timer.start()
            if self.render_update_timer.isAlive(): self.render_update_timer.join()
    
    def stats_timer(self):
        self.update_stats('', 'LuxRender: Rendering %s' % self.LuxManager.stats_thread.stats_string)
        if self.test_break():
            self.LuxManager.reset()
            self.update_stats('', '')

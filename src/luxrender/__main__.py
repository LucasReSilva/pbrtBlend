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
import os, time, threading

# Framework libs
from ef.ef import ef
from ef.engine import engine_base

# Exporter libs
from luxrender.module import LuxManager as LM
from luxrender.module import LuxLog
import luxrender.ui.materials
import luxrender.ui.textures
import luxrender.ui.render_panels
import luxrender.ui.camera
import luxrender.ui.lamps
import luxrender.ui.meshes
#import luxrender.nodes

import luxrender.export.geometry    as export_geometry
import luxrender.export.film        as export_film
import luxrender.export.lights      as export_lights
from luxrender.module.file_api import Files


# Add standard Blender Interface elements
import properties_render
properties_render.RENDER_PT_render.COMPAT_ENGINES.add('luxrender')
properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('luxrender')
properties_render.RENDER_PT_output.COMPAT_ENGINES.add('luxrender')
del properties_render

import properties_material
properties_material.MATERIAL_PT_context_material.COMPAT_ENGINES.add('luxrender')
del properties_material

import properties_data_lamp
properties_data_lamp.DATA_PT_context_lamp.COMPAT_ENGINES.add('luxrender')
# properties_data_lamp.DATA_PT_area.COMPAT_ENGINES.add('luxrender')
del properties_data_lamp

#import properties_texture
#properties_texture.TEXTURE_PT_context_texture.COMPAT_ENGINES.add('luxrender')
#del properties_texture

# compatible() copied from blender repository (netrender)
def compatible(module):
    module = __import__(module)
    for subclass in module.__dict__.values():
        try:		subclass.COMPAT_ENGINES.add('luxrender')
        except:	pass
    del module

compatible("properties_data_mesh")
compatible("properties_data_camera")
compatible("properties_texture")

class luxrender(engine_base):
    '''
    LuxRender Engine Exporter/Integration class
    '''
    
    bl_label = 'LuxRender'
    
    LuxManager = None
    render_update_timer = None
    output_file = 'default.png'
    
    # This member is read by the ExporterFramework to set up the UI panels
    interfaces = [
        luxrender.ui.render_panels.engine,
        luxrender.ui.render_panels.sampler,
        luxrender.ui.render_panels.integrator,
        luxrender.ui.render_panels.volume,
        luxrender.ui.render_panels.filter,
        luxrender.ui.render_panels.accelerator,

        # custom object data panels
        luxrender.ui.lamps.lamps,
        luxrender.ui.meshes.meshes,
        
        luxrender.ui.camera.camera,
        luxrender.ui.camera.tonemapping,
        
        luxrender.ui.materials.material_editor,
        luxrender.ui.textures.texture_editor,
        
        #luxrender.nodes.test_node
    ]
    
    def update_framebuffer(self, xres, yres, fb):
        '''
        xres        int
        yres        int
        fb          list
        
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
        self.end_result(result)
    
    def render(self, scene):
        '''
        scene        bpy.types.scene
        
        Export the given scene to LuxRender
        
        Returns None
        '''
        
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
            'Main render',
            api_type = scene.luxrender_engine.api_type,
            threads = threads
        )
        LM.SetActive(self.LuxManager)
        
        l = self.LuxManager.lux_context
        
        if scene.luxrender_engine.api_type == 'FILE':
            # TODO: insert an output path here ?
            # TODO: only if the user selects a 'keep files' option
            l.set_filename('default')
        
        # BEGIN!
        self.update_stats('', 'LuxRender: Parsing Scene')
        
        # Set up render engine parameters
        l.sampler(            *scene.luxrender_sampler.api_output()       )
        l.accelerator(        *scene.luxrender_accelerator.api_output()   )
        l.surfaceIntegrator(  *scene.luxrender_integrator.api_output()    )
        l.volumeIntegrator(   *scene.luxrender_volume.api_output()        )
        l.pixelFilter(        *scene.luxrender_filter.api_output()        )
        
        # Set up camera, view and film
        l.lookAt( *export_film.lookAt(scene) )
        l.camera( *scene.camera.data.luxrender_camera.api_output(scene) )
        l.film(   *export_film.film(scene)   )
        
        
        l.worldBegin()
        # Light source iteration and export goes here.
        if export_lights.lights(l, scene) == False:
            LuxLog('Error - No lights in scene.')
            return
        
        # Materials iteration and export goes here.
        
        # Geometry iteration and export goes here.
        export_geometry.write_lxo(self, l, scene)
        
        # TODO: this will be removed when direct framebuffer
        # access is implemented in Blender
        if os.path.exists(self.output_file):
            # reset output image file and
            os.remove(self.output_file)
            
        # Begin rendering
        self.LuxManager.start(self)
        self.update_stats('', 'LuxRender: Rendering warmup')
        
        while self.LuxManager.started:
            self.render_update_timer = threading.Timer(1, self.stats_timer)
            self.render_update_timer.start()
            if self.render_update_timer.isAlive(): self.render_update_timer.join()
            
        # TODO: tidy up scene files and output file ?
    
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

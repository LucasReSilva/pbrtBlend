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
import array
import math
import mathutils

# Blender libs
import bpy, bgl, bl_ui

# Framework libs
from ..extensions_framework import util as efutil

# Exporter libs
from .. import LuxRenderAddon
from ..export import get_output_filename
from ..export.scene import SceneExporter
from ..outputs import LuxManager, LuxFilmDisplay
from ..outputs import LuxLog
from ..outputs.pure_api import LUXRENDER_VERSION
from ..outputs.luxcore_api import PYLUXCORE_AVAILABLE, UseLuxCore

# Exporter Property Groups need to be imported to ensure initialisation
from ..properties import (
    accelerator, camera, engine, filter, integrator, ior_data, lamp, lampspectrum_data,
    material, node_material, node_inputs, node_texture, node_fresnel, node_converter,
    mesh, object as prop_object, particles, rendermode, sampler, texture, world,
    luxcore_engine, luxcore_sampler, luxcore_material
)

# Exporter Interface Panels need to be imported to ensure initialisation
from ..ui import (
    render_panels, camera, image, lamps, mesh, node_editor, object as ui_object, particles, world
)

# Legacy material editor panels, node editor UI is initialized above
from ..ui.materials import (
    main as mat_main, compositing, carpaint, cloth, glass, glass2, roughglass, glossytranslucent,
    glossycoating, glossy, layered, matte, mattetranslucent, metal, metal2, mirror, mix as mat_mix, null,
    scatter, shinymetal, velvet
)

#Legacy texture editor panels
from ..ui.textures import (
    main as tex_main, abbe, add, band, blender, bilerp, blackbody, brick, cauchy, constant, colordepth,
    checkerboard, cloud, densitygrid, dots, equalenergy, exponential, fbm, fresnelcolor, fresnelname, gaussian,
    harlequin, hitpointcolor, hitpointalpha, hitpointgrey, imagemap, imagesampling, normalmap,
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
_register_elm(bl_ui.properties_scene.SCENE_PT_physics)  # This is the gravity panel
_register_elm(bl_ui.properties_scene.SCENE_PT_keying_sets)
_register_elm(bl_ui.properties_scene.SCENE_PT_keying_set_paths)
_register_elm(bl_ui.properties_scene.SCENE_PT_unit)
_register_elm(bl_ui.properties_scene.SCENE_PT_color_management)

_register_elm(bl_ui.properties_scene.SCENE_PT_rigid_body_world)
_register_elm(bl_ui.properties_scene.SCENE_PT_rigid_body_cache)
_register_elm(bl_ui.properties_scene.SCENE_PT_rigid_body_field_weights)

_register_elm(bl_ui.properties_scene.SCENE_PT_custom_props)

_register_elm(bl_ui.properties_world.WORLD_PT_context_world, required=True)

_register_elm(bl_ui.properties_material.MATERIAL_PT_preview)
_register_elm(bl_ui.properties_texture.TEXTURE_PT_preview)

_register_elm(bl_ui.properties_data_lamp.DATA_PT_context_lamp)


# Some additions to Blender panels for better allocation in context
# Use this example for such overrides
# Add output format flags to output panel
def lux_output_hints(self, context):
    if context.scene.render.engine == 'LUXRENDER_RENDER':

        # In this mode, we don't use use the regular interval write
        pipe_mode = (context.scene.luxrender_engine.export_type == 'INT' and
                     not context.scene.luxrender_engine.write_files)

        # in this case, none of these buttons do anything, so don't even bother drawing the label
        if not pipe_mode:
            col = self.layout.column()
            col.label("LuxRender Output Formats")
        row = self.layout.row()
        if not pipe_mode:
            row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_png", text="PNG")

            if context.scene.camera.data.luxrender_camera.luxrender_film.write_png:
                row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_png_16bit",
                         text="Use 16bit PNG")

            row = self.layout.row()
            row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_tga", text="TARGA")
            row = self.layout.row()
            row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr", text="OpenEXR")

            if context.scene.camera.data.luxrender_camera.luxrender_film.write_exr:
                row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr_applyimaging",
                         text="Tonemap EXR")
                row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr_halftype",
                         text="Use 16bit EXR")
                row = self.layout.row()
                row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_exr_compressiontype",
                         text="EXR Compression")

            if context.scene.camera.data.luxrender_camera.luxrender_film.write_tga or \
                    context.scene.camera.data.luxrender_camera.luxrender_film.write_exr:
                row = self.layout.row()
                row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_zbuf",
                         text="Enable Z-Buffer")

                if context.scene.camera.data.luxrender_camera.luxrender_film.write_zbuf:
                    row = self.layout.row()
                    row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "zbuf_normalization",
                             text="Z-Buffer Normalization")

            row = self.layout.row()
            row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_flm", text="Write FLM")

            if context.scene.camera.data.luxrender_camera.luxrender_film.write_flm:
                row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "restart_flm", text="Restart FLM")
                row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "write_flm_direct",
                         text="Write FLM Directly")
        row = self.layout.row()

        # Integrated imaging always with premul named according to Blender usage
        row.prop(context.scene.camera.data.luxrender_camera.luxrender_film, "output_alpha",
                 text="Transparent Background")


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
        if context.camera.luxrender_camera.use_dof:
            row.prop(context.camera.luxrender_camera, "autofocus", text="Auto Focus")

            row = self.layout.row()
            row.prop(context.camera.luxrender_camera, "blades", text="Blades")

            row = self.layout.row(align=True)
            row.prop(context.camera.luxrender_camera, "distribution", text="Distribution")
            row.prop(context.camera.luxrender_camera, "power", text="Power")


_register_elm(bl_ui.properties_data_camera.DATA_PT_camera_dof.append(lux_use_dof))


# Add options by render image/anim buttons
def render_start_options(self, context):
    if context.scene.render.engine == 'LUXRENDER_RENDER':
        col = self.layout.column()
        row = self.layout.row()

        col.prop(context.scene.luxrender_engine, "selected_luxrender_api", text="LuxRender API")

        if not UseLuxCore():
            col.prop(context.scene.luxrender_engine, "export_type", text="Export Type")
            if context.scene.luxrender_engine.export_type == 'EXT':
                col.prop(context.scene.luxrender_engine, "binary_name", text="Render Using")
            if context.scene.luxrender_engine.export_type == 'INT':
                row.prop(context.scene.luxrender_engine, "write_files", text="Write to Disk")
                row.prop(context.scene.luxrender_engine, "integratedimaging", text="Integrated Imaging")


_register_elm(bl_ui.properties_render.RENDER_PT_render.append(render_start_options))


# Add standard Blender elements for legacy texture editor
@classmethod
def blender_texture_poll(cls, context):
    tex = context.texture
    show = tex and ((tex.type == cls.tex_type and not tex.use_nodes) and
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

# To draw the preview pause button
def DrawButtonPause(self, context):
    layout = self.layout
    scene = context.scene

    if scene.render.engine == "LUXRENDER_RENDER":
        view = context.space_data

        if view.viewport_shade == "RENDERED":
            layout.prop(scene.luxrender_engine, "preview_stop", icon="PAUSE", text="")


_register_elm(bpy.types.VIEW3D_HT_header.append(DrawButtonPause))


@LuxRenderAddon.addon_register_class
class RENDERENGINE_luxrender(bpy.types.RenderEngine):
    """
    LuxRender Engine Exporter/Integration class
    """

    bl_idname = 'LUXRENDER_RENDER'
    bl_label = 'LuxRender'
    bl_use_preview = True
    bl_use_texture_preview = True

    render_lock = threading.Lock()

    def render(self, scene):
        """
        scene:  bpy.types.Scene

        Export the given scene to LuxRender.
        Choose from one of several methods depending on what needs to be rendered.

        Returns None
        """

        with RENDERENGINE_luxrender.render_lock:  # just render one thing at a time
            if scene is None:
                LuxLog('ERROR: Scene to render is not valid')
                return

            if UseLuxCore():
                self.luxcore_render(scene)
            else:
                self.luxrender_render(scene)

    def view_update(self, context):
        if UseLuxCore():
            self.luxcore_view_update(context)

    def view_draw(self, context):
        if UseLuxCore():
            self.luxcore_view_draw(context)

    ############################################################################
    #
    # LuxRender classic API
    #
    ############################################################################

    def luxrender_render(self, scene):
        prev_cwd = os.getcwd()
        try:
            self.LuxManager = None
            self.render_update_timer = None
            self.output_dir = efutil.temp_directory()
            self.output_file = 'default.png'

            if scene.name == 'preview':
                self.luxrender_render_preview(scene)
                return

            if scene.display_settings.display_device != "sRGB":
                LuxLog('WARNING: Colour Management not set to sRGB, render results may look too dark.')

            api_type, write_files = self.set_export_path(scene)

            os.chdir(efutil.export_path)

            is_animation = hasattr(self, 'is_animation') and self.is_animation
            make_queue = scene.luxrender_engine.export_type == 'EXT' and \
                         scene.luxrender_engine.binary_name == 'luxrender' and write_files

            if is_animation and make_queue:
                queue_file = efutil.export_path + '%s.%s.lxq' % (
                    efutil.scene_filename(), bpy.path.clean_name(scene.name))

                # Open/reset a queue file
                if scene.frame_current == scene.frame_start:
                    open(queue_file, 'w').close()

                if hasattr(self, 'update_progress'):
                    fr = scene.frame_end - scene.frame_start
                    fo = scene.frame_current - scene.frame_start
                    self.update_progress(fo / fr)

            exported_file = self.export_scene(scene)
            if not exported_file:
                return  # Export frame failed, abort rendering

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
            LuxLog('%s' % err)
            self.report({'ERROR'}, '%s' % err)

        os.chdir(prev_cwd)

    def luxrender_render_preview(self, scene):
        if sys.platform == 'darwin':
            self.output_dir = efutil.filesystem_path(bpy.app.tempdir)
        else:
            self.output_dir = efutil.temp_directory()

        if self.output_dir[-1] != '/':
            self.output_dir += '/'

        efutil.export_path = self.output_dir

        from ..outputs.pure_api import PYLUX_AVAILABLE

        if not PYLUX_AVAILABLE:
            LuxLog('ERROR: Material previews require pylux')
            return

        from ..export import materials as export_materials

        # Iterate through the preview scene, finding objects with materials attached
        objects_mats = {}
        for obj in [ob for ob in scene.objects if ob.is_visible(scene) and not ob.hide_render]:
            for mat in export_materials.get_instance_materials(obj):
                if mat is not None:
                    if not obj.name in objects_mats.keys():
                        objects_mats[obj] = []
                    objects_mats[obj].append(mat)

        preview_type = None  # 'MATERIAL' or 'TEXTURE'

        # find objects that are likely to be the preview objects
        preview_objects = [o for o in objects_mats.keys() if o.name.startswith('preview')]
        if len(preview_objects) > 0:
            preview_type = 'MATERIAL'
        else:
            preview_objects = [o for o in objects_mats.keys() if o.name.startswith('texture')]
            if len(preview_objects) > 0:
                preview_type = 'TEXTURE'

        if preview_type is None:
            return

        # TODO: scene setup based on PREVIEW_TYPE

        # Find the materials attached to the likely preview object
        likely_materials = objects_mats[preview_objects[0]]
        if len(likely_materials) < 1:
            print('no preview materials')
            return

        pm = likely_materials[0]
        pt = None
        LuxLog('Rendering material preview: %s' % pm.name)

        if preview_type == 'TEXTURE':
            pt = pm.active_texture

        LM = LuxManager(
            scene.name,
            api_type='API',
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
                raise Exception('Skipping material thumbnail update, image too small (%ix%i)' % (xres, yres))

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
                while not self.test_break() and sec_elapsed <= sec:
                    sec_elapsed += increment
                    time.sleep(increment)

            for i in range(multiprocessing.cpu_count() - 2):
                # -2 since 1 thread already created and leave 1 spare
                if is_finished(preview_context):
                    break
                preview_context.addThread()

            while not is_finished(preview_context):
                if self.test_break() or bpy.context.scene.render.engine != 'LUXRENDER_RENDER':
                    raise Exception('Render interrupted')

                # progressively update the preview
                time.sleep(0.2)  # safety-sleep

                if preview_context.getAttribute('renderer_statistics', 'samplesPerPixel') > 6:
                    if preview_type == 'TEXTURE':
                        interruptible_sleep(0.8)  # reduce update to every 1.0 sec until haltthreshold kills the render
                    else:
                        interruptible_sleep(1.8)  # reduce update to every 2.0 sec until haltthreshold kills the render

                preview_context.updateStatisticsWindow()
                LuxLog('Updating preview (%ix%i - %s)' % (xres, yres,
                        preview_context.getAttribute('renderer_statistics_formatted_short', '_recommended_string')))

                result = self.begin_result(0, 0, xres, yres)

                if hasattr(preview_context, 'blenderCombinedDepthBuffers'):
                    # use fast buffers
                    pb, zb = preview_context.blenderCombinedDepthBuffers()
                    result.layers.foreach_set("rect", pb)
                else:
                    lay = result.layers[0]
                    lay.rect = preview_context.blenderCombinedDepthRects()[0]

                # Cycles tiles adaption
                self.end_result(result, 0) if bpy.app.version > (2, 63, 17 ) else self.end_result(result)
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

        scene_path = efutil.filesystem_path(fp)

        if os.path.isdir(scene_path):
            self.output_dir = scene_path
        else:
            self.output_dir = os.path.dirname(scene_path)

        if self.output_dir[-1] not in ('/', '\\'):
            self.output_dir += '/'

        if scene.luxrender_engine.export_type == 'INT':
            write_files = scene.luxrender_engine.write_files
            if write_files:
                api_type = 'FILE'
            else:
                api_type = 'API'
                if sys.platform == 'darwin':
                    self.output_dir = efutil.filesystem_path(bpy.app.tempdir)
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
            api_type=api_type,
        )
        LuxManager.SetActive(LM)

        if scene.luxrender_engine.export_type == 'INT':
            # Set up networking before export so that we get better server usage
            if scene.luxrender_networking.use_network_servers and scene.luxrender_networking.servers:
                LM.lux_context.setNetworkServerUpdateInterval(scene.luxrender_networking.serverinterval)
                for server in scene.luxrender_networking.servers.split(','):
                    LM.lux_context.addServer(server.strip())

        output_filename = get_output_filename(scene)

        scene_exporter = SceneExporter()
        scene_exporter.properties.directory = self.output_dir
        scene_exporter.properties.filename = output_filename
        scene_exporter.properties.api_type = api_type  # Set export target
        scene_exporter.properties.write_files = write_files  # Use file write decision from above
        scene_exporter.properties.write_all_files = False  # Use UI file write settings
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
        internal = (scene.luxrender_engine.export_type in ['INT'])
        write_files = scene.luxrender_engine.write_files and (scene.luxrender_engine.export_type in ['INT', 'EXT'])
        render = scene.luxrender_engine.render

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

        luxrender_path = efutil.filesystem_path(efutil.find_config_value(
                              'luxrender', 'defaults', 'install_path', ''))

        print('luxrender_path: ', luxrender_path)

        if not luxrender_path:
            return ['']

        if luxrender_path[-1] != '/':
            luxrender_path += '/'

        if sys.platform == 'darwin':
            # Get binary from OSX bundle
            luxrender_path += 'LuxRender.app/Contents/MacOS/%s' % scene.luxrender_engine.binary_name
            if not os.path.exists(luxrender_path):
                LuxLog('LuxRender not found at path: %s' % luxrender_path, ', trying default LuxRender location')
                luxrender_path = '/Applications/LuxRender/LuxRender.app/Contents/MacOS/%s' % \
                                 scene.luxrender_engine.binary_name  # try fallback to default installation path

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

        # Epsilon values if any
        if scene.luxrender_engine.binary_name != 'luxvr':
            if scene.luxrender_engine.min_epsilon:
                cmd_args.append('--minepsilon=%.8f' % scene.luxrender_engine.min_epsilon)
            if scene.luxrender_engine.max_epsilon:
                cmd_args.append('--maxepsilon=%.8f' % scene.luxrender_engine.max_epsilon)

        if scene.luxrender_engine.binary_name == 'luxrender':
            # Copy the GUI log to the console
            cmd_args.append('--logconsole')

        # Set number of threads for external processes
        if not scene.luxrender_engine.threads_auto:
            cmd_args.append('--threads=%i' % scene.luxrender_engine.threads)

        # Set fixed seeds, if enabled
        if scene.luxrender_engine.fixed_seed:
            cmd_args.append('--fixedseed')

        if scene.luxrender_networking.use_network_servers and scene.luxrender_networking.servers:
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
                self.LuxManager.fb_thread.set_kick_period(
                    scene.camera.data.luxrender_camera.luxrender_film.internal_updateinterval)

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
                    if self.render_update_timer.isAlive():
                        self.render_update_timer.join()
            else:
                cmd_args = self.get_process_args(scene, start_rendering)

                cmd_args.append(fn.replace('//', '/'))

                LuxLog('Launching: %s' % cmd_args)
                # LuxLog(' in %s' % self.outout_dir)
                luxrender_process = subprocess.Popen(cmd_args, cwd=self.output_dir)

                if not (
                        scene.luxrender_engine.binary_name == 'luxrender' and not
                        scene.luxrender_engine.monitor_external):
                    framebuffer_thread = LuxFilmDisplay({
                        'resolution': scene.camera.data.luxrender_camera.luxrender_film.resolution(scene),
                        'RE': self,
                    })
                    framebuffer_thread.set_kick_period(scene.camera.data.luxrender_camera.luxrender_film.writeinterval)
                    framebuffer_thread.start()
                    while luxrender_process.poll() is None and not self.test_break():
                        self.render_update_timer = threading.Timer(1, self.process_wait_timer)
                        self.render_update_timer.start()
                        if self.render_update_timer.isAlive():
                            self.render_update_timer.join()

                    # If we exit the wait loop (user cancelled) and luxconsole is still running, then send SIGINT
                    if luxrender_process.poll() is None and scene.luxrender_engine.binary_name != 'luxrender':
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
        """
        Update the displayed rendering statistics and detect end of rendering

        Returns None
        """

        LC = self.LuxManager.lux_context

        self.update_stats('', 'LuxRender: Rendering %s' % self.LuxManager.stats_thread.stats_string)

        if hasattr(self, 'update_progress') and LC.getAttribute('renderer_statistics', 'percentComplete') > 0:
            prg = LC.getAttribute('renderer_statistics', 'percentComplete') / 100.0
            self.update_progress(prg)

        if self.test_break() or \
                        LC.statistics('filmIsReady') == 1.0 or \
                        LC.statistics('terminated') == 1.0 or \
                        LC.getAttribute('film', 'enoughSamples'):
            self.LuxManager.reset()
            self.update_stats('', '')

    ############################################################################
    #
    # LuxCore code
    #
    ############################################################################

    def PrintStats(self, lcConfig, stats):
        lc_engine = lcConfig.GetProperties().Get('renderengine.type').GetString()

        if lc_engine == 'BIASPATHCPU' or lc_engine == 'BIASPATHOCL':
            converged = stats.Get('stats.biaspath.tiles.converged.count').GetInt()
            notconverged = stats.Get('stats.biaspath.tiles.notconverged.count').GetInt()
            pending = stats.Get('stats.biaspath.tiles.pending.count').GetInt()

            LuxLog('[Elapsed time: %3d][Pass %4d][Convergence %d/%d][Avg. samples/sec % 3.2fM on %.1fK tris]' % (
                stats.Get('stats.renderengine.time').GetFloat(),
                stats.Get('stats.renderengine.pass').GetInt(),
                converged, converged + notconverged + pending,
                (stats.Get('stats.renderengine.total.samplesec').GetFloat() / 1000000.0),
                (stats.Get('stats.dataset.trianglecount').GetFloat() / 1000.0)))
        else:
            LuxLog('[Elapsed time: %3d][Samples %4d][Avg. samples/sec % 3.2fM on %.1fK tris]' % (
                stats.Get('stats.renderengine.time').GetFloat(),
                stats.Get('stats.renderengine.pass').GetInt(),
                (stats.Get('stats.renderengine.total.samplesec').GetFloat() / 1000000.0),
                (stats.Get('stats.dataset.trianglecount').GetFloat() / 1000.0)))

        return stats.Get('stats.renderengine.convergence').GetFloat() == 1.0

    def CreateBlenderStats(self, lcConfig, stats):
        lc_engine = lcConfig.GetProperties().Get('renderengine.type').GetString()

        output = ''

        if lc_engine == 'BIASPATHCPU' or lc_engine == 'BIASPATHOCL':
            converged = stats.Get('stats.biaspath.tiles.converged.count').GetInt()
            notconverged = stats.Get('stats.biaspath.tiles.notconverged.count').GetInt()
            pending = stats.Get('stats.biaspath.tiles.pending.count').GetInt()

            output = ('Pass ' + str(stats.Get('stats.renderengine.pass').GetInt()) + '| Convergence ' + str(converged) + '/') + (
                        str(converged + notconverged + pending) + ' | Avg. samples/sec ') + (
                        ('%3.2f' % (stats.Get('stats.renderengine.total.samplesec').GetFloat() / 1000000.0))) + (
                        'M on ' + ('%.1f' % (stats.Get('stats.dataset.trianglecount').GetFloat() / 1000.0))) + (
                        'K tris')
        else:
            output = ('Pass ' + str(stats.Get('stats.renderengine.pass').GetInt()) + ' | Avg. samples/sec ') + (
                        ('%3.2f' % (stats.Get('stats.renderengine.total.samplesec').GetFloat() / 1000000.0))) + (
                        'M on ' + ('%.1f' % (stats.Get('stats.dataset.trianglecount').GetFloat() / 1000.0)) + 'K tris' )

        return output

    def normalizeChannel(self, channel_buffer):
        isInf = math.isinf

        # find max value
        maxValue = 0.0
        for elem in channel_buffer:
            if elem > maxValue and not isInf(elem):
                maxValue = elem

        if maxValue > 0.0:
            for i in range(0, len(channel_buffer)):
                channel_buffer[i] = channel_buffer[i] / maxValue

    def convertChannelToImage(self, lcSession, filmWidth, filmHeight, channelName, useHDR, outputType, arrayType,
                              arrayInitValue, arrayDepth, normalize, saveToDisk, buffer_id=-1):
        """
        Convert AOVs to Blender images

        Example arguments:
        channelName:        RGB
        useHDR:             False
        outputType:         pyluxcore.FilmOutputType.RGB
        arrayType:         'f'
        arrayInitValue:     0.0
        arrayDepth:         3
        normalize:          False
        saveToDisk:         False

        buffer_id is used only for obtaining the right MATERIAL_ID_MASK and BY_MATERIAL_ID buffer
        """
        from ..outputs.luxcore_api import pyluxcore
        # raw channel buffer
        channel_buffer = array.array(arrayType, [arrayInitValue] * (filmWidth * filmHeight * arrayDepth))
        # buffer for converted array (to RGBA)
        channel_buffer_converted = []

        if channelName == 'MATERIAL_ID':
            # MATERIAL_ID needs special treatment
            channel_buffer_converted = [None] * (filmWidth * filmHeight * 4)
            lcSession.GetFilm().GetOutputUInt(outputType, channel_buffer)

            mask_red = 0xff0000
            mask_green = 0xff00
            mask_blue = 0xff

            k = 0
            for i in range(0, len(channel_buffer)):
                red = float((channel_buffer[i] & mask_red) >> 16) / 255.0
                green = float((channel_buffer[i] & mask_green) >> 8) / 255.0
                blue = float(channel_buffer[i] & mask_blue) / 255.0

                channel_buffer_converted[k] = red
                channel_buffer_converted[k + 1] = green
                channel_buffer_converted[k + 2] = blue
                channel_buffer_converted[k + 3] = 1.0
                k += 4

        else:
            if channelName in ['MATERIAL_ID_MASK', 'BY_MATERIAL_ID'] and buffer_id != -1:
                lcSession.GetFilm().GetOutputFloat(outputType, channel_buffer, buffer_id)
            else:
                lcSession.GetFilm().GetOutputFloat(outputType, channel_buffer)

            # spread value to RGBA format

            if arrayDepth == 1:
                if getattr(pyluxcore, "ConvertFilmChannelOutput_1xFloat_To_4xFloatList", None) is not None:
                    channel_buffer_converted = pyluxcore.ConvertFilmChannelOutput_1xFloat_To_4xFloatList(filmWidth,
                                                                                                         filmHeight,
                                                                                                         channel_buffer,
                                                                                                         normalize)
                else:
                    # normalize channel_buffer values (map to 0..1 range)
                    if normalize:
                        self.normalizeChannel(channel_buffer)
                    for elem in channel_buffer:
                        channel_buffer_converted.extend([elem, elem, elem, 1.0])

            # UV channel, just add 0.0 for B and 1.0 for A components
            elif arrayDepth == 2:
                if getattr(pyluxcore, "ConvertFilmChannelOutput_2xFloat_To_4xFloatList", None) is not None:
                    channel_buffer_converted = pyluxcore.ConvertFilmChannelOutput_2xFloat_To_4xFloatList(filmWidth,
                                                                                                         filmHeight,
                                                                                                         channel_buffer,
                                                                                                         normalize)
                else:
                    # normalize channel_buffer values (map to 0..1 range)
                    if normalize:
                        self.normalizeChannel(channel_buffer)
                    i = 0
                    while i < len(channel_buffer):
                        channel_buffer_converted.extend([channel_buffer[i], channel_buffer[i + 1], 0.0, 1.0])
                        i += 2

            # RGB channels: just add 1.0 as alpha component
            elif arrayDepth == 3:
                if getattr(pyluxcore, "ConvertFilmChannelOutput_3xFloat_To_4xFloatList", None) is not None:
                    channel_buffer_converted = pyluxcore.ConvertFilmChannelOutput_3xFloat_To_4xFloatList(filmWidth,
                                                                                                         filmHeight,
                                                                                                         channel_buffer,
                                                                                                         normalize)
                else:
                    # normalize channel_buffer values (map to 0..1 range)
                    if normalize:
                        self.normalizeChannel(channel_buffer)
                    i = 0
                    while i < len(channel_buffer):
                        channel_buffer_converted.extend(
                            [channel_buffer[i], channel_buffer[i + 1], channel_buffer[i + 2], 1.0])
                        i += 3

            # RGBA channels: just copy the list
            else:
                channel_buffer_converted = channel_buffer

        imageName = 'pass_' + str(channelName)
        if buffer_id != -1:
            imageName += '_' + str(buffer_id)

        # remove channel from Blender if it already exists and has no users (to prevent duplicates)
        for bl_image in bpy.data.images:
            if bl_image.name == imageName and not bl_image.users:
                bpy.data.images.remove(bl_image)

        # write converted buffer with RGBA values to Blender image
        blenderImage = bpy.data.images.new(imageName, alpha=False, width=filmWidth, height=filmHeight,
                                           float_buffer=useHDR)
        blenderImage.pixels = channel_buffer_converted

        # write image to file
        suffix = '.png'
        image_format = 'PNG'
        if useHDR:
            suffix = '.exr'
            image_format = 'OPEN_EXR'

        blenderImage.filepath_raw = '//' + imageName + suffix
        blenderImage.file_format = image_format
        if saveToDisk:
            blenderImage.save()

    def luxcore_render(self, scene):
        if scene.name == 'preview':
            self.luxcore_render_preview(scene)
            return

        # LuxCore libs
        if not PYLUXCORE_AVAILABLE:
            LuxLog('ERROR: LuxCore rendering requires pyluxcore')
            self.report({'ERROR'}, 'LuxCore rendering requires pyluxcore')
            return
        from ..outputs.luxcore_api import pyluxcore
        from ..export.luxcore_scene import BlenderSceneConverter

        try:
            # convert the Blender scene
            lcConfig = BlenderSceneConverter(scene).Convert()

            lcSession = pyluxcore.RenderSession(lcConfig)

            filmWidth, filmHeight = scene.camera.data.luxrender_camera.luxrender_film.resolution(scene)
            imageBufferFloat = array.array('f', [0.0] * (filmWidth * filmHeight * 3))

            # Start the rendering
            lcSession.Start()

            startTime = time.time()
            lastRefreshTime = startTime
            done = False
            while not self.test_break() and not done:
                time.sleep(0.2)

                now = time.time()
                elapsedTimeSinceLastRefresh = now - lastRefreshTime
                elapsedTimeSinceStart = now - startTime

                if elapsedTimeSinceStart < 5.0 or elapsedTimeSinceLastRefresh > \
                        scene.camera.data.luxrender_camera.luxrender_film.displayinterval:
                    # Print some information about the rendering progress

                    # Update statistics
                    lcSession.UpdateStats()

                    stats = lcSession.GetStats()
                    done = self.PrintStats(lcConfig, stats)

                    blender_stats = self.CreateBlenderStats(lcConfig, stats)
                    self.update_stats('Rendering...', blender_stats)

                    # Update the image
                    lcSession.GetFilm().GetOutputFloat(pyluxcore.FilmOutputType.RGB_TONEMAPPED, imageBufferFloat)

                    # Here we write the pixel values to the RenderResult
                    result = self.begin_result(0, 0, filmWidth, filmHeight)
                    layer = result.layers[0]
                    layer.rect = pyluxcore.ConvertFilmChannelOutput_3xFloat_To_3xFloatList(filmWidth, filmHeight,
                                                                                           imageBufferFloat)
                    self.end_result(result)

                    lastRefreshTime = now

            channelCalcStartTime = time.time()
            LuxLog('Importing AOV channels into Blender...')
            self.update_stats('Importing AOV channels into Blender...', '')

            channels = scene.luxrender_channels

            if channels.RGB:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'RGB', True, pyluxcore.FilmOutputType.RGB,
                                           'f', 0.0, 3, False, channels.saveToDisk)
            if channels.RGBA:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'RGBA', True,
                                           pyluxcore.FilmOutputType.RGBA, 'f', 0.0, 4, False, channels.saveToDisk)
            if channels.RGB_TONEMAPPED:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'RGB_TONEMAPPED', False,
                                           pyluxcore.FilmOutputType.RGB_TONEMAPPED, 'f', 0.0, 3, False,
                                           channels.saveToDisk)
            if channels.RGBA_TONEMAPPED:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'RGBA_TONEMAPPED', False,
                                           pyluxcore.FilmOutputType.RGBA_TONEMAPPED, 'f', 0.0, 4, False,
                                           channels.saveToDisk)
            if channels.ALPHA:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'ALPHA', False,
                                           pyluxcore.FilmOutputType.ALPHA, 'f', 0.0, 1, False, channels.saveToDisk)
            if channels.DEPTH:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'DEPTH', True,
                                           pyluxcore.FilmOutputType.DEPTH, 'f', 0.0, 1, channels.normalize_DEPTH,
                                           channels.saveToDisk)
            if channels.POSITION:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'POSITION', True,
                                           pyluxcore.FilmOutputType.POSITION, 'f', 0.0, 3, False, channels.saveToDisk)
            if channels.GEOMETRY_NORMAL:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'GEOMETRY_NORMAL', True,
                                           pyluxcore.FilmOutputType.GEOMETRY_NORMAL, 'f', 0.0, 3, False,
                                           channels.saveToDisk)
            if channels.SHADING_NORMAL:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'SHADING_NORMAL', True,
                                           pyluxcore.FilmOutputType.SHADING_NORMAL, 'f', 0.0, 3, False,
                                           channels.saveToDisk)
            if channels.MATERIAL_ID:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'MATERIAL_ID', False,
                                           pyluxcore.FilmOutputType.MATERIAL_ID, 'I', 0, 1, False, channels.saveToDisk)
            if channels.DIRECT_DIFFUSE:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'DIRECT_DIFFUSE', True,
                                           pyluxcore.FilmOutputType.DIRECT_DIFFUSE, 'f', 0.0, 3,
                                           channels.normalize_DIRECT_DIFFUSE, channels.saveToDisk)
            if channels.DIRECT_GLOSSY:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'DIRECT_GLOSSY', True,
                                           pyluxcore.FilmOutputType.DIRECT_GLOSSY, 'f', 0.0, 3,
                                           channels.normalize_DIRECT_GLOSSY, channels.saveToDisk)
            if channels.EMISSION:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'EMISSION', True,
                                           pyluxcore.FilmOutputType.EMISSION, 'f', 0.0, 3, False, channels.saveToDisk)
            if channels.INDIRECT_DIFFUSE:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'INDIRECT_DIFFUSE', True,
                                           pyluxcore.FilmOutputType.INDIRECT_DIFFUSE, 'f', 0.0, 3,
                                           channels.normalize_INDIRECT_DIFFUSE, channels.saveToDisk)
            if channels.INDIRECT_GLOSSY:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'INDIRECT_GLOSSY', True,
                                           pyluxcore.FilmOutputType.INDIRECT_GLOSSY, 'f', 0.0, 3,
                                           channels.normalize_INDIRECT_GLOSSY, channels.saveToDisk)
            if channels.INDIRECT_SPECULAR:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'INDIRECT_SPECULAR', True,
                                           pyluxcore.FilmOutputType.INDIRECT_SPECULAR, 'f', 0.0, 3,
                                           channels.normalize_INDIRECT_SPECULAR, channels.saveToDisk)
            if channels.DIRECT_SHADOW_MASK:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'DIRECT_SHADOW_MASK', False,
                                           pyluxcore.FilmOutputType.DIRECT_SHADOW_MASK, 'f', 0.0, 1, False,
                                           channels.saveToDisk)
            if channels.INDIRECT_SHADOW_MASK:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'INDIRECT_SHADOW_MASK', False,
                                           pyluxcore.FilmOutputType.INDIRECT_SHADOW_MASK, 'f', 0.0, 1, False,
                                           channels.saveToDisk)
            if channels.UV:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'UV', True, pyluxcore.FilmOutputType.UV,
                                           'f', 0.0, 2, False, channels.saveToDisk)
            if channels.RAYCOUNT:
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'RAYCOUNT', True,
                                           pyluxcore.FilmOutputType.RAYCOUNT, 'f', 0.0, 1, channels.normalize_RAYCOUNT,
                                           channels.saveToDisk)

            props = lcSession.GetRenderConfig().GetProperties()
            # Convert all MATERIAL_ID_MASK channels
            mask_ids = set()
            for i in props.GetAllUniqueSubNames("film.outputs"):
                if props.Get(i + ".type").GetString() == "MATERIAL_ID_MASK":
                    mask_ids.add(props.Get(i + ".id").GetInt())

            for i in range(len(mask_ids)):
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'MATERIAL_ID_MASK', False,
                                           pyluxcore.FilmOutputType.MATERIAL_ID_MASK, 'f', 0.0, 1, False,
                                           channels.saveToDisk, i)

            # Convert all BY_MATERIAL_ID channels
            ids = set()
            for i in props.GetAllUniqueSubNames("film.outputs"):
                if props.Get(i + ".type").GetString() == "BY_MATERIAL_ID":
                    ids.add(props.Get(i + ".id").GetInt())

            for i in range(len(ids)):
                self.convertChannelToImage(lcSession, filmWidth, filmHeight, 'BY_MATERIAL_ID', True,
                                           pyluxcore.FilmOutputType.BY_MATERIAL_ID, 'f', 0.0, 3, False,
                                           channels.saveToDisk, i)

            channelCalcTime = time.time() - channelCalcStartTime
            LuxLog('AOV conversion took %i seconds' % channelCalcTime)

            lcSession.Stop()

            LuxLog('Done.')
        except Exception as exc:
            LuxLog('Rendering aborted: %s' % exc)
            import traceback

            traceback.print_exc()

    def luxcore_render_preview(self, scene):
        # LuxCore libs
        if not PYLUXCORE_AVAILABLE:
            LuxLog('ERROR: LuxCore preview rendering requires pyluxcore')
            return
        from ..outputs.luxcore_api import pyluxcore
        from ..export.luxcore_scene import BlenderSceneConverter

        try:
            xres, yres = scene.camera.data.luxrender_camera.luxrender_film.resolution(scene)

            # Don't render the tiny images
            if xres <= 96:
                raise Exception('Skipping material thumbnail update, image too small (%ix%i)' % (xres, yres))

            # Convert the Blender scene
            lcConfig = BlenderSceneConverter(scene).Convert()
            LuxLog('RenderConfig Properties:')
            LuxLog(str(lcConfig.GetProperties()))
            LuxLog('Scene Properties:')
            LuxLog(str(lcConfig.GetScene().GetProperties()))

            lcSession = pyluxcore.RenderSession(lcConfig)

            filmWidth, filmHeight = scene.camera.data.luxrender_camera.luxrender_film.resolution(scene)
            imageBufferFloat = array.array('f', [0.0] * (filmWidth * filmHeight * 3))

            # Start the rendering
            lcSession.Start()

            startTime = time.time()
            while not self.test_break() and time.time() - startTime < 10.0:
                time.sleep(0.2)

                # Print some information about the rendering progress

                # Update statistics
                lcSession.UpdateStats()

                stats = lcSession.GetStats()
                self.PrintStats(lcConfig, stats)

                # Update the image
                lcSession.GetFilm().GetOutputFloat(pyluxcore.FilmOutputType.RGB_TONEMAPPED, imageBufferFloat)

                # Here we write the pixel values to the RenderResult
                result = self.begin_result(0, 0, filmWidth, filmHeight)
                layer = result.layers[0]
                layer.rect = pyluxcore.ConvertFilmChannelOutput_3xFloat_To_3xFloatList(filmWidth, filmHeight,
                                                                                       imageBufferFloat)
                self.end_result(result)

            lcSession.Stop()

            LuxLog('Done.')
        except Exception as exc:
            LuxLog('Rendering aborted: %s' % exc)
            import traceback

            traceback.print_exc()

    ############################################################################
    # Viewport render
    ############################################################################

    lcConfig = None
    viewSession = None
    viewSessionRunning = False
    viewSessionStartTime = 0.0
    viewFilmWidth = -1
    viewFilmHeight = -1
    viewImageBufferFloat = None
    viewMatrix = []
    viewLens = -1
    viewCameraZoom = -1
    viewCameraOffset = []
    viewCameraShiftX = -1
    viewCameraShiftY = -1
    # store renderengine configuration and material definitions of last update
    lastRenderSettings = ''
    lastMaterialSettings = ''

    def build_viewport_camera(self, lcConfig, context, pyluxcore):
        view_persp = context.region_data.view_perspective
        self.viewMatrix = mathutils.Matrix(context.region_data.view_matrix)
        self.viewLens = context.space_data.lens
        self.viewCameraZoom = context.region_data.view_camera_zoom
        self.viewCameraOffset = list(context.region_data.view_camera_offset)
        self.viewCameraShiftX = context.scene.camera.data.shift_x
        self.viewCameraShiftY = context.scene.camera.data.shift_y

        if view_persp != 'ORTHO':
            zoom = 1.0
            dx = 0.0
            dy = 0.0
            xaspect = 1.0
            yaspect = 1.0
            cam_rotation = context.region_data.view_rotation
            cam_trans = mathutils.Vector((self.viewMatrix[0][3], self.viewMatrix[1][3], self.viewMatrix[2][3]))
            cam_lookat = list(context.region_data.view_location)

            rot = mathutils.Matrix(((-self.viewMatrix[0][0], -self.viewMatrix[1][0], -self.viewMatrix[2][0]),
                                    (-self.viewMatrix[0][1], -self.viewMatrix[1][1], -self.viewMatrix[2][1]),
                                    (-self.viewMatrix[0][2], -self.viewMatrix[1][2], -self.viewMatrix[2][2])))

            cam_origin = list(rot * cam_trans)
            cam_fov = 2 * math.atan(0.5 * 32.0 / self.viewLens)
            cam_up = list(rot * mathutils.Vector((0, -1, 0)))

            if self.viewFilmWidth > self.viewFilmHeight:
                xaspect = 1.0
                yaspect = self.viewFilmHeight / self.viewFilmWidth
            else:
                xaspect = self.viewFilmWidth / self.viewFilmHeight
                yaspect = 1.0

            if view_persp == 'CAMERA':
                blcamera = context.scene.camera
                #magic zoom formula for camera viewport zoom from blender source
                zoom = self.viewCameraZoom
                zoom = (1.41421 + zoom / 50.0)
                zoom *= zoom
                zoom = 2.0 / zoom

                #camera plane offset in camera viewport
                dx = 2.0 * (self.viewCameraShiftX + self.viewCameraOffset[0] * xaspect * 2.0)
                dy = 2.0 * (self.viewCameraShiftY + self.viewCameraOffset[1] * yaspect * 2.0)

                cam_fov = blcamera.data.angle
                luxCamera = context.scene.camera.data.luxrender_camera

                lookat = luxCamera.lookAt(blcamera)
                cam_origin = list(lookat[0:3])
                cam_lookat = list(lookat[3:6])
                cam_up = list(lookat[6:9])

            zoom *= 2.0

            scr_left = -xaspect * zoom
            scr_right = xaspect * zoom
            scr_bottom = -yaspect * zoom
            scr_top = yaspect * zoom

            screenwindow = [scr_left + dx, scr_right + dx, scr_bottom + dy, scr_top + dy]

            scene = lcConfig.GetScene()
            scene.Parse(pyluxcore.Properties().
                        Set(pyluxcore.Property('scene.camera.lookat.target', cam_lookat)).
                        Set(pyluxcore.Property('scene.camera.lookat.orig', cam_origin)).
                        Set(pyluxcore.Property('scene.camera.up', cam_up)).
                        Set(pyluxcore.Property('scene.camera.screenwindow', screenwindow)).
                        Set(pyluxcore.Property('scene.camera.fieldofview', math.degrees(cam_fov)))
            )
	
    def luxcore_view_update(self, context, updateCamera=False):
        # LuxCore libs
        if not PYLUXCORE_AVAILABLE:
            LuxLog('ERROR: LuxCore real-time rendering requires pyluxcore')
            return
            
        if context.scene.luxrender_engine.preview_stop:
            return
            
        # get update starttime in milliseconds
        view_update_startTime = int(round(time.time() * 1000))
        
        from ..outputs.luxcore_api import pyluxcore
        from ..export.luxcore_scene import BlenderSceneConverter
        
        if (self.viewFilmWidth == -1) or (self.viewFilmHeight == -1):
            self.viewFilmWidth = context.region.width
            self.viewFilmHeight = context.region.height
            self.viewImageBufferFloat = array.array('f', [0.0] * (self.viewFilmWidth * self.viewFilmHeight * 3))
        
        # check for config
        if self.lcConfig is None:
            LuxManager.SetCurrentScene(context.scene)

            # Convert the Blender scene
            self.lcConfig = BlenderSceneConverter(context.scene).Convert(
                imageWidth=self.viewFilmWidth,
                imageHeight=self.viewFilmHeight)
                
        # check for session
        if self.viewSession is None:
            self.build_viewport_camera(self.lcConfig, context, pyluxcore)
    
            self.viewSession = pyluxcore.RenderSession(self.lcConfig)
            
            try:
                self.viewSession.Start()
            except Exception as exc:
                LuxLog('View update aborted: %s' % exc)
                
                self.lcConfig = None
                self.viewSession = None
                
                import traceback
                traceback.print_exc()
                
            self.viewSessionStartTime = time.time()
            self.viewSessionRunning = True
        
        ########################################################################
        # Dynamic updates
        ########################################################################
        
        update_everything = True
        
        # only preview region size or camera position has changed
        if updateCamera:
            LuxLog("Dynamic updates: updating preview camera")
        
            self.viewFilmWidth = context.region.width
            self.viewFilmHeight = context.region.height
            self.viewImageBufferFloat = array.array('f', [0.0] * (self.viewFilmWidth * self.viewFilmHeight * 3))
            
            # Stop the rendering
            if self.viewSessionRunning:
                self.viewSession.Stop()
                self.viewSessionRunning = False
            self.viewSession = None

            # Set the new size
            self.lcConfig.Parse(pyluxcore.Properties().
	            Set(pyluxcore.Property("film.width", [self.viewFilmWidth])).
	            Set(pyluxcore.Property("film.height", [self.viewFilmHeight])))

            # adjust the camera
            self.build_viewport_camera(self.lcConfig, context, pyluxcore)
            
            # Re-start the rendering
            self.viewSession = pyluxcore.RenderSession(self.lcConfig)
            self.viewSession.Start()
            self.viewSessionStartTime = time.time()
            self.viewSessionRunning = True
            
            # when the preview region size is changed, nothing else can change
            # report time it took to update
            view_update_time = int(round(time.time() * 1000)) - view_update_startTime
            LuxLog("Dynamic updates: update took %dms" % view_update_time)
            return
        
        # check objects for updates
        if bpy.data.objects.is_updated:
            for ob in bpy.data.objects:
                if ob == None:
                    continue
                    
                if ob.is_updated_data:
                    LuxLog("Dynamic updates: updating data of object %s" % ob.name)
                    # missing
                    # note: currently one of the few cases triggering the fallback
                    # (by leaving update_everything set to True)
                    
                if ob.is_updated:
                    update_everything = False
                    
                    if ob.name == context.scene.camera.name:
                        LuxLog('Dynamic updates: updating camera: %s' % ob.name)
                        self.viewSession.BeginSceneEdit()
                        self.build_viewport_camera(self.lcConfig, context, pyluxcore)
                        self.viewSession.EndSceneEdit()
                    else:
                        LuxLog("Dynamic updates: updating object: %s" % ob.name)
                        
                        self.viewSession.BeginSceneEdit()
                        converter = BlenderSceneConverter(context.scene, self.viewSession)
                        converter.ConvertObject(ob)
                        
                        lcScene = self.lcConfig.GetScene()
                        lcScene.Parse(converter.scnProps)
                        
                        self.viewSession.EndSceneEdit()
        else:
            LuxLog('Dynamic updates: no objects changed, checking materials and config')
            
            # check for changes in materials
            # for now, just update all materials
            matConverter = BlenderSceneConverter(context.scene)
            
            for material in bpy.data.materials:
                matConverter.ConvertMaterial(material, bpy.data.materials)
            
            # prevent triggering a useless material update on startup
            if self.lastMaterialSettings == '':
                self.lastMaterialSettings = str(matConverter.scnProps)
            elif self.lastMaterialSettings != str(matConverter.scnProps):
                # material settings have changed, update them
                LuxLog("Dynamic updates: updating all materials")
                
                self.viewSession.BeginSceneEdit()
                scene = self.lcConfig.GetScene()
                scene.Parse(pyluxcore.Properties().Set(matConverter.scnProps))
                self.viewSession.EndSceneEdit()
                
                # save settings to compare with next update
                self.lastMaterialSettings = str(matConverter.scnProps)
                update_everything = False
            BlenderSceneConverter.clear()
                
            # check for changes in renderengine configuration
            # for now, just update whole renderengine configuration
            engineConverter = BlenderSceneConverter(context.scene)
            engineConverter.ConvertEngineSettings()
            
            # prevent triggering a useless renderconfig update on startup
            if self.lastRenderSettings == '':
                self.lastRenderSettings = str(engineConverter.cfgProps)
            elif self.lastRenderSettings != str(engineConverter.cfgProps):
                # renderengine config has changed, update it
                LuxLog("Dynamic updates: updating renderengine configuration")
                
                # Stop the rendering
                if self.viewSessionRunning:
                    self.viewSession.Stop()
                    self.viewSessionRunning = False
                self.viewSession = None
    
                # Set the new renderengine configuration
                self.lcConfig.Parse(pyluxcore.Properties().Set(engineConverter.cfgProps))
            
                # Re-start the rendering
                self.viewSession = pyluxcore.RenderSession(self.lcConfig)
                
                try:
                    self.viewSession.Start()
                except Exception as exc:
                    LuxLog('View update aborted: %s' % exc)
                
                    self.lcConfig = None
                    self.viewSession = None
                
                    import traceback
                    traceback.print_exc()
                
                self.viewSessionStartTime = time.time()
                self.viewSessionRunning = True
                
                # save settings to compare with next update
                self.lastRenderSettings = str(engineConverter.cfgProps)
                update_everything = False
            
            #if context.active_object.name == context.scene.camera.name:
            #    update_everything = False
                        
        ########################################################################
        # Fallback: if scene modification is unknown, update whole scene
        ########################################################################
        
        if update_everything:
            LuxLog('Dynamic updates: fallback, re-exporting whole scene')
            LuxManager.SetCurrentScene(context.scene)

            # Convert the Blender scene
            self.lcConfig = BlenderSceneConverter(context.scene).Convert(
                imageWidth=self.viewFilmWidth,
                imageHeight=self.viewFilmHeight)
                
            if self.viewSessionRunning:
                self.viewSession.Stop()
                self.viewSessionRunning = False
            self.viewSession = None
            
            self.build_viewport_camera(self.lcConfig, context, pyluxcore)
        
            self.viewSession = pyluxcore.RenderSession(self.lcConfig)
            self.viewSession.Start()
            self.viewSessionStartTime = time.time()
            self.viewSessionRunning = True
            
        # report time it took to update
        view_update_time = int(round(time.time() * 1000)) - view_update_startTime
        LuxLog("Dynamic updates: update took %dms" % view_update_time)

    def luxcore_view_draw(self, context):
        # LuxCore libs
        if not PYLUXCORE_AVAILABLE:
            LuxLog('ERROR: LuxCore real-time rendering requires pyluxcore')
            return
        from ..outputs.luxcore_api import pyluxcore

        # Check if the size of the window is changed
        if (self.viewFilmWidth != context.region.width) or (self.viewFilmHeight != context.region.height) or (
            self.viewMatrix != context.region_data.view_matrix) or (self.viewLens != context.space_data.lens) or (
            self.viewCameraOffset[0] != context.region_data.view_camera_offset[0]) or (
            self.viewCameraOffset[1] != context.region_data.view_camera_offset[1]) or (
            self.viewCameraZoom != context.region_data.view_camera_zoom):
            self.luxcore_view_update(context, updateCamera=True)

        # Update statistics
        if self.viewSessionRunning:
            self.viewSession.UpdateStats()

            stats = self.viewSession.GetStats()
            #self.PrintStats(self.viewSession.GetRenderConfig(), stats)
                    
            blender_stats = self.CreateBlenderStats(self.lcConfig, stats)
            self.update_stats('Rendering...', blender_stats)

            # Update the image buffer
            self.viewSession.GetFilm().GetOutputFloat(pyluxcore.FilmOutputType.RGB_TONEMAPPED,
                                                      self.viewImageBufferFloat)

        # Update the screen
        glBuffer = bgl.Buffer(bgl.GL_FLOAT, [self.viewFilmWidth * self.viewFilmHeight * 3], self.viewImageBufferFloat)
        bgl.glRasterPos2i(0, 0)
        bgl.glDrawPixels(self.viewFilmWidth, self.viewFilmHeight, bgl.GL_RGB, bgl.GL_FLOAT, glBuffer)

        if not context.scene.luxrender_engine.preview_stop:
            # Trigger another update
            nextRefreshTime = 0.2 if time.time() - self.viewSessionStartTime < 5.0 else 2.0
            threading.Timer(nextRefreshTime, self.tag_redraw).start()

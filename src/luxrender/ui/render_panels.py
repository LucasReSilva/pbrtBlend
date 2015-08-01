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
import bpy, bl_ui

from ..extensions_framework.ui import property_group_renderer

from ..outputs.luxcore_api import UseLuxCore
from .. import LuxRenderAddon


class render_panel(bl_ui.properties_render.RenderButtonsPanel, property_group_renderer):
    """
    Base class for render engine settings panels
    """

    COMPAT_ENGINES = 'LUXRENDER_RENDER'


@LuxRenderAddon.addon_register_class
class render_settings(render_panel):
    """
    Render settings UI Panel
    """

    bl_label = 'LuxRender Render Settings'

    display_property_groups = [
        ( ('scene',), 'luxrender_rendermode', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxrender_integrator', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxrender_sampler', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxrender_volumeintegrator', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxrender_filter', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxrender_accelerator', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxrender_halt', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxcore_enginesettings', lambda: UseLuxCore() ),
    ]

    def draw(self, context):
        layout = self.layout
        engine_settings = context.scene.luxcore_enginesettings

        if not UseLuxCore():
            row = layout.row(align=True)
            rd = context.scene.render
            split = layout.split()
            row.menu("LUXRENDER_MT_presets_engine", text=bpy.types.LUXRENDER_MT_presets_engine.bl_label)
            row.operator("luxrender.preset_engine_add", text="", icon="ZOOMIN")
            row.operator("luxrender.preset_engine_add", text="", icon="ZOOMOUT").remove_active = True

        # Draw LuxCore stuff above settings defined via property group (device selection)
        # This is done here so the device enums are expanded properly (horizontal, not vertical)
        if UseLuxCore():
            # Advanced settings checkbox
            split = layout.split()

            row = split.row()
            sub = row.row()
            sub.label(text='')

            row = split.row()
            sub = row.row()
            sub.prop(engine_settings, 'advanced', toggle=True)

            # Device enums
            split = layout.split()

            row = split.row()
            sub = row.row()
            sub.label(text='Final Device:')

            row = split.row()
            sub = row.row()

            if engine_settings.renderengine_type in ['PATH', 'BIASPATH']:
                # These engines have OpenCL versions
                sub.prop(engine_settings, 'device', expand=True)
            else:
                # Face device enum, always disabled, to show that BIDIR and BIDIRVM only have CPU support
                sub.enabled = False
                sub.prop(engine_settings, 'device_cpu_only', expand=True)

            split = layout.split()

            row = split.row()
            sub = row.row()
            sub.label(text='Preview Device:')

            row = split.row()
            sub = row.row()

            if engine_settings.renderengine_type in ['PATH', 'BIASPATH']:
                # These engines have OpenCL versions
                sub.prop(engine_settings, 'device_preview', expand=True)
            else:
                # Face device enum, always disabled, to show that BIDIR and BIDIRVM only have CPU support
                sub.enabled = False
                sub.prop(engine_settings, 'device_cpu_only', expand=True)

            if engine_settings.renderengine_type == 'BIASPATH':
                split = layout.split()

                row = split.row()
                sub = row.row()
                sub.label(text='')

                row = split.row()
                sub = row.row()
                sub.prop(engine_settings, 'biaspath_show_sample_estimates', toggle=True)

                if engine_settings.biaspath_show_sample_estimates:
                    # Sample settings
                    aa = engine_settings.biaspath_sampling_aa_size
                    diffuse = engine_settings.biaspath_sampling_diffuse_size
                    glossy = engine_settings.biaspath_sampling_glossy_size
                    specular = engine_settings.biaspath_sampling_specular_size
                    # Pathdepth settings
                    depth_total = engine_settings.biaspath_pathdepth_total
                    depth_diffuse = engine_settings.biaspath_pathdepth_diffuse
                    depth_glossy = engine_settings.biaspath_pathdepth_glossy
                    depth_specular = engine_settings.biaspath_pathdepth_specular

                    # Pixel samples
                    aaSamplesCount = aa ** 2
                    layout.label(text='AA: %d' % aaSamplesCount)

                    # Diffuse samples
                    maxDiffusePathDepth = max(0, min(depth_total, depth_diffuse - 1))
                    diffuseSamplesCount = aaSamplesCount * (diffuse ** 2)
                    maxDiffuseSamplesCount = diffuseSamplesCount * maxDiffusePathDepth
                    layout.label(text='Diffuse: %d (with max. bounces %d: %d)' %
                                      (diffuseSamplesCount, maxDiffusePathDepth, maxDiffuseSamplesCount))

                    # Glossy samples
                    maxGlossyPathDepth = max(0, min(depth_total, depth_glossy - 1))
                    glossySamplesCount = aaSamplesCount * (glossy ** 2)
                    maxGlossySamplesCount = glossySamplesCount * maxGlossyPathDepth
                    layout.label(text='Glossy: %d (with max. bounces %d: %d)' %
                                      (glossySamplesCount, maxGlossyPathDepth, maxGlossySamplesCount))

                    # Specular samples
                    maxSpecularPathDepth = max(0, min(depth_total, depth_specular - 1))
                    specularSamplesCount = aaSamplesCount * (specular ** 2)
                    maxSpecularSamplesCount = specularSamplesCount * maxSpecularPathDepth
                    layout.label(text='Specular: %d (with max. bounces %d: %d)' %
                                      (specularSamplesCount, maxSpecularPathDepth, maxSpecularSamplesCount))

                    # Direct light samples # TODO: implement
                    #directLightSamplesCount = aaSamplesCount * firstVertexLightSampleCount *
                    #        (directLightSamples * directLightSamples) * renderConfig->scene->lightDefs.GetSize()
                    #SLG_LOG("[BiasPathCPURenderEngine] Direct light samples on first hit: " << directLightSamplesCount)

                    # Total samples for a pixel with hit on diffuse surfaces
                    layout.label(text='Total on diffuse surfaces: %d' %
                                      (maxDiffuseSamplesCount + diffuseSamplesCount * max(0, maxDiffusePathDepth - 1)))

                    '''
                    // Total samples for a pixel with hit on diffuse surfaces
                    SLG_LOG("[BiasPathCPURenderEngine] Total samples for a pixel with hit on diffuse surfaces: " <<
                            // Direct light sampling on first hit
                            directLightSamplesCount +
                            // Diffuse samples
                            maxDiffuseSamplesCount +
                            // Direct light sampling for diffuse samples
                            diffuseSamplesCount * Max<int>(0, maxDiffusePathDepth - 1));
                    '''


        # Draw property groups
        super().draw(context)


@LuxRenderAddon.addon_register_class
class device_settings(render_panel):
    """
    OpenCL Devices UI Panel
    """

    bl_label = 'LuxRender Compute Settings'

    def draw(self, context):
        engine_settings = context.scene.luxcore_enginesettings
        render_mode = context.scene.luxrender_rendermode.rendermode
    
        if (render_mode in ['hybridpath', 'luxcorepathocl', 'luxcorebiaspathocl'] and not UseLuxCore()) \
                or ((UseLuxCore() and (engine_settings.renderengine_type in ['PATH', 'BIASPATH']
                                       and engine_settings.device == 'OCL')
                or engine_settings.device_preview == 'OCL')):
            self.layout.operator('luxrender.opencl_device_list_update')
            # This is a "special" panel section for the list of OpenCL devices
            for dev_index in range(len(context.scene.luxcore_enginesettings.luxcore_opencl_devices)):
                dev = context.scene.luxcore_enginesettings.luxcore_opencl_devices[dev_index]
                row = self.layout.row()
                row.prop(dev, 'opencl_device_enabled', text="")
                subrow = row.row()
                subrow.enabled = dev.opencl_device_enabled
                subrow.label(dev.name)

        if UseLuxCore() and (engine_settings.renderengine_type in ['BIDIR', 'BIDIRVM']
                or engine_settings.device == 'CPU'
                or engine_settings.device_preview == 'CPU'):
            # LuxCore Threads
            #self.layout.prop(engine_settings, 'native_threads_count')

            if engine_settings.auto_threads:
                self.layout.prop(engine_settings, 'auto_threads')
            else:
                row = self.layout.row()
                sub = row.row()
                sub.prop(engine_settings, 'auto_threads')
                sub.prop(engine_settings, 'native_threads_count')

        if not UseLuxCore() and not 'ocl' in render_mode:
            # Classic Threads
            threads = context.scene.luxrender_engine
            row = self.layout.row()
            row.prop(threads, 'threads_auto')
            if not threads.threads_auto:
                row.prop(threads, 'threads')

        # Tile settings
        if context.scene.luxcore_enginesettings.renderengine_type == 'BIASPATH':
            self.layout.prop(engine_settings, 'tile_size')
			
@LuxRenderAddon.addon_register_class
class translator(render_panel):
    """
    Translator settings UI Panel
    """

    bl_label = 'LuxRender Export Settings'
    bl_options = {'DEFAULT_CLOSED'}

    display_property_groups = [
        ( ('scene',), 'luxcore_scenesettings', lambda: UseLuxCore() ),
        ( ('scene',), 'luxrender_engine', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxrender_testing', lambda: not UseLuxCore() ),
        ( ('scene',), 'luxcore_translatorsettings', lambda: UseLuxCore() ),
    ]

    def draw(self, context):
        if not UseLuxCore():
            super().draw(context)
            row = self.layout.row(align=True)
            rd = context.scene.render
        else:
            #self.layout.label("Note: not yet supported by LuxCore")
            super().draw(context)

@LuxRenderAddon.addon_register_class
class networking(render_panel):
    """
    Networking settings UI Panel
    """

    bl_label = 'LuxRender Networking'
    bl_options = {'DEFAULT_CLOSED'}

    display_property_groups = [
        ( ('scene',), 'luxrender_networking', lambda: not UseLuxCore() )
    ]

    def draw_header(self, context):
        if not UseLuxCore():
            self.layout.prop(context.scene.luxrender_networking, "use_network_servers", text="")

    def draw(self, context):
        if not UseLuxCore():
            row = self.layout.row(align=True)
            row.menu("LUXRENDER_MT_presets_networking", text=bpy.types.LUXRENDER_MT_presets_networking.bl_label)
            row.operator("luxrender.preset_networking_add", text="", icon="ZOOMIN")
            row.operator("luxrender.preset_networking_add", text="", icon="ZOOMOUT").remove_active = True
        else:
            self.layout.label("Note: not yet supported by LuxCore")

        super().draw(context)

@LuxRenderAddon.addon_register_class
class postprocessing(render_panel):
    """
    Post Pro UI panel
    """

    bl_label = 'Post Processing'
    bl_options = {'DEFAULT_CLOSED'}

    # We make our own post-pro panel so we can have one without BI's options
    # here. Theoretically, if Lux gains the ability to do lens effects through
    # the command line/API, we could add that here

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        split = layout.split()

        col = split.column()
        col.prop(rd, "use_compositing")
        col.prop(rd, "use_sequencer")

        split.prop(rd, "dither_intensity", text="Dither", slider=True)

@LuxRenderAddon.addon_register_class
class layer_selector(render_panel):
    """
    Render Layers Selector panel
    """

    bl_label = 'Layer Selector'
    bl_options = {'HIDE_HEADER'}
    bl_context = "render_layer"

    def draw(self, context):
        # Add in Blender's layer chooser, this is taken from Blender's startup/properties_render_layer.py
        layout = self.layout

        scene = context.scene
        rd = scene.render

        row = layout.row()
        row.template_list("RENDERLAYER_UL_renderlayers", "", rd, "layers", rd.layers, "active_index", rows=2)

        col = row.column(align=True)
        col.operator("scene.render_layer_add", icon='ZOOMIN', text="")
        col.operator("scene.render_layer_remove", icon='ZOOMOUT', text="")

        row = layout.row()
        rl = rd.layers.active
        if rl:
            row.prop(rl, "name")

        row.prop(rd, "use_single_layer", text="", icon_only=True)


@LuxRenderAddon.addon_register_class
class layers(render_panel):
    """
    Render Layers panel
    """

    bl_label = 'Layer'
    bl_context = "render_layer"

    def draw(self, context):
        # Add in Blender's layer stuff, this is taken from Blender's startup/properties_render_layer.py
        layout = self.layout

        scene = context.scene
        rd = scene.render
        rl = rd.layers.active

        split = layout.split()

        col = split.column()
        col.prop(scene, "layers", text="Scene")
        col.label(text="")
        col = split.column()
        col.prop(rl, "layers", text="Layer")

@LuxRenderAddon.addon_register_class
class passes_lg(render_panel):
    """
    Render passes UI panel
    """

    bl_label = 'LuxRender Lightgroups'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "render_layer"

    display_property_groups = [
        ( ('scene',), 'luxrender_lightgroups' )
    ]

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        super().draw(context)

        # Light groups, this is a "special" panel section
        for lg_index in range(len(context.scene.luxrender_lightgroups.lightgroups)):
            lg = context.scene.luxrender_lightgroups.lightgroups[lg_index]
            row = self.layout.row()
            row.prop(lg, 'lg_enabled', text="")
            subrow = row.row()
            subrow.enabled = lg.lg_enabled
            subrow.prop(lg, 'name', text="")

            for control in lg.controls:
                self.draw_column(
                    control,
                    subrow.column(),
                    lg,
                    context,
                    property_group=lg
                )

            row.operator('luxrender.lightgroup_remove', text="", icon="ZOOMOUT").lg_index = lg_index

        layout.separator()  # give a little gap to seperate next panel

@LuxRenderAddon.addon_register_class
class passes_aov(render_panel):
    """
    Render passes UI panel
    """

    bl_label = 'LuxRender Passes'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "render_layer"

    display_property_groups = [
        ( ('scene',), 'luxrender_lightgroups' )
    ]

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if UseLuxCore():
            # Show AOV channel panel
            channels = context.scene.luxrender_channels
            split = layout.split()
            col = split.column()

            for control in channels.controls:
                self.draw_column(
                    control,
                    col,
                    channels,
                    context,
                    property_group=channels
                )
        else:
            # Add in the relevant bits from Blender's passes stuff, this is
            # taken from Blender's startup/properties_render_layer.py
            rd = scene.render
            rl = rd.layers.active
            split = layout.split()
            col = split.column()
            col.label(text="Passes:")
            col.prop(rl, "use_pass_combined")
            col.prop(rl, "use_pass_z")

        layout.separator()  # give a little gap to seperate next panel

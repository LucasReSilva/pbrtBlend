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
import bl_ui
import bpy

from ..extensions_framework.ui import property_group_renderer

from ..outputs.luxcore_api import UseLuxCore
from .. import LuxRenderAddon
from ..export import get_worldscale


class camera_panel(bl_ui.properties_data_camera.CameraButtonsPanel, property_group_renderer):
    COMPAT_ENGINES = 'LUXRENDER_RENDER'


@LuxRenderAddon.addon_register_class
class camera(camera_panel):
    bl_label = 'LuxRender Camera'

    display_property_groups = [
        ( ('camera',), 'luxrender_camera' ),
    ]

    def draw(self, context):
        layout = self.layout
        blender_cam = context.camera
        lux_cam = context.camera.luxrender_camera

        # Draw property groups
        super().draw(context)

        if lux_cam.use_dof and not lux_cam.usemblur:
            # mblur already has a trailing separator if enabled
            layout.separator()

        layout.prop(lux_cam, "use_dof", toggle=True)

        if lux_cam.use_dof:
            split = layout.split()

            column = split.column()
            column.label("Focus:")
            column.prop(lux_cam, "autofocus")

            # Disable "Distance" and "Object" settings if autofocus is used
            sub_autofocus = column.column()
            sub_autofocus.enabled = not lux_cam.autofocus
            sub_autofocus.prop(blender_cam, "dof_object", text="")

            # Disable "Distance" setting if a focus object is used
            sub_distance = sub_autofocus.row()
            sub_distance.enabled = blender_cam.dof_object is None
            sub_distance.prop(blender_cam, "dof_distance", text="Distance")

            column = split.column(align=True)
            column.enabled = not UseLuxCore()
            column.label("Bokeh Shape:")

            if UseLuxCore():
                column.label("No LuxCore support", icon="INFO")
            else:
                sub_bokeh = column.column()
                sub_bokeh.prop(lux_cam, "blades", text="Blades")
                sub_bokeh.prop(lux_cam, "distribution", text="")
                sub_bokeh.prop(lux_cam, "power", text="Power")

        if UseLuxCore():
            if lux_cam.enable_clipping_plane or lux_cam.use_dof:
                layout.separator()

            layout.prop(lux_cam, "enable_clipping_plane", toggle=True)

            if lux_cam.enable_clipping_plane:
                layout.prop_search(lux_cam, "clipping_plane_obj", context.scene, "objects", text="Plane")


@LuxRenderAddon.addon_register_class
class film(camera_panel):
    bl_label = 'LuxRender Film'

    display_property_groups = [
        ( ('camera', 'luxrender_camera'), 'luxrender_film', lambda: not UseLuxCore() ),
        ( ('camera', 'luxrender_camera', 'luxrender_film'), 'luxrender_colorspace', lambda: not UseLuxCore() ),
        ( ('camera', 'luxrender_camera', 'luxrender_film'), 'luxrender_tonemapping', lambda: not UseLuxCore() ),
        ( ('camera', 'luxrender_camera'), 'luxcore_imagepipeline_settings', lambda: UseLuxCore() ),
    ]

    def draw_crf_preset_menu(self, context):
        if UseLuxCore():
            self.layout.menu('IMAGEPIPELINE_MT_luxrender_crf',
                         text=context.camera.luxrender_camera.luxcore_imagepipeline_settings.crf_preset)
        else:
            self.layout.menu('CAMERA_MT_luxrender_crf',
                         text=context.camera.luxrender_camera.luxrender_film.luxrender_colorspace.crf_preset)

    def draw(self, context):
        super().draw(context)

        if UseLuxCore():
            imagepipeline_settings = context.scene.camera.data.luxrender_camera.luxcore_imagepipeline_settings
            self.layout.label('Framerate: %d fps' % (1 / (imagepipeline_settings.viewport_interval / 1000)))

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

from extensions_framework.ui import property_group_renderer

from .. import LuxRenderAddon

class render_panel(bl_ui.properties_render.RenderButtonsPanel, property_group_renderer):
	'''
	Base class for render engine settings panels
	'''
	
	COMPAT_ENGINES = {LuxRenderAddon.BL_IDNAME}

@LuxRenderAddon.addon_register_class
class engine(render_panel):
	'''
	Engine settings UI Panel
	'''
	
	bl_label = 'LuxRender Engine Configuration'
	
	display_property_groups = [
		( ('scene',), 'luxrender_engine' )
	]
	
	def draw(self, context):
		row = self.layout.row(align=True)
		row.menu("LUXRENDER_MT_presets_engine", text=bpy.types.LUXRENDER_MT_presets_engine.bl_label)
		row.operator("luxrender.preset_engine_add", text="", icon="ZOOMIN")
		row.operator("luxrender.preset_engine_add", text="", icon="ZOOMOUT").remove_active = True
		
		super().draw(context)
		
@LuxRenderAddon.addon_register_class
class render_settings(render_panel):
	'''
	Render settings UI Panel
	'''
	
	bl_label = 'LuxRender Render Settings'
	
	display_property_groups = [
		( ('scene',), 'luxrender_rendermode' ),
		( ('scene',), 'luxrender_integrator' ),
		( ('scene',), 'luxrender_sampler' ),
		( ('scene',), 'luxrender_volumeintegrator' ),
		( ('scene',), 'luxrender_filter' ),
		( ('scene',), 'luxrender_accelerator' ),
		( ('scene',), 'luxrender_halt' ),
	]
	
@LuxRenderAddon.addon_register_class
class testing(render_panel):
	bl_label = 'LuxRender Test/Debugging Options'
	bl_options = {'DEFAULT_CLOSED'}
	
	display_property_groups = [
		( ('scene',), 'luxrender_testing' )
	]

@LuxRenderAddon.addon_register_class
class networking(render_panel):
	'''
	Networking settings UI Panel
	'''
	
	bl_label = 'LuxRender Networking'
	bl_options = {'DEFAULT_CLOSED'}
	
	display_property_groups = [
		( ('scene',), 'luxrender_networking' )
	]
	
	def draw_header(self, context):
		self.layout.prop(context.scene.luxrender_networking, "use_network_servers", text="")
	
	def draw(self, context):
		row = self.layout.row(align=True)
		row.menu("LUXRENDER_MT_presets_networking", text=bpy.types.LUXRENDER_MT_presets_networking.bl_label)
		row.operator("luxrender.preset_networking_add", text="", icon="ZOOMIN")
		row.operator("luxrender.preset_networking_add", text="", icon="ZOOMOUT").remove_active = True
		
		super().draw(context)

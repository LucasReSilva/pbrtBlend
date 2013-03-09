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
	
	COMPAT_ENGINES = 'LUXRENDER_RENDER'

@LuxRenderAddon.addon_register_class
class layers(render_panel):
	'''
	Render Layers UI panel
	'''
	
	bl_label = 'Layers'
	bl_options = {'DEFAULT_CLOSED'}
	
	display_property_groups = [
		( ('scene',), 'luxrender_lightgroups' )
	]
	
	def draw(self, context): 
		#Add in Blender's layer stuff, this taken from Blender's startup/properties_render.py
		layout = self.layout

		scene = context.scene
		rd = scene.render

		row = layout.row()
		if bpy.app.version < (2, 65, 3 ):
			row.template_list(rd, "layers", rd.layers, "active_index", rows=2)
		else:
			row.template_list("RENDER_UL_renderlayers", "", rd, "layers", rd.layers, "active_index", rows=2)


		col = row.column(align=True)
		col.operator("scene.render_layer_add", icon='ZOOMIN', text="")
		col.operator("scene.render_layer_remove", icon='ZOOMOUT', text="")

		row = layout.row()
		rl = rd.layers.active
		if rl:
			row.prop(rl, "name")

		row.prop(rd, "use_single_layer", text="", icon_only=True)
		
		split = layout.split()

		col = split.column()
		col.prop(scene, "layers", text="Scene")
		col.label(text="")
		col = split.column()
		col.prop(rl, "layers", text="Layer")
		
		split = layout.split()

		col = split.column()
		col.label(text="Passes:")
		col.prop(rl, "use_pass_combined")
		col.prop(rl, "use_pass_z")
		
		super().draw(context)
		
		#Light groups, this is a "special" panel section
		for lg_index in range(len(context.scene.luxrender_lightgroups.lightgroups)):
			lg = context.scene.luxrender_lightgroups.lightgroups[lg_index]
			row = self.layout.row()
			row.prop(lg, 'lg_enabled', text="")
			subrow=row.row()
			subrow.enabled = lg.lg_enabled
			subrow.prop(lg, 'name', text="")
			# Here we draw the currently selected luxrender_volumes_data property group
			for control in lg.controls:
				self.draw_column(
					control,
					subrow.column(),
					lg,
					context,
					property_group = lg
				)
			row.operator('luxrender.lightgroup_remove', text="", icon="ZOOMOUT").lg_index=lg_index
			
@LuxRenderAddon.addon_register_class
class postprocessing(render_panel):
	'''
	Post Pro UI panel
	'''
	
	bl_label = 'Post Processing'
	bl_options = {'DEFAULT_CLOSED'}

	
	#We make our own post-pro panel so we can have one without BI's option here. Theoretically, if Lux gains the ability to do lens effects through the command line/API, we could add that here
	
	def draw(self, context):
		layout = self.layout

		rd = context.scene.render

		split = layout.split()

		col = split.column()
		col.prop(rd, "use_compositing")
		col.prop(rd, "use_sequencer")

		split.prop(rd, "dither_intensity", text="Dither", slider=True)
	
@LuxRenderAddon.addon_register_class
class engine(render_panel):
	'''
	Engine settings UI Panel
	'''
	
	bl_label = 'LuxRender Engine Configuration'
	bl_options = {'DEFAULT_CLOSED'}
	
	display_property_groups = [
		( ('scene',), 'luxrender_engine' )
	]
	
	def draw(self, context):
		super().draw(context)
		
		row = self.layout.row(align=True)
		rd = context.scene.render
		if bpy.app.version < (2, 63, 19 ):
			row.prop(rd, "use_color_management")
			if rd.use_color_management == True:
				row.prop(rd, "use_color_unpremultiply")
		
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
	
	def draw(self, context):
		row = self.layout.row(align=True)
		rd = context.scene.render
		split = self.layout.split()
		row.menu("LUXRENDER_MT_presets_engine", text=bpy.types.LUXRENDER_MT_presets_engine.bl_label)
		row.operator("luxrender.preset_engine_add", text="", icon="ZOOMIN")
		row.operator("luxrender.preset_engine_add", text="", icon="ZOOMOUT").remove_active = True
		
		super().draw(context)
	
	
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

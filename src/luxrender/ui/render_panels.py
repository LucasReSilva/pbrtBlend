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
import bpy
from properties_render import RenderButtonsPanel

from extensions_framework.ui import property_group_renderer

class render_described_context(RenderButtonsPanel, property_group_renderer):
	'''
	Base class for render engine settings panels
	'''
	
	COMPAT_ENGINES = {'luxrender'}

@bpy.utils.register_class
class engine(render_described_context, bpy.types.Panel):
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

@bpy.utils.register_class
class sampler(render_described_context, bpy.types.Panel):
	'''
	Sampler settings UI Panel
	'''
	
	bl_label = 'Sampler'
	
	display_property_groups = [
		( ('scene',), 'luxrender_sampler' )
	]

@bpy.utils.register_class
class integrator(render_described_context, bpy.types.Panel):
	'''
	Surface Integrator settings UI Panel
	'''
	
	bl_label = 'Surface Integrator'
	
	display_property_groups = [
		( ('scene',), 'luxrender_integrator' )
	]

@bpy.utils.register_class
class volume(render_described_context, bpy.types.Panel):
	'''
	Volume Integrator settings UI panel
	'''
	
	bl_label = 'Volume Integrator'
	bl_options = 'DEFAULT_CLOSED'
	
	display_property_groups = [
		( ('scene',), 'luxrender_volumeintegrator' )
	]

@bpy.utils.register_class
class filter(render_described_context, bpy.types.Panel):
	'''
	PixelFilter settings UI Panel
	'''
	
	bl_label = 'Filter'
	bl_options = 'DEFAULT_CLOSED'
	
	display_property_groups = [
		( ('scene',), 'luxrender_filter' )
	]

@bpy.utils.register_class
class accelerator(render_described_context, bpy.types.Panel):
	'''
	Accelerator settings UI Panel
	'''
	
	bl_label = 'Accelerator'
	bl_options = 'DEFAULT_CLOSED'
	
	display_property_groups = [
		( ('scene',), 'luxrender_accelerator' )
	]

@bpy.utils.register_class
class networking(render_described_context, bpy.types.Panel):
	'''
	Networking settings UI Panel
	'''
	
	bl_label = 'LuxRender Networking'
	bl_options = 'DEFAULT_CLOSED'
	
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

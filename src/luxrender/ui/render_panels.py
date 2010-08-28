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
import bpy
from properties_render import RenderButtonsPanel

from ef.ui import property_group_renderer

class render_described_context(RenderButtonsPanel, property_group_renderer):
	'''
	Base class for render engine settings panels
	'''
	
	COMPAT_ENGINES = {'luxrender'}

class engine(render_described_context, bpy.types.Panel):
	'''
	Engine settings UI Panel
	'''
	
	bl_label = 'LuxRender Engine Configuration'
	
	display_property_groups = [
		( ('scene',), 'luxrender_engine' )
	]

class sampler(render_described_context, bpy.types.Panel):
	'''
	Sampler settings UI Panel
	'''
	
	bl_label = 'Sampler'
	
	display_property_groups = [
		( ('scene',), 'luxrender_sampler' )
	]

class integrator(render_described_context, bpy.types.Panel):
	'''
	Surface Integrator settings UI Panel
	'''
	
	bl_label = 'Surface Integrator'
	
	display_property_groups = [
		( ('scene',), 'luxrender_integrator' )
	]

class volume(render_described_context, bpy.types.Panel):
	'''
	Volume Integrator settings UI panel
	'''
	
	bl_label = 'Volume Integrator'
	
	display_property_groups = [
		( ('scene',), 'luxrender_volume' )
	]

class filter(render_described_context, bpy.types.Panel):
	'''
	PixelFilter settings UI Panel
	'''
	
	bl_label = 'Filter'
	
	display_property_groups = [
		( ('scene',), 'luxrender_filter' )
	]

class accelerator(render_described_context, bpy.types.Panel):
	'''
	Accelerator settings UI Panel
	'''
	
	bl_label = 'Accelerator'
	
	display_property_groups = [
		( ('scene',), 'luxrender_accelerator' )
	]

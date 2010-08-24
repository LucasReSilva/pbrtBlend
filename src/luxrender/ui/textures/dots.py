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

from ...export import ParamSet
from ...export.materials import add_texture_parameter
from ...outputs import LuxManager
from ...properties.texture import FloatTextureParameter
from ..textures import luxrender_texture_base

class dots(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		dots_params = ParamSet()
			
		dots_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'inside', self.variant, self)
		)
		dots_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'outside', self.variant, self)
		)
		
		return {'2DMAPPING'}, dots_params

inside	= FloatTextureParameter('texture', 'inside', 'inside', 'dots', default=1.0, min=0.0, max=100.0)
outside	= FloatTextureParameter('texture', 'outside', 'outside', 'dots', default=0.0, min=0.0, max=100.0)

class ui_panel_dots(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender Dots Texture'
	
	LUX_COMPAT = {'dots'}
	
	property_group = dots
	
	controls = [
		# None
	] + \
	inside.get_controls() + \
	outside.get_controls()
	
	visibility = {
		'inside_usefloattexture':		{ 'variant': 'float' },
		'inside_floatvalue':			{ 'variant': 'float' },
		'inside_floattexture':			{ 'variant': 'float', 'inside_usefloattexture': True },
		
		'outside_usefloattexture':		{ 'variant': 'float' },
		'outside_floatvalue':			{ 'variant': 'float' },
		'outside_floattexture':			{ 'variant': 'float', 'outside_usefloattexture': True },
	} 
	
	properties = [
		{
			'attr': 'variant',
			'type': 'string',
			'default': 'float'
		},
	] + \
	inside.get_properties() + \
	outside.get_properties()

	
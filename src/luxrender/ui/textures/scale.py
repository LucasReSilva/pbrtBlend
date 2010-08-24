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
from ...properties.texture import ColorTextureParameter, FloatTextureParameter
from ..textures import luxrender_texture_base

class scale(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		scale_params = ParamSet()
		
		scale_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex1', self.variant, self)
		)
		scale_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex2', self.variant, self)
		)
		
		return set(), scale_params

tex1_f		= FloatTextureParameter('texture', 'tex1', 'tex1', 'scale', default=1.0, min=0.0, max=100.0)
tex1_c		= ColorTextureParameter('texture', 'tex1', 'tex1', 'scale', default=(1.0,1.0,1.0))
tex2_f		= FloatTextureParameter('texture', 'tex2', 'tex2', 'scale', default=0.0, min=0.0, max=100.0)
tex2_c		= ColorTextureParameter('texture', 'tex2', 'tex2', 'scale', default=(0.0,0.0,0.0))

class ui_panel_scale(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender scale Texture'
	
	LUX_COMPAT = {'scale'}
	
	property_group = scale
	
	controls = [
		'variant',
		
	] + \
	tex1_f.get_controls() + \
	tex1_c.get_controls() + \
	tex2_f.get_controls() + \
	tex2_c.get_controls()
	
	# Visibility we do manually because of the variant switch
	visibility = {
		'tex1_colorlabel':				{ 'variant': 'color' },
		'tex1_color': 					{ 'variant': 'color' },
		'tex1_usecolortexture':			{ 'variant': 'color' },
		'tex1_colortexture':			{ 'variant': 'color', 'tex1_usecolortexture': True },
		
		'tex1_usefloattexture':			{ 'variant': 'float' },
		'tex1_floatvalue':				{ 'variant': 'float' },
		'tex1_floattexture':			{ 'variant': 'float', 'tex1_usefloattexture': True },
		
		
		'tex2_colorlabel':				{ 'variant': 'color' },
		'tex2_color': 					{ 'variant': 'color' },
		'tex2_usecolortexture':			{ 'variant': 'color' },
		'tex2_colortexture':			{ 'variant': 'color', 'tex2_usecolortexture': True },
		
		'tex2_usefloattexture':			{ 'variant': 'float' },
		'tex2_floatvalue':				{ 'variant': 'float' },
		'tex2_floattexture':			{ 'variant': 'float', 'tex2_usefloattexture': True },
	}
	
	properties = [
		{
			'attr': 'variant',
			'type': 'enum',
			'name': 'Variant',
			'items': [
				('float', 'Float', 'float'),
				('color', 'Color', 'color'),
			],
			'expand': True
		},
	] + \
	tex1_f.get_properties() + \
	tex1_c.get_properties() + \
	tex2_f.get_properties() + \
	tex2_c.get_properties()
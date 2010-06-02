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
from ...module import LuxManager
from ...properties.texture import FloatTextureParameter
from ..textures import luxrender_texture_base

class checkerboard(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		checkerboard_params = ParamSet() \
			.add_string('aamode', self.aamode) \
			.add_integer('dimension', self.dimension)
		
		checkerboard_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex1', self.variant, self)
		)
		checkerboard_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex2', self.variant, self)
		)
		
		if self.dimension == 2:
			features = {'2DMAPPING'}
		else:
			features = {'3DMAPPING'}
		
		return features, checkerboard_params

tex1 = FloatTextureParameter('texture', 'tex1', 'Texture 1', 'checkerboard', default=1.0, min=0.0, max=100.0)
tex2 = FloatTextureParameter('texture', 'tex2', 'Texture 2', 'checkerboard', default=0.0, min=0.0, max=100.0)

class ui_panel_checkerboard(luxrender_texture_base):
	bl_label = 'LuxRender Checkerboard Texture'
	
	LUX_COMPAT = {'checkerboard'}
	
	property_group = checkerboard
	
	controls = [
		'aamode',
		'dimension',
	] + \
	tex1.get_controls() + \
	tex2.get_controls()
	
	visibility = {
		'tex1_floattexture':	{ 'tex1_usefloattexture': True },
		'tex2_floattexture':	{ 'tex2_usefloattexture': True },
	}
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'float'
		},
		{
			'attr': 'aamode',
			'type': 'enum',
			'name': 'Anti-Alias Mode',
			'default': 'closedform',
			'items': [
				('closedform', 'closedform', 'closedform'),
				('supersample', 'supersample', 'supersample'),
				('none', 'none', 'none')
			]
		},
		{
			'attr': 'dimension',
			'type': 'int',
			'name': 'Dimensions',
			'default': 2,
			'min': 2,
			'soft_min': 2,
			'max': 3,
			'soft_max': 3,
		},
		
	] + \
	tex1.get_properties() + \
	tex2.get_properties()


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
from ..textures import luxrender_texture_base

class bilerp(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		if self.variant == 'float':
			params = ParamSet() \
				.add_float('v00', self.v00_f) \
				.add_float('v10', self.v10_f) \
				.add_float('v01', self.v01_f) \
				.add_float('v11', self.v11_f)
		else:
			params = ParamSet() \
				.add_color('v00', self.v00_c) \
				.add_color('v10', self.v10_c) \
				.add_color('v01', self.v01_c) \
				.add_color('v11', self.v11_c)
				
		return {'2DMAPPING'}, params

class ui_panel_bilerp(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender BiLerp Texture'
	
	LUX_COMPAT = {'bilerp'}
	
	property_group = bilerp
	
	controls = [
		'variant',
		['v00_f', 'v10_f'],
		['v01_f', 'v11_f'],
		
		['v00_c', 'v10_c'],
		['v01_c', 'v11_c'],
	]
	
	visibility = {
		'v00_f':			{ 'variant': 'float' },
		'v01_f':			{ 'variant': 'float' },
		'v10_f':			{ 'variant': 'float' },
		'v11_f':			{ 'variant': 'float' },
		
		'v00_c':			{ 'variant': 'color' },
		'v01_c':			{ 'variant': 'color' },
		'v10_c':			{ 'variant': 'color' },
		'v11_c':			{ 'variant': 'color' },
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
		{
			'attr': 'v00_f',
			'type': 'float',
			'name': '(0,0)',
			'default': 0.0
		},
		{
			'attr': 'v01_f',
			'type': 'float',
			'name': '(0,1)',
			'default': 1.0
		},
		{
			'attr': 'v10_f',
			'type': 'float',
			'name': '(1,0)',
			'default': 0.0
		},
		{
			'attr': 'v11_f',
			'type': 'float',
			'name': '(1,1)',
			'default': 1.0
		},
		
		{
			'attr': 'v00_c',
			'type': 'float_vector',
			'subtype': 'COLOR',
			'name': '(0,0)',
			'default': (0.0, 0.0, 0.0)
		},
		{
			'attr': 'v01_c',
			'type': 'float_vector',
			'subtype': 'COLOR',
			'name': '(0,1)',
			'default': (1.0, 1.0, 1.0)
		},
		{
			'attr': 'v10_c',
			'type': 'float_vector',
			'subtype': 'COLOR',
			'name': '(1,0)',
			'default': (0.0, 0.0, 0.0)
		},
		{
			'attr': 'v11_c',
			'type': 'float_vector',
			'subtype': 'COLOR',
			'name': '(1,1)',
			'default': (1.0, 1.0, 1.0)
		},
	]

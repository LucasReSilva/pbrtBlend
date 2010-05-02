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

from ef.validate import Logic_OR as O

from ..textures import luxrender_texture_base

class mapping(bpy.types.IDPropertyGroup):
	pass

class ui_panel_mapping(luxrender_texture_base):
	bl_label = 'LuxRender Texture Mapping'
	
	LUX_COMPAT = {'bilerp', 'checkerboard', 'dots', 'imagemap', 'uv'}
	
	property_group = mapping
	
	controls = [
		'type',
		['uscale', 'vscale'],
		['udelta', 'vdelta'],
		'v1', 'v2',
	]
	
	visibility = {
		'v1':				{ 'type': 'planar' },
		'v2':				{ 'type': 'planar' },
		'uscale':			{ 'type': O(['uv', 'spherical', 'cylindrical']) },
		'vscale':			{ 'type': O(['uv', 'spherical']) },
		# 'udelta': # always visible
		'vdelta':			{ 'type': O(['uv', 'spherical', 'planar']) },
	}
	
	properties = [
		{
			'attr': 'type',
			'type': 'enum',
			'name': 'Mapping Type',
			'items': [
				('uv','uv','uv'),
				('planar','planar','planar'),
				('spherical','spherical','spherical'),
				('cylindrical','cylindrical','cylindrical'),
			]
		},
		{
			'attr': 'uscale',
			'type': 'float',
			'name': 'U Scale',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
		},
		{
			'attr': 'vscale',
			'type': 'float',
			'name': 'V Scale',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
		},
		{
			'attr': 'udelta',
			'type': 'float',
			'name': 'U Offset',
			'default': 0.0,
		},
		{
			'attr': 'vdelta',
			'type': 'float',
			'name': 'V Offset',
			'default': 0.0,
		},
		{
			'attr': 'v1',
			'type': 'float_vector',
			'name': 'V1',
			'default': (1.0, 0.0, 0.0),
		},
		{
			'attr': 'v2',
			'type': 'float_vector',
			'name': 'V2',
			'default': (0.0, 1.0, 0.0),
		},
	]

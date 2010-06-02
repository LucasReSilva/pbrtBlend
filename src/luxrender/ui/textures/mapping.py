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

from ...export import ParamSet
from ..textures import luxrender_texture_base

class mapping(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		mapping_params = ParamSet()
		
		mapping_params.add_string('mapping', self.type)
		mapping_params.add_float('udelta', self.udelta)
		
		if self.type == 'planar':
			mapping_params.add_vector('v1', self.v1)
			mapping_params.add_vector('v2', self.v2)
			
		if self.type in {'uv', 'spherical', 'cylindrical'}:
			mapping_params.add_float('uscale', self.uscale)
			
		if self.type in {'uv', 'spherical'}:
			mapping_params.add_float('vscale', self.vscale)
			
		if self.type in {'uv', 'spherical', 'planar'}:
			mapping_params.add_float('vdelta', self.vdelta)
		
		return mapping_params

class ui_panel_mapping(luxrender_texture_base):
	bl_label = 'LuxRender Texture Mapping'
	bl_default_closed = True
	bl_show_header = True
	
	LUX_COMPAT = {'bilerp', 'checkerboard', 'dots', 'imagemap', 'uv', 'uvmask'}
	
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
			'min': -100.0,
			'soft_min': -100.0,
			'max': 100.0,
			'soft_max': 100.0
		},
		{
			'attr': 'vscale',
			'type': 'float',
			'name': 'V Scale',
			'default': -1.0,
			'min': -100.0,
			'soft_min': -100.0,
			'max': 100.0,
			'soft_max': 100.0
		},
		{
			'attr': 'udelta',
			'type': 'float',
			'name': 'U Offset',
			'default': 0.0,
			'min': -100.0,
			'soft_min': -100.0,
			'max': 100.0,
			'soft_max': 100.0
		},
		{
			'attr': 'vdelta',
			'type': 'float',
			'name': 'V Offset',
			'default': 0.0,
			'min': -100.0,
			'soft_min': -100.0,
			'max': 100.0,
			'soft_max': 100.0
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

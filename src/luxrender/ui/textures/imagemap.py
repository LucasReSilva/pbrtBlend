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

from ef.util import util as efutil

from ...export import ParamSet
from ..textures import luxrender_texture_base

class imagemap(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		params = ParamSet()
		
		params.add_string('filename', efutil.path_relative_to_export(self.filename) ) \
			  .add_integer('discardmipmaps', self.discardmipmaps) \
			  .add_string('filtertype', self.filtertype) \
			  .add_float('gain', self.gain) \
			  .add_float('gamma', self.gamma) \
			  .add_float('maxanisotropy', self.maxanisotropy) \
			  .add_string('wrap', self.wrap)
		
		if self.variant == 'float':
			params.add_string('channel', self.channel)
		
		return {'2DMAPPING'}, params

class ui_panel_imagemap(luxrender_texture_base):
	bl_label = 'LuxRender Imagemap Texture'
	
	LUX_COMPAT = {'imagemap'}
	
	property_group = imagemap
	
	controls = [
		'variant',
		'filename',
		'channel',
		'discardmipmaps',
		'filtertype',
		'gain',
		'gamma',
		'maxanisotropy',
		'wrap',
	]
	
	visibility = {
		'channel':				{ 'variant': 'float' },
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
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'filename',
			'name': 'File Name'
		},
		{
			'type': 'enum',
			'attr': 'channel',
			'name': 'Channel',
			'items': [
				('mean', 'mean', 'mean'),
				('red', 'red', 'red'),
				('green', 'green', 'green'),
				('blue', 'blue', 'blue'),
				('alpha', 'alpha', 'alpha'),
				('colored_mean', 'colored_mean', 'colored_mean')
			]
		},
		{
			'type': 'int',
			'attr': 'discardmipmaps',
			'name': 'Discard MipMaps below',
			'description': 'Set to 0 to disable',
			'default': 0,
			'min': 0
		},
		{
			'type': 'enum',
			'attr': 'filtertype',
			'name': 'Filter type',
			'items': [
				('bilinear', 'bilinear', 'bilinear'),
				('mipmap_trilinear', 'MipMap Trilinear', 'mipmap_trilinear'),
				('mipmap_ewa', 'MipMap EWA', 'mipmap_ewa'),
				('nearest', 'nearest', 'nearest'),
			],
		},
		{
			'type': 'float',
			'attr': 'gain',
			'name': 'Gain',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'type': 'float',
			'attr': 'gamma',
			'name': 'Gamma',
			'default': 2.2,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 6.0,
			'soft_max': 6.0
		},
		{
			'type': 'float',
			'attr': 'maxanisotropy',
			'name': 'Max. Anisotropy',
			'default': 8.0,
		},
		{
			'type': 'enum',
			'attr': 'wrap',
			'name': 'Wrapping',
			'items': [
				('repeat', 'repeat', 'repeat'),
				('black', 'black', 'black'),
				('white', 'white', 'white'),
				('clamp', 'clamp', 'clamp')
			]
		},
	]
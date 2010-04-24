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
from ef.validate import Logic_AND as A, Logic_OR as O, Logic_Operator as OP

def has_property(property_name):
	'''
	Refer to http://www.luxrender.net/static/materials-parameters.xhtml
	for contents of this mapping
	'''
	
	map = {
		'amount':			O(['mix']),
		'architectural':	O(['glass', 'glass2']),
		'bumpmap':			O(['carpaint', 'glass', 'glass2', 'glossy_lossy', 'glossy', 'matte', 'mattetranslucent', 'metal', 'mirror', 'roughglass', 'shinymetal']),
		'cauchyb':			O(['glass', 'roughglass']),
		'd':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'dispersion':		O(['glass2']),
		'film':				O(['glass', 'mirror', 'shinymetal']),
		'filmindex':		O(['glass', 'mirror', 'shinymetal']),
		'index':			O(['glass', 'glossy_lossy', 'glossy', 'roughglass']),
		'Ka':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'Kd':				O(['carpaint', 'glossy_lossy', 'glossy', 'matte']),
		'Kr':				O(['glass', 'mattetranslucent', 'mirror', 'roughglass', 'shinymetal']),
		'Ks':				O(['glossy_lossy', 'glossy', 'shinymetal']),
		'Ks1':				O(['carpaint']),
		'Ks2':				O(['carpaint']),
		'Ks3':				O(['carpaint']),
		'Kt':				O(['glass', 'mattetranslucent', 'roughglass']),
		'M1':				O(['carpaint']),
		'M2':				O(['carpaint']),
		'M3':				O(['carpaint']),
		'name':				O(['carpaint', 'metal']),
		'namedmaterial1':	O(['mix']),
		'namedmaterial2':	O(['mix']),
		'R1':				O(['carpaint']),
		'R2':				O(['carpaint']),
		'R3':				O(['carpaint']),
		'sigma':			O(['matte', 'mattetranslucent']),
		'uroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
		'vroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
	}
	
	return map[property_name]

class ColorTexture(object):
	attr			= None
	name			= None
	property_group	= None
	
	def __init__(self, attr, name, property_group):
		self.attr = attr
		self.name = name
		self.property_group = property_group
	
	def get_controls(self):
		return [
			[ 0.9, ['%s_label' % self.attr, self.attr], '%s_usetexture' % self.attr ],
			'%s_texture' % self.attr
		]
	
	def get_visibility(self):
		return {
			'%s_label' % self.attr: 			{ 'material': has_property(self.attr) },
			self.attr: 							{ 'material': has_property(self.attr) },
			'%s_usetexture' % self.attr:		{ 'material': has_property(self.attr) },
			'%s_texture' % self.attr:			{ 'material': has_property(self.attr), '%s_usetexture' % self.attr: True },
		}
	
	def get_properties(self):
		return [
			{
				'attr': '%s_usetexture' % self.attr,
				'type': 'bool',
				'name': 'T',
				'description': 'Textured %s' % self.name,
				'default': False,
				'toggle': True,
			},
			{
				'type': 'text',
				'attr': '%s_label' % self.attr,
				'name': self.name
			},
			{
				'type': 'float_vector',
				'attr': self.attr,
				'name': '', #self.name,
				'description': self.name,
				'default': (0.8,0.8,0.8),
				'subtype': 'COLOR',
			},
			{
				'attr': '%s_texturename' % self.attr,
				'type': 'string',
				'name': '%s_texturename' % self.attr,
				'description': '%s Texture' % self.name,
			},
			{
				'type': 'prop_object',
				'attr': '%s_texture' % self.attr,
				'src': lambda s,c: s.object.material_slots[s.object.active_material_index].material,
				'src_attr': 'texture_slots',
				'trg': lambda s,c: getattr(c, self.property_group),
				'trg_attr': '%s_texturename' % self.attr,
				'name': self.name
			},
		]

class FloatTexture(object):
	attr			= None
	name			= None
	property_group	= None
	default			= 0.0
	min				= 0.0
	max				= 1.0
	precision		= 3
	
	def __init__(self,
			attr, name, property_group,
			default = 0.0, min = 0.0, max = 1.0, precision=3
		):
		self.attr = attr
		self.name = name
		self.property_group = property_group
		self.default = default
		self.min = min
		self.max = max
		self.precision = precision
	
	def get_controls(self):
		return [
			[0.9, '%s_floatvalue' % self.attr, '%s_usetexture' % self.attr],
			'%s_texture' % self.attr,
		]
	
	def get_visibility(self):
		return {
			'%s_usetexture' % self.attr:		{ 'material': has_property(self.attr) },
			'%s_floatvalue' % self.attr:		{ 'material': has_property(self.attr) },
			'%s_texture' % self.attr:			{ 'material': has_property(self.attr), '%s_usetexture' % self.attr: True },
		}
	
	def get_properties(self):
		return [
			{
				'attr': '%s_usetexture' % self.attr,
				'type': 'bool',
				'name': 'T',
				'description': 'Textured %s' % self.name,
				'default': False,
				'toggle': True,
			},
			{
				'attr': '%s_floatvalue' % self.attr,
				'type': 'float',
				'name': self.name,
				'description': '%s Value' % self.name,
				'default': self.default,
				'min': self.min,
				'soft_min': self.min,
				'max': self.max,
				'soft_max': self.max,
				'precision': self.precision,
				'slider': True
			},
			{
				'attr': '%s_texturename' % self.attr,
				'type': 'string',
				'name': '%s_texturename' % self.attr,
				'description': '%s Texture' % self.name,
			},
			{
				'type': 'prop_object',
				'attr': '%s_texture' % self.attr,
				'src': lambda s,c: s.object.material_slots[s.object.active_material_index].material,
				'src_attr': 'texture_slots',
				'trg': lambda s,c: getattr(c, self.property_group),
				'trg_attr': '%s_texturename' % self.attr,
				'name': self.name
			},
		]

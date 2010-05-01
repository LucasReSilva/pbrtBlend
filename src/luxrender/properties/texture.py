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

from .util import has_property

class TextureBase(object):
	parent_type		= None
	attr			= None
	name			= None
	property_group	= None
	def __init__(self, parent_type, attr, name, property_group):
		self.parent_type = parent_type
		self.attr = attr
		self.name = name
		self.property_group = property_group
	
	def texture_slot_finder(self):
		def func(s,c):
			if s.object.type == 'LAMP':
				return s.object.data
			else:
				return s.object.material_slots[s.object.active_material_index].material
		
		return func
	
	def get_extra_controls(self):
		'''
		Subclasses can override this for their own needs
		'''	
		return []
	
	def get_extra_visibility(self):
		'''
		Subclasses can override this for their own needs
		'''	
		return {}
	
	def get_extra_properties(self):
		'''
		Subclasses can override this for their own needs
		'''	
		return []

class ColorTexture(TextureBase):

	def get_controls(self):
		return [
			[ 0.9, [0.375,'%s_label' % self.attr, '%s_color' % self.attr], '%s_usetexture' % self.attr ],
			'%s_texture' % self.attr
		] + self.get_extra_controls()
	
	def get_visibility(self):
		vis = {
			'%s_label' % self.attr: 			{ self.parent_type: has_property(self.parent_type, self.attr) },
			'%s_color' % self.attr: 			{ self.parent_type: has_property(self.parent_type, self.attr) },
			'%s_usetexture' % self.attr:		{ self.parent_type: has_property(self.parent_type, self.attr) },
			'%s_texture' % self.attr:			{ self.parent_type: has_property(self.parent_type, self.attr), '%s_usetexture' % self.attr: True },
		}
		vis.update(self.get_extra_visibility())
		return vis
	
	def get_properties(self):
		return [
			{
				'attr': self.attr,
				'type': 'string',
				'default': 'lux_color_texture',
			},
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
				'attr': '%s_color' % self.attr,
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
				'src': self.texture_slot_finder(),
				'src_attr': 'texture_slots',
				'trg': lambda s,c: getattr(c, self.property_group),
				'trg_attr': '%s_texturename' % self.attr,
				'name': self.name
			},
		] + self.get_extra_properties()

class FloatTexture(TextureBase):
	default			= 0.0
	min				= 0.0
	max				= 1.0
	precision		= 3
	texture_only	= False
	
	def __init__(self,
			parent_type, attr, name, property_group,
			add_float_value = True,
			default = 0.0, min = 0.0, max = 1.0, precision=3
		):
		self.parent_type = parent_type
		self.attr = attr
		self.name = name
		self.property_group = property_group
		self.texture_only = (not add_float_value)
		self.default = default
		self.min = min
		self.max = max
		self.precision = precision
	
	def get_controls(self):
		if self.texture_only:
			return [
				'%s_texture' % self.attr,
			] + self.get_extra_controls()
		else:
			return [
				[0.9, '%s_floatvalue' % self.attr, '%s_usetexture' % self.attr],
				'%s_texture' % self.attr,
			] + self.get_extra_controls()
	
	def get_visibility(self):
		if self.texture_only:
			vis = {
				'%s_texture' % self.attr:			{ self.parent_type: has_property(self.parent_type, self.attr) },
			}
		else:
			vis = {
				'%s_usetexture' % self.attr:		{ self.parent_type: has_property(self.parent_type, self.attr) },
				'%s_floatvalue' % self.attr:		{ self.parent_type: has_property(self.parent_type, self.attr) },
				'%s_texture' % self.attr:			{ self.parent_type: has_property(self.parent_type, self.attr), '%s_usetexture' % self.attr: True },
			}
		vis.update(self.get_extra_visibility())
		return vis
	
	def get_properties(self):
		return [
			{
				'attr': self.attr,
				'type': 'string',
				'default': 'lux_float_texture',
			},
			
			{
				'attr': '%s_usetexture' % self.attr,
				'type': 'bool',
				'name': 'T',
				'description': 'Textured %s' % self.name,
				'default': False if not self.texture_only else True,
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
				'src': self.texture_slot_finder(),
				'src_attr': 'texture_slots',
				'trg': lambda s,c: getattr(c, self.property_group),
				'trg_attr': '%s_texturename' % self.attr,
				'name': self.name
			},
		] + self.get_extra_properties()

#------------------------------------------------------------------------------ 
class luxrender_texture(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender Texture settings.
	This class will be instantiated within a Blender Texture
	object.
	'''
	
	pass
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

from luxrender.properties.material import has_material_property
from luxrender.export import ParamSet

def has_property(parent_type, property_name):
	if parent_type == 'material':
		return has_material_property(property_name)

class TextureParameterBase(object):
	parent_type		= None
	attr			= None
	name			= None
	property_group	= None
	default			= (0.8, 0.8, 0.8)
	min				= 0.0
	max				= 1.0
	
	def __init__(self, parent_type, attr, name, property_group, default=None, min=None, max=None):
		self.parent_type = parent_type
		self.attr = attr
		self.name = name
		self.property_group = property_group
		if default is not None:
			self.default = default
		if min is not None:
			self.min = min
		if max is not None:
			self.max = max
	
	def texture_slot_finder(self):
		def func(s,c):
			if s.object.type == 'LAMP':
				return s.object.data
			else:
				return s.object.material_slots[s.object.active_material_index].material
		
		return func
	
	def texture_slot_set_attr(self):
		return lambda s,c: getattr(c, self.property_group)
	
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

class ColorTextureParameter(TextureParameterBase):

	def get_controls(self):
		return [
			#[ 0.8, [0.425,'%s_colorlabel' % self.attr, '%s_color' % self.attr], '%s_usecolorrgc' % self.attr, '%s_usecolortexture' % self.attr ],
			[ 0.9, [0.375,'%s_colorlabel' % self.attr, '%s_color' % self.attr], '%s_usecolortexture' % self.attr ],
			'%s_colortexture' % self.attr
		] + self.get_extra_controls()
	
	def get_visibility(self):
		vis = {
			'%s_colorlabel' % self.attr: 			{ self.parent_type: has_property(self.parent_type, self.attr) },
			'%s_color' % self.attr: 				{ self.parent_type: has_property(self.parent_type, self.attr) },
			'%s_usecolorrgc' % self.attr:			{ self.parent_type: has_property(self.parent_type, self.attr) },
			'%s_usecolortexture' % self.attr:		{ self.parent_type: has_property(self.parent_type, self.attr) },
			'%s_colortexture' % self.attr:			{ self.parent_type: has_property(self.parent_type, self.attr), '%s_usecolortexture' % self.attr: True },
		}
		vis.update(self.get_extra_visibility())
		return vis
	
	# Decide which material property sets the viewport object
	# colour for each material type. If the property name is
	# not set, then the color won't be changed.
	master_color_map = {
		'carpaint': 'Kd',
		'glass': 'Kt',
		'roughglass': 'Kt',
		'glossy': 'Kd',
		'glossy_lossy': 'Kd',
		'matte': 'Kd',
		'mattetranslucent': 'Kt',
		'shinymetal': 'Ks',
		'mirror': 'Kr',
	}
	
	def set_master_colour(self, c):
		'''
		This neat little hack will set the blender material colour to the value
		given in the material panel via the property's 'draw' lambda function.
		we can specify more than one property to be 'master_colour' so long as
		they are not both visible in the panel simultaneously.
		'''
		if hasattr(c, 'luxrender_material'):
			if c.luxrender_material.material in self.master_color_map.keys() and self.attr == self.master_color_map[c.luxrender_material.material]:
				c.diffuse_color = getattr(c.luxrender_material, self.attr+'_color')
	
	def get_properties(self):
		return [
			{
				'attr': self.attr,
				'type': 'string',
				'default': 'lux_color_texture',
			},
			{
				'attr': '%s_usecolortexture' % self.attr,
				'type': 'bool',
				'name': 'T',
				'description': 'Textured %s' % self.name,
				'default': False,
				'toggle': True,
			},
			{
				'attr': '%s_usecolorrgc' % self.attr,
				'type': 'bool',
				'name': 'R',
				'description': 'Reverse Gamma Correct %s' % self.name,
				'default': False,
				'toggle': True,
			},
			{
				'type': 'text',
				'attr': '%s_colorlabel' % self.attr,
				'name': self.name
			},
			{
				'type': 'float_vector',
				'attr': '%s_color' % self.attr,
				'name': '', #self.name,
				'description': self.name,
				'default': self.default,
				'min': self.min,
				'soft_min': self.min,
				'max': self.max,
				'soft_max': self.max,
				'subtype': 'COLOR',
				'draw': lambda s,c: self.set_master_colour(c)
			},
			{
				'attr': '%s_colortexturename' % self.attr,
				'type': 'string',
				'name': '%s_colortexturename' % self.attr,
				'description': '%s Texture' % self.name,
			},
			{
				'type': 'prop_search',
				'attr': '%s_colortexture' % self.attr,
				'src': self.texture_slot_finder(),
				'src_attr': 'texture_slots',
				'trg': self.texture_slot_set_attr(),
				'trg_attr': '%s_colortexturename' % self.attr,
				'name': self.name
			},
		] + self.get_extra_properties()

class FloatTextureParameter(TextureParameterBase):
	default			= 0.0
	min				= 0.0
	max				= 1.0
	precision		= 6
	texture_only	= False
	multiply_float  = False
	ignore_zero     = False
	
	def __init__(self,
			parent_type, attr, name, property_group,
			add_float_value = True,      # True: Show float value input, and [T] button; False: Just show texture slot
			multiply_float = False,      # Specify that when texture is in use, it should be scaled by the float value
			ignore_zero = False,         # Don't export this parameter if the float value == 0.0
			default = 0.0, min = 0.0, max = 1.0, precision=6
		):
		self.parent_type = parent_type
		self.attr = attr
		self.name = name
		self.property_group = property_group
		self.texture_only = (not add_float_value)
		self.multiply_float = multiply_float
		self.ignore_zero = ignore_zero
		self.default = default
		self.min = min
		self.max = max
		self.precision = precision
	
	def get_controls(self):
		if self.texture_only:
			return [
				'%s_floattexture' % self.attr,
			] + self.get_extra_controls()
		else:
			return [
				[0.9, '%s_floatvalue' % self.attr, '%s_usefloattexture' % self.attr],
				'%s_floattexture' % self.attr,
			] + self.get_extra_controls()
	
	def get_visibility(self):
		if self.texture_only:
			vis = {
				'%s_floattexture' % self.attr:		{ self.parent_type: has_property(self.parent_type, self.attr) },
			}
		else:
			vis = {
				'%s_usefloattexture' % self.attr:	{ self.parent_type: has_property(self.parent_type, self.attr) },
				'%s_floatvalue' % self.attr:		{ self.parent_type: has_property(self.parent_type, self.attr) },
				'%s_floattexture' % self.attr:		{ self.parent_type: has_property(self.parent_type, self.attr), '%s_usefloattexture' % self.attr: True },
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
				'attr': '%s_multiplyfloat' % self.attr,
				'type': 'bool',
				'default': self.multiply_float
			},
			{
				'attr': '%s_ignorezero' % self.attr,
				'type': 'bool',
				'default': self.ignore_zero
			},
			{
				'attr': '%s_usefloattexture' % self.attr,
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
				#'slider': True
			},
			{
				'attr': '%s_floattexturename' % self.attr,
				'type': 'string',
				'name': '%s_floattexturename' % self.attr,
				'description': '%s Texture' % self.name,
			},
			{
				'type': 'prop_search',
				'attr': '%s_floattexture' % self.attr,
				'src': self.texture_slot_finder(),
				'src_attr': 'texture_slots',
				'trg': self.texture_slot_set_attr(),
				'trg_attr': '%s_floattexturename' % self.attr,
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
	
	def get_paramset(self):
		'''
		Discover the type of this LuxRender texture, and return its
		variant name and its ParamSet.
		We also add in the ParamSets of any panels shared by texture
		types, eg. 2D/3D mapping and transform params
		
		Return		tuple(string('float'|'color'), ParamSet)
		'''
		
		# this requires the sub-IDPropertyGroup name to be the same as the texture name
		lux_texture = getattr(self, self.type) 
		features, params = lux_texture.get_paramset() 
		
		# 2D Mapping options
		#if self.type in {'bilerp', 'checkerboard', 'dots', 'imagemap', 'uv', 'uvmask'}:
		if '2DMAPPING' in features:
			params.update( self.mapping.get_paramset() )
			
		# 3D Mapping options
		#if self.type in {'brick', 'checkerboard', 'fbm', 'marble', 'windy', 'wrinkled'}:
		if '3DMAPPING' in features:
			params.update( self.transform.get_paramset() )
			
		return lux_texture.variant, params
	
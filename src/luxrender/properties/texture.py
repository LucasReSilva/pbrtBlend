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

from ef.ef import declarative_property_group
from ef.validate import Logic_OR as O

from luxrender.properties import has_property
from luxrender.properties.lampspectrum_data import lampspectrum_list
from luxrender.export import ParamSet, get_worldscale
from luxrender.export.materials import add_texture_parameter
from luxrender.outputs import LuxManager

#------------------------------------------------------------------------------ 
# Texture property group construction helpers
#------------------------------------------------------------------------------ 

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
				if c.diffuse_color != getattr(c.luxrender_material, self.attr+'_color'):
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
# The main luxrender_texture property group
#------------------------------------------------------------------------------ 

class luxrender_texture(declarative_property_group):
	'''
	Storage class for LuxRender Texture settings.
	This class will be instantiated within a Blender Texture
	object.
	'''
	
	controls = [
		'type'
	]
	visibility = {
		#'type': { 'use_lux_texture': True }
	}
	properties = [
		{
			'attr': 'use_lux_texture',
			'type': 'bool',
			'default': False,
		},
		{
			'attr': 'type',
			'name': 'LuxRender Type',
			'type': 'enum',
			'items': [
				#('none', 'none', 'none'),
				('BLENDER', 'Use Blender Texture', 'BLENDER'),
				('bilerp', 'bilerp', 'bilerp'),
				('blackbody','blackbody','blackbody'),
				('brick', 'brick', 'brick'),
				('checkerboard', 'checkerboard', 'checkerboard'),
				('dots', 'dots', 'dots'),
				('equalenergy', 'equalenergy', 'equalenergy'),
				('fbm', 'fbm', 'fbm'),
				('gaussian', 'gaussian', 'gaussian'),
				('harlequin', 'harlequin', 'harlequin'),
				('imagemap', 'imagemap', 'imagemap'),
				('lampspectrum', 'lampspectrum', 'lampspectrum'),
				('marble', 'marble', 'marble'),
				('mix', 'mix', 'mix'),
				('scale', 'scale', 'scale'),
				('uv', 'uv', 'uv'),
				('windy', 'windy', 'windy'),
				('wrinkled', 'wrinkled', 'wrinkled'),
			],
		},
	]
	
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

#------------------------------------------------------------------------------ 
# Sub property groups of luxrender_texture follow
#------------------------------------------------------------------------------ 

class bilerp(declarative_property_group):
	
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
			'default': (0.0, 0.0, 0.0),
			'min': 0.0,
			'max': 1.0
		},
		{
			'attr': 'v01_c',
			'type': 'float_vector',
			'subtype': 'COLOR',
			'name': '(0,1)',
			'default': (1.0, 1.0, 1.0),
			'min': 0.0,
			'max': 1.0
		},
		{
			'attr': 'v10_c',
			'type': 'float_vector',
			'subtype': 'COLOR',
			'name': '(1,0)',
			'default': (0.0, 0.0, 0.0),
			'min': 0.0,
			'max': 1.0
		},
		{
			'attr': 'v11_c',
			'type': 'float_vector',
			'subtype': 'COLOR',
			'name': '(1,1)',
			'default': (1.0, 1.0, 1.0),
			'min': 0.0,
			'max': 1.0
		},
	]
	
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

class blackbody(declarative_property_group):
	
	controls = [
		'temperature'
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'color'
		},
		{
			'type': 'float',
			'attr': 'temperature',
			'name': 'Temperature',
			'default': 6500.0
		}
	]
	
	def get_paramset(self):
		
		return set(), ParamSet().add_float('temperature', self.temperature)

brickmodtex_f	= FloatTextureParameter('texture', 'brickmodtex', 'brickmodtex', 'brick', default=0.0, min=0.0, max=1.0)
brickmodtex_c	= ColorTextureParameter('texture', 'brickmodtex', 'brickmodtex', 'brick', default=(1.0,1.0,1.0))
bricktex_f		= FloatTextureParameter('texture', 'bricktex', 'bricktex', 'brick', default=0.0, min=0.0, max=1.0)
bricktex_c		= ColorTextureParameter('texture', 'bricktex', 'bricktex', 'brick', default=(1.0,1.0,1.0))
mortartex_f		= FloatTextureParameter('texture', 'mortartex', 'mortartex', 'brick', default=0.0, min=0.0, max=1.0)
mortartex_c		= ColorTextureParameter('texture', 'mortartex', 'mortartex', 'brick', default=(1.0,1.0,1.0))

class brick(declarative_property_group):
	
	controls = [
		'variant',
		'brickbond',
		'brickbevel',
		'brickrun',
		'mortarsize',
		['brickwidth', 'brickdepth', 'brickheight'],
	] + \
	brickmodtex_f.get_controls() + \
	brickmodtex_c.get_controls() + \
	bricktex_f.get_controls() + \
	bricktex_c.get_controls() + \
	mortartex_f.get_controls() + \
	mortartex_c.get_controls()
	
	# Visibility we do manually because of the variant switch
	visibility = {
		'brickmodtex_colorlabel':			{ 'variant': 'color' },
		'brickmodtex_color': 				{ 'variant': 'color' },
		'brickmodtex_usecolortexture':		{ 'variant': 'color' },
		'brickmodtex_colortexture':			{ 'variant': 'color', 'brickmodtex_usecolortexture': True },
		
		'brickmodtex_usefloattexture':		{ 'variant': 'float' },
		'brickmodtex_floatvalue':			{ 'variant': 'float' },
		'brickmodtex_floattexture':			{ 'variant': 'float', 'brickmodtex_usefloattexture': True },
		
		
		'bricktex_colorlabel':				{ 'variant': 'color' },
		'bricktex_color': 					{ 'variant': 'color' },
		'bricktex_usecolortexture':			{ 'variant': 'color' },
		'bricktex_colortexture':			{ 'variant': 'color', 'bricktex_usecolortexture': True },
		
		'bricktex_usefloattexture':			{ 'variant': 'float' },
		'bricktex_floatvalue':				{ 'variant': 'float' },
		'bricktex_floattexture':			{ 'variant': 'float', 'bricktex_usefloattexture': True },
		
		
		'mortartex_colorlabel':				{ 'variant': 'color' },
		'mortartex_color': 					{ 'variant': 'color' },
		'mortartex_usecolortexture':		{ 'variant': 'color' },
		'mortartex_colortexture':			{ 'variant': 'color', 'mortartex_usecolortexture': True },
		
		'mortartex_usefloattexture':		{ 'variant': 'float' },
		'mortartex_floatvalue':				{ 'variant': 'float' },
		'mortartex_floattexture':			{ 'variant': 'float', 'mortartex_usefloattexture': True },
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
			'attr': 'brickbond',
			'type': 'enum',
			'name': 'Bond Type',
			'items': [
				('running', 'running', 'running'),
				('stacked', 'stacked', 'stacked'),
				('flemish', 'flemish', 'flemish'),
				('english', 'english', 'english'),
				('herringbone', 'herringbone', 'herringbone'),
				('basket', 'basket', 'basket'),
				('chain link', 'chain link', 'chain link')
			]
		},
		{
			'attr': 'brickbevel',
			'type': 'float',
			'name': 'Bevel',
			'default': 0.0,
		},
		{
			'attr': 'brickrun',
			'type': 'float',
			'name': 'brickrun',
			'default': 0.5,
			'min': -10.0,
			'soft_min': -10.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'attr': 'mortarsize',
			'type': 'float',
			'name': 'Mortar Size',
			'default': 0.01,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0
		},
		{
			'attr': 'brickwidth',
			'type': 'float',
			'name': 'Width',
			'default': 0.3,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'attr': 'brickdepth',
			'type': 'float',
			'name': 'Depth',
			'default': 0.15,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'attr': 'brickheight',
			'type': 'float',
			'name': 'Height',
			'default': 0.1,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
	] + \
	brickmodtex_f.get_properties() + \
	brickmodtex_c.get_properties() + \
	bricktex_f.get_properties() + \
	bricktex_c.get_properties() + \
	mortartex_f.get_properties() + \
	mortartex_c.get_properties()
	
	def get_paramset(self):
		
		brick_params = ParamSet() \
			.add_float('brickbevel', self.brickbevel) \
			.add_string('brickbond', self.brickbond) \
			.add_float('brickdepth', self.brickdepth) \
			.add_float('brickheight', self.brickheight) \
			.add_float('brickwidth', self.brickwidth) \
			.add_float('brickrun', self.brickrun) \
			.add_float('mortarsize', self.mortarsize)
			
		brick_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'brickmodtex', self.variant, self)
		)
		brick_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'bricktex', self.variant, self)
		)
		brick_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'mortartex', self.variant, self)
		)
		
		return {'3DMAPPING'}, brick_params

tex1 = FloatTextureParameter('texture', 'tex1', 'Texture 1', 'checkerboard', default=1.0, min=0.0, max=100.0)
tex2 = FloatTextureParameter('texture', 'tex2', 'Texture 2', 'checkerboard', default=0.0, min=0.0, max=100.0)

class checkerboard(declarative_property_group):
	
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

inside	= FloatTextureParameter('texture', 'inside', 'inside', 'dots', default=1.0, min=0.0, max=100.0)
outside	= FloatTextureParameter('texture', 'outside', 'outside', 'dots', default=0.0, min=0.0, max=100.0)

class dots(declarative_property_group):
	
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
	
	def get_paramset(self):
		
		dots_params = ParamSet()
			
		dots_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'inside', self.variant, self)
		)
		dots_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'outside', self.variant, self)
		)
		
		return {'2DMAPPING'}, dots_params

class equalenergy(declarative_property_group):
	
	controls = [
		'energy'
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'color'
		},
		{
			'type': 'float',
			'attr': 'energy',
			'name': 'Energy',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0
		}
	]
	
	def get_paramset(self):
		
		return set(), ParamSet().add_float('energy', self.energy)

class fbm(declarative_property_group):
	
	controls = [
		'octaves',
		'roughness',
	]
	
	visibility = {} 
	
	properties = [
		{
			'attr': 'variant',
			'type': 'string',
			'default': 'float'
		},
		{
			'type': 'int',
			'attr': 'octaves',
			'name': 'Octaves',
			'default': 8,
			'min': 1,
			'soft_min': 1,
			'max': 100,
			'soft_max': 100
		},
		{
			'type': 'float',
			'attr': 'roughness',
			'name': 'Roughness',
			'default': 0.5,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0
		},
	]
	
	def get_paramset(self):
		
		fbm_params = ParamSet().add_integer('octaves', self.octaves) \
							   .add_float('roughness', self.roughness)
		
		return {'3DMAPPING'}, fbm_params

class gaussian(declarative_property_group):
	
	controls = [
		'energy',
		'wavelength',
		'width',
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'color'
		},
		{
			'type': 'float',
			'attr': 'energy',
			'name': 'Energy',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0
		},
		{
			'type': 'float',
			'attr': 'wavelength',
			'name': 'Wavelength (nm)',
			'default': 550.0,
			'min': 380.0,
			'soft_min': 380.0,
			'max': 720.0,
			'soft_max': 720.0,
		},
		{
			'type': 'float',
			'attr': 'width',
			'name': 'Width (nm)',
			'default': 50.0,
			'min': 20.0,
			'soft_min': 20.0,
			'max': 300.0,
			'soft_max': 300.0,
		},
	]
	
	def get_paramset(self):
		
		return set(), ParamSet().add_float('energy', self.energy) \
								.add_float('wavelength', self.wavelength) \
								.add_float('width', self.width)

class harlequin(declarative_property_group):
	
	controls = [
		# None
	]
	
	visibility = {} 
	
	properties = [
		{
			'attr': 'variant',
			'type': 'string',
			'default': 'color'
		},
	]
	
	def get_paramset(self):
		
		harlequin_params = ParamSet()
		
		return set(), harlequin_params

class imagemap(declarative_property_group):
	
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
		'channel':	{ 'variant': 'float' },
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

class lampspectrum(declarative_property_group):
	
	controls = [
		'preset'
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'color'
		},
		{
			'type': 'enum',
			'attr': 'preset',
			'name': 'Name',
			'items': lampspectrum_list()
		}
	]
	
	def get_paramset(self):
		
		return set(), ParamSet().add_string('name', self.preset)

class mapping(declarative_property_group):
	
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

class marble(declarative_property_group):
	
	controls = [
		'octaves',
		'roughness',
		'scale',
		'variation',
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'color'
		},
		{
			'type': 'int',
			'attr': 'octaves',
			'name': 'Octaves',
			'default': 8,
			'min': 1,
			'soft_min': 1,
			'max': 100,
			'soft_max': 100
		},
		{
			'type': 'float',
			'attr': 'roughness',
			'name': 'Roughness',
			'default': 0.5,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0
		},
		{
			'type': 'float',
			'attr': 'scale',
			'name': 'Scale',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 100.0,
			'soft_max': 100.0
		},
		{
			'type': 'float',
			'attr': 'variation',
			'name': 'Variation',
			'default': 0.2,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 100.0,
			'soft_max': 100.0
		},
	]
	
	def get_paramset(self):
		
		return {'3DMAPPING'}, ParamSet().add_integer('octaves', self.octaves) \
										.add_float('roughness', self.roughness) \
										.add_float('scale', self.scale) \
										.add_float('variation', self.variation)

amount_f	= FloatTextureParameter('texture', 'amount', 'amount', 'mix', default=0.5, min=0.0, max=1.0)
tex1_f		= FloatTextureParameter('texture', 'tex1', 'tex1', 'mix', default=1.0, min=0.0, max=100.0)
tex1_c		= ColorTextureParameter('texture', 'tex1', 'tex1', 'mix', default=(1.0,1.0,1.0))
tex2_f		= FloatTextureParameter('texture', 'tex2', 'tex2', 'mix', default=0.0, min=0.0, max=100.0)
tex2_c		= ColorTextureParameter('texture', 'tex2', 'tex2', 'mix', default=(0.0,0.0,0.0))

class mix(declarative_property_group):
	
	controls = [
		'variant',
		
	] + \
	amount_f.get_controls() + \
	tex1_f.get_controls() + \
	tex1_c.get_controls() + \
	tex2_f.get_controls() + \
	tex2_c.get_controls()
	
	# Visibility we do manually because of the variant switch
	visibility = {
		'amount_floattexture':			{ 'amount_usefloattexture': True },
		
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
	amount_f.get_properties() + \
	tex1_f.get_properties() + \
	tex1_c.get_properties() + \
	tex2_f.get_properties() + \
	tex2_c.get_properties()
	
	def get_paramset(self):
		
		mix_params = ParamSet()
		
		mix_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'amount', 'float', self)
		)
		mix_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex1', self.variant, self)
		)
		mix_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex2', self.variant, self)
		)
		
		return set(), mix_params

tex1_f		= FloatTextureParameter('texture', 'tex1', 'tex1', 'scale', default=1.0, min=0.0, max=100.0)
tex1_c		= ColorTextureParameter('texture', 'tex1', 'tex1', 'scale', default=(1.0,1.0,1.0))
tex2_f		= FloatTextureParameter('texture', 'tex2', 'tex2', 'scale', default=0.0, min=0.0, max=100.0)
tex2_c		= ColorTextureParameter('texture', 'tex2', 'tex2', 'scale', default=(0.0,0.0,0.0))

class scale(declarative_property_group):
	
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
	
	def get_paramset(self):
		
		scale_params = ParamSet()
		
		scale_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex1', self.variant, self)
		)
		scale_params.update(
			add_texture_parameter(LuxManager.ActiveManager.lux_context, 'tex2', self.variant, self)
		)
		
		return set(), scale_params

class transform(declarative_property_group):
	
	controls = [
		'translate',
		'rotate',
		'scale',
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'float_vector',
			'attr': 'translate',
			'name': 'Translate',
			'default': (0.0, 0.0, 0.0),
		},
		{
			'type': 'float_vector',
			'attr': 'rotate',
			'name': 'Rotate',
			'default': (0.0, 0.0, 0.0),
		},
		{
			'type': 'float_vector',
			'attr': 'scale',
			'name': 'Scale',
			'default': (1.0, 1.0, 1.0),
		},
	]
	
	def get_paramset(self):
		transform_params = ParamSet()
		
		ws = get_worldscale(as_scalematrix=False)
		
		transform_params.add_vector('translate', [i*ws for i in self.translate])
		transform_params.add_vector('rotate', self.rotate)
		transform_params.add_vector('scale', [i*ws for i in self.scale])
		
		return transform_params

class uv(declarative_property_group):
	
	controls = [
		# None
	]
	
	visibility = {} 
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'color'
		},
	]
	
	def get_paramset(self):
		
		uv_params = ParamSet()
			
		return {'2DMAPPING'}, uv_params

class windy(declarative_property_group):
	
	controls = [
		# None
	]
	
	visibility = {} 
	
	properties = [
		{
			'attr': 'variant',
			'type': 'string',
			'default': 'float'
		},
	]
	
	def get_paramset(self):
		
		windy_params = ParamSet()
		
		return {'3DMAPPING'}, windy_params

class wrinkled(declarative_property_group):
	
	controls = [
		'octaves',
		'roughness',
	]
	
	visibility = {} 
	
	properties = [
		{
			'attr': 'variant',
			'type': 'string',
			'default': 'float'
		},
		{
			'type': 'int',
			'attr': 'octaves',
			'name': 'Octaves',
			'default': 8,
			'min': 1,
			'soft_min': 1,
			'max': 100,
			'soft_max': 100
		},
		{
			'type': 'float',
			'attr': 'roughness',
			'name': 'Roughness',
			'default': 0.5,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0
		},
	]
	
	def get_paramset(self):
		
		wrinkled_params = ParamSet().add_integer('octaves', self.octaves) \
									.add_float('roughness', self.roughness)
		
		return {'3DMAPPING'}, wrinkled_params


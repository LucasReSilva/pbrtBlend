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

from luxrender.export import ParamSet
from luxrender.export.materials import add_texture_parameter
from luxrender.outputs import LuxManager
from luxrender.properties.texture import ColorTextureParameter, FloatTextureParameter
from luxrender.ui.textures import luxrender_texture_base

class brick(bpy.types.IDPropertyGroup):
	
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

brickmodtex_f	= FloatTextureParameter('texture', 'brickmodtex', 'brickmodtex', 'brick', default=0.0, min=0.0, max=1.0)
brickmodtex_c	= ColorTextureParameter('texture', 'brickmodtex', 'brickmodtex', 'brick', default=(1.0,1.0,1.0))
bricktex_f		= FloatTextureParameter('texture', 'bricktex', 'bricktex', 'brick', default=0.0, min=0.0, max=1.0)
bricktex_c		= ColorTextureParameter('texture', 'bricktex', 'bricktex', 'brick', default=(1.0,1.0,1.0))
mortartex_f		= FloatTextureParameter('texture', 'mortartex', 'mortartex', 'brick', default=0.0, min=0.0, max=1.0)
mortartex_c		= ColorTextureParameter('texture', 'mortartex', 'mortartex', 'brick', default=(1.0,1.0,1.0))

class ui_panel_brick(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender Brick Texture'
	
	LUX_COMPAT = {'brick'}
	
	property_group = brick
	
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
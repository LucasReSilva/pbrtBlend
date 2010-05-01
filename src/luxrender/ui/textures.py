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

from properties_texture import context_tex_datablock
from properties_texture import TextureButtonsPanel

from ef.ui import context_panel
from ef.ui import described_layout

from ef.ef import ef

import luxrender.properties.texture
from ..properties.util import has_property, texture_property_map, texture_translate_dict
from ..properties.texture import FloatTexture, ColorTexture

TF_amount			= FloatTexture('texture', 'amount', 'Amount',			'luxrender_texture')
TF_inside			= FloatTexture('texture', 'inside', 'Inside',			'luxrender_texture', add_float_value=False)
TF_outside			= FloatTexture('texture', 'outside', 'Outside',			'luxrender_texture', add_float_value=False)

TF_brickmodtex		= FloatTexture('texture', 'f_brickmodtex', 'Mod Tex',	'luxrender_texture')
TF_brickrun			= FloatTexture('texture', 'f_brickrun', 'Run',			'luxrender_texture')
TF_bricktex			= FloatTexture('texture', 'f_bricktex', 'Tex',			'luxrender_texture')
TF_mortartex		= FloatTexture('texture', 'f_mortartex', 'Mortar Tex',	'luxrender_texture')
TF_tex1				= FloatTexture('texture', 'f_tex1', 'Tex 1',			'luxrender_texture')
TF_tex2				= FloatTexture('texture', 'f_tex2', 'Tex 2',			'luxrender_texture')

TC_brickmodtex		= ColorTexture('texture', 'c_brickmodtex', 'Mod Tex',	'luxrender_texture')
TC_brickrun			= ColorTexture('texture', 'c_brickrun', 'Run',			'luxrender_texture')
TC_bricktex			= ColorTexture('texture', 'c_bricktex', 'Tex',			'luxrender_texture')
TC_mortartex		= ColorTexture('texture', 'c_mortartex', 'Mortar Tex',	'luxrender_texture')
TC_tex1				= ColorTexture('texture', 'c_tex1', 'Tex 1',			'luxrender_texture')
TC_tex2				= ColorTexture('texture', 'c_tex2', 'Tex 2',			'luxrender_texture')

def lampspectrum_names():
	return [
		('Alcohol', 'Alcohol', 'Alcohol'),
		('AntiInsect', 'AntiInsect', 'AntiInsect'),
		# TODO: add the others
	]

def discover_float_color(context):
	'''
	Try to determine whether to display float-type controls or color-type
	controls for this texture, depending on which type of texture slot
	it has been loaded into.
	
	There will be issues if the same texture is used both as a float and
	a colour, since the type returned will be the first one found only.
	'''
	
	float_col = False
	
	for ms in context.object.material_slots:
		# first search in the parent object's materials
		lm = ms.material.luxrender_material
		for p in dir(lm):
			if p.endswith('_texturename') and getattr(lm, p) == context.texture.name:
				tex_slot = p.replace('_texturename', '')
				return getattr(lm, tex_slot)
		
		# then search in textures
		for ts in ms.material.texture_slots:
			if hasattr(ts, 'texture') and hasattr(ts.texture, 'luxrender_texture'):
				lt = ts.texture.luxrender_texture
				for p in dir(lt):
					if p.endswith('_texturename') and getattr(lt, p) == context.texture.name:
						tex_slot = p.replace('_texturename', '')
						return getattr(lt, tex_slot)
	
	return float_col

def texture_controls(context=None):
	
	ctrl = [
		'texture',
		
		'aamode',
		'brickbevel', 'brickbond', ['brickwidth', 'brickdepth', 'brickheight'],
		'channel',
		'dimension',
		'discardmipmaps',
		'end',
		'energy',
		'filename',
		'filtertype',
		'freq',
		'gain',
		'gamma',
		'mapping',
		'maxanisotropy',
		'mortarsize',
		'lampspectrum_name',
		'octaves',
		'phase',
		'roughness',
		'scale',
		'start',
		'temperature',
		['uscale', 'vscale'],
		['udelta', 'vdelta'],
		'variation',
		'wavelength',
		'width',
		'wrap'
	] + \
	TF_amount.get_controls() + \
	TF_inside.get_controls() + \
	TF_outside.get_controls()
	
	if context != None:
		float_col = discover_float_color(context)
		
		if float_col == 'lux_float_texture':
			context.texture.luxrender_texture.variant = 'FLOAT'
			
			# this is NOT the same as append() !
			ctrl += \
				TF_brickmodtex.get_controls() + \
				TF_brickrun.get_controls() + \
				TF_bricktex.get_controls() + \
				TF_mortartex.get_controls() + \
				TF_tex1.get_controls() + \
				TF_tex2.get_controls()
				
		elif float_col == 'lux_color_texture':
			context.texture.luxrender_texture.variant = 'COLOR'
			
			# this is NOT the same as append() !
			ctrl += \
				TC_brickmodtex.get_controls() + \
				TC_brickrun.get_controls() + \
				TC_bricktex.get_controls() + \
				TC_mortartex.get_controls() + \
				TC_tex1.get_controls() + \
				TC_tex2.get_controls()
	
	return ctrl

def texture_visibility(context=None):
	vis = {}
	reverse_translate = texture_translate_dict()
	for k, v in texture_property_map().items():
		if k in reverse_translate.values():
			k = list(reverse_translate.keys())[ list(reverse_translate.values()).index(k) ]
		vis[k] = { 'texture': v }
		
	vis.update( TF_amount.get_visibility() )
	vis.update( TF_inside.get_visibility() )
	vis.update( TF_outside.get_visibility() )
	
	if context != None:
		float_col = discover_float_color(context)
		if float_col == 'lux_float_texture':
			vis.update( TF_brickmodtex.get_visibility() )
			vis.update( TF_brickrun.get_visibility() )
			vis.update( TF_bricktex.get_visibility() )
			vis.update( TF_mortartex.get_visibility() )
			vis.update( TF_tex1.get_visibility() )
			vis.update( TF_tex2.get_visibility() )
		elif float_col == 'lux_color_texture':
			vis.update( TC_brickmodtex.get_visibility() )
			vis.update( TC_brickrun.get_visibility() )
			vis.update( TC_bricktex.get_visibility() )
			vis.update( TC_mortartex.get_visibility() )
			vis.update( TC_tex1.get_visibility() )
			vis.update( TC_tex2.get_visibility() )
	
	return vis

class texture_editor(context_panel, TextureButtonsPanel, described_layout):
	'''
	Texture Editor UI Panel
	'''
	
	bl_label = 'LuxRender Textures'
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender.properties.texture.luxrender_texture
	
	# prevent creating luxrender_texture property group in Scene
	property_group_non_global = True
	
	def poll(self, context):
		'''
		Only show LuxRender panel with 'Plugin' texture type
		'''
		
		return TextureButtonsPanel.poll(self, context) and context.texture.type == 'PLUGIN'
	
	@staticmethod
	def property_reload():
		for tex in bpy.data.textures:
			texture_editor.property_create(tex)
			
	@staticmethod
	def property_create(texture):
		if not hasattr(texture, texture_editor.property_group.__name__):
			ef.init_properties(texture, [{
				'type': 'pointer',
				'attr': texture_editor.property_group.__name__,
				'ptype': texture_editor.property_group,
				'name': texture_editor.property_group.__name__,
				'description': texture_editor.property_group.__name__
			}], cache=False)
			ef.init_properties(texture_editor.property_group, texture_editor.properties, cache=False)
	
	# Overridden to provide data storage in the texture, not the scene
	def draw(self, context):
		if context.texture is not None:
			texture_editor.property_create(context.texture)
			
			texture_editor.controls = texture_controls(context)
			texture_editor.visibility = texture_visibility(context)
			
			for p in self.controls:
				self.draw_column(p, self.layout, context.texture, supercontext=context)
				
	controls = texture_controls()
	visibility = texture_visibility()
	
	properties = [
		{
			'attr': 'texture',
			'type': 'enum',
			'name': 'Type',
			'description': 'LuxRender Texture Type',
			'items': [
				('bilerp', 'bilerp', 'bilerp'),
				('blackbody', 'blackbody', 'blackbody'),
				('brick', 'brick', 'brick'),
				#('cauchy', 'cauchy', 'cauchy'),
				('checkerboard', 'checkerboard', 'checkerboard'),
				('constant', 'constant', 'constant'),
				('dots', 'dots', 'dots'),
				('equalenergy', 'equalenergy', 'equalenergy'),
				('fbm', 'fbm', 'fbm'),
				('frequency', 'frequency', 'frequency'),
				('gaussian', 'gaussian', 'gaussian'),
				('harlequin', 'harlequin', 'harlequin'),
				('imagemap', 'imagemap', 'imagemap'),
				#('irregulardata', 'irregulardata', 'irregulardata'),
				('lampspectrum', 'lampspectrum', 'lampspectrum'),
				('marble', 'marble', 'marble'),
				('mix', 'mix', 'mix'),
				#('regulardata', 'regulardata', 'regulardata'),
				('scale', 'scale', 'scale'),
				#('sellmeier', 'sellmeier', 'sellmeier'),
				#('tabulateddata', 'tabulateddata', 'tabulateddata'),
				#('tabulatedfresnel', 'tabulatedfresnel', 'tabulatedfresnel'),
				('uv', 'uv', 'uv'),
				('windy', 'windy', 'windy'),
				('wrinkled', 'wrinkled', 'wrinkled'),
			],
		},
		{
			'attr': 'variant',
			'type': 'enum',
			'items': [
				('FLOAT', 'FLOAT', 'FLOAT'),
				('COLOR', 'COLOR', 'COLOR'),
			]
		},
		{
			'attr': 'aamode',
			'type': 'enum',
			'name': 'Anti-Aliasing Mode',
			'default': 'closedform',
			'items': [
				('closedform', 'closedform', 'closedform'),
				('supersample', 'supersample', 'supersample'),
				('none', 'none', 'none'),
			]
		},
		{
			'attr': 'brickbevel',
			'type': 'float',
			'name': 'Bevel',
		},
		{
			'attr': 'brickdepth',
			'type': 'float',
			'name': 'Depth',
		},
		{
			'attr': 'brickheight',
			'type': 'float',
			'name': 'Height',
		},
		{
			'attr': 'brickwidth',
			'type': 'float',
			'name': 'Width',
		},
		{
			'attr': 'channel',
			'type': 'enum',
			'name': 'Channel',
			'default': 'mean',
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
			'attr': 'dimension',
			'type': 'int',
			'name': 'Dimension',
			'min': 2,
			'soft_min': 2,
			'max': 3,
			'soft_max': 3,
		},
		{
			'attr': 'discardmipmaps',
			'type': 'int',
			'name': 'Discard MipMap Levels',
			'min': 0,
			'soft_min': 0,
			'max': 6,
			'soft_max': 6,
			'default': 0,
		},
		{
			'attr': 'end',
			'type': 'float',
			'name': 'End Wavelength',
		},
		{
			'attr': 'energy',
			'type': 'float',
			'name': 'Energy',
		},
		{
			'attr': 'filename',
			'type': 'string',
			'subtype': 'FILE_PATH',
			'name': 'File name',
		},
		{
			'attr': 'filtertype',
			'type': 'enum',
			'name': 'Filter type',
			'default': 'bilinear',
			'items': [
				('bilinear', 'bilinear', 'bilinear'),
				('mipmap_trilinear', 'mipmap_trilinear', 'mipmap_trilinear'),
				('mipmap_ewa', 'mipmap_ewa', 'mipmap_ewa'),
				('nearest', 'nearest', 'nearest'),
			]
		},
		{
			'attr': 'freq',
			'type': 'float',
			'name': 'Frequency',
		},
		{
			'attr': 'gain',
			'type': 'float',
			'name': 'Gain',
			'default': 1.0
		},
		{
			'attr': 'gamma',
			'type': 'float',
			'name': 'Gamma',
			'default': 2.2
		},
		{
			'attr': 'mapping',
			'type': 'enum',
			'name': 'Mapping',
			'default': 'uv',
			'items': [
				('uv', 'uv', 'uv'),
				('spherical', 'spherical', 'spherical'),
				('cylindrical', 'cylindrical', 'cylindrical'),
				('planar', 'planar', 'planar'),
			]
		},
		{
			'attr': 'maxanisotropy',
			'type': 'float',
			'name': 'Max. Anisotropy',
		},
		{
			'attr': 'mortarsize',
			'type': 'float',
			'name': 'Mortar Size',
		},
		{
			'attr': 'lampspectrum_name',
			'type': 'enum',
			'name': 'Lamp Name',
			'items': lampspectrum_names()
		},
		{
			'attr': 'octaves',
			'type': 'integer',
			'name': 'Octaves',
		},
		{
			'attr': 'phase',
			'type': 'float',
			'name': 'Phase',
		},
		{
			'attr': 'roughness',
			'type': 'float',
			'name': 'Roughness',
		},
		{
			'attr': 'scale',
			'type': 'float',
			'name': 'Scale',
		},
		{
			'attr': 'start',
			'type': 'float',
			'name': 'Start Wavelength',
		},
		{
			'attr': 'temperature',
			'type': 'float',
			'name': 'Temperature',
			'default': 6500.0
		},
		{
			'attr': 'uscale',
			'type': 'float',
			'name': 'U Scale',
			'default': 1.0
		},
		{
			'attr': 'vscale',
			'type': 'float',
			'name': 'V Scale',
			'default': -1.0
		},
		{
			'attr': 'udelta',
			'type': 'float',
			'name': 'U Offset',
			'default': 0.0
		},
		{
			'attr': 'vdelta',
			'type': 'float',
			'name': 'V Offset',
			'default': 0.0
		},
		{
			'attr': 'variation',
			'type': 'float',
			'name': 'Variation',
		},
		{
			'attr': 'wavelength',
			'type': 'float',
			'name': 'Wavelength'
		},
		{
			'attr': 'width',
			'type': 'float',
			'name': 'Width'
		},
		{
			'attr': 'wrap',
			'type': 'enum',
			'name': 'Wrapping',
			'default': 'repeat',
			'items': [
				('repeat', 'repeat', 'repeat'),
				('black', 'black', 'black'),
				('clamp', 'clamp', 'clamp'),
			]
		},
	] + \
	TF_amount.get_properties() + \
	TF_brickmodtex.get_properties() + \
	TF_brickrun.get_properties() + \
	TF_bricktex.get_properties() + \
	TF_mortartex.get_properties() + \
	TF_tex1.get_properties() + \
	TF_tex2.get_properties() + \
	TF_inside.get_properties() + \
	TF_outside.get_properties() + \
	TC_brickmodtex.get_properties() + \
	TC_brickrun.get_properties() + \
	TC_bricktex.get_properties() + \
	TC_mortartex.get_properties() + \
	TC_tex1.get_properties() + \
	TC_tex2.get_properties()

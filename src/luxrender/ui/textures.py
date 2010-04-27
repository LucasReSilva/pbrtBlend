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
from ..properties.util import has_property
from ..properties.texture import FloatTexture, ColorTexture

# TODO: Not sure how to morph type of tex1/tex2 from Float/Color depending on context
#TF_tex1 = FloatTexture('texture', 'tex1', 'Texture 1', 'luxrender_texture')
#TF_tex2 = FloatTexture('texture', 'tex2', 'Texture 2', 'luxrender_texture')

TF_A				= FloatTexture('texture', 'A', 'A', 'luxrender_texture')
TF_amount			= FloatTexture('texture', 'amount', 'Amount', 'luxrender_texture')
TF_B				= FloatTexture('texture', 'B', 'B', 'luxrender_texture')
TF_brickbevel		= FloatTexture('texture', 'brickbevel', 'Bevel', 'luxrender_texture')
TF_brickdepth		= FloatTexture('texture', 'brickdepth', 'Depth', 'luxrender_texture')
TF_brickheight		= FloatTexture('texture', 'brickheight', 'Height', 'luxrender_texture')
TF_brickwidth		= FloatTexture('texture', 'brickwidth', 'Width', 'luxrender_texture')
TF_C				= FloatTexture('texture', 'C', 'C', 'luxrender_texture')
TF_cauchya			= FloatTexture('texture', 'cauchya', 'Cauchy A', 'luxrender_texture')
TF_cauchyb			= FloatTexture('texture', 'cauchyb', 'Cauchy B', 'luxrender_texture')
TF_energy			= FloatTexture('texture', 'evergy', 'Energy', 'luxrender_texture')
TF_freq				= FloatTexture('texture', 'freq', 'Frequency', 'luxrender_texture')
TF_gain				= FloatTexture('texture', 'gain', 'Gain', 'luxrender_texture')
TF_gamma			= FloatTexture('texture', 'gamma', 'Gamma', 'luxrender_texture')
TF_index			= FloatTexture('texture', 'index', 'IOR', 'luxrender_texture')
TF_inside			= FloatTexture('texture', 'inside', 'Inside', 'luxrender_texture')
TF_maxanisotropy	= FloatTexture('texture', 'maxanisotropy', 'Max Anisotropy', 'luxrender_texture')
TF_mortarsize		= FloatTexture('texture', 'mortarsize', 'Mortar Size', 'luxrender_texture')
TF_outside			= FloatTexture('texture', 'outside', 'Outside', 'luxrender_texture')
TF_wavelength		= FloatTexture('texture', 'wavelength', 'Wavelength', 'luxrender_texture')
TF_width			= FloatTexture('texture', 'width', 'Width', 'luxrender_texture')
TF_temperature		= FloatTexture('texture', 'temperature', 'Temperature', 'luxrender_texture', min=1500.0, max=15000.0, default=6500.0)

def texture_visibility():
	vis = {}
	
	vis.update( TF_A.get_visibility() )
	vis.update( TF_amount.get_visibility() )
	vis.update( TF_B.get_visibility() )
	vis.update( TF_brickbevel.get_visibility() )
	vis.update( TF_brickdepth.get_visibility() )
	vis.update( TF_brickheight.get_visibility() )
	vis.update( TF_brickwidth.get_visibility() )
	vis.update( TF_C.get_visibility() )
	vis.update( TF_cauchya.get_visibility() )
	vis.update( TF_cauchyb.get_visibility() )
	vis.update( TF_energy.get_visibility() )
	vis.update( TF_freq.get_visibility() )
	vis.update( TF_gain.get_visibility() )
	vis.update( TF_gamma.get_visibility() )
	vis.update( TF_index.get_visibility() )
	vis.update( TF_inside.get_visibility() )
	vis.update( TF_maxanisotropy.get_visibility() )
	vis.update( TF_mortarsize.get_visibility() )
	vis.update( TF_outside.get_visibility() )
	vis.update( TF_wavelength.get_visibility() )
	vis.update( TF_width.get_visibility() )
	vis.update( TF_temperature.get_visibility() )
	
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
		
			for p in self.controls:
				self.draw_column(p, self.layout, context.texture, supercontext=context)
				
	controls = [
		'texture',
	] + \
	TF_A.get_controls() + \
	TF_amount.get_controls() + \
	TF_B.get_controls() + \
	TF_brickbevel.get_controls() + \
	TF_brickdepth.get_controls() + \
	TF_brickheight.get_controls() + \
	TF_brickwidth.get_controls() + \
	TF_C.get_controls() + \
	TF_cauchya.get_controls() + \
	TF_cauchyb.get_controls() + \
	TF_energy.get_controls() + \
	TF_freq.get_controls() + \
	TF_gain.get_controls() + \
	TF_gamma.get_controls() + \
	TF_index.get_controls() + \
	TF_inside.get_controls() + \
	TF_maxanisotropy.get_controls() + \
	TF_mortarsize.get_controls() + \
	TF_outside.get_controls() + \
	TF_wavelength.get_controls() + \
	TF_width.get_controls() + \
	TF_temperature.get_controls()
	
	visibility = texture_visibility()
	
	properties = [
		{
			'attr': 'texture',
			'type': 'enum',
			'name': 'Type',
			'description': 'LuxRender Texture Type',
			'items': [
				('blackbody', 'Blackbody', 'blackbody'),
			],
		},
	] + \
	TF_A.get_properties() + \
	TF_amount.get_properties() + \
	TF_B.get_properties() + \
	TF_brickbevel.get_properties() + \
	TF_brickdepth.get_properties() + \
	TF_brickheight.get_properties() + \
	TF_brickwidth.get_properties() + \
	TF_C.get_properties() + \
	TF_cauchya.get_properties() + \
	TF_cauchyb.get_properties() + \
	TF_energy.get_properties() + \
	TF_freq.get_properties() + \
	TF_gain.get_properties() + \
	TF_gamma.get_properties() + \
	TF_index.get_properties() + \
	TF_inside.get_properties() + \
	TF_maxanisotropy.get_properties() + \
	TF_mortarsize.get_properties() + \
	TF_outside.get_properties() + \
	TF_wavelength.get_properties() + \
	TF_width.get_properties() + \
	TF_temperature.get_properties()

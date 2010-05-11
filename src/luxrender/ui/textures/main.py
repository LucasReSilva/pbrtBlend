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

from properties_texture import TextureButtonsPanel

from ef.ui import described_layout
from ef.ef import ef

from ...properties.texture import luxrender_texture

class ui_panel_main(TextureButtonsPanel, described_layout):
	'''
	Texture Editor UI Panel
	'''
	
	bl_label = 'LuxRender Textures'
	bl_show_header = False
	
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender_texture
	# prevent creating luxrender_texture property group in Scene
	property_group_non_global = True
	
	def poll(self, context):
		'''
		Only show LuxRender panel with 'Plugin' texture type
		'''
		
		return TextureButtonsPanel.poll(self, context) # and context.texture.type == 'PLUGIN'
	
	@classmethod
	def property_reload(r_class):
		for tex in bpy.data.textures:
			r_class.property_create(tex)
			
	@classmethod
	def property_create(r_class, texture):
		pg = r_class.property_group
		if not hasattr(texture, pg.__name__):
			ef.init_properties(texture, [{
				'type': 'pointer',
				'attr': pg.__name__,
				'ptype': pg,
				'name': pg.__name__,
				'description': pg.__name__
			}], cache=False)
			ef.init_properties(pg, r_class.properties, cache=False)
	
	# Overridden to provide data storage in the texture, not the scene
	def draw(self, context):
		if context.texture is not None:
			self.property_create(context.texture)
			
			context.texture.luxrender_texture.use_lux_texture = (context.texture.type == 'PLUGIN')
			
			for p in self.controls:
				self.draw_column(p, self.layout, context.texture, supercontext=context)
				
	controls = [
		'type'
	]
	visibility = {
		'type': { 'use_lux_texture': True }
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
				('bilerp', 'bilerp', 'bilerp'),
				('blackbody','blackbody','blackbody'),
				('brick', 'brick', 'brick'),
				('checkerboard', 'checkerboard', 'checkerboard'),
				('dots', 'dots', 'dots'),
				('equalenergy', 'equalenergy', 'equalenergy'),
				('gaussian', 'gaussian', 'gaussian'),
				
				('imagemap', 'imagemap', 'imagemap'),
			],
		},
	]

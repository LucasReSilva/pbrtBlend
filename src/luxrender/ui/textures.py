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
from luxrender.ui import FloatTexture, ColorTexture

TF_tex1 = FloatTexture('tex1', 'Texture 1', 'luxrender_texture')
TF_tex2 = FloatTexture('tex2', 'Texture 2', 'luxrender_texture')

def texture_visibility():
	return {}

class texture_editor(context_panel, TextureButtonsPanel, described_layout):
	'''
	Texture Editor UI Panel
	'''
	
	bl_label = 'LuxRender Textures'
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender.properties.texture.luxrender_texture
	
	# prevent creating luxrender_texture property group in Scene
	property_group_non_global = True
	
	# Overridden to provide data storage in the texture, not the scene
	def draw(self, context):
		if context.texture is not None:
			if not hasattr(context.texture, self.property_group.__name__):
				ef.init_properties(context.texture, [{
					'type': 'pointer',
					'attr': self.property_group.__name__,
					'ptype': self.property_group,
					'name': self.property_group.__name__,
					'description': self.property_group.__name__
				}], cache=False)
				ef.init_properties(self.property_group, self.properties, cache=False)
			
			for p in self.controls:
				self.draw_column(p, self.layout, context.texture, supercontext=context)
	
	controls = [
		'type',
	] + \
	TF_tex1.get_controls() + \
	TF_tex2.get_controls()
	
	visibility = texture_visibility()
	
	properties = [
		{
			'attr': 'type',
			'type': 'enum',
			'name': 'Type',
			'description': 'LuxRender Texture Type',
			'items': [
				('scale','scale','scale'),
			],
		},
	] + \
	TF_tex1.get_properties() + \
	TF_tex2.get_properties()

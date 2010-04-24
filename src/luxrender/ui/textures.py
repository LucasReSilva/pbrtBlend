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

def ParamTextureFloat(attr, name, property_group, fl_default=0.0, fl_min=0.0, fl_max=1.0, rows=5, type='DEFAULT'):
	return [
		{
			'attr': '%s_type' % attr,
			'type': 'enum',
			'name': '%s Type' % name,
			'default': 'float',
			'items': [
				('float', 'Value', 'float'),
				('texture', 'Texture', 'texture'),
			]
		},
		{
			'attr': '%s_floatvalue' % attr,
			'type': 'float',
			'name': name,
			'default': fl_default,
			'min': fl_min,
			'soft_min': fl_min,
			'max': fl_max,
			'soft_max': fl_min,
		},
		{
			'attr': '%s_texturename' % attr,
			'type': 'string',
			'name': '%s_texturename' % attr,
			'description': '%s_texturename' % attr,
		},
		{
			'type': 'prop_object',
			'attr': '%s_texture' % attr,
			'src': lambda s,c: s.object.material_slots[s.object.active_material_index].material, #context_tex_datablock(s),
			'src_attr': 'texture_slots',
			'trg': lambda s,c: getattr(c, property_group),
			'trg_attr': '%s_texturename' % attr,
			'name': name
		},
	]

def ParamTextureColor(attr, name, property_group, rows=5, type='DEFAULT'):
	return [
		{
			'type': 'float_vector',
			'attr': attr,
			'name': name,
			'description': name,
			'default': (0.8,0.8,0.8),
			'subtype': 'COLOR',
			'precision': 5,
		},
#		{
#			'attr': '%s_texture' % attr,
#			'type': 'string',
#			'name': '%s_texture' % attr,
#			'description': '%s_texture' % attr,
#		},
#		{
#			'type': 'prop_object',
#			'attr': attr,
#			'src': lambda s,c: s.object.material_slots[s.object.active_material_index].material, #context_tex_datablock(s),
#			'src_attr': 'texture_slots',
#			'trg': lambda s,c: getattr(c, property_group),
#			'trg_attr': '%s_texture' % attr,
#			'name': name
#		},
	]

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
		
		'tex1',
		'tex2'
	]
	
	visibility = {
	}
	
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
	ParamTextureFloat('tex1', 'Texture 1', 'luxrender_texture') + \
	ParamTextureFloat('tex2', 'Texture 2', 'luxrender_texture')

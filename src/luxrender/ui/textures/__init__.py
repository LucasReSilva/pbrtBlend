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
from ef.ef import init_properties

class luxrender_texture_base(TextureButtonsPanel, described_layout):
	'''
	This is the base class for all LuxRender texture sub-panels.
	All subpanels should have their own property_groups, and define
	a string attribute in thier property_group called 'variant'.
	It should be set to either 'float' or 'color' depending on the
	texture type, and may display the choice to the user as a switch,
	or keep it as a hidden attribute if the texture is mono-typed.
	'''
	
	bl_show_header = False
	COMPAT_ENGINES = {'luxrender'}
	LUX_COMPAT = set()
	property_group_non_global = True
	
	@classmethod
	def property_reload(r_class):
		for tex in bpy.data.textures:
			r_class.property_create(tex.luxrender_texture)
	
	@classmethod
	def property_create(r_class, lux_tex_property_group):
		if not hasattr(lux_tex_property_group, r_class.property_group.__name__):
			init_properties(lux_tex_property_group, [{
				'type': 'pointer',
				'attr': r_class.property_group.__name__,
				'ptype': r_class.property_group,
				'name': r_class.property_group.__name__,
				'description': r_class.property_group.__name__
			}], cache=False)
			init_properties(r_class.property_group, r_class.properties, cache=False)
	
	# Overridden to provide data storage in the material, not the scene
	def draw(self, context):
		if context.texture is not None:
			self.property_create(context.texture.luxrender_texture)
			
			for p in self.controls:
				self.draw_column(p, self.layout, context.texture.luxrender_texture, supercontext=context)
	
	@classmethod
	def poll(cls, context):
		'''
		Only show LuxRender panel with 'Plugin' texture type, and
		if luxrender_texture.type in LUX_COMPAT
		'''
		
		tex = context.texture
		return	tex and \
				(context.scene.render.engine in cls.COMPAT_ENGINES) and \
				context.texture.luxrender_texture.type in cls.LUX_COMPAT
				#(tex.type != 'NONE' or tex.use_nodes) and \
				#context.texture.type == 'PLUGIN' and \


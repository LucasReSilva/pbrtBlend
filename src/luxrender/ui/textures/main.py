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

from luxrender.ui.textures import luxrender_texture_base

class ui_panel_main(luxrender_texture_base, bpy.types.Panel):
	'''
	Texture Editor UI Panel
	'''
	
	bl_label = 'LuxRender Textures'
	bl_options = {'HIDE_HEADER'}
	
	display_property_groups = [
		'luxrender_texture'
	]
	
	@classmethod
	def poll(cls, context):
		'''
		Only show LuxRender panel with 'Plugin' texture type
		'''
		
		tex = context.texture
		return	tex and \
				(context.scene.render.engine in cls.COMPAT_ENGINES) \
				and context.texture.luxrender_texture.type is not 'BLENDER'
				#(tex.type != 'NONE' or tex.use_nodes) and \
	
	# Overridden to draw property groups from texture object, not the scene
	def draw(self, context):
		if context.texture is not None:
			
			context.texture.luxrender_texture.use_lux_texture = (context.texture.luxrender_texture != 'BLENDER')
			
			for property_group_name in self.display_property_groups:
				property_group = getattr(context.texture, property_group_name)
				for p in property_group.controls:
					self.draw_column(p, self.layout, context.texture, supercontext=context, property_group=property_group)

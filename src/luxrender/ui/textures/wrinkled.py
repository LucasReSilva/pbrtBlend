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
from luxrender.ui.textures import luxrender_texture_base

class wrinkled(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		wrinkled_params = ParamSet().add_integer('octaves', self.octaves) \
									.add_float('roughness', self.roughness)
		
		return {'3DMAPPING'}, wrinkled_params

class ui_panel_wrinkled(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender wrinkled Texture'
	
	LUX_COMPAT = {'wrinkled'}
	
	property_group = wrinkled
	
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

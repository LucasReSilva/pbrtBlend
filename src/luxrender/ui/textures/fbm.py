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

from ...export import ParamSet
from ..textures import luxrender_texture_base

class fbm(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		fbm_params = ParamSet().add_integer('octaves', self.octaves) \
							   .add_float('roughness', self.roughness)
		
		return {'3DMAPPING'}, fbm_params

class ui_panel_fbm(luxrender_texture_base):
	bl_label = 'LuxRender fbm Texture'
	
	LUX_COMPAT = {'fbm'}
	
	property_group = fbm
	
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
			'default': 8
		},
		{
			'type': 'float',
			'attr': 'roughness',
			'name': 'Roughness',
			'default': 0.5
		},
	]

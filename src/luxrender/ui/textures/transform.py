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

from ef.validate import Logic_OR as O

from luxrender.export import ParamSet, get_worldscale
from luxrender.ui.textures import luxrender_texture_base

class transform(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		transform_params = ParamSet()
		
		ws = get_worldscale(as_scalematrix=False)
		
		transform_params.add_vector('translate', [i*ws for i in self.translate])
		transform_params.add_vector('rotate', self.rotate)
		transform_params.add_vector('scale', [i*ws for i in self.scale])
		
		return transform_params

class ui_panel_transform(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender Texture Transform'
	bl_default_closed = True
	bl_show_header = True
	
	LUX_COMPAT = {'BLENDER', 'brick', 'checkerboard', 'fbm', 'marble', 'windy', 'wrinkled'}
	
	property_group = transform
	
	controls = [
		'translate',
		'rotate',
		'scale',
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'float_vector',
			'attr': 'translate',
			'name': 'Translate',
			'default': (0.0, 0.0, 0.0),
		},
		{
			'type': 'float_vector',
			'attr': 'rotate',
			'name': 'Rotate',
			'default': (0.0, 0.0, 0.0),
		},
		{
			'type': 'float_vector',
			'attr': 'scale',
			'name': 'Scale',
			'default': (1.0, 1.0, 1.0),
		},
	]

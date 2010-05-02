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

from ..textures import luxrender_texture_base

class bilerp(bpy.types.IDPropertyGroup):
	pass

class ui_panel_bilerp(luxrender_texture_base):
	bl_label = 'LuxRender BiLerp Texture'
	
	LUX_COMPAT = {'bilerp'}
	
	property_group = bilerp
	
	controls = [
		['v00', 'v01'],
		['v10', 'v11'],
	]
	
	properties = [
		{
			'attr': 'v00',
			'type': 'float',
			'name': '(0,0)',
			'default': 0.0
		},
		{
			'attr': 'v01',
			'type': 'float',
			'name': '(0,1)',
			'default': 1.0
		},
		{
			'attr': 'v10',
			'type': 'float',
			'name': '(1,0)',
			'default': 0.0
		},
		{
			'attr': 'v11',
			'type': 'float',
			'name': '(1,1)',
			'default': 1.0
		},
	]

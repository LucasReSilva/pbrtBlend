# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
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
from extensions_framework import declarative_property_group

from .. import LuxRenderAddon

@LuxRenderAddon.addon_register_class
class luxrender_object(declarative_property_group):
	ef_attach_to = ['Object']
	
	controls = [
		'append_external_mesh',
		['use_smoothing', 'hide_proxy_mesh'],
		'external_mesh'
	]
	visibility = {
		'use_smoothing':	{ 'append_external_mesh': True },
		'hide_proxy_mesh':	{ 'append_external_mesh': True },
		'external_mesh':	{ 'append_external_mesh': True },
	}
	properties = [
		{
			'type': 'bool',
			'attr': 'append_external_mesh',
			'name': 'External PLY or STL Mesh',
			'description': 'Use this object to place an external PLY or STL mesh file in the scene',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 'use_smoothing',
			'name': 'Use smoothing',
			'description': 'Smooth the external mesh data',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 'hide_proxy_mesh',
			'name': 'Hide proxy',
			'description': 'Don\'t export this object\'s data',
			'default': True
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'external_mesh',
			'name': 'Mesh file',
			'description': 'External PLY or STL mesh file to place in scene',
		}
	]

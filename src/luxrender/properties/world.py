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
from extensions_framework import declarative_property_group, ef_initialise_properties

from .material import VolumeParameter

def WorldVolumeParameter(attr, name):
	return [
		{
			'attr': '%s_volume' % attr,
			'type': 'string',
			'name': '%s_volume' % attr,
			'description': '%s_volume' % attr,
			'save_in_preset': True
		},
		{
			'type': 'prop_search',
			'attr': attr,
			'src': lambda s,c: s.scene.luxrender_volumes,
			'src_attr': 'volumes',
			'trg': lambda s,c: c.luxrender_world,
			'trg_attr': '%s_volume' % attr,
			'name': name
		},
	]

@ef_initialise_properties
class luxrender_world(declarative_property_group):
	ef_attach_to = ['Scene']
	
	controls = [
		'default_interior',
		'default_exterior'
	]
	
	properties = [] + \
		WorldVolumeParameter('default_interior', 'Default Interior') + \
		WorldVolumeParameter('default_exterior', 'Default Exterior')

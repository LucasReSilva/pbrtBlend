# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Daniel Genrich
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
from ef import declarative_property_group

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

class luxrender_mesh(declarative_property_group):
	'''
	Storage class for LuxRender Camera settings.
	This class will be instantiated within a Blender
	mesh object.
	'''
	
	controls = [
		'portal',
		['subdiv','sublevels'],
		['nsmooth', 'sharpbound'],
	]
	
	visibility = {
		
		'nsmooth':		{ 'subdiv': True },
		'sharpbound':	{ 'subdiv': True },
		'sublevels':	{ 'subdiv': True }
	}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'portal',
			'name': 'Exit Portal',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'subdiv',
			'name': 'Use Subdivision',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'nsmooth',
			'name': 'Use Autosmoothing',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'sharpbound',
			'name': 'Sharpen Bounds',
			'default': False,
		},
		{
			'type': 'int',
			'attr': 'sublevels',
			'name': 'Subdivision Levels',
			'default': 2,
			'min': 0,
			'soft_min': 0,
			'max': 15,
			'soft_max': 15
		},
	]
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

from luxrender.properties.texture import ColorTextureParameter

class luxrender_object(declarative_property_group):
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
			'name': 'External PLY Mesh',
			'description': 'Use this object to place an external PLY mesh file in the scene',
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
			'description': 'External PLY mesh file to place in scene',
		}
	]

class EmissionColorTextureParameter(ColorTextureParameter):
	def texture_slot_set_attr(self):
		# Looks in a different location than other ColorTextureParameters
		return lambda s,c: c.luxrender_emission

TC_L = EmissionColorTextureParameter('L', 'Emission color', default=(1.0,1.0,1.0) )

class luxrender_emission(declarative_property_group):
	'''
	Storage class for LuxRender Material emission settings.
	This class will be instantiated within a Blender Object.
	'''
	
	controls = [
		'use_emission',
		'lightgroup',
	] + \
	TC_L.controls + \
	[
		'gain',
		'power',
		'efficacy',
	]
	
	visibility = {
		'lightgroup': 			{ 'use_emission': True },
		'L_colorlabel': 		{ 'use_emission': True },
		'L_color': 				{ 'use_emission': True },
		'L_usecolorrgc':		{ 'use_emission': True },
		'L_usecolortexture':	{ 'use_emission': True },
		'L_colortexture':		{ 'use_emission': True, 'L_usecolortexture': True },
		'gain': 				{ 'use_emission': True },
		'power': 				{ 'use_emission': True },
		'efficacy': 			{ 'use_emission': True },
	}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'use_emission',
			'name': 'Use Emission',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'string',
			'attr': 'lightgroup',
			'name': 'Light Group',
			'default': 'default',
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'gain',
			'name': 'Gain',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e8,
			'soft_max': 1e8,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'power',
			'name': 'Power',
			'default': 100.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e5,
			'soft_max': 1e5,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'efficacy',
			'name': 'Efficacy',
			'default': 17.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e4,
			'soft_max': 1e4,
			'save_in_preset': True
		},
	] + \
	TC_L.properties

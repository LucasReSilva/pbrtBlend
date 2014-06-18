# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli
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

from ..extensions_framework import declarative_property_group
from ..extensions_framework.validate import Logic_OR as O, Logic_Operator as LO

from .. import LuxRenderAddon
from ..outputs.luxcore_api import ScenePrefix

@LuxRenderAddon.addon_register_class
class luxcore_enginesettings(declarative_property_group):
	'''
	Storage class for LuxCore engine settings.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		'engine',
		'custom_properties',
		# BIASPATH
		'biaspath_tilesize',
		'biaspath_totaldepth', 
		['biaspath_diffusedepth', 'biaspath_glossydepth', 'biaspath_speculardepth'],
	]
	
	visibility = {
		# BIASPATH
		'biaspath_tilesize':			{ 'engine': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_totaldepth':			{ 'engine': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_diffusedepth':		{ 'engine': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_glossydepth':			{ 'engine': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_speculardepth':		{ 'engine': O(['BIASPATHCPU', 'BIASPATHOCL']) },
	}
	
	alert = {}
	
	properties = [
		{
			'type': 'enum', 
			'attr': 'engine',
			'name': 'Rendering engine',
			'description': 'Render engine to use',
			'default': 'PATHCPU',
			'items': [
				('PATHCPU', 'Path', 'Path tracer'),
				('PATHOCL', 'Path OpenCL', 'Pure OpenCL path tracer'),
				('BIASPATHCPU', 'Biased Path', 'Biased path tracer'),
				('BIASPATHOCL', 'Biased Path OpenCL', 'Pure OpenCL biased path tracer'),
				('BIDIRCPU', 'Bidir', 'Bidirectional path tracer'),
				('BIDIRVMCPU', 'BidirVCM', 'Bidirectional path tracer with vertex merging'),
			],
			'save_in_preset': True
		},
		{
			'type': 'string',
			'attr': 'custom_properties',
			'name': 'Custom properties',
			'description': 'LuxCore custom properties (separated by \'|\', suggested only for advanced users)',
			'default': '',
			'save_in_preset': True
		},
		########################################################################
		# BIASPATH
		########################################################################
		{
			'type': 'int', 
			'attr': 'biaspath_tilesize',
			'name': 'Tile size',
			'description': 'Tile size in pixel',
			'default': 32,
			'min': 8,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_totaldepth',
			'name': 'Max Total Depth',
			'description': 'Max recursion total depth for a path',
			'default': 10,
			'min': 1,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_diffusedepth',
			'name': 'Max Diffuse Depth',
			'description': 'Max recursion depth for a diffuse path',
			'default': 2,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_glossydepth',
			'name': 'Max Glossy Depth',
			'description': 'Max recursion depth for a glossy path',
			'default': 1,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_speculardepth',
			'name': 'Max Specular Depth',
			'description': 'Max recursion depth for a specular path',
			'default': 2,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
	]

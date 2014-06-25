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
		'renderengine_type',
		'custom_properties',
		# BIASPATH
		'label_tiles',
		'tile_size',
		'tile_multipass_enable',
		'tile_multipass_convergencetest_threshold',
		'tile_multipass_convergencetest_threshold_reduction',
		'label_sampling',
		'biaspath_sampling_aa_size',
		['biaspath_sampling_diffuse_size', 'biaspath_sampling_glossy_size', 'biaspath_sampling_specular_size'],
		'label_path_depth',
		'biaspath_pathdepth_total', 
		['biaspath_pathdepth_diffuse', 'biaspath_pathdepth_glossy', 'biaspath_pathdepth_specular'],
		'label_clamping',
		'biaspath_clamping_radiance_maxvalue',
		'biaspath_clamping_pdf_value',
	]
	
	visibility = {
		# BIASPATH
		'tile_size':							{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'tile_multipass_enable':				{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'tile_multipass_convergencetest_threshold':	
												{ 'tile_multipass_enable': True, 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'tile_multipass_convergencetest_threshold_reduction':
												{ 'tile_multipass_enable': True, 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'label_sampling':						{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_sampling_aa_size':			{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_sampling_diffuse_size':		{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_sampling_glossy_size':		{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_sampling_specular_size':		{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'label_path_depth':						{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_pathdepth_total':				{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_pathdepth_diffuse':			{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_pathdepth_glossy':			{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_pathdepth_specular':			{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'label_clamping':						{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_clamping_radiance_maxvalue':	{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
		'biaspath_clamping_pdf_value':			{ 'renderengine_type': O(['BIASPATHCPU', 'BIASPATHOCL']) },
	}
	
	alert = {}
	
	properties = [
		{
			'type': 'enum', 
			'attr': 'renderengine_type',
			'name': 'Rendering engine',
			'description': 'Rendering engine to use',
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
			'type': 'text', 
			'name': 'Tiles:',
			'attr': 'label_tiles',
		},
		{
			'type': 'int', 
			'attr': 'tile_size',
			'name': 'Tile size',
			'description': 'Tile width and height in pixels',
			'default': 32,
			'min': 8,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'bool', 
			'attr': 'tile_multipass_enable',
			'name': 'Enable halt condition',
			'description': 'Enable halt condition (and multi-pass)',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'float', 
			'attr': 'tile_multipass_convergencetest_threshold',
			'name': 'Error threshold:',
			'description': 'Max acceptable error for a tile',
			'default': 0.04,
			'min': 0.001,
			'max': 0.9,
			'save_in_preset': True
		},
		{
			'type': 'float', 
			'attr': 'tile_multipass_convergencetest_threshold_reduction',
			'name': 'Error threshold reduction:',
			'description': 'Avoid to stop the rendering and reduce the error threshold instead (0.0 = disabled)',
			'default': 0.0,
			'min': 0.0,
			'max': 0.99,
			'save_in_preset': True
		},
		{
			'type': 'text', 
			'name': 'Sampling:',
			'attr': 'label_sampling',
		},
		{
			'type': 'int', 
			'attr': 'biaspath_sampling_aa_size',
			'name': 'AA',
			'description': 'Anti-aliasing sampling (size x size)',
			'default': 3,
			'min': 1,
			'max': 64,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_sampling_diffuse_size',
			'name': 'Diffuse materials',
			'description': 'Diffuse materials sampling (size x size)',
			'default': 2,
			'min': 1,
			'max': 64,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_sampling_glossy_size',
			'name': 'Glossy materials',
			'description': 'Glossy materials sampling (size x size)',
			'default': 2,
			'min': 1,
			'max': 64,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_sampling_specular_size',
			'name': 'Specular materials',
			'description': 'Specular materials sampling (size x size)',
			'default': 1,
			'min': 1,
			'max': 64,
			'save_in_preset': True
		},
		{
			'type': 'text', 
			'name': 'Path depths:',
			'attr': 'label_path_depth',
		},
		{
			'type': 'int', 
			'attr': 'biaspath_pathdepth_total',
			'name': 'Max Total Depth',
			'description': 'Max recursion total depth for a path',
			'default': 10,
			'min': 1,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_pathdepth_diffuse',
			'name': 'Max Diffuse Depth',
			'description': 'Max recursion depth for a diffuse path',
			'default': 2,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_pathdepth_glossy',
			'name': 'Max Glossy Depth',
			'description': 'Max recursion depth for a glossy path',
			'default': 1,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'biaspath_pathdepth_specular',
			'name': 'Max Specular Depth',
			'description': 'Max recursion depth for a specular path',
			'default': 2,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'text', 
			'name': 'Clamping:',
			'attr': 'label_clamping',
		},
		{
			'type': 'float', 
			'attr': 'biaspath_clamping_radiance_maxvalue',
			'name': 'Radiance clamping',
			'description': 'Max acceptable radiance value for a sample',
			'default': 10.0,
			'min': 0,
			'max': 999999.0,
			'save_in_preset': True
		},
		{
			'type': 'float', 
			'attr': 'biaspath_clamping_pdf_value',
			'name': 'PDF clamping',
			'description': 'Max acceptable PDF (0.0 = disabled)',
			'default': 0.0,
			'min': 0,
			'max': 999.0,
			'save_in_preset': True
		},
	]

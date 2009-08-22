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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
class properties():
	
	# This render engine's UI display name
	__label__ = 'LuxRender'
	
	# This should match the engine __main__ class name,
	# and is used to detect if the UI should draw engine-
	# specific panels etc.
	context_name = 'luxrender'
	
	all_properties = []
	
	@classmethod
	def get_all_properties(r_class):
		for p in r_class.properties:
			r_class.all_properties.append(p)
		
		for s in [r_class.sampler_properties,
				  r_class.integrator_properties]:
			for p in s.values():
				for pp in p:
					r_class.all_properties.append(pp)
		
		return r_class.all_properties
	
	# Main Engine Render Settings
	properties = [
		{
			'type': 'enum',
			'attr': 'lux_sampler',
			'name': 'Pixel Sampler',
			'description': 'Pixel Sampler',
			'default': 'metropolis',
			'items': [
				('metropolis', 'metropolis', 'Metropolis'),
				('erpt', 'erpt', 'ERPT'),
				('lowdiscrepancy', 'lowdiscrepancy', 'Low Discrepancy'),
				('random', 'random', 'Random')
			]
		},
		{
			'type': 'enum', 
			'attr': 'lux_surfaceintegrator',
			'name': 'Surface Integrator',
			'description': 'Surface Integrator',
			'default': 'bidirectional',
			'items': [
				('directlighting', 'directlighting', 'Direct Lighting'),
				('path', 'path', 'Path'),
				('bidirectional', 'bidirectional', 'Bi-Directional'),
				('distributedpath', 'distributedpath', 'Distributed Path')
			]
		},
		{
			'type': 'enum',
			'attr': 'lux_volumeintegrator',
			'name': 'Volume Integrator',
			'description': 'Volume Integrator',
			'default': 'single',
			'items': [
				('emission', 'emission', 'Emission'),
				('single', 'single', 'Single'),
			]
		},
		{
			'type': 'enum',
			'attr': 'lux_filter',
			'name': 'Filter',
			'description': 'Pixel sampling filter',
			'default': 'mitchell',
			'items': [
				('box', 'box', 'Box'),
				('gaussian', 'gaussian', 'Gaussian'),
				('mitchell', 'mitchell', 'Mitchell'),
				('sinc', 'sinc', 'Sinc'),
				('triangle', 'triangle', 'Triangle'),
			]
		},
	]
	
	# Sampler Render Settings
	sampler_properties = {
		# common is a special case, it shows up in all sampler types
		'common': [
			{
				'type': 'bool',
				'attr': 'lux_sampler_advanced',
				'name': 'Show Advanced Settings',
				'description': 'Configure advanced sampler settings',
				'default': False
			},
		],
		'common_advanced': [],
		'metropolis': [
			{
				'type': 'float',
				'attr': 'lux_sampler_metro_strength',
				'name': 'Mutation Strength',
				'description': 'Metropolis sampler mutation strength',
				'default': 0.66,
				'min': 0,
				'max': 1,
			},
		],
		'metropolis_advanced': [
			{
				'type': 'float',
				'attr': 'lux_sampler_metro_lmprob',
				'name': 'Large Mutation Probability',
				'description': 'Large Mutation Probability',
				'default': 0.4,
				'min': 0,
				'max': 1,
			},
			{
				'type': 'int', 
				'attr': 'lux_sampler_metro_mncr',
				'name': 'Max Consec Rejects',
				'description': 'Maximum number of consecutive rejections',
				'default': 512,
				'min': 0,
				'max': 32768,
			},
			{
				'type': 'int',
				'attr': 'lux_sampler_metro_initsamples',
				'name': 'Initial Samples', 'description': 'Initial Samples',
				'default': 262144,
				'min': 1,
				'max': 1000000,
			},
			{
				'type': 'bool',
				'attr': 'lux_sampler_metro_variance',
				'name': 'Use Variance',
				'description': 'Use Variance',
				'default': False,
			},
		],
		'erpt': [
			{
				'type': 'int',
				'attr': 'lux_sampler_erpt_initsamples',
				'name': 'Initial Samples', 'description': 'Initial Samples',
				'default': 100000,
				'min': 1,
				'max': 10000000,
			},
			{
				'type': 'int', 
				'attr': 'lux_sampler_erpt_chainlength',
				'name': 'Chain Length',
				'description': 'Chain Length',
				'default': 512,
				'min': 1,
				'max': 32768,
			},
			{
				'type': 'int', 
				'attr': 'lux_sampler_erpt_stratawidth',
				'name': 'Strata Width',
				'description': 'Strata Width',
				'default': 256,
				'min': 1,
				'max': 32768,
			},
		],
		'erpt_advanced': [],
		'lowdiscrepancy': [
			{
				'type': 'enum',
				'attr': 'lux_sampler_ld_pixelsampler',
				'name': 'Pixel Sampler',
				'description': 'Pixel sampling strategy',
				'default': 'lowdiscrepancy',
				'items': [
					('linear', 'linear', 'Linear'),
					('tile', 'tile', 'Tile'),
					('random', 'random', 'Random'),
					('vegas', 'vegas', 'Vegas'),
					('lowdiscrepancy', 'lowdiscrepancy', 'Low Discrepancy'),
					('hilbert', 'hilbert', 'Hilbert'),
				]
			},
			{
				'type': 'int', 
				'attr': 'lux_sampler_ld_samples',
				'name': 'Samples',
				'description': 'Average number of samples taken per pixel. More samples create a higher quality image at the cost of render time',
				'default': 4,
				'min': 1,
				'max': 8192,
			},
		],
		'lowdiscrepancy_advanced': [],
		'random': [
			{
				'type': 'enum',
				'attr': 'lux_sampler_rnd_pixelsampler',
				'name': 'Pixel Sampler',
				'description': 'Pixel sampling strategy',
				'default': 'vegas',
				'items': [
					('linear', 'linear', 'Linear'),
					('tile', 'tile', 'Tile'),
					('random', 'random', 'Random'),
					('vegas', 'vegas', 'Vegas'),
					('lowdiscrepancy', 'lowdiscrepancy', 'Low Discrepancy'),
					('hilbert', 'hilbert', 'Hilbert'),
				]
			},
			{
				'type': 'int', 
				'attr': 'lux_sampler_rnd_xsamples',
				'name': 'X Samples',
				'description': 'Samples in X dimension',
				'default': 2,
				'min': 1,
				'max': 512,
			},
			{
				'type': 'int', 
				'attr': 'lux_sampler_rnd_ysamples',
				'name': 'Y Samples',
				'description': 'Samples in Y dimension',
				'default': 2,
				'min': 1,
				'max': 512,
			},
		],
		'random_advanced': [],
	}
	
	integrator_properties = {
		# common is a special case, it shows up in all integrator types
		'common': [
			{
				'type': 'bool',
				'attr': 'lux_integrator_advanced',
				'name': 'Show Advanced Settings',
				'description': 'Configure advanced integrator settings',
				'default': False
			},
		],
		'common_advanced': [
			{
				'type': 'enum',
				'attr': 'lux_integrator_strategy',
				'name': 'Strategy',
				'description': 'Strategy',
				'default': 'auto',
				'items': [
					('auto', 'auto', 'Auto'),
					('one', 'one', 'One'),
					('all', 'all', 'All'),
				]
			},
		],
		'directlighting': [],
		'directlighting_advanced': [],
		'path': [],
		'path_advanced': [],
		'bidirectional': [
			{
				'type': 'int', 
				'attr': 'lux_integrator_bidir_depth',
				'name': 'Depth',
				'description': 'Max recursion depth for ray casting',
				'default': 16,
				'min': 5,
				'max': 32,
			},
		],
		'bidirectional_advanced': [
			{
				'type': 'int', 
				'attr': 'lux_integrator_bidir_edepth',
				'name': 'Eye Depth',
				'description': 'Max recursion depth for ray casting from eye',
				'default': 16,
				'min': 0,
				'max': 2048,
			},
			{
				'type': 'int', 
				'attr': 'lux_integrator_bidir_ldepth',
				'name': 'Light Depth',
				'description': 'Max recursion depth for ray casting from light',
				'default': 16,
				'min': 0,
				'max': 2048,
			},
		],
		'distributedpath': [],
		'distributedpath_advanced': [],
	}
	
	
	
	

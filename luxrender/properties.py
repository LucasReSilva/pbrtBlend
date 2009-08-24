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
		for s in [	r_class.engine_properties,
					r_class.sampler_properties,
					r_class.integrator_properties,
					r_class.volume_integrator_properties,
					r_class.filter_properties
				]:
			for p in s:
				r_class.all_properties.append(p)
		
		return r_class.all_properties
	
	# Main Engine Render Settings
	engine_properties = []
	
	sampler_layout = [
		'lux_sampler', 'lux_sampler_advanced',
		
		# metropolis
		'lux_sampler_metro_strength',										# simple
		['lux_sampler_metro_lmprob', 'lux_sampler_metro_mncr'],				# adv
		['lux_sampler_metro_initsamples','lux_sampler_metro_variance'],		# adv
		
		# erpt
		['lux_sampler_erpt_initsamples', 'lux_sampler_erpt_chainlength', 'lux_sampler_erpt_stratawidth'], # simple
		
		# lowdiscrepancy
		['lux_sampler_ld_pixelsampler', 'lux_sampler_ld_samples'],			# simple
		
		# random
		'lux_sampler_rnd_pixelsampler',
		['lux_sampler_rnd_xsamples', 'lux_sampler_rnd_ysamples'],			# simple 
	]
	
	sampler_properties = [
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
			'type': 'bool',
			'attr': 'lux_sampler_advanced',
			'name': 'Advanced',
			'description': 'Configure advanced sampler settings',
			'default': False
		},
		{
			'type': 'float',
			'attr': 'lux_sampler_metro_strength',
			'name': 'Strength',
			'description': 'Metropolis sampler mutation strength',
			'default': 0.66,
			'min': 0,
			'max': 1,
		},
		{
			'type': 'float',
			'attr': 'lux_sampler_metro_lmprob',
			'name': 'LM Prob',
			'description': 'Large Mutation Probability',
			'default': 0.4,
			'min': 0,
			'max': 1,
		},
		{
			'type': 'int', 
			'attr': 'lux_sampler_metro_mncr',
			'name': 'MNCR',
			'description': 'Maximum number of consecutive rejections',
			'default': 512,
			'min': 0,
			'max': 32768,
		},
		{
			'type': 'int',
			'attr': 'lux_sampler_metro_initsamples',
			'name': 'Initial',
			'description': 'Initial Samples',
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
		{
			'type': 'int',
			'attr': 'lux_sampler_erpt_initsamples',
			'name': 'Initial',
			'description': 'Initial Samples',
			'default': 100000,
			'min': 1,
			'max': 10000000,
		},
		{
			'type': 'int', 
			'attr': 'lux_sampler_erpt_chainlength',
			'name': 'Ch. Len.',
			'description': 'Chain Length',
			'default': 512,
			'min': 1,
			'max': 32768,
		},
		{
			'type': 'int', 
			'attr': 'lux_sampler_erpt_stratawidth',
			'name': 'Str. Width',
			'description': 'Strata Width',
			'default': 256,
			'min': 1,
			'max': 32768,
		},
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
	]
	
	integrator_layout = [
		'lux_surfaceintegrator',
		'lux_integrator_advanced',
		'lux_integrator_strategy',											# advanced
		
		# bidir
		'lux_integrator_bidir_depth',										# simple
		['lux_integrator_bidir_edepth', 'lux_integrator_bidir_ldepth'],		# advanced
	]
	
	integrator_properties = [
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
			'type': 'bool',
			'attr': 'lux_integrator_advanced',
			'name': 'Show Advanced Settings',
			'description': 'Configure advanced integrator settings',
			'default': False
		},
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
		{
			'type': 'int', 
			'attr': 'lux_integrator_bidir_depth',
			'name': 'Depth',
			'description': 'Max recursion depth for ray casting',
			'default': 16,
			'min': 5,
			'max': 32,
		},
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
	]
	
	volume_integrator_layout = [
		'lux_volumeintegrator', 'lux_volume_stepsize'
	]
	
	volume_integrator_properties = [
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
			'type': 'float',
			'attr': 'lux_volume_stepsize',
			'name': 'Step Size',
			'description': 'Volume Integrator Step Size',
			'default': 1,
			'min': 0,
			'soft_min': 0,
			'max': 100,
			'soft_max': 100,
		}
	]
	
	filter_layout = [
		'lux_filter'
	]
	
	filter_properties = [
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

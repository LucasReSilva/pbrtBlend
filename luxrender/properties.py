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
					r_class.filter_properties,
					r_class.accelerator_properties,
				]:
			for p in s:
				r_class.all_properties.append(p)
		
		return r_class.all_properties
	
	engine_layout = [
		['lux_threads_auto', 'lux_threads'],
		'lux_priority',
		['lux_rgc', 'lux_colclamp', 'lux_noopengl'],
		[ 'lux_meshopt', 'lux_nolg' ],
		
		'lux_singlefile',
		[ 'lux_file_lxs', 'lux_file_lxo', 'lux_file_lxm', 'lux_file_lxv' ],
	]
	
	engine_properties = [
		{
			'type': 'bool',
			'attr': 'lux_threads_auto',
			'name': 'Auto Threads',
			'description': 'Let LuxRender decide how many threads to use',
			'default': True
		},
		{
			'type': 'int',
			'attr': 'lux_threads',
			'name': 'Render Threads',
			'description': 'Number of threads to use',
			'default': 1,
			'min': 1,
			'soft_min': 1,
			'max': 64,
			'soft_max': 64
		},
		{
			'type': 'enum',
			'attr': 'lux_priority',
			'name': 'Process Priority',
			'description': 'Set the process priority for LuxRender',
			'default': 'belownormal',
			'items': [
				('low','Low','low'),
				('belownormal', 'Below Normal', 'belownormal'),
				('normal', 'Normal', 'normal'),
				('abovenormal', 'Above Normal', 'abovenormal'),
			]
		},
		{
			'type': 'bool',
			'attr': 'lux_noopengl',
			'name': 'No OpenGL',
			'description': 'Disable OpenGL viewport (for buggy display drivers)',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'lux_rgc',
			'name': 'RGC',
			'description': 'Reverse Gamma Colour Correction',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'lux_colclamp',
			'name': 'Colour Clamp',
			'description': 'Clamp all colours to range 0 - 0.9',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'lux_meshopt',
			'name': 'Optimise Meshes',
			'description': 'Output optimised mesh data',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'lux_nolg',
			'name': 'No Lightgroups',
			'description': 'Combine all light groups',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'lux_singlefile',
			'name': 'Combine LXS',
			'description': 'Write only a single LXS file',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'lux_file_lxs',
			'name': 'LXS',
			'description': 'Write LXS (Scene) file',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'lux_file_lxo',
			'name': 'LXO',
			'description': 'Write LXO (Objects) file',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'lux_file_lxm',
			'name': 'LXM',
			'description': 'Write LXM (Materials) file',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'lux_file_lxv',
			'name': 'LXV',
			'description': 'Write LXV (volumes) file',
			'default': True,
		},
	]
	
	sampler_layout = [
		[
			0.7,
			'lux_sampler',
			'lux_sampler_advanced',
		],
		
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
				('metropolis', 'Metropolis', 'metropolis'),
				('erpt', 'ERPT', 'erpt'),
				('lowdiscrepancy', 'Low Discrepancy', 'lowdiscrepancy'),
				('random', 'Random', 'random')
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
				('linear', 'Linear', 'linear'),
				('tile', 'Tile', 'tile'),
				('random', 'Random', 'random'),
				('vegas', 'Vegas', 'vegas'),
				('lowdiscrepancy', 'Low Discrepancy', 'lowdiscrepancy'),
				('hilbert', 'Hilbert', 'hilbert'),
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
				('linear', 'Linear', 'linear'),
				('tile', 'Tile', 'tile'),
				('random', 'Random', 'random'),
				('vegas', 'Vegas', 'vegas'),
				('lowdiscrepancy', 'Low Discrepancy', 'lowdiscrepancy'),
				('hilbert', 'Hilbert', 'hilbert'),
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
		[
			0.7,
			'lux_surfaceintegrator',
			'lux_integrator_advanced',
		],
		
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
				('directlighting', 'Direct Lighting', 'directlighting'),
				('path', 'Path', 'path'),
				('bidirectional', 'Bi-Directional', 'bidirectional'),
				('distributedpath', 'Distributed Path', 'distributedpath')
			]
		},
		{
			'type': 'bool',
			'attr': 'lux_integrator_advanced',
			'name': 'Advanced',
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
				('auto', 'Auto', 'auto'),
				('one', 'One', 'one'),
				('all', 'All', 'all'),
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
				('emission', 'Emission', 'emission'),
				('single', 'Single', 'single'),
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
		[
			0.75,
			'lux_filter',
			'lux_filter_advanced',
		],
		
		['lux_filter_xwidth', 'lux_filter_ywidth'],			# advanced
		'lux_filter_gaussian_alpha',						# gaussian advanced
		
		[
			0.4,
			'lux_filter_mitchell_mode',						# mitchell advanced
			'lux_filter_mitchell_b',						# mitchell advanced + mode=manual
			'lux_filter_mitchell_c',						# mitchell advanced + mode=manual
		],
		'lux_filter_mitchell_sharpness',					# mitchell simple || (mitchell advanced && mode = slider)
		
		'lux_filter_sinc_tau'								# sinc advanced
	]
	
	filter_properties = [
		{
			'type': 'enum',
			'attr': 'lux_filter',
			'name': 'Filter',
			'description': 'Pixel sampling filter',
			'default': 'mitchell',
			'items': [
				('box', 'Box', 'box'),
				('gaussian', 'Gaussian', 'gaussian'),
				('mitchell', 'Mitchell', 'mitchell'),
				('sinc', 'Sinc', 'sinc'),
				('triangle', 'Triangle', 'triangle'),
			]
		},
		{
			'type': 'bool',
			'attr': 'lux_filter_advanced',
			'name': 'Advanced',
			'description': 'Configure advanced filter settings',
			'default': False
		},
		{
			'type': 'float',
			'attr': 'lux_filter_xwidth',
			'name': 'X Width',
			'description': 'Width of filter in X dimension',
			'default': 2,
			'min': 0,
			'soft_min': 0,
			'max': 10,
			'soft_max': 10,
		},
		{
			'type': 'float',
			'attr': 'lux_filter_ywidth',
			'name': 'Y Width',
			'description': 'Width of filter in Y dimension',
			'default': 2,
			'min': 0,
			'soft_min': 0,
			'max': 10,
			'soft_max': 10,
		},
		{
			'type': 'float',
			'attr': 'lux_filter_gaussian_alpha',
			'name': 'Alpha',
			'description': 'Gaussian Alpha parameter',
			'default': 2,
			'min': 0,
			'soft_min': 0,
			'max': 10,
			'soft_max': 10,
		},
		{
			'type': 'float',
			'attr': 'lux_filter_mitchell_sharpness',
			'name': 'Sharpness',
			'description': 'Sharpness of Mitchell Filter',
			'default': 0.5,
			'min': 0,
			'soft_min': 0,
			'max': 1,
			'soft_max': 1,
		},
		{
			'type': 'enum',
			'attr': 'lux_filter_mitchell_mode',
			'name': 'Mode',
			'description': 'Mitchell Mode',
			'items': [
				('manual', 'Manual', 'manual'),
				('slider', 'Slider', 'slider'),
				#('preset', 'preset', 'Preset'),
			]
		},
		{
			'type': 'float',
			'attr': 'lux_filter_mitchell_b',
			'name': 'B',
			'description': 'Mitchell B parameter',
			'default': 0.333,
			'min': 0,
			'soft_min': 0,
			'max': 1,
			'soft_max': 1,
		},
		{
			'type': 'float',
			'attr': 'lux_filter_mitchell_c',
			'name': 'C',
			'description': 'Mitchell C parameter',
			'default': 0.333,
			'min': 0,
			'soft_min': 0,
			'max': 1,
			'soft_max': 1,
		},
		{
			'type': 'float',
			'attr': 'lux_filter_sinc_tau',
			'name': 'Tau',
			'description': 'Sinc Tau parameter',
			'default': 3,
			'min': 0,
			'soft_min': 0,
			'max': 10,
			'soft_max': 10,
		},
	]
	
	accelerator_layout = [
		'lux_accelerator',
		
		[ 'lux_accel_kd_intcost', 'lux_accel_kd_travcost' ],		# tabreckdtree
		[ 'lux_accel_kd_ebonus', 'lux_accel_kd_maxprims' ],			# tabreckdtree
		'lux_accel_kd_maxdepth',									# tabreckdtree
		
		'lux_accel_grid_refineim',									# grid
		
		'lux_accel_qbvh_maxprims',									# qbvh
	]
	
	accelerator_properties = [
		{
			'type': 'enum',
			'attr': 'lux_accelerator',
			'name': 'Accelerator',
			'description': 'Scene accelerator type',
			'default': 'tabreckdtree',
			'items': [
				('none', 'none', 'None'),
				('tabreckdtree', 'KD Tree', 'tabreckdtree'),
				('grid', 'Grid', 'grid'),
				('qbvh', 'QBVH', 'qbvh'),
			]
		},
		{
			'type': 'int',
			'attr': 'lux_accel_kd_intcost',
			'name': 'Inters. Cost',
			'description': 'Intersection Cost',
			'default': 80,
			'min': 0,
			'soft_min': 0,
			'max': 1000,
			'soft_max': 1000,
		},
		{
			'type': 'int',
			'attr': 'lux_accel_kd_travcost',
			'name': 'Trav. Cost',
			'description': 'Traversal Cost',
			'default': 1,
			'min': 0,
			'soft_min': 0,
			'max': 1000,
			'soft_max': 1000,
		},
		{
			'type': 'float',
			'attr': 'lux_accel_kd_ebonus',
			'name': 'Empty Bonus',
			'description': 'Empty Bonus',
			'default': 0.2,
			'min': 0,
			'soft_min': 0,
			'max': 100,
			'soft_max': 100,
		},
		{
			'type': 'int',
			'attr': 'lux_accel_kd_maxprims',
			'name': 'Max. Prims.',
			'description': 'Max Primitives',
			'default': 1,
			'min': 0,
			'soft_min': 0,
			'max': 1000,
			'soft_max': 1000,
		},
		{
			'type': 'int',
			'attr': 'lux_accel_kd_maxdepth',
			'name': 'Max. Depth',
			'description': 'Maximum Depth',
			'default': -1,
			'min': -1,
			'soft_min': -1,
			'max': 100,
			'soft_max': 100,
		},
		{
			'type': 'bool',
			'attr': 'lux_accel_grid_refineim',
			'name': 'Refine Immediately',
			'description': 'Refine Immediately',
			'default': False
		},
		{
			'type': 'int',
			'attr': 'lux_accel_qbvh_maxprims',
			'name': 'Max. Prims.',
			'description': 'Max Primitives per leaf',
			'default': 4,
			'min': 1,
			'soft_min': 1,
			'max': 64,
			'soft_max': 64,
		},
	]

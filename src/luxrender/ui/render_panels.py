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
from properties_render import RenderButtonsPanel

import ef.ui
from ef.validate import Logic_OR as O, Logic_AND as A

import luxrender.properties.engine
import luxrender.properties.sampler
import luxrender.properties.integrator
import luxrender.properties.volume
import luxrender.properties.filter
import luxrender.properties.accelerator

class render_described_context(RenderButtonsPanel, ef.ui.described_layout):
	'''
	Base class for render engine settings panels
	'''
	
	COMPAT_ENGINES = {'luxrender'}

class engine(render_described_context):
	'''
	Engine settings UI Panel
	'''
	
	bl_label = 'LuxRender Engine Configuration'
	
	property_group = luxrender.properties.engine.luxrender_engine
	
	controls = [
		'api_type',
		['threads_auto', 'threads'],
		'priority',
		['rgc', 'colclamp'],
		['meshopt', 'nolg'],
	]
	
	visibility = {
		'threads':				{ 'threads_auto': False },
	}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'threads_auto',
			'name': 'Auto Threads',
			'description': 'Let LuxRender decide how many threads to use',
			'default': True
		},
		{
			'type': 'int',
			'attr': 'threads',
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
			'attr': 'api_type',
			'name': 'Output type',
			'description': 'How to export the scene',
			'default': 'FILE',
			'items': [
				('FILE', 'Write files', 'FILE'),
				('API', 'Direct export', 'API')
			] 
		},
		{
			'type': 'enum',
			'attr': 'priority',
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
			'attr': 'rgc',
			'name': 'RGC',
			'description': 'Reverse Gamma Colour Correction',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'colclamp',
			'name': 'Colour Clamp',
			'description': 'Clamp all colours to range 0 - 0.9',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'meshopt',
			'name': 'Optimise Meshes',
			'description': 'Output optimised mesh data',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'nolg',
			'name': 'No Lightgroups',
			'description': 'Combine all light groups',
			'default': False,
		},
	]
			
class sampler(render_described_context):
	'''
	Sampler settings UI Panel
	'''
	
	bl_label = 'Sampler'
	
	property_group = luxrender.properties.sampler.luxrender_sampler
	
	controls = [
		[
			0.7,
			'sampler',
			'advanced',
		],
		'haltspp',
		
		# metropolis
		'metro_strength',							# simple
		['metro_lmprob', 'metro_mncr'],				# adv
		['metro_initsamples','metro_variance'],		# adv
		
		# erpt
		['erpt_initsamples', 'erpt_chainlength',
#		 'erpt_mutationrange'
		], # simple
		
		# random & lowdiscrepancy
		'pixelsampler',
		['pixelsamples'],			# simple 
	]
	
	visibility = {
		'advanced':				{ 'sampler': 'metropolis'},
	
		'metro_strength':		{ 'advanced': False, 'sampler': 'metropolis'},
		'metro_lmprob':			{ 'advanced': True , 'sampler': 'metropolis'},
		'metro_mncr':			{ 'advanced': True , 'sampler': 'metropolis'},
		'metro_initsamples':	{ 'advanced': True , 'sampler': 'metropolis'},
		'metro_variance':		{ 'advanced': True , 'sampler': 'metropolis'},
		
		'erpt_initsamples':		{ 'sampler': 'erpt'},
		'erpt_chainlength':		{ 'sampler': 'erpt'},
#		'erpt_mutationrange':   { 'sampler': 'erpt'},
		
		'pixelsampler':			{ 'sampler': O(['random', 'lowdiscrepancy']) },
		'pixelsamples':			{ 'sampler': O(['random', 'lowdiscrepancy']) },
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'sampler',
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
			'attr': 'advanced',
			'name': 'Advanced',
			'description': 'Configure advanced sampler settings',
			'default': False
		},
		{
			'type': 'int',
			'attr': 'haltspp',
			'name': 'Halt SPP',
			'description': 'Halt the rendering at this number od samples/px (0=disabled)',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 65535,
			'soft_max': 65535,
		},
		{
			'type': 'float',
			'attr': 'metro_strength',
			'name': 'Strength',
			'description': 'Metropolis sampler mutation strength',
			'default': 0.66,
			'min': 0,
			'max': 1,
		},
		{
			'type': 'float',
			'attr': 'metro_lmprob',
			'name': 'LM Prob',
			'description': 'Large Mutation Probability',
			'default': 0.4,
			'min': 0,
			'max': 1,
		},
		{
			'type': 'int', 
			'attr': 'metro_mncr',
			'name': 'MNCR',
			'description': 'Maximum number of consecutive rejections',
			'default': 512,
			'min': 0,
			'max': 32768,
		},
		{
			'type': 'int',
			'attr': 'metro_initsamples',
			'name': 'Initial',
			'description': 'Initial Samples',
			'default': 262144,
			'min': 1,
			'max': 1000000,
		},
		{
			'type': 'bool',
			'attr': 'metro_variance',
			'name': 'Use Variance',
			'description': 'Use Variance',
			'default': False,
		},
		{
			'type': 'int',
			'attr': 'erpt_initsamples',
			'name': 'Initial',
			'description': 'Initial Samples',
			'default': 100000,
			'min': 1,
			'max': 10000000,
		},
		{
			'type': 'int', 
			'attr': 'erpt_chainlength',
			'name': 'Ch. Len.',
			'description': 'Chain Length',
			'default': 512,
			'min': 1,
			'max': 32768,
		},
#		{
#			'type': 'int', 
#			'attr': 'erpt_mutationrange',
#			'name': 'Str. Width',
#			'description': 'Strata Width',
#			'default': 256,
#			'min': 1,
#			'max': 32768,
#		},
		{
			'type': 'enum',
			'attr': 'pixelsampler',
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
			'attr': 'pixelsamples',
			'name': 'Pixel Samples',
			'description': 'Average number of samples taken per pixel. More samples create a higher quality image at the cost of render time',
			'default': 4,
			'min': 1,
			'max': 8192,
		},

	]
				
class integrator(render_described_context):
	'''
	Surface Integrator settings UI Panel
	'''
	
	bl_label = 'Surface Integrator'
	
	property_group = luxrender.properties.integrator.luxrender_integrator
	
	controls = [
		[
			0.7,
			'surfaceintegrator',
			'advanced',
		],
		
		'strategy',								# advanced
		
		# bidir
		'bidir_depth',							# simple
		['bidir_edepth', 'bidir_ldepth'],		# advanced
	]
	
	visibility = {
		'strategy':		{ 'advanced': True },
		
		'bidir_depth':	{ 'advanced': False, 'surfaceintegrator': 'bidirectional' },
		'bidir_edepth':	{ 'advanced': True , 'surfaceintegrator': 'bidirectional' },
		'bidir_ldepth':	{ 'advanced': True , 'surfaceintegrator': 'bidirectional' },
	}
	
	properties = [
		{
			'type': 'enum', 
			'attr': 'surfaceintegrator',
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
			'attr': 'advanced',
			'name': 'Advanced',
			'description': 'Configure advanced integrator settings',
			'default': False
		},
		{
			'type': 'enum',
			'attr': 'strategy',
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
			'attr': 'bidir_depth',
			'name': 'Depth',
			'description': 'Max recursion depth for ray casting',
			'default': 16,
			'min': 5,
			'max': 32,
		},
		{
			'type': 'int', 
			'attr': 'bidir_edepth',
			'name': 'Eye Depth',
			'description': 'Max recursion depth for ray casting from eye',
			'default': 16,
			'min': 0,
			'max': 2048,
		},
		{
			'type': 'int', 
			'attr': 'bidir_ldepth',
			'name': 'Light Depth',
			'description': 'Max recursion depth for ray casting from light',
			'default': 16,
			'min': 0,
			'max': 2048,
		},
	]

class volume(render_described_context):
	'''
	Volume Integrator settings UI panel
	'''
	
	bl_label = 'Volume Integrator'
	
	property_group = luxrender.properties.volume.luxrender_volume
	
	controls = [
		'volumeintegrator', 'stepsize'
	]
	
	properties = [
		{
			'type': 'enum',
			'attr': 'volumeintegrator',
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
			'attr': 'stepsize',
			'name': 'Step Size',
			'description': 'Volume Integrator Step Size',
			'default': 1,
			'min': 0,
			'soft_min': 0,
			'max': 100,
			'soft_max': 100,
		}
	]
			
class filter(render_described_context):
	'''
	PixelFilter settings UI Panel
	'''
	
	bl_label = 'Filter'
	
	property_group = luxrender.properties.filter.luxrender_filter
	
	controls = [
		[
			0.75,
			'filter',
			'advanced',
		],
		
		['xwidth', 'ywidth'],			# advanced
		'gaussian_alpha',				# gaussian advanced
		
		[
			0.4,
			'mitchell_mode',			# mitchell advanced
			'mitchell_b',				# mitchell advanced + mode=manual
			'mitchell_c',				# mitchell advanced + mode=manual
		],
		'mitchell_sharpness',			# mitchell simple || (mitchell advanced && mode = slider)
		
		'sinc_tau'						# sinc advanced
	]
	
	visibility = {
		'xwidth':				{ 'advanced': True},
		'ywidth':				{ 'advanced': True},
		
		'gaussian_alpha':		{ 'advanced': True, 'filter': 'gaussian' },
		
		'mitchell_mode':		{ 'advanced': True, 'filter': 'mitchell' },
		'mitchell_b':			{ 'advanced': True, 'filter': 'mitchell', 'mitchell_mode': 'manual' },
		'mitchell_c':			{ 'advanced': True, 'filter': 'mitchell', 'mitchell_mode': 'manual' },		
		'mitchell_sharpness':	{ 'filter': 'mitchell' },
		
		'sinc_tau':				{ 'advanced': True, 'filter': 'sinc' },
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'filter',
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
			'attr': 'advanced',
			'name': 'Advanced',
			'description': 'Configure advanced filter settings',
			'default': False
		},
		{
			'type': 'float',
			'attr': 'xwidth',
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
			'attr': 'ywidth',
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
			'attr': 'gaussian_alpha',
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
			'attr': 'mitchell_sharpness',
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
			'attr': 'mitchell_mode',
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
			'attr': 'mitchell_b',
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
			'attr': 'mitchell_c',
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
			'attr': 'sinc_tau',
			'name': 'Tau',
			'description': 'Sinc Tau parameter',
			'default': 3,
			'min': 0,
			'soft_min': 0,
			'max': 10,
			'soft_max': 10,
		},
	]

class accelerator(render_described_context):
	'''
	Accelerator settings UI Panel
	'''
	
	bl_label = 'Accelerator'
	
	property_group = luxrender.properties.accelerator.luxrender_accelerator
	
	controls = [
		'accelerator',
		
		['kd_intcost', 'kd_travcost'],			# tabreckdtree
		['kd_ebonus', 'kd_maxprims'],			# tabreckdtree
		'kd_maxdepth',							# tabreckdtree
		
		'grid_refineim',						# grid
		
		'qbvh_maxprims',						# qbvh
	]
	
	visibility = {
		'kd_intcost':		{ 'accelerator': 'tabreckdtree' },
		'kd_travcost':		{ 'accelerator': 'tabreckdtree' },
		'kd_ebonus':		{ 'accelerator': 'tabreckdtree' },
		'kd_maxprims':		{ 'accelerator': 'tabreckdtree' },
		'kd_maxdepth':		{ 'accelerator': 'tabreckdtree' },
		'grid_refineim':	{ 'accelerator': 'grid' },
		'qbvh_maxprims':	{ 'accelerator': 'qbvh' },
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'accelerator',
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
			'attr': 'kd_intcost',
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
			'attr': 'kd_travcost',
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
			'attr': 'kd_ebonus',
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
			'attr': 'kd_maxprims',
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
			'attr': 'kd_maxdepth',
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
			'attr': 'grid_refineim',
			'name': 'Refine Immediately',
			'description': 'Refine Immediately',
			'default': False
		},
		{
			'type': 'int',
			'attr': 'qbvh_maxprims',
			'name': 'Max. Prims.',
			'description': 'Max Primitives per leaf',
			'default': 4,
			'min': 1,
			'soft_min': 1,
			'max': 64,
			'soft_max': 64,
		},
	]

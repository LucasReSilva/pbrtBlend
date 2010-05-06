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

from ..module.pure_api import PYLUX_AVAILABLE

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
		'export_type',
		['write_files', 'render'],
		['write_lxs', 'write_lxm', 'write_lxo'],
		'priority',
		['threads_auto', 'threads'],
		['rgc', 'colclamp'],
		['meshopt', 'nolg'],
	]
	
	visibility = {
		'write_files':			{ 'export_type': 'INT' },
		'render':				O([{'write_files': True}, {'export_type': 'EXT'}]),
		'write_lxs':			{ 'export_type': 'INT', 'write_files': True },
		'write_lxm':			{ 'export_type': 'INT', 'write_files': True },
		'write_lxo':			{ 'export_type': 'INT', 'write_files': True },
		'threads_auto':			A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }]),
		'threads':				A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }, { 'threads_auto': False }]),
		'priority':				{ 'export_type': 'EXT', 'render': True },
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
			'attr': 'export_type',
			'name': 'Renderer',
			'description': 'Run LuxRender inside or outside of Blender',
			'default': 'INT' if PYLUX_AVAILABLE else 'EXT',
			'items': [
				('EXT', 'External', 'EXT'),
				('INT', 'Internal', 'INT')
			] if PYLUX_AVAILABLE else [
				('EXT', 'External', 'EXT'),
			]
		},
		{
			'type': 'bool',
			'attr': 'render',
			'name': 'Run Renderer',
			'description': 'Run Renderer after export',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'write_files',
			'name': 'Write to disk',
			'description': 'Write scene files to disk',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'write_lxs',
			'name': 'LXS',
			'description': 'Write master scene file',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'write_lxm',
			'name': 'LXM',
			'description': 'Write materials file',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'write_lxo',
			'name': 'LXO',
			'description': 'Write objects file',
			'default': True,
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
		[ 0.7, 'sampler', 'advanced'],
		'haltspp',
		
		'chainlength',
		'mutationrange',
		'basesampler',
		
		'pixelsampler',
		'pixelsamples',
		
		'maxconsecrejects',
		'largemutationprob',
		'usevariance',
	]
	
	visibility = {
		'chainlength':			{ 'sampler': 'erpt' },
		'mutationrange':		{ 'advanced': True, 'sampler': O(['erpt', 'metropolis']) },
		'basesampler':			{ 'sampler': 'erpt' },
		'pixelsampler':			O([{ 'sampler': O(['lowdiscrepancy', 'random']) },			{'sampler':'erpt', 'basesampler':O(['lowdiscrepancy', 'random'])} ]),
		'pixelsamples':			O([{ 'sampler': O(['lowdiscrepancy', 'random']) },			{'sampler':'erpt', 'basesampler':O(['lowdiscrepancy', 'random'])} ]),
		'maxconsecrejects':		A([{ 'advanced': True }, O([{ 'sampler': 'metropolis' }, 	{'sampler':'erpt', 'basesampler': 'metropolis' } ]) ]),
		'largemutationprob':	O([{ 'sampler': 'metropolis' },								{'sampler':'erpt', 'basesampler': 'metropolis' } ]),
		'usevariance':			O([{ 'sampler': 'metropolis' },								{'sampler':'erpt', 'basesampler': 'metropolis' } ]),
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'sampler',
			'name': 'Sampler Type',
			'description': 'Sampler Type',
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
			'description': 'Halt the rendering at this number of samples/px (0=disabled)',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 65535,
			'soft_max': 65535,
		},
		{
			'type': 'float',
			'attr': 'largemutationprob',
			'name': 'Large Mutation Probability',
			'description': 'Large Mutation Probability',
			'default': 0.4,
			'min': 0,
			'max': 1,
		},
		{
			'type': 'int', 
			'attr': 'maxconsecrejects',
			'name': 'Max. Consecutive Rejections',
			'description': 'Maximum number of consecutive rejections',
			'default': 512,
			'min': 0,
			'max': 32768,
		},
		{
			'type': 'bool',
			'attr': 'usevariance',
			'name': 'Use Variance',
			'description': 'Use Variance',
			'default': False,
		},
		{
			'type': 'enum',
			'attr': 'basesampler',
			'name': 'Base Sampler',
			'items': [
				('random','random', 'random'),
				('lowdiscrepancy', 'lowdiscrepancy', 'lowdiscrepancy'),
				('metropolis', 'metropolis', 'metropolis')
			]
		},
		{
			'type': 'int', 
			'attr': 'chainlength',
			'name': 'Chain Length',
			'description': 'Chain Length',
			'default': 100,
			'min': 1,
			'max': 32768,
		},
		{
			'type': 'int', 
			'attr': 'mutationrange',
			'name': 'Mutation Range',
			'default': 256,
			'min': 1,
			'max': 32768,
		},
		{
			'type': 'enum',
			'attr': 'pixelsampler',
			'name': 'Pixel Sampler',
			'description': 'Pixel sampling strategy',
			'default': 'lowdiscrepancy',
			'items': [
				('linear', 'Linear', 'linear'),
				('tile', 'Tile', 'tile'),
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
		[0.7, 'accelerator', 'advanced'],
		
		'intersectcost',
		'traversalcost',
		'emptybonus'
		'treetype',
		'costsample',
		'maxprims',
		'maxdepth',
		'refineimmediately',
		'maxprimsperleaf',
		'fullsweepthreshold',
		'skipfactor',
	]
	
	visibility = {
		'intersectcost':		{ 'advanced': True, 'accelerator': O(['bvh', 'tabreckdtree']) },
		'traversalcost':		{ 'advanced': True, 'accelerator': O(['bvh', 'tabreckdtree']) },
		'emptybonus':			{ 'advanced': True, 'accelerator': O(['bvh', 'tabreckdtree']) },
		'treetype':				{ 'advanced': True, 'accelerator': 'bvh' },
		'costsample':			{ 'advanced': True, 'accelerator': 'bvh' },
		'maxprims':				{ 'advanced': True, 'accelerator': 'tabreckdtree' },
		'maxdepth':				{ 'advanced': True, 'accelerator': 'tabreckdtree' },
		'refineimmediately':	{ 'advanced': True, 'accelerator': 'grid' },
		'maxprimsperleaf':		{ 'advanced': True, 'accelerator': 'qbvh' },
		'fullsweepthreshold':	{ 'advanced': True, 'accelerator': 'qbvh' },
		'skipfactor':			{ 'advanced': True, 'accelerator': 'qbvh' },
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'accelerator',
			'name': 'Accelerator',
			'description': 'Scene accelerator type',
			'default': 'tabreckdtree',
			'items': [
				#('none', 'none', 'None'),
				#('bruteforce', 'bruteforce', 'bruteforce'),
				('tabreckdtree', 'KD Tree', 'tabreckdtree'),
				('grid', 'Grid', 'grid'),
				('bvh', 'BVH', 'bvh'),
				('qbvh', 'QBVH', 'qbvh'),
			]
		},
		{
			'attr': 'advanced',
			'type': 'bool',
			'name': 'Advanced',
			'default': False,
		},
		{
			'attr': 'intersectcost',
			'type': 'int',
			'name': 'Intersect Cost',
			'default': 80
		},
		{
			'attr': 'traversalcost',
			'type': 'int',
			'name': 'Traversal Cost',
			'default': 1
		},
		{
			'attr': 'emptybonus',
			'type': 'float',
			'name': 'Empty Bonus',
			'default': 0.5
		},
		{
			'attr': 'treetype',
			'type': 'enum',
			'name': 'Tree Type',
			'default': '2',
			'items': [
				('2', 'Binary', '2'),
				('4', 'Quad', '4'),
				('8', 'Oct', '8'),
			]
		},
		{
			'attr': 'costsample',
			'type': 'int',
			'name': 'Costsample',
			'default': 0
		},
		{
			'attr': 'maxprims',
			'type': 'int',
			'name': 'Max. Prims',
			'default': 1
		},
		{
			'attr': 'maxdepth',
			'type': 'int',
			'name': 'Max. depth',
			'default': -1
		},
		{
			'attr': 'refineimmediately',
			'type': 'bool',
			'name': 'Refine Immediately',
			'default': False
		},
		{
			'attr': 'maxprimsperleaf',
			'type': 'int',
			'name': 'Max. prims per leaf',
			'default': 4
		},
		{
			'attr': 'fullsweepthreshold',
			'type': 'int',
			'name': 'Full sweep threshold',
			'default': 16,
		},
		{
			'attr': 'skipfactor',
			'type': 'int',
			'name': 'Skip factor',
			'default': 1
		},
	]

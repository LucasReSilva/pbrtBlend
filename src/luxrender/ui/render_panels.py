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
import ef.ui
import bpy

DEBUG = True

class render_described_context(ef.ui.context_panel, ef.ui.render_settings_panel, ef.ui.described_layout):
	context_name = 'luxrender'

# TODO these propery group classes shouldn't strictly be in the UI module (they are called from engine render())

# TODO remove all the lux_ prefixes off the members of the property groups

# TODO adapt values written to d based on simple/advanced views

# TODO check parameter completeness against Lux API

class luxrender_engine(bpy.types.IDPropertyGroup):
    pass
  
class luxrender_sampler(bpy.types.IDPropertyGroup):
    def api_output(self):
    	d = {}
    	
    	if self.lux_sampler in ['random', 'lowdiscrepancy']:
    		d['pixelsamples']         = self.lux_sampler_pixelsamples
    		d['pixelsampler']         = self.lux_sampler_pixelsampler
    	
    	if self.lux_sampler == 'erpt':
    		d['initsamples']          = self.lux_sampler_erpt_initsamples
    		d['chainlength']          = self.lux_sampler_erpt_chainlength
#    		d['mutationrange']        = self.lux_sampler_erpt_mutationrange
    	
    	if self.lux_sampler == 'metropolis':
    		d['initsamples']          = self.lux_sampler_metro_initsamples
    		d['maxconsecrejects']     = self.lux_sampler_metro_mncr
    		d['largemutationprob']    = self.lux_sampler_metro_lmprob
#    		d['micromutationprob']    = self.??
#    		d['mutationrange']        = self.??
    		d['usevariance']          = self.lux_sampler_metro_variance
    	
    	out = self.lux_sampler, list(d.items())
    	if DEBUG: print(out)
    	return out
    		
   
class luxrender_integrator(bpy.types.IDPropertyGroup):
    def api_output(self):
    	d={}
    	
    	if self.lux_surfaceintegrator in ['directlighting', 'path']:
    		d['lightstrategy']    = self.lux_integrator_strategy
#    		d['maxdepth']         = self.??
    	
    	if self.lux_surfaceintegrator == 'bidirectional':
    		d['eyedepth']         = self.lux_integrator_bidir_edepth
    		d['lightdepth']       = self.lux_integrator_bidir_ldepth
#    		d['eyerrthreshold']   = self.??
#    		d['lightrrthreshold'] = self.??
    	
    	if self.lux_surfaceintegrator == 'distributedpath':
    		d['strategy']         = self.lux_integrator_strategy
#    		d['diffusedepth']     = self.??
#    		d['glossydepth']      = self.??
#    		d['speculardepth']    = self.??
    	
#    	if self.lux_surfaceintegrator == 'exphotonmap':
#    		pass
    	
    	out = self.lux_surfaceintegrator, list(d.items())
    	if DEBUG: print(out)
    	return out
   
class luxrender_volume(bpy.types.IDPropertyGroup):
    pass

class luxrender_filter(bpy.types.IDPropertyGroup):
    pass
   
class luxrender_accelerator(bpy.types.IDPropertyGroup):
    pass

class engine(render_described_context):
	bl_label = 'LuxRender Engine Configuration'
	
	property_group = luxrender_engine
	
	controls = [
		['lux_threads_auto', 'lux_threads'],
		'lux_priority',
		['lux_rgc', 'lux_colclamp',
#		 'lux_noopengl'
		],
		['lux_meshopt', 'lux_nolg'],
		
#		'lux_singlefile',
#		['lux_file_lxs', 'lux_file_lxo', 'lux_file_lxm', 'lux_file_lxv'],
	]
	
	selection = {
		'lux_threads':				[{ 'lux_threads_auto': False }],
#		'lux_file_lxs':				[{ 'lux_singlefile': False }],
#		'lux_file_lxo':				[{ 'lux_singlefile': False }],
#		'lux_file_lxm':				[{ 'lux_singlefile': False }],
#		'lux_file_lxv':				[{ 'lux_singlefile': False }],
	}
	
	properties = [
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
#		{
#			'type': 'bool',
#			'attr': 'lux_noopengl',
#			'name': 'No OpenGL',
#			'description': 'Disable OpenGL viewport (for buggy display drivers)',
#			'default': False,
#		},
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
#		{
#			'type': 'bool',
#			'attr': 'lux_singlefile',
#			'name': 'Combine LXS',
#			'description': 'Write only a single LXS file',
#			'default': False,
#		},
#		{
#			'type': 'bool',
#			'attr': 'lux_file_lxs',
#			'name': 'LXS',
#			'description': 'Write LXS (Scene) file',
#			'default': True,
#		},
#		{
#			'type': 'bool',
#			'attr': 'lux_file_lxo',
#			'name': 'LXO',
#			'description': 'Write LXO (Objects) file',
#			'default': True,
#		},
#		{
#			'type': 'bool',
#			'attr': 'lux_file_lxm',
#			'name': 'LXM',
#			'description': 'Write LXM (Materials) file',
#			'default': True,
#		},
#		{
#			'type': 'bool',
#			'attr': 'lux_file_lxv',
#			'name': 'LXV',
#			'description': 'Write LXV (volumes) file',
#			'default': True,
#		},
	]
			
class sampler(render_described_context):
	bl_label = 'Sampler'
	
	property_group = luxrender_sampler
	
	controls = [
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
		['lux_sampler_erpt_initsamples', 'lux_sampler_erpt_chainlength',
#		 'lux_sampler_erpt_mutationrange'
		], # simple
		
		# random & lowdiscrepancy
		'lux_sampler_pixelsampler',
		['lux_sampler_pixelsamples'],			# simple 
	]
	
	selection = {
		'lux_sampler_advanced':				[{ 'lux_sampler': 'metropolis'}],
	
		'lux_sampler_metro_strength':		[{ 'lux_sampler_advanced': False }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_lmprob':			[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_mncr':			[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_initsamples':	[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_variance':		[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		
		'lux_sampler_erpt_initsamples':		[{ 'lux_sampler': 'erpt'}],
		'lux_sampler_erpt_chainlength':		[{ 'lux_sampler': 'erpt'}],
#		'lux_sampler_erpt_mutationrange':   [{ 'lux_sampler': 'erpt'}],
		
		'lux_sampler_pixelsampler':		    [{ 'lux_sampler': ['random', 'lowdiscrepancy']}],
		'lux_sampler_pixelsamples':			[{ 'lux_sampler': ['random', 'lowdiscrepancy']}],
	}
	
	properties = [
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
#		{
#			'type': 'int', 
#			'attr': 'lux_sampler_erpt_mutationrange',
#			'name': 'Str. Width',
#			'description': 'Strata Width',
#			'default': 256,
#			'min': 1,
#			'max': 32768,
#		},
		{
			'type': 'enum',
			'attr': 'lux_sampler_pixelsampler',
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
			'attr': 'lux_sampler_pixelsamples',
			'name': 'Pixel Samples',
			'description': 'Average number of samples taken per pixel. More samples create a higher quality image at the cost of render time',
			'default': 4,
			'min': 1,
			'max': 8192,
		},

	]
				
class integrator(render_described_context):
	bl_label = 'Surface Integrator'
	
	property_group = luxrender_integrator
	
	controls = [
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
	
	selection = {
		'lux_integrator_strategy':		[{ 'lux_integrator_advanced': True  }],
		
		'lux_integrator_bidir_depth':	[{ 'lux_integrator_advanced': False }, { 'lux_surfaceintegrator': 'bidirectional' }],
		'lux_integrator_bidir_edepth':	[{ 'lux_integrator_advanced': True  }, { 'lux_surfaceintegrator': 'bidirectional' }],
		'lux_integrator_bidir_ldepth':	[{ 'lux_integrator_advanced': True  }, { 'lux_surfaceintegrator': 'bidirectional' }],
	}
	
	properties = [
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

class volume(render_described_context):
	bl_label = 'Volume Integrator'
	
	property_group = luxrender_volume
	
	controls = [
		'lux_volumeintegrator', 'lux_volume_stepsize'
	]
	
	properties = [
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
			
class filter(render_described_context):
	bl_label = 'Filter'
	
	property_group = luxrender_filter
	
	controls = [
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
	
	selection = {
		'lux_filter_xwidth':				[{ 'lux_filter_advanced': True }],
		'lux_filter_ywidth':				[{ 'lux_filter_advanced': True }],
		
		'lux_filter_gaussian_alpha':		[{ 'lux_filter_advanced': True }, { 'lux_filter': 'gaussian' }],
		
		'lux_filter_mitchell_mode':			[{ 'lux_filter_advanced': True }, { 'lux_filter': 'mitchell' }],
		'lux_filter_mitchell_b':			[{ 'lux_filter_advanced': True }, { 'lux_filter': 'mitchell' }, { 'lux_filter_mitchell_mode': 'manual' }],
		'lux_filter_mitchell_c':			[{ 'lux_filter_advanced': True }, { 'lux_filter': 'mitchell' }, { 'lux_filter_mitchell_mode': 'manual' }],		
		'lux_filter_mitchell_sharpness':	[{ 'lux_filter': 'mitchell' }],
		
		'lux_filter_sinc_tau':				[{ 'lux_filter_advanced': True }, { 'lux_filter': 'sinc' }],
	}
	
	properties = [
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

class accelerator(render_described_context):
	bl_label = 'Accelerator'
	
	property_group = luxrender_accelerator
	
	controls = [
		'lux_accelerator',
		
		['lux_accel_kd_intcost', 'lux_accel_kd_travcost'],			# tabreckdtree
		['lux_accel_kd_ebonus', 'lux_accel_kd_maxprims'],			# tabreckdtree
		'lux_accel_kd_maxdepth',									# tabreckdtree
		
		'lux_accel_grid_refineim',									# grid
		
		'lux_accel_qbvh_maxprims',									# qbvh
	]
	
	selection = {
		'lux_accel_kd_intcost':			[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_travcost':		[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_ebonus':			[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_maxprims':		[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_maxdepth':		[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_grid_refineim':		[{ 'lux_accelerator': 'grid' }],
		'lux_accel_qbvh_maxprims':		[{ 'lux_accelerator': 'qbvh' }],
	}
	
	properties = [
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

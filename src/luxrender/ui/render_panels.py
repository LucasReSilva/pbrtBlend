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
from ef.util import util as efutil
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
		# TODO: write_files forced to True until segfaulting pylux can be fixed
		#'write_files',
		'render',
		'exe_path',
		['write_lxs', 'write_lxm', 'write_lxo'],
		# 'priority',
		['threads_auto', 'threads'],
		# ['rgc', 'colclamp'],
		# ['meshopt', 'nolg'],
	]
	
	visibility = {
		#'write_files':			{ 'export_type': 'INT' },
		'render':				O([{'write_files': True}, {'export_type': 'EXT'}]),
		'exe_path':				{ 'render': True, 'export_type': 'EXT' },
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
			'default': efutil.find_config_value('luxrender', 'defaults', 'auto_start', False),
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'exe_path',
			'name': 'Path to LuxRender',
			'description': 'Path to LuxRender',
			'default': efutil.find_config_value('luxrender', 'defaults', 'exe_path', '')
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
			'default': False,
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
			'default': 512,
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
		[ 0.7, 'surfaceintegrator', 'advanced'],
		
		# bidir +
		'strategy',
		['eyedepth', 'lightdepth'],
		['eyerrthreshold', 'lightrrthreshold'],
		
		# dl +
		'maxdepth',
		
		# dp
		['lbl_direct',
		'directsamples'],
		['directsampleall',
		'directdiffuse',
		'directglossy'],
		['lbl_indirect',
		'indirectsamples'],
		['indirectsampleall',
		'indirectdiffuse',
		'indirectglossy'],
		'lbl_diffuse',
		['diffusereflectsamples',
		'diffusereflectdepth'],
		['diffuserefractsamples',
		'diffuserefractdepth'],
		'lbl_glossy',
		['glossyreflectsamples',
		'glossyreflectdepth'],
		['glossyrefractsamples',
		'glossyrefractdepth'],
		'lbl_specular',
		['specularreflectdepth',
		'specularrefractdepth'],
		'lbl_rejection',
		['diffusereflectreject',
		'diffusereflectreject_threshold'],
		['diffuserefractreject',
		'diffuserefractreject_threshold'],
		['glossyreflectreject',
		'glossyreflectreject_threshold'],
		['glossyrefractreject',
		'glossyrefractreject_threshold'],
		
		# epm
		'maxphotondepth',
		'directphotons',
		'causticphotons',
		'indirectphotons',
		'radiancephotons',
		'nphotonsused',
		'maxphotondist',
		'finalgather',
		'finalgathersamples',
		'gatherangle',
		'renderingmode',
		'rrstrategy',
		'rrcontinueprob',
		# epm advanced
		'distancethreshold',
		'photonmapsfile',
		'dbg_enabledirect',
		'dbg_enableradiancemap',
		'dbg_enableindircaustic',
		'dbg_enableindirdiffuse',
		'dbg_enableindirspecular',
		
		# igi
		'nsets',
		'nlights',
		'mindist',
		
		# path
		'includeenvironment',
	]
	
	visibility = {
		# bidir +
		'strategy':							{ 'surfaceintegrator': O(['bidirectional', 'distributedpath']) },
		'eyedepth':							{ 'surfaceintegrator': 'bidirectional' },
		'lightdepth':						{ 'surfaceintegrator': 'bidirectional' },
		'eyerrthreshold':					{ 'advanced': True, 'surfaceintegrator': 'bidirectional' },
		'lightrrthreshold':					{ 'advanced': True, 'surfaceintegrator': 'bidirectional' },
		
		# dl +
		'maxdepth':							{ 'surfaceintegrator': O(['directlighting', 'exphotonmap', 'igi', 'path']) },
		
		# dp
		'lbl_direct':						{ 'surfaceintegrator': 'distributedpath' },
		'directsampleall':					{ 'surfaceintegrator': 'distributedpath' },
		'directsamples':					{ 'surfaceintegrator': 'distributedpath' },
		'directdiffuse':					{ 'surfaceintegrator': 'distributedpath' },
		'directglossy':						{ 'surfaceintegrator': 'distributedpath' },
		'lbl_indirect':						{ 'surfaceintegrator': 'distributedpath' },
		'indirectsampleall':				{ 'surfaceintegrator': 'distributedpath' },
		'indirectsamples':					{ 'surfaceintegrator': 'distributedpath' },
		'indirectdiffuse':					{ 'surfaceintegrator': 'distributedpath' },
		'indirectglossy':					{ 'surfaceintegrator': 'distributedpath' },
		'lbl_diffuse':						{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectsamples':			{ 'surfaceintegrator': 'distributedpath' },
		'diffuserefractdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'diffuserefractsamples':			{ 'surfaceintegrator': 'distributedpath' },
		'lbl_glossy':						{ 'surfaceintegrator': 'distributedpath' },
		'glossyreflectdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyreflectsamples':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyrefractdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyrefractsamples':				{ 'surfaceintegrator': 'distributedpath' },
		'lbl_specular':						{ 'surfaceintegrator': 'distributedpath' },
		'specularreflectdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'specularrefractdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'lbl_rejection':					{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectreject':				{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectreject_threshold':	{ 'diffusereflectreject': True, 'surfaceintegrator': 'distributedpath' },
		'diffuserefractreject':				{ 'surfaceintegrator': 'distributedpath' },
		'diffuserefractreject_threshold':	{ 'diffuserefractreject': True, 'surfaceintegrator': 'distributedpath' },
		'glossyreflectreject':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyreflectreject_threshold':	{ 'glossyreflectreject': True, 'surfaceintegrator': 'distributedpath' },
		'glossyrefractreject':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyrefractreject_threshold':	{ 'glossyrefractreject': True, 'surfaceintegrator': 'distributedpath' },
		
		# epm
		'maxphotondepth':					{ 'surfaceintegrator': 'exphotonmap' },
		'directphotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'causticphotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'indirectphotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'radiancephotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'nphotonsused':						{ 'surfaceintegrator': 'exphotonmap' },
		'maxphotondist':					{ 'surfaceintegrator': 'exphotonmap' },
		'finalgather':						{ 'surfaceintegrator': 'exphotonmap' },
		'finalgathersamples':				{ 'finalgather': True, 'surfaceintegrator': 'exphotonmap' },
		'gatherangle':						{ 'finalgather': True, 'surfaceintegrator': 'exphotonmap' },
		'renderingmode':					{ 'surfaceintegrator': 'exphotonmap' },
		'rrstrategy':						{ 'surfaceintegrator': O(['exphotonmap', 'path']) },
		'rrcontinueprob':					{ 'surfaceintegrator': O(['exphotonmap', 'path']) },
		# epm advanced
		'distancethreshold':				{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'photonmapsfile':					{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enabledirect':					{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableradiancemap':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableindircaustic':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableindirdiffuse':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableindirspecular':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		
		# igi
		'nsets':							{ 'surfaceintegrator': 'igi' },
		'nlights':							{ 'surfaceintegrator': 'igi' },
		'mindist':							{ 'surfaceintegrator': 'igi' },
		
		# path
		'includeenvironment':				{ 'surfaceintegrator': 'path' },
	}
	
	properties = [
		{
			'type': 'enum', 
			'attr': 'surfaceintegrator',
			'name': 'Surface Integrator',
			'description': 'Surface Integrator',
			'default': 'bidirectional',
			'items': [
				('bidirectional', 'Bi-Directional', 'bidirectional'),
				('path', 'Path', 'path'),
				('directlighting', 'Direct Lighting', 'directlighting'),
				('distributedpath', 'Distributed Path', 'distributedpath'),
				('igi', 'Instant Global Illumination', 'igi',),
				('exphotonmap', 'Ex-Photon Map', 'exphotonmap'),
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
			'attr': 'eyedepth',
			'name': 'Eye Depth',
			'description': 'Max recursion depth for ray casting from eye',
			'default': 16,
			'min': 0,
			'max': 2048,
		},
		{
			'type': 'int', 
			'attr': 'lightdepth',
			'name': 'Light Depth',
			'description': 'Max recursion depth for ray casting from light',
			'default': 16,
			'min': 0,
			'max': 2048,
		},
		{
			'type': 'float',
			'attr': 'eyerrthreshold',
			'name': 'Eye RR Threshold',
			'default': 0.0,
		},
		{
			'type': 'float',
			'attr': 'lightrrthreshold',
			'name': 'Light RR Threshold',
			'default': 0.0,
		},
		{
			'type': 'int',
			'attr': 'maxdepth',
			'name': 'Max. depth',
			'default': 8,
		},
		
		{
			'type': 'text',
			'attr': 'lbl_direct',
			'name': 'Direct light sampling',
		},
		{
			'type': 'bool',
			'attr': 'directsampleall',
			'name': 'Sample all',
			'default': True
		},
		{
			'type': 'int',
			'attr': 'directsamples',
			'name': 'Samples',
			'default': 1,
		},
		{
			'type': 'bool',
			'attr': 'directdiffuse',
			'name': 'Diffuse',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'directglossy',
			'name': 'Glossy',
			'default': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_indirect',
			'name': 'Indirect light sampling',
		},
		{
			'type': 'bool',
			'attr': 'indirectsampleall',
			'name': 'Sample all',
			'default': False
		},
		{
			'type': 'int',
			'attr': 'indirectsamples',
			'name': 'Samples',
			'default': 1,
		},
		{
			'type': 'bool',
			'attr': 'indirectdiffuse',
			'name': 'Diffuse',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'indirectglossy',
			'name': 'Glossy',
			'default': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_diffuse',
			'name': 'Diffuse settings',
		},
		{
			'type': 'int',
			'attr': 'diffusereflectdepth',
			'name': 'Reflection depth',
			'default': 3
		},
		{
			'type': 'int',
			'attr': 'diffusereflectsamples',
			'name': 'Reflection samples',
			'default': 1
		},
		{
			'type': 'int',
			'attr': 'diffuserefractdepth',
			'name': 'Refraction depth',
			'default': 5
		},
		{
			'type': 'int',
			'attr': 'diffuserefractsamples',
			'name': 'Refraction samples',
			'default': 1
		},
		
		{
			'type': 'text',
			'attr': 'lbl_glossy',
			'name': 'Glossy settings',
		},
		{
			'type': 'int',
			'attr': 'glossyreflectdepth',
			'name': 'Reflection depth',
			'default': 2
		},
		{
			'type': 'int',
			'attr': 'glossyreflectsamples',
			'name': 'Reflection samples',
			'default': 1
		},
		{
			'type': 'int',
			'attr': 'glossyrefractdepth',
			'name': 'Refraction depth',
			'default': 5
		},
		{
			'type': 'int',
			'attr': 'glossyrefractsamples',
			'name': 'Refraction samples',
			'default': 1
		},
		
		{
			'type': 'text',
			'attr': 'lbl_specular',
			'name': 'Specular settings',
		},
		{
			'type': 'int',
			'attr': 'specularreflectdepth',
			'name': 'Reflection depth',
			'default': 3
		},
		{
			'type': 'int',
			'attr': 'specularrefractdepth',
			'name': 'Refraction depth',
			'default': 5
		},
		
		{
			'type': 'text',
			'attr': 'lbl_rejection',
			'name': 'Rejection settings',
		},
		{
			'type': 'bool',
			'attr': 'diffusereflectreject',
			'name': 'Diffuse reflection reject',
			'default': False,
		},
		{
			'type': 'float',
			'attr': 'diffusereflectreject_threshold',
			'name': 'Threshold',
			'default': 10.0
		},
		{
			'type': 'bool',
			'attr': 'diffuserefractreject',
			'name': 'Diffuse refraction reject',
			'default': False,
		},
		{
			'type': 'float',
			'attr': 'diffuserefractreject_threshold',
			'name': 'Threshold',
			'default': 10.0
		},
		{
			'type': 'bool',
			'attr': 'glossyreflectreject',
			'name': 'Glossy reflection reject',
			'default': False,
		},
		{
			'type': 'float',
			'attr': 'glossyreflectreject_threshold',
			'name': 'Threshold',
			'default': 10.0
		},
		{
			'type': 'bool',
			'attr': 'glossyrefractreject',
			'name': 'Glossy refraction reject',
			'default': False,
		},
		{
			'type': 'float',
			'attr': 'glossyrefractreject_threshold',
			'name': 'Threshold',
			'default': 10.0
		},
		
		{
			'type': 'int',
			'attr': 'maxphotondepth',
			'name': 'Max. photon depth',
			'default': 10
		},
		{
			'type': 'int',
			'attr': 'directphotons',
			'name': 'Direct photons',
			'default': 1000000
		},
		{
			'type': 'int',
			'attr': 'causticphotons',
			'name': 'Caustic photons',
			'default': 20000,
		},
		{
			'type': 'int',
			'attr': 'indirectphotons',
			'name': 'Indirect photons',
			'default': 200000
		},
		{
			'type': 'int',
			'attr': 'radiancephotons',
			'name': 'Radiance photons',
			'default': 200000
		},
		{
			'type': 'int',
			'attr': 'nphotonsused',
			'name': 'Number of photons used',
			'default': 50
		},
		{
			'type': 'float',
			'attr': 'maxphotondist',
			'name': 'Max. photon distance',
			'default': 0.1,
		},
		{
			'type': 'bool',
			'attr': 'finalgather',
			'name': 'Final Gather',
			'default': True
		},
		{
			'type': 'int',
			'attr': 'finalgathersamples',
			'name': 'Final gather samples',
			'default': 32
		},
		{
			'type': 'float',
			'attr': 'gatherangle',
			'name': 'Gather angle',
			'default': 10.0
		},
		{
			'type': 'enum',
			'attr': 'renderingmode',
			'name': 'Rendering mode',
			'default': 'directlighting',
			'items': [
				('directlighting', 'directlighting', 'directlighting'),
				('path', 'path', 'path'),
			]
		},
		{
			'type': 'float',
			'attr': 'distancethreshold',
			'name': 'Distance threshold',
			'default': 0.75
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'photonmapsfile',
			'name': 'Photonmaps file',
			'default': ''
		},
		{
			'type': 'bool',
			'attr': 'dbg_enabledirect',
			'name': 'Debug: Enable direct',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableradiancemap',
			'name': 'Debug: Enable radiance map',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableindircaustic',
			'name': 'Debug: Enable indirect caustics',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableindirdiffuse',
			'name': 'Debug: Enable indirect diffuse',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableindirspecular',
			'name': 'Debug: Enable indirect specular',
			'default': True,
		},
		{
			'type': 'int',
			'attr': 'nsets',
			'name': 'Number of sets',
			'default': 4
		},
		{
			'type': 'int',
			'attr': 'nlights',
			'name': 'Number of lights',
			'default': 64,
		},
		{
			'type': 'float',
			'attr': 'mindist',
			'name': 'Min. Distance',
			'default': 0.1,
		},
		{
			'type': 'float',
			'attr': 'rrcontinueprob',
			'name': 'RR continue probability',
			'default': 0.65,
		},
		{
			'type': 'enum',
			'attr': 'rrstrategy',
			'name': 'RR strategy',
			'default': 'efficiency',
			'items': [
				('efficiency', 'efficiency', 'efficiency'),
				('probability', 'probability', 'probability'),
				('none', 'none', 'none'),
			]
		},
		{
			'type': 'bool',
			'attr': 'includeenvironment',
			'name': 'Include Environment',
			'default': True
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
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 100.0,
			'soft_max': 100.0,
		}
	]
			
class filter(render_described_context):
	'''
	PixelFilter settings UI Panel
	'''
	
	bl_label = 'Filter'
	
	property_group = luxrender.properties.filter.luxrender_filter
	
	controls = [
		[ 0.7, 'filter', 'advanced'],
		
		['xwidth', 'ywidth'],
		'alpha',
		['b', 'c'],
		'supersample',
		'tau'
	]
	
	visibility = {
		'xwidth':				{ 'advanced': True },
		'ywidth':				{ 'advanced': True },
		'alpha':				{ 'advanced': True, 'filter': 'gaussian' },
		'b':					{ 'advanced': True, 'filter': 'mitchell' },
		'c':					{ 'advanced': True, 'filter': 'mitchell' },
		'supersample':			{ 'advanced': True, 'filter': 'mitchell' },
		'tau':					{ 'advanced': True, 'filter': 'sinc' },
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'filter',
			'name': 'Filter',
			'description': 'Pixel splatting filter',
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
			'default': 2.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0,
		},
		{
			'type': 'float',
			'attr': 'ywidth',
			'name': 'Y Width',
			'description': 'Width of filter in Y dimension',
			'default': 2.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0,
		},
		{
			'type': 'float',
			'attr': 'alpha',
			'name': 'Alpha',
			'description': 'Gaussian Alpha parameter',
			'default': 2.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0,
		},
		{
			'type': 'float',
			'attr': 'b',
			'name': 'B',
			'description': 'Mitchell B parameter',
			'default': 1/3,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0,
		},
		{
			'type': 'float',
			'attr': 'c',
			'name': 'C',
			'description': 'Mitchell C parameter',
			'default': 1/3,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0,
		},
		{
			'type': 'float',
			'attr': 'tau',
			'name': 'Tau',
			'description': 'Sinc Tau parameter',
			'default': 3.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0,
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
			'default': 0.2
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

# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Jason Clarke
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

from .. import LuxRenderAddon
from ..export import ParamSet

from extensions_framework.validate import Logic_OR as O

#This class holds the renderingmode menu and renderer prefs. Surface integrators settings are in a seperate class, due to there being a hell of a lot of them
@LuxRenderAddon.addon_register_class
class luxrender_rendermode(declarative_property_group):
	'''
	Storage class for LuxRender SurfaceIntegrator settings.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		'rendermode',
		'opencl_prefs',
		['usegpus', 'usecpus'],
		'opencl_platform_index',
		'configfile',
		'raybuffersize',
		'statebuffercount',
		'workgroupsize',
		'qbvhstacksize',
		'deviceselection',
		]
	
	visibility = {
		'opencl_prefs':				{ 'rendermode': O(['hybridpath','hybridbidir','slgpath']) },
		'opencl_platform_index':	{ 'renderer': 'hybrid' },
		'configfile':				{ 'opencl_prefs': True, 'renderer': 'hybrid' },
		'raybuffersize':			{ 'opencl_prefs': True, 'renderer': 'hybrid' },
		'statebuffercount':			{ 'opencl_prefs': True, 'renderer': 'hybrid' },
		'workgroupsize':			{ 'opencl_prefs': True, 'rendermode': O(['hybridpath','hybridbidir','slgpath']) },
		'qbvhstacksize':			{ 'opencl_prefs': True, 'renderer': 'hybrid' },
		'deviceselection':			{ 'opencl_prefs': True, 'rendermode': O(['hybridpath','hybridbidir','slgpath']) },
		'usegpus':					{ 'opencl_prefs': True, 'rendermode': O(['hybridpath','hybridbidir','slgpath']) },
		'usecpus':					{ 'opencl_prefs': True, 'rendermode': 'slgpath' },
		}
	
	#This function sets renderer and surface integrator according to rendermode setting
	def update_rendering_mode(self, context):
		if self.rendermode in ('slgpath', 'hybridpath'):
			context.scene.luxrender_integrator.surfaceintegrator = 'path'
		elif self.rendermode in ('slgbidir', 'hybridbidir'):
			context.scene.luxrender_integrator.surfaceintegrator = 'bidirectional'
		else:
			context.scene.luxrender_integrator.surfaceintegrator = self.rendermode
		
		if self.rendermode in ('hybridpath', 'hybridbidir'):
			self.renderer = 'hybrid'
		elif self.rendermode == 'sppm':
			self.renderer = 'sppm'
		elif self.rendermode in ('slgpath', 'slgbidir'):
			self.renderer = 'slg'
		else:
			self.renderer = 'sampler'
	
	properties = [
		{
			'type': 'enum', 
			'attr': 'rendermode',
			'name': 'Rendering Mode',
			'description': 'Renderer and surface integrator combination to use',
			'default': 'bidirectional',
			'items': [
				('bidirectional', 'Bidirectional', 'Bidirectional path tracer'),
				('path', 'Path', 'Simple (eye-only) path tracer'),
				('directlighting', 'Direct Lighting', 'Direct-light (Whitted) ray tracer'),
				('distributedpath', 'Distributed Path', 'Distributed path tracer'),
# 				('igi', 'Instant Global Illumination', 'Instant global illumination renderer',),
				('exphotonmap', 'Ex-Photon Map', 'Traditional photon mapping integrator'),
				('sppm', 'SPPM (Experimental)', 'Experimental stochastic progressive photon mapping integrator'),
#				('hybridbidir', 'Hybrid Bidirectional', 'Experimental OpenCL-acclerated bidirectional path tracer'),
				('hybridpath', 'Hybrid Path (Experimental)', 'OpenCL-accelerated simple (eye-only) path tracer'),
#   				('slgpath', 'SLG Path OpenCL', 'Experimental pure GPU path tracer'),
#   				('slgbidir', 'SLG BidirVCM', 'Experimental OpenCL bidirectional/vertex merging integrator'),
			],
			'update': update_rendering_mode,
			'save_in_preset': True
		},
		#This parameter is fed to the "renderer' context, and holds the actual renderer setting. The user does not interact with it directly, and it does not appear in the panels
		{
			'type': 'enum',
			'attr': 'renderer',
			'name': 'Renderer',
			'description': 'Renderer type',
			'default': 'sampler',
			'items': [
				('sampler', 'Sampler (traditional CPU)', 'sampler'),
				('hybrid', 'Hybrid (CPU+GPU)', 'hybrid'),
				('sppm', 'SPPM (CPU)', 'sppm'),
				('slg', 'SLG (GPU)', 'slg'),
			],
			# 'update': lambda s,c: check_renderer_settings(c),
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'opencl_prefs',
			'name': 'Show OpenCL options',
			'description': 'Enable manual OpenCL configuration options',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'opencl_platform_index',
			'name': 'OpenCL platform index',
			'description': 'OpenCL Platform to target. Try increasing this value 1 at a time if LuxRender fails to use your GPU. -1=all platforms',
			'default': 0,
			'min': -1,
			'soft_min': 0,
			'max': 16,
			'soft_max': 16,
			'save_in_preset': True
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'configfile',
			'name': 'OpenCL config file',
			'description': 'Path to a machine-specific OpenCL configuration file. The settings from the lxs (set below) are used if this is not specified or found',
			'default': '',
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'raybuffersize',
			'name': 'Ray buffer size',
			'description': 'Size of ray "bundles" fed to OpenCL device',
			'default': 8192,
			'min': 2,
			'soft_min': 2,
			'max': 16384,
			'soft_max': 16384,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'statebuffercount',
			'name': 'State buffer count',
			'description': 'Numbers of ray buffers to maintain simultaneously',
			'default': 1,
			'min': 1,
			'soft_min': 1,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'workgroupsize',
			'name': 'OpenCL work group size',
			'description': 'Size of OpenCL work group. Use 0 for auto',
			'default': 64,
			'min': 0,
			'soft_min': 0,
			'max': 1024,
			'soft_max': 1024,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'qbvhstacksize',
			'name': 'QBVH Stack Size',
			'description': 'Max depth of GPU QBVH stack. Lower this if you get an out-of-resources error',
			'default': 32,
			'min': 16,
			'max': 64,
			'save_in_preset': True
		},
		{
			'type': 'string',
			'attr': 'deviceselection',
			'name': 'OpenCL devices',
			'description': 'Enter target OpenCL devices here. Leave blank to use all available',
			'default': '',
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'usegpus',
			'name': 'Use GPUs',
			'description': 'Target GPU devices in slg or hybrid',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'usecpus',
			'name': 'Use CPUs',
			'description': 'Target CPU devices in slg render',
			'default': True,
			'save_in_preset': True
		},
		]
	
	def api_output(self):
		renderer_params = ParamSet()
		
		if self.renderer in ['hybrid'] and self.opencl_prefs == True:
			renderer_params.add_integer('opencl.platform.index', self.opencl_platform_index)
			renderer_params.add_bool('opencl.gpu.use', self.usegpus)
			renderer_params.add_string('configfile', self.configfile)
			renderer_params.add_integer('raybuffersize', self.raybuffersize)
			renderer_params.add_integer('statebuffercount', self.statebuffercount)
			renderer_params.add_integer('opencl.gpu.workgroup.size', self.workgroupsize)
			renderer_params.add_integer('accelerator.qbvh.stacksize.max', self.qbvhstacksize)
			renderer_params.add_string('opencl.devices.select', self.deviceselection)
		
		if self.renderer in ['slg'] and self.opencl_prefs == True: # this is WIP to take over some slg configs
			slg_gpu_workgroups = "opencl.gpu.workgroup.size = " + str(self.workgroupsize)
			slg_use_gpu = "opencl.gpu.use = 1" if self.usegpus else "opencl.gpu.use = 0"
			slg_use_cpu = "opencl.cpu.use = 1" if self.usecpus else "opencl.cpu.use = 0"
			slg_devices_select =  "opencl.devices.select = " + self.deviceselection if self.deviceselection else "opencl.devices.select = " # blank
			slg_config_seperator = '" "'
			slg_params = slg_gpu_workgroups	+ slg_config_seperator + slg_use_gpu + slg_config_seperator + slg_use_cpu + slg_config_seperator + slg_devices_select
			renderer_params.add_string('config', slg_params)
		
		return self.renderer, renderer_params

@LuxRenderAddon.addon_register_class
class luxrender_halt(declarative_property_group):
	'''
	Storage class for LuxRender Halt settings.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		['haltthreshold', 'convergencestep'],
		['haltspp','halttime'],
		]
	
	properties = [
		{
			'type': 'int',
			'attr': 'haltspp',
			'name': 'Halt SPP',
			'description': 'Halt the rendering at this number of samples/px or passes (0=disabled)',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 65535,
			'soft_max': 65535,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'halttime',
			'name': 'Halt time',
			'description': 'Halt the rendering at this number seconds (0=disabled)',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 65535,
			'soft_max': 65535,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'haltthreshold',
			'name': 'HaltThreshhold',
			'description': 'Halt the rendering at this percentage of noise eliminated (0=disabled )',
			'default': 0.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 100.0,
			'soft_max': 100.0,
			'precision': 3,
			'subtype': 'PERCENTAGE',
			'unit': 'NONE',
			'slider': True,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'convergencestep',
			'name': 'Convergence Step',
			'description': 'Update steps of the convergence test',
			'default': 32.0,
			'min': 4.0,
			'soft_min': 4.0,
			'max': 512.0,
			'soft_max': 512.0,
			'step' : 1600,
			'save_in_preset': True
		},
	]

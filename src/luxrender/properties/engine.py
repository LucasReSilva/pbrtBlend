# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
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
import os

from extensions_framework import declarative_property_group
from extensions_framework import util as efutil
from extensions_framework.validate import Logic_OR as O, Logic_AND as A

from .. import LuxRenderAddon
from ..export import ParamSet
from ..outputs.pure_api import PYLUX_AVAILABLE
from ..outputs.pure_api import LUXRENDER_VERSION

def find_luxrender_path():
	return os.getenv(
		# Use the env var path, if set ...
		'LUXRENDER_ROOT',
		# .. or load the last path from CFG file
		efutil.find_config_value('luxrender', 'defaults', 'install_path', '')
	)

def find_apis():
	apis = [
		('EXT', 'External', 'EXT'),
	]
	if PYLUX_AVAILABLE:
		apis.append( ('INT', 'Internal', 'INT') )
	
	return apis

@LuxRenderAddon.addon_register_class
class luxrender_testing(declarative_property_group):
	"""
	Properties related to exporter and scene testing
	"""
	
	ef_attach_to = ['Scene']
	
	controls = [
		'clay_render',
		'object_analysis',
		're_raise'
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'clay_render',
			'name': 'Clay render',
			'description': 'Export all materials as default "clay"',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 'object_analysis',
			'name': 'Debug: print object analysis',
			'description': 'Show extra output as objects are processed',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 're_raise',
			'name': 'Debug: show full trace on export error',
			'description': '',
			'default': False
		},
	]

@LuxRenderAddon.addon_register_class
class luxrender_engine(declarative_property_group):
	'''
	Storage class for LuxRender Engine settings.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		[ 0.7, 'renderer', 'advanced'],
		
		'opencl_platform_index',
		'raybuffersize',
		'statebuffercount',
		'workgroupsize',
		'deviceselection',
		'usegpus',
		'export_type',
		'binary_name',
		'log_verbosity'
		'write_files',
		'install_path',
		['write_lxv',
		'embed_filedata'],
		
		'mesh_type',
		'partial_ply',
		['render','monitor_external'],
		['threads_auto', 'threads'],
		]
	
	# Insert 'renderer' before 'binary_name'
	controls.insert(controls.index('binary_name'), 'renderer')
	# Also insert renderer specific controls
	controls.insert(controls.index('binary_name'), 'opencl_platform_index',)
	controls.insert(controls.index('binary_name'), 'raybuffersize',)
	controls.insert(controls.index('binary_name'), 'workgroupsize',)
	controls.insert(controls.index('binary_name'), 'deviceselection',)
	controls.insert(controls.index('binary_name'), 'usegpus',)
	controls.append('log_verbosity')
	
	visibility = {
		'opencl_platform_index':	{ 'renderer': 'hybrid' },
		'raybuffersize':			{ 'advanced': True, 'renderer': 'hybrid' },
		'statebuffercount':			{ 'advanced': True, 'renderer': 'hybrid' },
		'workgroupsize':			{ 'advanced': True, 'renderer': 'hybrid' },
		'deviceselection':			{ 'advanced': True, 'renderer': 'hybrid' },
		'usegpus':					{ 'renderer': 'hybrid' },
		'write_files':				{ 'export_type': 'INT' },
		#'write_lxv':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'embed_filedata':			O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'mesh_type':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'binary_name':				{ 'export_type': 'EXT' },
		'render':					O([{'write_files': True}, {'export_type': 'EXT'}]),
		'monitor_external':			{'export_type': 'EXT', 'binary_name': 'luxrender', 'render': True },
		'partial_ply':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'install_path':				{ 'export_type': 'EXT' },
		'threads_auto':				A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }]),
		'threads':					A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }, { 'threads_auto': False }]),
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
			'type': 'bool',
			'attr': 'advanced',
			'name': 'Advanced',
			'description': 'Configure advanced renderer settings',
			'default': False,
			'save_in_preset': True
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
			'name': 'Rendering Mode',
			'description': 'Run LuxRender inside or outside of Blender',
			'default': 'EXT', # if not PYLUX_AVAILABLE else 'INT',
			'items': find_apis(),
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'render',
			'name': 'Run Renderer',
			'description': 'Run Renderer after export',
			'default': efutil.find_config_value('luxrender', 'defaults', 'auto_start', False),
		},
		{
			'type': 'bool',
			'attr': 'monitor_external',
			'name': 'Monitor External',
			'description': 'Monitor external GUI rendering; when selected, LuxBlend will copy the render image from the external GUI',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'partial_ply',
			'name': 'Partial PLY Export',
			'description': 'Skip PLY file write',
			'default': False,
			'save_in_preset': True
		},
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
			],
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'opencl_platform_index',
			'name': 'OpenCL platform index',
			'description': 'Try increasing this value 1 at a time if LuxRender fails to use your GPU',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 16,
			'soft_max': 16,
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
			'description': 'Numbers of buffers used for surface integrator states',
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
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 1024,
			'soft_max': 1024,
			'save_in_preset': True
		},
		{
			'type': 'string',
			'attr': 'deviceselection',
			'name': 'OpenCL devices',
			'description': 'Enter target OpenCL devices here. Leave blank to use all available.',
			'default': '',
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'usegpus',
			'name': 'Use GPUs',
			'description': 'Target GPU devices instead of using native threads.',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'binary_name',
			'name': 'External type',
			'description': 'Choose full GUI or console renderer',
			'default': 'luxrender',
			'items': [
				('luxrender', 'LuxRender GUI', 'luxrender'),
				('luxconsole', 'LuxConsole', 'luxconsole'),
			],
			'save_in_preset': True
		},
		{
			'type': 'string',
			'subtype': 'DIR_PATH',
			'attr': 'install_path',
			'name': 'Path to LuxRender Installation',
			'description': 'Path to LuxRender',
			'default': find_luxrender_path()
		},
		{
			'type': 'bool',
			'attr': 'write_files',
			'name': 'Write to Disk',
			'description': 'Write scene files to disk',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'write_lxv',
			'name': 'Export Smoke',
			'description': 'Process and export smoke simulations',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'embed_filedata',
			'name': 'Embed File Data',
			'description': 'Embed all external files (images etc) inline into the exporter output',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'is_saving_lbm2',
			'name': '<for internal use>',
			'default': False,
			'save_in_preset': False
		},
		{
			'type': 'enum',
			'attr': 'mesh_type',
			'name': 'Default mesh format',
			'items': [
				('native', 'LuxRender mesh', 'native'),
				('binary_ply', 'Binary PLY', 'binary_ply')
			],
			'default': 'binary_ply',
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'log_verbosity',
			'name': 'Log verbosity',
			'description': 'Logging verbosity',
			'default': 'default',
			'items': [
				('verbose', 'Verbose', 'verbose'),
				('default', 'Default', 'default'),
				('quiet', 'Quiet', 'quiet'),
				('very-quiet', 'Very quiet', 'very-quiet'),
			],
			'save_in_preset': True
		}
	]
	
	def allow_file_embed(self):
		saving_files = (self.export_type == 'EXT' or (self.export_type == 'INT' and self.write_files == True))
		
		return self.is_saving_lbm2 or (saving_files and self.embed_filedata)
	
	def api_output(self):
		renderer_params = ParamSet()
		
		if self.renderer == 'hybrid':
			renderer_params.add_integer('opencl.platform.index', self.opencl_platform_index)
			renderer_params.add_bool('opencl.gpu.use', self.usegpus)
			if self.advanced:
				renderer_params.add_integer('raybuffersize', self.raybuffersize)
				renderer_params.add_integer('statebuffercount', self.statebuffercount)
				renderer_params.add_integer('opencl.gpu.workgroup.size', self.workgroupsize)
				renderer_params.add_string('opencl.devices.select', self.deviceselection)
		
		return self.renderer, renderer_params

@LuxRenderAddon.addon_register_class
class luxrender_networking(declarative_property_group):
	
	ef_attach_to = ['Scene']
	
	controls = [
		'servers',
		'serverinterval'
	]
	
	visibility = {
		'servers':			{ 'use_network_servers': True },
		'serverinterval':	{ 'use_network_servers': True },
	}
	
	properties = [
		{	# drawn in panel header
			'type': 'bool',
			'attr': 'use_network_servers',
			'name': 'Use Networking',
			'default': efutil.find_config_value('luxrender', 'defaults', 'use_network_servers', False),
			'save_in_preset': True
		},
		{
			'type': 'string',
			'attr': 'servers',
			'name': 'Servers',
			'description': 'Comma separated list of Lux server IP addresses',
			'default': efutil.find_config_value('luxrender', 'defaults', 'servers', ''),
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'serverinterval',
			'name': 'Upload interval',
			'description': 'Interval for server image transfers (seconds)',
			'default': int(efutil.find_config_value('luxrender', 'defaults', 'serverinterval', '180')),
			'min': 10,
			'soft_min': 10,
			'save_in_preset': True
		},
	]
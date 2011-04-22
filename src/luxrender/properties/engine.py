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
class luxrender_engine(declarative_property_group):
	'''
	Storage class for LuxRender Engine settings.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		'export_type',
		'binary_name',
		'write_files',
		['write_lxs', 'write_lxm', 'write_lxo', 'write_lxv'],
		'embed_filedata',
		
		'mesh_type',
		'partial_ply',
		['render','monitor_external'],
		'install_path',
		['threads_auto', 'threads'],
		'ignore_lightgroups',
	]
	
	if LUXRENDER_VERSION >= '0.8':
		# Insert 'renderer' before 'binary_name'
		controls.insert(controls.index('binary_name'), 'renderer')
		controls.insert(controls.index('binary_name'), 'opencl_platform_index')
		controls.append('log_verbosity')
	
	visibility = {
		'opencl_platform_index':	{ 'renderer': 'hybrid' },
		'write_files':				{ 'export_type': 'INT' },
		'write_lxs':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'write_lxm':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'write_lxo':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'write_lxv':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'embed_filedata':			O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'mesh_type':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'binary_name':				{ 'export_type': 'EXT' },
		'render':					O([{'write_files': True}, {'export_type': 'EXT'}]),
		'monitor_external':			{'export_type': 'EXT', 'binary_name': 'luxrender', 'render': True },
		'partial_ply':				O([ {'export_type':'EXT'}, A([ {'export_type':'INT'}, {'write_files': True} ]) ]),
		'install_path':				{ 'render': True, 'export_type': 'EXT' },
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
			'name': 'Monitor external',
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
				('hybrid', 'Hybrid (CPU + GPU)', 'hybrid'),
			],
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'opencl_platform_index',
			'name': 'OpenCL Platform Index',
			'description': 'Try increasing this value 1 at a time if LuxRender fails to use your GPU',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 16,
			'soft_max': 16,
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
			'name': 'Write to disk',
			'description': 'Write scene files to disk',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'write_lxs',
			'name': 'LXS',
			'description': 'Write master scene file',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'write_lxm',
			'name': 'LXM',
			'description': 'Write materials file',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'write_lxo',
			'name': 'LXO',
			'description': 'Write objects file',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'write_lxv',
			'name': 'LXV',
			'description': 'Write volumes file',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'embed_filedata',
			'name': 'Embed File data',
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
		},
		{
			'type': 'bool',
			'attr': 'ignore_lightgroups',
			'name': 'Ignore LightGroups',
			'description': 'Enable this for final renders, or to decrease RAM usage.',
			'default': False,
			'save_in_preset': True
		},
	]
	
	def allow_file_embed(self):
		saving_files = (self.export_type == 'EXT' or (self.export_type == 'INT' and self.write_files == True))
		
		return self.is_saving_lbm2 or (saving_files and self.embed_filedata)
	
	def api_output(self):
		renderer_params = ParamSet()
		
		if self.renderer == 'hybrid':
			renderer_params.add_integer('opencl.platform.index', self.opencl_platform_index)
		
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
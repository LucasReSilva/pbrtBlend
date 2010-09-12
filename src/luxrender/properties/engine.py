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
from ef.ef import declarative_property_group
from ef.util import util as efutil
from ef.validate import Logic_OR as O, Logic_AND as A

from luxrender.export					import ParamSet
from luxrender.outputs.pure_api			import PYLUX_AVAILABLE
from luxrender.outputs.pure_api			import LUXRENDER_VERSION
from luxrender.outputs.luxfire_client	import LUXFIRE_CLIENT_AVAILABLE

def find_apis():
	apis = [
		('EXT', 'External', 'EXT'),
	]
	if PYLUX_AVAILABLE:
		apis.append( ('INT', 'Internal', 'INT') )
	if LUXFIRE_CLIENT_AVAILABLE:
		apis.append( ('LFC', 'LuxFire Client', 'LFC') )
	
	return apis

def engine_controls():
	ectl = [
		'export_type',
		'binary_name',
		'write_files',
		['write_lxs', 'write_lxm', 'write_lxo'],
		
		# Other mesh types disabled because cannot set active object
		# to pass to PLY operator. Even so, Lux fails to load the PLY
		# TODO: find solutions
		# 'mesh_type',
		
		'render',
		'install_path',
		# 'priority',
		['threads_auto', 'threads'],
		# ['rgc', 'colclamp'],
		# ['meshopt', 'nolg'],
		
		'writeinterval',
		'displayinterval',
	]
	
	if LUXRENDER_VERSION >= '0.8':
		# Insert 'renderer' before 'binary_name'
		ectl.insert(ectl.index('binary_name'), 'renderer')
	
	
	return ectl

class luxrender_engine(declarative_property_group):
	'''
	Storage class for LuxRender Engine settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	controls = engine_controls()
	
	visibility = {
		'write_files':		{ 'export_type': 'INT' },
		'binary_name':		{ 'export_type': 'EXT' },
		'render':			O([{'write_files': True}, {'export_type': 'EXT'}]),
		'install_path':		{ 'render': True, 'export_type': 'EXT' },
		'write_lxs':		O([{ 'export_type': 'EXT' }, { 'write_files': True }]),
		'write_lxm':		O([{ 'export_type': 'EXT' }, { 'write_files': True }]),
		'write_lxo':		O([{ 'export_type': 'EXT' }, { 'write_files': True }]),
		'threads_auto':		A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }]),
		'threads':			A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }, { 'threads_auto': False }]),
		'priority':			{ 'export_type': 'EXT', 'render': True },
		
		# displayinterval is applicable only to the Lux GUI
		'displayinterval':	{ 'export_type': 'EXT', 'binary_name': 'luxrender' },
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
			'items': find_apis()
		},
		{
			'type': 'bool',
			'attr': 'render',
			'name': 'Run Renderer',
			'description': 'Run Renderer after export',
			'default': efutil.find_config_value('luxrender', 'defaults', 'auto_start', False),
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
			]
		},
		{
			'type': 'string',
			'subtype': 'DIR_PATH',
			'attr': 'install_path',
			'name': 'Path to LuxRender Installation',
			'description': 'Path to LuxRender',
			'default': efutil.find_config_value('luxrender', 'defaults', 'install_path', '')
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
			'attr': 'mesh_type',
			'name': 'Mesh Export type',
			'description': 'The type of mesh data to export',
			'items': [
				('native', 'Lux Mesh', 'native'),
				('ply', 'Stanford PLY', 'ply'),
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
		{
			'type': 'int',
			'attr': 'writeinterval',
			'name': 'Save interval',
			'description': 'Period for writing images to disk (seconds)',
			'default': 10,
			'min': 2,
			'soft_min': 2
		},
		{
			'type': 'int',
			'attr': 'displayinterval',
			'name': 'GUI refresh interval',
			'description': 'Period for updating rendering on screen (seconds)',
			'default': 10,
			'min': 2,
			'soft_min': 2
		},
	]
	
	def api_output(self):
		renderer_params = ParamSet()
		
		return self.renderer, renderer_params

class luxrender_networking(declarative_property_group):
	
	controls = [
		'use_network_servers',
		'servers',
		'serverinterval'
	]
	
	visibility = {
		'servers':			{ 'use_network_servers': True },
		'serverinterval':	{ 'use_network_servers': True },
	}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'use_network_servers',
			'name': 'Use Networking',
			'default': efutil.find_config_value('luxrender', 'defaults', 'use_network_servers', False),
		},
		{
			'type': 'string',
			'attr': 'servers',
			'name': 'Servers',
			'description': 'Comma separated list of Lux server IP addresses',
			'default': efutil.find_config_value('luxrender', 'defaults', 'servers', ''),
		},
		{
			'type': 'int',
			'attr': 'serverinterval',
			'name': 'Upload interval',
			'description': 'Interval for server image transfers (seconds)',
			'default': int(efutil.find_config_value('luxrender', 'defaults', 'serverinterval', '180')),
			'min': 10,
			'soft_min': 10
		},
	]
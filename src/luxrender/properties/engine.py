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
import bpy

from ef.ui import declarative_property_group
from ef.util import util as efutil
from ef.validate import Logic_OR as O, Logic_AND as A

from luxrender.outputs.pure_api			import PYLUX_AVAILABLE
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

class luxrender_engine(bpy.types.IDPropertyGroup, declarative_property_group):
	'''
	Storage class for LuxRender Engine settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	controls = [
		'export_type',
		'write_files',
		'render',
		'exe_path',
		['write_lxs', 'write_lxm', 'write_lxo'],
		# 'priority',
		['threads_auto', 'threads'],
		# ['rgc', 'colclamp'],
		# ['meshopt', 'nolg'],
	]
	
	visibility = {
		'write_files':		{ 'export_type': 'INT' },
		'render':			O([{'write_files': True}, {'export_type': 'EXT'}]),
		'exe_path':			{ 'render': True, 'export_type': 'EXT' },
		'write_lxs':		{ 'export_type': 'INT', 'write_files': True },
		'write_lxm':		{ 'export_type': 'INT', 'write_files': True },
		'write_lxo':		{ 'export_type': 'INT', 'write_files': True },
		'threads_auto':		A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }]),
		'threads':			A([O([{'write_files': True}, {'export_type': 'EXT'}]), { 'render': True }, { 'threads_auto': False }]),
		'priority':			{ 'export_type': 'EXT', 'render': True },
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
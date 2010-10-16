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
from luxrender.outputs import LuxLog
try:
	# If pylux is not available, revert to 0.7 feature set
	LUXRENDER_VERSION = '0.7'
	
	try:
		tmp = PYLUX_AVAILABLE
	except:
		from luxrender import pylux
		
		LUXRENDER_VERSION = pylux.version()
		
		class Custom_Context(pylux.Context):
			'''
			This is the 'pure' entry point to the pylux.Context API
			
			Some methods in this class have been overridden with
			extensions to provide additional functionality in other
			API types (eg. file_api).
			
			The other Custom_Context APIs are based on this one
			'''
			
			PYLUX = pylux
			API_TYPE = 'PURE'
			
			def attributeBegin(self, comment='', file=None):
				'''
				Added for compatibility with file_api
				'''
				
				pylux.Context.attributeBegin(self)
			
			def transformBegin(self, comment='', file=None):
				'''
				Added for compatibility with file_api
				'''
				
				pylux.Context.transformBegin(self)
			
			# no further action required
		
		if LUXRENDER_VERSION < '0.8':
			from ef.util.util import format_elapsed_time
			
			def printableStatistics(self, add_total):
				stats_dict = {
					'secElapsed': 0.0,
					'samplesSec': 0.0,
					'samplesTotSec': 0.0,
					'samplesPx': 0.0,
					'efficiency': 0.0,
				}
				stats_format = {
					'secElapsed':		format_elapsed_time,
					'samplesSec':		lambda x: 'Samples/Sec: %0.2f'%x,
					'samplesTotSec':	lambda x: 'Total Samples/Sec: %0.2f'%x,
					'samplesPx':		lambda x: 'Samples/Px: %0.2f'%x,
					'efficiency':		lambda x: 'Efficiency: %0.2f %%'%x,
				}
				for k in stats_dict.keys():
					stats_dict[k] = self.statistics(k)
				
					stats_string = ' | '.join(['%s'%stats_format[k](v) for k,v in stats_dict.items()])
					network_servers = self.getServerCount()
					if network_servers > 0:
						stats_string += ' | %i Network Servers Active' % network_servers
				
				return stats_string
			
			Custom_Context.printableStatistics = printableStatistics
		
		PYLUX_AVAILABLE = True
		LuxLog('Using pylux version %s' % LUXRENDER_VERSION)
	
except ImportError as err:
	LuxLog('WARNING: Binary pylux module not available! Visit http://www.luxrender.net/ to obtain one for your system.')
	LuxLog(' (ImportError was: %s)' % err)
	PYLUX_AVAILABLE = False

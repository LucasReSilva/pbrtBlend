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
from luxrender.outputs import LuxLog
try:
	from .LuxFire.Client import ListLuxFireGroup, ServerLocator
	from .LuxFire.Client.Renderer import RendererClient
	
	def Client_Locator(context_name):
		LuxSlavesNames = ListLuxFireGroup()
		
		if len(LuxSlavesNames) > 0:
			#slaves = {}
			for LN, i in LuxSlavesNames.items():
				RS = ServerLocator.get_by_name(LN)
				LS = RendererClient(RS)
				#slaves[LN] = (LS, RS)
				LuxLog('Found LuxFire server %s' % LN)
				break
			
			return LS
		else:
			raise Exception('No remote Lux components available')
	
	LUXFIRE_CLIENT_AVAILABLE = True
except ImportError as err:
	# LuxLog('WARNING: LuxFire/Pyro library not available.')
	LUXFIRE_CLIENT_AVAILABLE = False

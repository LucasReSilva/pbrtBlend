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
class properties_base():
	# This render engine's UI display name
	__label__ = 'LuxRender'
	
	# This should match the engine __main__ class name,
	# and is used to detect if the UI should draw engine-
	# specific panels etc.
	context_name = 'luxrender'
		
	controls = [
		# this list controls the order of property
		# layout in the Panel. This can be a nested
		# list, where each list becomes a row in the
		# panel layout. nesting may be to any depth
	]
	
	# Include some properties in display based on values of others
	selection = {
		# Example: PROPA should be shown if PROPB == VALUE
		# 'PROPA':		[{ 'PROPB': VALUE }],
		
		# Example: PROPA should be shown if (PROPB == VALUEA) or (PROPB == VALUEB)
		# 'PROPA':		[{ 'PROPB': [VALUEA, VALUEB] }],
		
		# Example: PROPA should be shown if (PROPB == VALUEB) and (PROPC == VALUEC)
		# 'PROPA':		[{ 'PROPB': VALUEB }, { 'PROPC': VALUEC }],
		
		# Example: PROPA should be shown if (PROPB == VALUEB) and ((PROPC == VALUEC) or (PROPC == VALUED))
		# 'PROPA':		[{ 'PROPB': VALUEB }, { 'PROPC': [VALUEC, VALUED] }],
	}
	
	properties = []
	
	def get_all_properties(self):
		return self.properties

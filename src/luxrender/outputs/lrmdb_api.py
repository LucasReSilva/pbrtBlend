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

# TODO: Implement
from luxrender.outputs.pure_api import Custom_Context as Pylux_Context

class Custom_Context(Pylux_Context):
	'''
	This class mimicks the pylux.Context API for collecting
	Volume/Texture/Material data to be submitted to the
	LRMDB.
	
	TODO: might also use this class for exporting material
	preview data ?
	'''
	
	API_TYPE = 'LRMDB'
	
	material_definitions = []
	
	def makeNamedVolume(self):
		pass
	
	def texture(self):
		pass
	
	def makeNamedMaterial(self):
		pass

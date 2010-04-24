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

from luxrender.properties import dbo
from luxrender.export import ParamSet

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

class luxrender_integrator(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender SurfaceIntegrator settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	def api_output(self):
		'''
		Format this class's members into a LuxRender ParamSet
		
		Returns tuple
		'''
		
		params = ParamSet()
		
		if self.surfaceintegrator in ['directlighting', 'path']:
			params.add_string('lightstrategy', self.strategy)
		
		if self.surfaceintegrator == 'bidirectional':
			params.add_integer('eyedepth', self.bidir_edepth)
			params.add_integer('lightdepth', self.bidir_ldepth)
		
		if self.surfaceintegrator == 'distributedpath':
			params.add_string('strategy', self.strategy)

#		if self.lux_surfaceintegrator == 'exphotonmap':
#			pass
		
		out = self.surfaceintegrator, params
		dbo('SURFACE INTEGRATOR', out)
		return out

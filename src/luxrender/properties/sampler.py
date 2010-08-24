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

class luxrender_sampler(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender Sampler settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	def api_output(self):
		'''
		Format this class's members into a LuxRender ParamSet
		
		Returns tuple
		'''
		
		params = ParamSet()
		
		if self.sampler in ['random', 'lowdiscrepancy'] or (self.sampler == 'erpt' and self.basesampler in ['random', 'lowdiscrepancy']):
			params.add_integer('pixelsamples', self.pixelsamples)
			params.add_string('pixelsampler', self.pixelsampler)
		
		if self.sampler == 'erpt':
			params.add_integer('chainlength', self.chainlength)
			params.add_string('basesampler', self.basesampler)
		
		if self.sampler == 'metropolis':
			params.add_float('largemutationprob', self.largemutationprob)
			params.add_bool('usevariance', self.usevariance)
			
		if self.advanced:
			if self.sampler == 'metropolis' or (self.sampler == 'erpt' and self.basesampler == 'metropolis'):
				params.add_integer('maxconsecrejects', self.maxconsecrejects)
			if self.sampler in ['metropolis', 'erpt']:
				params.add_integer('mutationrange', self.mutationrange)
		
		out = self.sampler, params
		dbo('SAMPLER', out)
		return out

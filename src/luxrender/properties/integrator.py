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

from . import dbo
from ..export import ParamSet

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
		
		if self.surfaceintegrator == 'bidirectional':
			params.add_string('strategy', self.strategy) \
				  .add_integer('eyedepth', self.eyedepth) \
				  .add_integer('lightdepth', self.lightdepth)
			if self.advanced:
				params.add_float('eyerrthreshold', self.eyerrthreshold)
				params.add_float('lightrrthreshold', self.lightrrthreshold)
		
		if self.surfaceintegrator == 'directlighting':
			params.add_integer('maxdepth', self.maxdepth)
		
		if self.surfaceintegrator == 'distributedpath':
			params.add_string('strategy', self.strategy) \
				  .add_bool('directsampleall', self.directsampleall) \
				  .add_integer('directsamples', self.directsamples) \
				  .add_bool('directdiffuse', self.directdiffuse) \
				  .add_bool('directglossy', self.directglossy) \
				  .add_bool('indirectsampleall', self.indirectsampleall) \
				  .add_integer('indirectsamples', self.indirectsamples) \
				  .add_bool('indirectdiffuse', self.indirectdiffuse) \
				  .add_bool('indirectglossy', self.indirectglossy) \
				  .add_integer('diffusereflectdepth', self.diffusereflectdepth) \
				  .add_integer('diffusereflectsamples', self.diffusereflectsamples) \
				  .add_integer('diffuserefractdepth', self.diffuserefractdepth) \
				  .add_integer('diffuserefractsamples', self.diffuserefractsamples) \
				  .add_integer('glossyreflectdepth', self.glossyreflectdepth) \
				  .add_integer('glossyreflectsamples', self.glossyreflectsamples) \
				  .add_integer('glossyrefractdepth', self.glossyrefractdepth) \
				  .add_integer('glossyrefractsamples', self.glossyrefractsamples) \
				  .add_integer('specularreflectdepth', self.specularreflectdepth) \
				  .add_integer('specularrefractdepth', self.specularrefractdepth) \
				  .add_bool('diffusereflectreject', self.diffusereflectreject) \
				  .add_float('diffusereflectreject_threshold', self.diffusereflectreject_threshold) \
				  .add_bool('diffuserefractreject', self.diffuserefractreject) \
				  .add_float('diffuserefractreject_threshold', self.diffuserefractreject_threshold) \
				  .add_bool('glossyreflectreject', self.glossyreflectreject) \
				  .add_float('glossyreflectreject_threshold', self.glossyreflectreject_threshold) \
				  .add_bool('glossyrefractreject', self.glossyrefractreject) \
				  .add_float('glossyrefractreject_threshold', self.glossyrefractreject_threshold)
		
		if self.surfaceintegrator == 'exphotonmap':
			params.add_integer('maxdepth', self.maxdepth) \
				  .add_integer('maxphotondepth', self.maxphotondepth) \
				  .add_integer('directphotons', self.directphotons) \
				  .add_integer('causticphotons', self.causticphotons) \
				  .add_integer('indirectphotons', self.indirectphotons) \
				  .add_integer('radiancephotons', self.radiancephotons) \
				  .add_integer('nphotonsused', self.nphotonsused) \
				  .add_float('maxphotondist', self.maxphotondist) \
				  .add_bool('finalgather', self.finalgather) \
				  .add_integer('finalgathersamples', self.finalgathersamples) \
				  .add_string('renderingmode', self.renderingmode) \
				  .add_float('gatherangle', self.gatherangle) \
				  .add_string('rrstrategy', self.rrstrategy) \
				  .add_float('rrcontinueprob', self.rrcontinueprob)
			if self.advanced:
				params.add_float('distancethreshold', self.distancethreshold) \
					  .add_string('photonmapsfile', self.photonmapsfile) \
					  .add_bool('dbg_enabledirect', self.dbg_enabledirect) \
					  .add_bool('dbg_enableradiancemap', self.dbg_enableradiancemap) \
					  .add_bool('dbg_enableindircaustic', self.dbg_enableindircaustic) \
					  .add_bool('dbg_enableindirdiffuse', self.dbg_enableindirdiffuse) \
					  .add_bool('dbg_enableindirspecular', self.dbg_enableindirspecular)
		
		if self.surfaceintegrator == 'igi':
			params.add_integer('nsets', self.nsets) \
				  .add_integer('nlights', self.nlights) \
				  .add_integer('maxdepth', self.maxdepth) \
				  .add_float('mindist', self.mindist)
		
		if self.surfaceintegrator == 'path':
			params.add_integer('maxdepth', self.maxdepth) \
				  .add_float('rrcontinueprob', self.rrcontinueprob) \
				  .add_string('rrstrategy', self.rrstrategy) \
				  .add_bool('includeenvironment', self.includeenvironment)
		
		out = self.surfaceintegrator, params
		dbo('SURFACE INTEGRATOR', out)
		return out

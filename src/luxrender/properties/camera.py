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
import math

import bpy

from . import dbo
from ..export.film import resolution
from ..export import ParamSet

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

class luxrender_camera(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender Camera settings.
	This class will be instantiated within a Blender camera
	object.
	'''
	
	def screenwindow(self, xr, yr, cam):
		'''
		xr			float
		yr			float
		cam		   bpy.types.camera
		
		Calculate LuxRender camera's screenwindow parameter
		
		Returns list[4]
		'''
		
		shiftX = cam.shift_x
		shiftY = cam.shift_x
		
		# TODO:
		scale = 1.0
		
		aspect = xr/yr
		invaspect = 1.0/aspect
		
		if aspect > 1.0:
			sw = [
				((2*shiftX)-1) * scale,
				((2*shiftX)+1) * scale,
				((2*shiftY)-invaspect) * scale,
				((2*shiftY)+invaspect) * scale
			]
		else:
			sw = [
				((2*shiftX)-aspect) * scale,
				((2*shiftX)+aspect) * scale,
				((2*shiftY)-1) * scale,
				((2*shiftY)+1) * scale
				]
				
		return sw
	
	def api_output(self, scene, is_cam_animated):
		'''
		scene			bpy.types.scene
		
		Format this class's members into a LuxRender ParamSet
		
		Returns tuple
		'''
		
		cam = scene.camera.data
		xr, yr = resolution(scene)
		
		params = ParamSet()
		
		params.add_float('fov', math.degrees(scene.camera.data.angle))
		params.add_float('screenwindow', self.screenwindow(xr, yr, cam))
		params.add_bool('autofocus', False)
		params.add_float('shutteropen', 0.0)
		params.add_float('shutterclose', self.exposure)
		
		if self.use_dof:
			params.add_float('lensradius', (cam.lens / 1000.0) / ( 2.0 * self.fstop ))
		
		if self.autofocus:
			params.add_bool('autofocus', True)
		else:
			if cam.dof_object is not None:
				params.add_float('focaldistance', (scene.camera.location - cam.dof_object.location).length)
			elif cam.dof_distance > 0:
				params.add_float('focaldistance', cam.dof_distance)
			
		if self.use_clipping:
			params.add_float('hither', cam.clip_start)
			params.add_float('yon', cam.clip_end)

		if self.usemblur:
			# update the camera settings with motion blur settings
			params.add_string('shutterdistribution', self.shutterdistribution)

			if self.cammblur and is_cam_animated:
				   params.add_string('endtransform', 'CameraEndTransform')
		
		out = self.type, params
		dbo('CAMERA', out)
		return out

class luxrender_colorspace(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender Colour-Space settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	pass

class luxrender_tonemapping(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender ToneMapping settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	def api_output(self, scene):
		'''
		scene			bpy.types.scene
		
		Format this class's members into a LuxRender ParamSet
		
		Returns tuple
		'''
		
		cam = scene.camera.data
		
		params = ParamSet()
		
		params.add_string('tonemapkernel', self.type)
		
		if self.type == 'reinhard':
			params.add_float('reinhard_prescale', self.reinhard_prescale)
			params.add_float('reinhard_postscale', self.reinhard_postscale)
			params.add_float('reinhard_burn', self.reinhard_burn)
			
		if self.type == 'linear':
			params.add_float('linear_sensitivity', cam.luxrender_camera.sensitivity)
			params.add_float('linear_exposure', cam.luxrender_camera.exposure)
			params.add_float('linear_fstop', cam.luxrender_camera.fstop)
			params.add_float('linear_gamma', self.linear_gamma)
			
		out = self.type, params
		dbo('TONEMAPPING', out)
		return out


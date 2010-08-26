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

from ef.ui import declarative_property_group

from luxrender.properties import dbo
from luxrender.export import get_worldscale
from luxrender.export.film import resolution
from luxrender.export import ParamSet
from luxrender.outputs import LuxManager as LM

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

class luxrender_camera(bpy.types.IDPropertyGroup, declarative_property_group):
	'''
	Storage class for LuxRender Camera settings.
	This class will be instantiated within a Blender
	camera object.
	'''
	
	controls = [
		['autofocus', 'use_dof', 'use_clipping'],
		'type',
		'fstop',
		'sensitivity',
		'exposure',
		'usemblur',
		'shutterdistribution', 
		['cammblur', 'objectmblur'], 
	]
	
	visibility = {
		'type':						{ 'is_perspective': True }, 
		'shutterdistribution':		{ 'usemblur': True },
		'cammblur':					{ 'usemblur': True },
		'objectmblur':				{ 'usemblur': True },
	}
	
	properties = [
		# hidden property set via draw() method
		{
			'type': 'bool',
			'attr': 'is_perspective',
			'name': 'is_perspective',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'use_clipping',
			'name': 'Clipping',
			'description': 'Use near/far geometry clipping',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'use_dof',
			'name': 'DOF',
			'description': 'Use DOF effect',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'autofocus',
			'name': 'Auto focus',
			'description': 'Use auto focus',
			'default': True,
		},
		{
			'type': 'enum',
			'attr': 'type',
			'name': 'Camera type',
			'description': 'Choose camera type',
			'default': 'perspective',
			'items': [
				('perspective', 'Perspective', 'perspective'),
				('environment', 'Environment', 'environment'),
				#('realistic', 'Realistic', 'realistic'),
			]
		},
		{
			'type': 'float',
			'attr': 'fstop',
			'name': 'f/Stop',
			'description': 'f/Stop',
			'default': 2.8,
			'min': 0.4,
			'soft_min': 0.4,
			'max': 128.0,
			'soft_max': 128.0
		},
		{
			'type': 'float',
			'attr': 'sensitivity',
			'name': 'ISO',
			'description': 'Sensitivity (ISO)',
			'default': 320.0,
			'min': 10.0,
			'soft_min': 10.0,
			'max': 6400.0,
			'soft_max': 6400.0
		},
		{
			'type': 'float',
			'attr': 'exposure',
			'name': 'Exposure',
			'description': 'Exposure time (secs)',
			'precision': 6,
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 25.0,
			'soft_max': 25.0
		},
		{
			'type': 'bool',
			'attr': 'usemblur',
			'name': 'Motion Blur',
			'default': False
		},
		{
			'type': 'enum',
			'attr': 'shutterdistribution',
			'name': 'Distribution',
			'default': 'uniform',
			'items': [
				('uniform', 'Uniform', 'uniform'),
				('gaussian', 'Gaussian', 'gaussian'),
			]
		},
		{
			'type': 'bool',
			'attr': 'cammblur',
			'name': 'Camera Motion Blur',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'objectmblur',
			'name': 'Object Motion Blur',
			'default': True
		},	
	]
	
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
			# Do not world-scale this, it is already in meters !
			params.add_float('lensradius', (cam.lens / 1000.0) / ( 2.0 * self.fstop ))
		
		ws = get_worldscale(scene=scene, as_scalematrix=False)
		
		if self.autofocus:
			params.add_bool('autofocus', True)
		else:
			if cam.dof_object is not None:
				params.add_float('focaldistance', ws*((scene.camera.location - cam.dof_object.location).length))
			elif cam.dof_distance > 0:
				params.add_float('focaldistance', ws*cam.dof_distance)
			
		if self.use_clipping:
			params.add_float('hither', ws*cam.clip_start)
			params.add_float('yon', ws*cam.clip_end)

		if self.usemblur:
			# update the camera settings with motion blur settings
			params.add_string('shutterdistribution', self.shutterdistribution)

			if self.cammblur and is_cam_animated:
				   params.add_string('endtransform', 'CameraEndTransform')
		
		out = self.type, params
		dbo('CAMERA', out)
		return out

class luxrender_colorspace(bpy.types.IDPropertyGroup, declarative_property_group):
	'''
	Storage class for LuxRender Colour-Space settings.
	This class will be instantiated within a Blender
	camera object.
	'''
	
	controls = [
		'gamma',
		
		[0.1, 'preset', 'preset_name'],
		['cs_whiteX', 'cs_whiteY'],
		['cs_redX', 'cs_redY'],
		['cs_greenX', 'cs_greenY'],
		['cs_blueX', 'cs_blueY'],
	]
	
	visibility = {
		'preset_name':	{ 'preset': True },
		'cs_whiteX':	{ 'preset': False },
		'cs_whiteY':	{ 'preset': False },
		'cs_redX':		{ 'preset': False },
		'cs_redY':		{ 'preset': False },
		'cs_greenX':	{ 'preset': False },
		'cs_greenY':	{ 'preset': False },
		'cs_blueX':		{ 'preset': False },
		'cs_blueY':		{ 'preset': False },
	}
	
	properties = [
		{
			'attr': 'gamma',
			'type': 'float',
			'name': 'Gamma',
			'default': 2.2
		},
		{
			'attr': 'preset',
			'type': 'bool',
			'name': 'P',
			'default': True,
			'toggle': True
		},
		# TODO - change actual parameter values when user chooses a preset
		{
			'attr': 'preset_name',
			'type': 'enum',
			'name': 'Preset',
			'default': 'sRGB',
			'items': [
				('sRGB', 'sRGB - HDTV (ITU-R BT.709-5)', 'sRGB'),
				('romm_rgb', 'ROMM RGB', 'romm_rgb'),
				('adobe_rgb_98', 'Adobe RGB 98', 'adobe_rgb_98'),
				('apple_rgb', 'Apple RGB', 'apple_rgb'),
				('ntsc_1953', 'NTSC (FCC 1953, ITU-R BT.470-2 System M)', 'ntsc_1953'),
				('ntsc_1979', 'NTSC (1979) (SMPTE C, SMPTE-RP 145)', 'ntsc_1979'),
				('pal_secam', 'PAL/SECAM (EBU 3213, ITU-R BT.470-6)', 'pal_secam'),
				('cie_e', 'CIE (1931) E', 'cie_e'),
			]
		},
		{
			'attr': 'cs_whiteX',
			'type': 'float',
			'name': 'White X',
			'precision': 6,
			'default': 0.314275
		},
		{
			'attr': 'cs_whiteY',
			'type': 'float',
			'name': 'White Y',
			'precision': 6,
			'default': 0.329411
		},
		
		{
			'attr': 'cs_redX',
			'type': 'float',
			'name': 'Red X',
			'precision': 6,
			'default': 0.63
		},
		{
			'attr': 'cs_redY',
			'type': 'float',
			'name': 'Red Y',
			'precision': 6,
			'default': 0.34
		},
		
		{
			'attr': 'cs_greenX',
			'type': 'float',
			'name': 'Green X',
			'precision': 6,
			'default': 0.31
		},
		{
			'attr': 'cs_greenY',
			'type': 'float',
			'name': 'Green Y',
			'precision': 6,
			'default': 0.595
		},
		
		{
			'attr': 'cs_blueX',
			'type': 'float',
			'name': 'Blue X',
			'precision': 6,
			'default': 0.155
		},
		{
			'attr': 'cs_blueY',
			'type': 'float',
			'name': 'Blue Y',
			'precision': 6,
			'default': 0.07
		},
	]

class tonemapping_live_update(object):
	prop_lookup = {
		#'type':				 'LUX_FILM_TM_TONEMAPKERNEL',
		'reinhard_prescale':	'LUX_FILM_TM_REINHARD_PRESCALE',
		'reinhard_postscale':	'LUX_FILM_TM_REINHARD_POSTSCALE',
		'reinhard_burn':		'LUX_FILM_TM_REINHARD_BURN',
	}
	prop_vals = {}
	@staticmethod
	def update(context, scene, property):
		if LM.ActiveManager is not None and LM.ActiveManager.started:
			prop_val = getattr(scene.camera.data.luxrender_tonemapping, property)
			if property not in tonemapping_live_update.prop_vals.keys():
				tonemapping_live_update.prop_vals[property] = prop_val
			
			if tonemapping_live_update.prop_vals[property] != prop_val:
				tonemapping_live_update.prop_vals[property] = prop_val
				c = LM.ActiveManager.lux_context
				c.setParameterValue(
					c.PYLUX.luxComponent.LUX_FILM,
					getattr(c.PYLUX.luxComponentParameters, tonemapping_live_update.prop_lookup[property]),
					prop_val,
					0
				)

class luxrender_tonemapping(bpy.types.IDPropertyGroup, declarative_property_group):
	'''
	Storage class for LuxRender ToneMapping settings.
	This class will be instantiated within a Blender
	camera object.
	'''
	
	property_group_non_global = True
	
	controls = [
		'type',
		
		# Reinhard
		['reinhard_prescale', 'reinhard_postscale', 'reinhard_burn'],
		
		# Linear
		'linear_gamma',
		
		# Contrast
		'ywa',
	]
	
	visibility = {
		# Reinhard
		'reinhard_prescale':	{ 'type': 'reinhard' },
		'reinhard_postscale':	{ 'type': 'reinhard' },
		'reinhard_burn':		{ 'type': 'reinhard' },
		
		# Linear
		'linear_gamma':			{ 'type': 'linear' },
		
		# Contrast
		'ywa':					{ 'type': 'contrast' },
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'type',
			'name': 'Tonemapper',
			'description': 'Choose tonemapping type',
			'default': 'reinhard',
			'items': [
				('reinhard', 'Reinhard', 'reinhard'),
				('linear', 'Linear', 'linear'),
				('contrast', 'Contrast', 'contrast'),
				('maxwhite', 'Maxwhite', 'maxwhite')
			],
			#'draw': lambda context, scene: tonemapping_live_update.update(context, scene, 'type')
		},
		
		# Reinhard
		{
			'type': 'float',
			'attr': 'reinhard_prescale',
			'name': 'Pre',
			'description': 'Reinhard Pre-Scale factor',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 25.0,
			'soft_max': 25.0,
			# 'draw': lambda context, scene: tonemapping_live_update.update(context, scene, 'reinhard_prescale') 
		},
		{
			'type': 'float',
			'attr': 'reinhard_postscale',
			'name': 'Post',
			'description': 'Reinhard Post-Scale factor',
			'default': 1.2,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 25.0,
			'soft_max': 25.0,
			# 'draw': lambda context, scene: tonemapping_live_update.update(context, scene, 'reinhard_postscale')
		},
		{
			'type': 'float',
			'attr': 'reinhard_burn',
			'name': 'Burn',
			'description': 'Reinhard Burn factor',
			'default': 6.0,
			'min': 0.01,
			'soft_min': 0.01,
			'max': 25.0,
			'soft_max': 25.0,
			# 'draw': lambda context, scene: tonemapping_live_update.update(context, scene, 'reinhard_burn')
		},
		
		#Linear
		{
			'type': 'float',
			'attr': 'linear_gamma',
			'name': 'Gamma',
			'description': 'Linear gamma',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 5.0,
			'soft_max': 5.0
		},
		
		#Contrast
		{
			'type': 'float',
			'attr': 'ywa',
			'name': 'Ywa',
			'description': 'World adaption luminance',
			'default': 0.1,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 2e5,
			'soft_max': 2e5
		}
	]
	
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
			
		if self.type == 'contrast':
			params.add_float('ywa', self.ywa)
			
		out = self.type, params
		dbo('TONEMAPPING', out)
		return out


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

from properties_data_camera import DataButtonsPanel

# EF API
from ef.ui import described_layout
from ef.ef import ef

import luxrender.properties.camera
from ..module import LuxManager as LM

class camera(DataButtonsPanel, described_layout):
	bl_label = 'LuxRender Camera'
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender.properties.camera.luxrender_camera
	# prevent creating luxrender_camera property group in Scene
	property_group_non_global = True
	
	@staticmethod
	def property_reload():
		for cam in bpy.data.cameras:
			camera.property_create(cam)
	
	@staticmethod
	def property_create(cam):
		if not hasattr(cam, camera.property_group.__name__):
			ef.init_properties(cam, [{
				'type': 'pointer',
				'attr': camera.property_group.__name__,
				'ptype': camera.property_group,
				'name': camera.property_group.__name__,
				'description': camera.property_group.__name__
			}], cache=False)
			ef.init_properties(camera.property_group, camera.properties, cache=False)
	
	# Overridden to provide data storage in the camera, not the scene
	def draw(self, context):
		if context.camera is not None:
			camera.property_create(context.camera)
			
			# Show only certain controls for Blender's perspective camera type 
			context.camera.luxrender_camera.is_perspective = (context.camera.type == 'PERSP')
			
			for p in self.controls:
				self.draw_column(p, self.layout, context.camera, supercontext=context)
	
	controls = [
		['autofocus', 'use_dof', 'use_clipping'],
		'type',
		'fstop',
		'sensitivity',
		'exposure',
	]
	
	visibility = {
		'type':			{ 'is_perspective': True }, 
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
			'min': 0.1,
			'soft_min': 0.1,
			'max': 64.0,
			'soft_max': 64.0
		},
		{
			'type': 'float',
			'attr': 'sensitivity',
			'name': 'ISO',
			'description': 'Sensitivity (ISO)',
			'default': 50.0,
			'min': 0.0,
			'soft_min': 0.0,
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
			prop_val = getattr(scene.luxrender_tonemapping, property)
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

class tonemapping(DataButtonsPanel, described_layout):
	bl_label = 'LuxRender ToneMapping'
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender.properties.camera.luxrender_tonemapping
	
	controls = [
		'type',
		
		# Reinhard
		['reinhard_prescale', 'reinhard_postscale', 'reinhard_burn'],
		
		# Linear
		'linear_gamma',
	]
	
	visibility = {
		# Reinhard
		'reinhard_prescale':			{ 'type': 'reinhard' },
		'reinhard_postscale':			{ 'type': 'reinhard' },
		'reinhard_burn':				{ 'type': 'reinhard' },
		
		# Linear
		'linear_gamma':					{ 'type': 'linear' },
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
			'default': 2.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 25.0,
			'soft_max': 25.0,
			'draw': lambda context, scene: tonemapping_live_update.update(context, scene, 'reinhard_prescale') 
		},
		{
			'type': 'float',
			'attr': 'reinhard_postscale',
			'name': 'Post',
			'description': 'Reinhard Post-Scale factor',
			'default': 1.04,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 25.0,
			'soft_max': 25.0,
			'draw': lambda context, scene: tonemapping_live_update.update(context, scene, 'reinhard_postscale')
		},
		{
			'type': 'float',
			'attr': 'reinhard_burn',
			'name': 'Burn',
			'description': 'Reinhard Burn factor',
			'default': 6.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 25.0,
			'soft_max': 25.0,
			'draw': lambda context, scene: tonemapping_live_update.update(context, scene, 'reinhard_burn')
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
	]
	
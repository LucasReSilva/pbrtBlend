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
import math
import os

import bpy

from extensions_framework import util as efutil
from extensions_framework import declarative_property_group

from luxrender.properties import dbo
from luxrender.export import get_worldscale
from luxrender.export import ParamSet, LuxManager
from luxrender.outputs.pure_api import LUXRENDER_VERSION

def CameraVolumeParameter(attr, name):
	return [
		{
			'attr': '%s_volume' % attr,
			'type': 'string',
			'name': '%s_volume' % attr,
			'description': '%s volume; leave blank to use World default' % attr,
			'save_in_preset': True
		},
		{
			'type': 'prop_search',
			'attr': attr,
			'src': lambda s,c: s.scene.luxrender_volumes,
			'src_attr': 'volumes',
			'trg': lambda s,c: c.luxrender_camera,
			'trg_attr': '%s_volume' % attr,
			'name': name
		},
	]

class luxrender_camera(declarative_property_group):
	'''
	Storage class for LuxRender Camera settings.
	This class will be instantiated within a Blender
	camera object.
	'''
	
	controls = [
		'Exterior',
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
		'shutterdistribution':		{ 'usemblur': True },
		'cammblur':					{ 'usemblur': True },
		'objectmblur':				{ 'usemblur': True },
	}
	
	properties = CameraVolumeParameter('Exterior', 'Exterior') + [
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
	
	def lookAt(self, camera):
		'''
		Derive a list describing 3 points for a LuxRender LookAt statement
		
		Returns		tuple(9) (floats)
		'''
		matrix = camera.matrix_world.copy()
		ws = get_worldscale()
		matrix *= ws
		ws = get_worldscale(as_scalematrix=False)
		matrix[3][0] *= ws
		matrix[3][1] *= ws
		matrix[3][2] *= ws
		pos = matrix[3]
		forwards = -matrix[2]
		target = (pos + forwards)
		up = matrix[1]
		return (pos[0], pos[1], pos[2], target[0], target[1], target[2], up[0], up[1], up[2])
	
	def screenwindow(self, xr, yr, cam):
		'''
		xr			float
		yr			float
		cam		   bpy.types.camera
		
		Calculate LuxRender camera's screenwindow parameter
		
		Returns list[4]
		'''
		
		shiftX = cam.shift_x
		shiftY = cam.shift_y
		
		if cam.type == 'ORTHO':
			scale = cam.ortho_scale / 2.0
		else:
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
		xr, yr = self.luxrender_film.resolution()
		
		params = ParamSet()
		
		if cam.type == 'PERSP' and self.type == 'perspective':
			params.add_float('fov', math.degrees(scene.camera.data.angle))
		
		params.add_float('screenwindow', self.screenwindow(xr, yr, cam))
		params.add_bool('autofocus', False)
		params.add_float('shutteropen', 0.0)
		params.add_float('shutterclose', self.exposure)
		
		if self.use_dof:
			# Do not world-scale this, it is already in meters !
			params.add_float('lensradius', (cam.lens / 1000.0) / ( 2.0 * self.fstop ))
		
		ws = get_worldscale(as_scalematrix=False)
		
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
		
		cam_type = 'orthographic' if cam.type == 'ORTHO' else self.type
		out = cam_type, params
		dbo('CAMERA', out)
		return out

def luxrender_colorspace_controls():
	ctl = [
		'cs_label',
		[0.1, 'preset', 'preset_name'],
		['cs_whiteX', 'cs_whiteY'],
		['cs_redX', 'cs_redY'],
		['cs_greenX', 'cs_greenY'],
		['cs_blueX', 'cs_blueY'],
		
		'gamma_label',
		'gamma',
	]
	
	if LUXRENDER_VERSION >= '0.8':
		ctl.extend([
			'use_crf',
			'crf_file'
		])
	
	return ctl

class luxrender_colorspace(declarative_property_group):
	'''
	Storage class for LuxRender Colour-Space settings.
	This class will be instantiated within a Blender
	camera object.
	'''
	
	controls = luxrender_colorspace_controls()
	
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
		'crf_file':		{ 'use_crf': True },
	}
	
	properties = [
		{
			'attr': 'cs_label',
			'type': 'text',
			'name': 'Color Space'
		},
		{
			'attr': 'gamma_label',
			'type': 'text',
			'name': 'Gamma'
		},
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
		
		# Camera Response Functions
		{
			'attr': 'use_crf',
			'type': 'bool',
			'name': 'Use Camera Response Function',
			'default': False
		},
		{
			'attr': 'crf_file',
			'type': 'string',
			'subtype': 'FILE_PATH',
			'name': 'CRF File',
			'default': '',
		},
	]

class colorspace_presets(object):
	class sRGB(object):
		cs_whiteX	= 0.314275
		cs_whiteY	= 0.329411
		cs_redX		= 0.63
		cs_redY		= 0.34
		cs_greenX	= 0.31
		cs_greenY	= 0.595
		cs_blueX	= 0.155
		cs_blueY	= 0.07
	class romm_rgb(object):
		cs_whiteX	= 0.346
		cs_whiteY	= 0.359
		cs_redX		= 0.7347
		cs_redY		= 0.2653
		cs_greenX	= 0.1596
		cs_greenY	= 0.8404
		cs_blueX	= 0.0366
		cs_blueY	= 0.0001
	class adobe_rgb_98(object):
		cs_whiteX	= 0.313
		cs_whiteY	= 0.329
		cs_redX		= 0.64
		cs_redY		= 0.34
		cs_greenX	= 0.21
		cs_greenY	= 0.71
		cs_blueX	= 0.15
		cs_blueY	= 0.06
	class apple_rgb(object):
		cs_whiteX	= 0.313
		cs_whiteY	= 0.329
		cs_redX		= 0.625
		cs_redY		= 0.34
		cs_greenX	= 0.28
		cs_greenY	= 0.595
		cs_blueX	= 0.155
		cs_blueY	= 0.07
	class ntsc_1953(object):
		cs_whiteX	= 0.31
		cs_whiteY	= 0.316
		cs_redX		= 0.67
		cs_redY		= 0.33
		cs_greenX	= 0.21
		cs_greenY	= 0.71
		cs_blueX	= 0.14
		cs_blueY	= 0.08
	class ntsc_1979(object):
		cs_whiteX	= 0.313
		cs_whiteY	= 0.329
		cs_redX		= 0.63
		cs_redY		= 0.34
		cs_greenX	= 0.31
		cs_greenY	= 0.595
		cs_blueX	= 0.155
		cs_blueY	= 0.07
	class pal_secam(object):
		cs_whiteX	= 0.313
		cs_whiteY	= 0.329
		cs_redX		= 0.64
		cs_redY		= 0.33
		cs_greenX	= 0.29
		cs_greenY	= 0.6
		cs_blueX	= 0.15
		cs_blueY	= 0.06
	class cie_e(object):
		cs_whiteX	= 0.333
		cs_whiteY	= 0.333
		cs_redX		= 0.7347
		cs_redY		= 0.2653
		cs_greenX	= 0.2738
		cs_greenY	= 0.7174
		cs_blueX	= 0.1666
		cs_blueY	= 0.0089

# TODO, move all film properties into this property group

class luxrender_film(declarative_property_group):
	controls = [
		'writeinterval',
		'displayinterval',
		'lbl_outputs',
		'integratedimaging',
		['write_png', 'write_exr','write_tga','write_flm'],
		'output_alpha',
		'outlierrejection_k',
	]
	
	visibility = {}
	
	properties = [
		
		{
			'type': 'int',
			'attr': 'writeinterval',
			'name': 'Save interval',
			'description': 'Period for writing images to disk (seconds)',
			'default': 10,
			'min': 2,
			'soft_min': 2,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'displayinterval',
			'name': 'GUI refresh interval',
			'description': 'Period for updating rendering on screen (seconds)',
			'default': 10,
			'min': 2,
			'soft_min': 2,
			'save_in_preset': True
		},
		{
			'type': 'text',
			'attr': 'lbl_outputs',
			'name': 'Output formats'
		},
		{
			'type': 'bool',
			'attr': 'integratedimaging',
			'name': 'Integrated Imaging workflow',
			'description': 'Transfer rendered image directly to Blender without saving to disk (adds Alpha and Z-buffer support)',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 'write_png',
			'name': 'PNG',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'write_exr',
			'name': 'EXR',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 'write_tga',
			'name': 'TGA',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 'write_flm',
			'name': 'FLM',
			'default': False
		},
		{
			'type': 'bool',
			'attr': 'output_alpha',
			'name': 'Enable alpha channel',
			'default': False
		},
		{
			'type': 'int',
			'attr': 'outlierrejection_k',
			'name': 'Firefly rejection',
			'description': 'Firefly (outlier) rejection k parameter',
			'default': 0,
			'min': 0,
			'soft_min': 0,
		},
	]
	
	def resolution(self):
		'''
		Calculate the output render resolution
		
		Returns		tuple(2) (floats)
		'''
		scene = LuxManager.CurrentScene
		
		xr = scene.render.resolution_x * scene.render.resolution_percentage / 100.0
		yr = scene.render.resolution_y * scene.render.resolution_percentage / 100.0
		
		return xr, yr
	
	def api_output(self):
		'''
		Calculate type and parameters for LuxRender Film statement
		
		Returns		tuple(2) (string, list) 
		'''
		scene = LuxManager.CurrentScene
		
		xr, yr = self.resolution()
		
		params = ParamSet()
		
		# Set resolution
		params.add_integer('xresolution', int(xr))
		params.add_integer('yresolution', int(yr))
		
		# ColourSpace
		cso = self.luxrender_colorspace
		params.add_float('gamma', cso.gamma)
		if cso.preset:
			cs_object = getattr(colorspace_presets, cso.preset_name)
		else:
			cs_object = cso
		
		params.add_float('colorspace_white',	[cs_object.cs_whiteX,	cs_object.cs_whiteY])
		params.add_float('colorspace_red',		[cs_object.cs_redX,		cs_object.cs_redY])
		params.add_float('colorspace_green',	[cs_object.cs_greenX,	cs_object.cs_greenY])
		params.add_float('colorspace_blue',		[cs_object.cs_blueX,	cs_object.cs_blueY])
		
		# Camera Response Function
		if LUXRENDER_VERSION >= '0.8' and cso.use_crf:
			if scene.camera.library is not None:
				local_crf_filepath = bpy.path.abspath(cso.crf_file, scene.camera.library.filepath)
			else:
				local_crf_filepath = cso.crf_file
			local_crf_filepath = efutil.filesystem_path( local_crf_filepath )
			if scene.luxrender_engine.embed_filedata:
				from luxrender.util import bencode_file2string
				params.add_string('cameraresponse', os.path.basename(local_crf_filepath))
				params.add_string('cameraresponse_data', bencode_file2string(local_crf_filepath) )
			else:
				params.add_string('cameraresponse', local_crf_filepath)
		
		# Output types
		params.add_string('filename', efutil.path_relative_to_export(efutil.export_path))
		params.add_bool('write_resume_flm', self.write_flm)
		
		if scene.luxrender_engine.export_type == 'INT' and self.integratedimaging:
			# Set up params to enable z buffer and set gamma=1.0
			params.add_string('write_exr_channels', 'RGBA')
			params.add_bool('write_exr_halftype', False)
			params.add_bool('write_exr_applyimaging', True)
			params.add_bool('write_exr_ZBuf', True)
			params.add_string('write_exr_zbuf_normalizationtype', 'Camera Start/End clip')
			params.add_float('gamma', 1.0) # Linear workflow !
		
		if self.output_alpha:
			output_channels = 'RGBA'
		else:
			output_channels = 'RGB'
		
		params.add_bool('write_exr', self.write_exr)
		params.add_string('write_exr_channels', output_channels)
		params.add_bool('write_png', self.write_png)
		params.add_string('write_png_channels', output_channels)
		params.add_bool('write_tga', self.write_tga)
		params.add_string('write_tga_channels', output_channels)
		
		params.add_integer('displayinterval', self.displayinterval)
		params.add_integer('writeinterval', self.writeinterval)
		
		# Halt conditions
		if scene.luxrender_sampler.haltspp > 0:
			params.add_integer('haltspp', scene.luxrender_sampler.haltspp)
		
		if scene.luxrender_sampler.halttime > 0:
			params.add_integer('halttime', scene.luxrender_sampler.halttime)
		
		if self.outlierrejection_k > 0:
			params.add_integer('outlierrejection_k', self.outlierrejection_k)
		
		# update the film settings with tonemapper settings
		params.update( self.luxrender_tonemapping.get_paramset() )
		
		return ('fleximage', params)

def get_tonemaps():
	
	items =  [
		('reinhard', 'Reinhard', 'reinhard'),
		('linear', 'Linear (manual)', 'linear'),
		# put autolinear in this space for supported versions
		('contrast', 'Contrast', 'contrast'),
		('maxwhite', 'Maxwhite', 'maxwhite')
	]
	
	if LUXRENDER_VERSION >= '0.8':
		items.insert(2,
			('autolinear', 'Linear (auto-exposure)', 'autolinear')
		)
	
	return items

class luxrender_tonemapping(declarative_property_group):
	'''
	Storage class for LuxRender ToneMapping settings.
	This class will be instantiated within a Blender
	camera object.
	'''
	
	controls = [
		'tm_label',
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
			'attr': 'tm_label',
			'type': 'text',
			'name': 'Tonemapping'
		},
		{
			'type': 'enum',
			'attr': 'type',
			'name': 'Tonemapper',
			'description': 'Choose tonemapping type',
			'default': 'reinhard',
			'items': get_tonemaps(),
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
	
	def get_paramset(self):
		cam = LuxManager.CurrentScene.camera.data
		
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
			params.add_float('contrast_ywa', self.ywa)
		
		return params

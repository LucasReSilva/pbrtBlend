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
from extensions_framework import util as efutil

from luxrender.export import get_worldscale
from luxrender.export import ParamSet
from luxrender.outputs import LuxManager as LM

def lookAt(scene):
	'''
	scene		bpy.types.scene
	
	Derive a list describing 3 points for a LuxRender LookAt statement
	
	Returns		tuple(9) (floats)
	'''
	
	matrix = scene.camera.matrix_world.copy()
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
	
def resolution(scene):
	'''
	scene		bpy.types.scene
	
	Calculate the output render resolution
	
	Returns		tuple(2) (floats)
	'''
	
	xr = scene.render.resolution_x * scene.render.resolution_percentage / 100.0
	yr = scene.render.resolution_y * scene.render.resolution_percentage / 100.0
	
	return xr, yr

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

def film(scene):
	'''
	scene		bpy.types.scene
	
	Calculate type and parameters for LuxRender Film statement
	
	Returns		tuple(2) (string, list) 
	'''
	
	xr, yr = resolution(scene)
	
	params = ParamSet()
	
	# Set resolution
	params.add_integer('xresolution', int(xr))
	params.add_integer('yresolution', int(yr))
	
	# ColourSpace
	cso = scene.camera.data.luxrender_colorspace
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
	if cso.use_crf:
		params.add_string('cameraresponse', efutil.path_relative_to_export(cso.crf_file) )
	
	# Output types
	params.add_string('filename', efutil.path_relative_to_export(efutil.export_path))
	params.add_bool('write_resume_flm', scene.camera.data.luxrender_camera.write_flm)
	
	if scene.luxrender_engine.export_type == 'INT':
		# EXR is used to bring the image back into blender
		write_exr = True
		params.add_bool('write_exr_channels', 'RGBA')
		params.add_bool('write_exr_halftype', False)
		params.add_bool('write_exr_applyimaging', True)
		params.add_bool('write_exr_ZBuf', True)
		params.add_float('gamma', 1.0) # Linear workflow !
	else:
		write_exr = scene.camera.data.luxrender_camera.write_exr
	
	params.add_bool('write_exr', write_exr)
	params.add_bool('write_png', scene.camera.data.luxrender_camera.write_png)
	params.add_bool('write_tga', scene.camera.data.luxrender_camera.write_tga)
	
	
	params.add_integer('displayinterval', scene.luxrender_engine.displayinterval)
	params.add_integer('writeinterval', scene.luxrender_engine.writeinterval)
	
	# Halt conditions
	if scene.luxrender_sampler.haltspp > 0:
		params.add_integer('haltspp', scene.luxrender_sampler.haltspp)
	
	# update the film settings with tonemapper settings
	tonemapping_type, tonemapping_params = scene.camera.data.luxrender_tonemapping.api_output(scene)
	params.update(tonemapping_params)
	
	return ('fleximage', params)

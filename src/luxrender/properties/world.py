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

from extensions_framework import declarative_property_group
from extensions_framework.validate import Logic_OR as O, Logic_AND as A

from .. import LuxRenderAddon
from ..export import ParamSet
from ..outputs.pure_api import LUXRENDER_VERSION
from ..properties.material import texture_append_visibility
from ..properties.texture import (
	ColorTextureParameter, FloatTextureParameter, FresnelTextureParameter
)
from ..util import dict_merge

def WorldVolumeParameter(attr, name):
	return [
		{
			'attr': '%s_volume' % attr,
			'type': 'string',
			'name': '%s_volume' % attr,
			'description': '%s_volume' % attr,
			'save_in_preset': True
		},
		{
			'type': 'prop_search',
			'attr': attr,
			'src': lambda s,c: s.scene.luxrender_volumes,
			'src_attr': 'volumes',
			'trg': lambda s,c: c.luxrender_world,
			'trg_attr': '%s_volume' % attr,
			'name': name
		},
	]

@LuxRenderAddon.addon_register_class
class luxrender_world(declarative_property_group):
	ef_attach_to = ['Scene']
	
	controls = [
		'default_interior',
		'default_exterior'
	]
	
	properties = [] + \
		WorldVolumeParameter('default_interior', 'Default Interior') + \
		WorldVolumeParameter('default_exterior', 'Default Exterior')

class VolumeDataColorTextureParameter(ColorTextureParameter):
	#texture_collection = 'textures'
	def texture_collection_finder(self):
		def func(s,c):
			return s.world	# Look in the current world object for fresnel textures
		return func
	
	def texture_slot_set_attr(self):
		def func2(s,c):
			return c
		return func2

class VolumeDataFloatTextureParameter(FloatTextureParameter):
	#texture_collection = 'textures'
	def texture_collection_finder(self):
		def func(s,c):
			return s.world	# Look in the current world object for fresnel textures
		return func
	
	def texture_slot_set_attr(self):
		def func2(s,c):
			return c
		return func2

class VolumeDataFresnelTextureParameter(FresnelTextureParameter):
	#texture_collection = 'textures'
	def texture_collection_finder(self):
		def func(s,c):
			return s.world	# Look in the current world object for fresnel textures
		return func
	
	def texture_slot_set_attr(self):
		def func2(s,c):
			return c
		return func2

# Volume related Textures
TFR_IOR			= VolumeDataFresnelTextureParameter('fresnel', 'IOR',			add_float_value = True, min=0.0, max=25.0, default=1.0)

TC_absorption	= VolumeDataColorTextureParameter('absorption', 'Absorption',	default=(1.0,1.0,1.0))
TC_sigma_a		= VolumeDataColorTextureParameter('sigma_a', 'Absorption',		default=(1.0,1.0,1.0))
TC_sigma_s		= VolumeDataColorTextureParameter('sigma_s', 'Scattering',		default=(0.0,0.0,0.0))

def volume_types():
	v_types =  [
		('clear', 'Clear', 'clear')
	]
	
	if LUXRENDER_VERSION >= '0.8':
		v_types.extend([
			('homogeneous', 'Homogeneous', 'homogeneous')
		])
	
	return v_types

@LuxRenderAddon.addon_register_class
class luxrender_volume_data(declarative_property_group):
	'''
	Storage class for LuxRender volume data. The
	luxrender_volumes object will store 1 or more of
	these in its CollectionProperty 'volumes'.
	'''
	
	ef_attach_to = []	# not attached
	
	controls = [
		'type',
	] + \
	[
		'draw_ior_menu',
	] + \
	TFR_IOR.controls + \
	TC_absorption.controls + \
	TC_sigma_a.controls + \
	[
		'depth','absorption_scale'
	] + \
	TC_sigma_s.controls + \
	[
		'scattering_scale',
		'g',
	]
	
	visibility = dict_merge(
		{
			'scattering_scale': { 'type': 'homogeneous', 'sigma_s_usecolortexture': False },
			'g': { 'type': 'homogeneous' },
			'depth': O([ A([{ 'type': 'clear' }, { 'absorption_usecolortexture': False }]), A([{'type': 'homogeneous' }, { 'sigma_a_usecolortexture': False }]) ])
		},
		TFR_IOR.visibility,
		TC_absorption.visibility,
		TC_sigma_a.visibility,
		TC_sigma_s.visibility
	)
	
	visibility = texture_append_visibility(visibility, TC_absorption, { 'type': 'clear' })
	visibility = texture_append_visibility(visibility, TC_sigma_a, { 'type': 'homogeneous' })
	visibility = texture_append_visibility(visibility, TC_sigma_s, { 'type': 'homogeneous' })
	
	properties = [
		{
			'type': 'ef_callback',
			'attr': 'draw_ior_menu',
			'method': 'draw_ior_menu',
		},
		{
			'type': 'enum',
			'attr': 'type',
			'name': 'Type',
			'items': volume_types(),
			'save_in_preset': True
		},
	] + \
	TFR_IOR.properties + \
	TC_absorption.properties + \
	TC_sigma_a.properties + \
	TC_sigma_s.properties + \
	[
		{
			'type': 'float',
			'attr': 'depth',
			'name': 'Abs. at depth',
			'description': 'Object will match absorption color at this depth in metres',
			'default': 1.0,
			'min': 0.00001,
			'soft_min': 0.00001,
			'max': 1000.0,
			'soft_max': 1000.0,
			'precision': 6,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'absorption_scale',
			'name': 'Abs. scale',
			'description': 'Scale the absorption by this value',
			'default': 1.0,
			'min': 0.00001,
			'soft_min': 0.00001,
			'max': 1000.0,
			'soft_max': 1000.0,
			'precision': 6,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'scattering_scale',
			'name': 'Scattering scale factor',
			'description': 'Scattering colour will be multiplied by this value',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10000.0,
			'soft_max': 10000.0,
			'precision': 6,
			'save_in_preset': True
		},
		{
			'type': 'float_vector',
			'attr': 'g',
			'name': 'Asymmetry',
			'description': 'Scattering asymmetry RGB. -1 means backscatter, 0 is isotropic, 1 is forwards scattering.',
			'default': (0.0, 0.0, 0.0),
			'min': -1.0,
			'soft_min': -1.0,
			'max': 1.0,
			'soft_max': 1.0,
			'precision': 4,
			'save_in_preset': True
		},
	]
	
	def api_output(self, lux_context):
		vp = ParamSet()
		
		def absorption_at_depth_scaled(i):
			# This is copied from the old LuxBlend, I don't pretend to understand it, DH
			depthed = (-math.log(max([(float(i)),1e-30]))/(self.depth*self.absorption_scale)) * ((float(i))==1.0 and -1 or 1)
			#print('abs xform: %f -> %f' % (i,depthed))
			return depthed
		
		if self.type == 'clear':
			vp.update( TFR_IOR.get_paramset(self) )
			vp.update( TC_absorption.get_paramset(self, value_transform_function=absorption_at_depth_scaled) )
		
		if self.type == 'homogeneous':
			def scattering_scale(i):
				return i * self.scattering_scale
			vp.update( TFR_IOR.get_paramset(self) )
			vp.add_color('g', self.g)
			vp.update( TC_sigma_a.get_paramset(self, value_transform_function=absorption_at_depth_scaled) )
			vp.update( TC_sigma_s.get_paramset(self, value_transform_function=scattering_scale) )
		
		return self.type, vp

@LuxRenderAddon.addon_register_class
class luxrender_volumes(declarative_property_group):
	'''
	Storage class for LuxRender Material volumes.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		'volumes_select',
		['op_vol_add', 'op_vol_rem']
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'collection',
			'ptype': luxrender_volume_data,
			'name': 'volumes',
			'attr': 'volumes',
			'items': [
				
			]
		},
		{
			'type': 'int',
			'name': 'volumes_index',
			'attr': 'volumes_index',
		},
		{
			'type': 'template_list',
			'name': 'volumes_select',
			'attr': 'volumes_select',
			'trg': lambda sc,c: c.luxrender_volumes,
			'trg_attr': 'volumes_index',
			'src': lambda sc,c: c.luxrender_volumes,
			'src_attr': 'volumes',
		},
		{
			'type': 'operator',
			'attr': 'op_vol_add',
			'operator': 'luxrender.volume_add',
			'text': 'Add',
			'icon': 'ZOOMIN',
		},
		{
			'type': 'operator',
			'attr': 'op_vol_rem',
			'operator': 'luxrender.volume_remove',
			'text': 'Remove',
			'icon': 'ZOOMOUT',
		},
	]

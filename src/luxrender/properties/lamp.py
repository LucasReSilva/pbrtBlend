# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Daniel Genrich
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

from extensions_framework import declarative_property_group
import extensions_framework.util as efutil
from extensions_framework.validate import Logic_Operator as LO

from .. import LuxRenderAddon
from ..export import ParamSet
from ..properties.texture import ColorTextureParameter
from ..util import dict_merge

def LampVolumeParameter(attr, name):
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
			'trg': lambda s,c: c.luxrender_lamp,
			'trg_attr': '%s_volume' % attr,
			'name': name
		},
	]

def LampLightGroupParameter():
	return [
		{
			'attr': 'lightgroup',
			'type': 'string',
			'name': 'lightgroup',
			'description': 'lightgroup; leave blank to use default',
			'save_in_preset': True
		},
		{
			'type': 'prop_search',
			'attr': 'lightgroup_chooser',
			'src': lambda s,c: s.scene.luxrender_lightgroups,
			'src_attr': 'lightgroups',
			'trg': lambda s,c: c.luxrender_lamp,
			'trg_attr': 'lightgroup',
			'name': 'Light Group'
		},
	]

class LampColorTextureParameter(ColorTextureParameter):
	def texture_slot_set_attr(self):
		return lambda s,c: getattr(c, 'luxrender_lamp_%s'%s.lamp.type.lower())
	
	def texture_collection_finder(self):
		return lambda s,c: s.object.data
	
	def get_visibility(self):
		vis = {
			'%s_colortexture' % self.attr:	{ '%s_usecolortexture' % self.attr: True },
			'%s_multiplycolor' % self.attr:	{ '%s_usecolortexture' % self.attr: True },
		}
		return vis

TC_L = LampColorTextureParameter('L', 'Colour')

@LuxRenderAddon.addon_register_class
class luxrender_lamp(declarative_property_group):
	'''
	Storage class for LuxRender Camera settings.
	'''
	
	ef_attach_to = ['Lamp']
	
	controls = [
		'importance',
		'lightgroup_chooser',
		'Exterior'
	]
	
	properties = [
		{
			'type': 'float',
			'attr': 'importance',
			'name': 'Importance',
			'description': 'Light source importance',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e3,
			'soft_max': 1e3,
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'iesname',
			'name': 'IES Data',
			'description': 'Use IES data for this light\'s distribution'
		},
	] + \
		LampVolumeParameter('Exterior', 'Exterior') + \
		LampLightGroupParameter()
	
	def get_paramset(self):
		params = ParamSet()
		params.add_float('importance', self.importance)
		return params

class luxrender_lamp_basic(declarative_property_group):
	controls = TC_L.controls
	visibility = TC_L.visibility
	properties = TC_L.properties
	
	def get_paramset(self, lamp_object):
		params = ParamSet()
		params.update( TC_L.get_paramset(self) )
		return params

@LuxRenderAddon.addon_register_class
class luxrender_lamp_point(luxrender_lamp_basic):
	ef_attach_to = ['luxrender_lamp']
	
	controls = TC_L.controls[:] + [
		'flipz',
		'power',
		'efficacy',
		'usesphere',
		'pointsize',
		'nsamples',
		'null_lamp',
	]
	
	visibility = dict_merge(
		luxrender_lamp_basic.visibility,
		{ 'pointsize':				{ 'usesphere': True} },
		{ 'nsamples':				{ 'usesphere': True} },
		{ 'null_lamp':				{ 'usesphere': True} },
		)
	
	properties = TC_L.properties[:] + [
		{
			'type': 'bool',
			'attr': 'flipz',
			'name': 'Flip Z ( IES correction )',
			'description': 'Flip Z direction in mapping',
			'default': True
		},
				{
			'type': 'float',
			'attr': 'power',
			'name': 'Power',
			'default': 0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		},
		{
			'type': 'float',
			'attr': 'efficacy',
			'name': 'Efficacy',
			'default': 0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		},
		{
			'type': 'bool',
			'attr': 'usesphere',
			'name': 'Use Sphere',
			'description': 'Use a spherical area light instead of a true point light. This is more realistic, but can deform IES profiles',
			'default': False,

		},	
		{
			'type': 'float',
			'attr': 'pointsize',
			'name': 'Radius',
			'default': 0.025, #2.5cm default, this is roughly the radius of a common light bulb.
			'description': 'Radius of the lamp sphere',
			'min': 0.000001, #1-micron minimum radius. This needs to be non-zero.
			'soft_min': 0.0000001,
			'sub_type': 'DISTANCE',
			'unit': 'LENGTH'
		},
		{
			'type': 'int',
			'attr': 'nsamples',
			'name': 'Shadow ray samples',
			'description': 'The suggested number of shadow samples',
			'default': 1 ,
			'min': 1 ,
			'soft_min': 1 ,
			'max': 100,
			'soft_max': 100,
		},
		{
			'type': 'bool',
			'attr': 'null_lamp',
			'name': 'Hide geometry',
			'description': 'Use a null material for lamp geometry (lamp will still be visible when viewed directly, as it emits its own light',
			'default': True,
		},	
	]

	def get_paramset(self, lamp_object):
		params = super().get_paramset(lamp_object)
		params.add_bool('flipz', self.flipz)
		params.add_float('power', self.power)
		params.add_float('efficacy', self.efficacy)
		return params

@LuxRenderAddon.addon_register_class
class luxrender_lamp_spot(luxrender_lamp_basic):
	ef_attach_to = ['luxrender_lamp']
	
	controls = luxrender_lamp_basic.controls[:] + [
		'projector',
		'mapname',
		'power',
		'efficacy'
	]
	visibility = dict_merge(
		luxrender_lamp_basic.visibility,
		{ 'mapname': { 'projector': True } },
	)
	properties = luxrender_lamp_basic.properties[:] + [
		{
			'type': 'bool',
			'attr': 'projector',
			'name': 'Projector',
			'default': False
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'mapname',
			'name': 'Projector image',
			'description': 'Image to project from this lamp',
			'default': ''
		},
		{
			'type': 'float',
			'attr': 'power',
			'name': 'Power',
			'default': 0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		},
		{
			'type': 'float',
			'attr': 'efficacy',
			'name': 'Efficacy',
			'default': 0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		}
	]
	def get_paramset(self, lamp_object):
		params = super().get_paramset(lamp_object)
		params.add_float('power', self.power)
		params.add_float('efficacy', self.efficacy)
		if self.projector:
			params.add_string('mapname', self.mapname)
		return params

@LuxRenderAddon.addon_register_class
class luxrender_lamp_sun(declarative_property_group):
	ef_attach_to = ['luxrender_lamp']
	
	controls = [
		'sunsky_type',
		'nsamples',
		'turbidity',
		'sunsky_advanced',
		'relsize',
		'horizonbrightness',
		'horizonsize',
		'sunhalobrightness',
		'sunhalosize',
		'backscattering',
	]
	
	visibility = {
		'relsize':				{ 'sunsky_advanced': True, 'sunsky_type': LO({'!=':'sky'}) },
		'horizonbrightness':	{ 'sunsky_advanced': True, 'sunsky_type': LO({'!=':'sun'}) },
		'horizonsize':			{ 'sunsky_advanced': True, 'sunsky_type': LO({'!=':'sun'}) },
		'sunhalobrightness':	{ 'sunsky_advanced': True, 'sunsky_type': LO({'!=':'sun'}) },
		'sunhalosize':			{ 'sunsky_advanced': True, 'sunsky_type': LO({'!=':'sun'}) },
		'backscattering':		{ 'sunsky_advanced': True, 'sunsky_type': LO({'!=':'sun'}) },
	}
	
	properties = [
		{
			'type': 'float',
			'attr': 'turbidity',
			'name': 'turbidity',
			'default': 2.2,
			'min': 1.2,
			'soft_min': 1.2,
			'max': 30.0,
			'soft_max': 30.0,
		},
		{
			'type': 'enum',
			'attr': 'sunsky_type',
			'name': 'Sky Type',
			'default': 'sunsky',
			'items': [
				('sunsky', 'Sun & Sky', 'sunsky'),
				('sun', 'Sun Only', 'sun'),
				('sky', 'Sky Only', 'sky'),
			]
		},
		{
			'type': 'bool',
			'attr': 'sunsky_advanced',
			'name': 'Advanced',
			'default': False
		},
		{
			'type': 'float',
			'attr': 'relsize',
			'name': 'Relative sun disk size',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 100.0,
			'soft_max': 100.0
		},
		{
			'type': 'float',
			'attr': 'horizonbrightness',
			'name': 'Horizon brightness',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.32,		# anything greater than this causes sky to break
			'soft_max': 1.32
		},
		{
			'type': 'float',
			'attr': 'horizonsize',
			'name': 'Horizon size',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'type': 'float',
			'attr': 'sunhalobrightness',
			'name': 'Sun halo brightness',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'type': 'float',
			'attr': 'sunhalosize',
			'name': 'Sun halo size',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'type': 'float',
			'attr': 'backscattering',
			'name': 'Back scattering',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 10.0,
			'soft_max': 10.0
		},
		{
			'type': 'int',
			'attr': 'nsamples',
			'name': 'Shadow ray samples',
			'description': 'The suggested number of shadow samples',
			'default': 1 ,
			'min': 1 ,
			'soft_min': 1 ,
			'max': 100,
			'soft_max': 100,
		},
	]
	
	def get_paramset(self, lamp_object):
		params = ParamSet()
		
		params.add_float('turbidity', self.turbidity)
		params.add_integer('nsamples', self.nsamples)
		
		if self.sunsky_advanced and self.sunsky_type != 'sky':
			params.add_float('relsize', self.relsize)
		
		if self.sunsky_advanced and self.sunsky_type != 'sun':
			params.add_float('horizonbrightness', self.horizonbrightness)
			params.add_float('horizonsize', self.horizonsize)
			params.add_float('sunhalobrightness', self.sunhalobrightness)
			params.add_float('sunhalosize', self.sunhalosize)
			params.add_float('backscattering', self.backscattering)
		
		return params

@LuxRenderAddon.addon_register_class
class luxrender_lamp_area(declarative_property_group):
	ef_attach_to = ['luxrender_lamp']
	
	controls = TC_L.controls[:] + [
		'nsamples',
		'power',
		'efficacy',
		'null_lamp',
	]
	
	visibility = TC_L.visibility
	
	properties = TC_L.properties[:] + [
		{
			'type': 'float',
			'attr': 'power',
			'name': 'Power',
			'default': 100.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		},
		{
			'type': 'float',
			'attr': 'efficacy',
			'name': 'Efficacy',
			'default': 17.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e6,
			'soft_max': 1e6,
		},
		{
			'type': 'int',
			'attr': 'nsamples',
			'name': 'Shadow ray samples',
			'description': 'The suggested number of shadow samples',
			'default': 1 ,
			'min': 1 ,
			'soft_min': 1 ,
			'max': 100,
			'soft_max': 100,
		},
		{
			'type': 'bool',
			'attr': 'null_lamp',
			'name': 'Hide geometry',
			'description': 'Use a null material for lamp geometry (lamp will still be visible when viewed on emitting side, as it emits its own light',
			'default': True,
		},
	]
	
	def get_paramset(self, lamp_object):
		params = ParamSet()
		params.add_float('power', self.power)
		params.add_float('efficacy', self.efficacy)
		params.update( TC_L.get_paramset(self) )
		params.add_integer('nsamples', self.nsamples)
		return params

@LuxRenderAddon.addon_register_class
class luxrender_lamp_hemi(declarative_property_group):
	ef_attach_to = ['luxrender_lamp']
	
	controls = [
		'type',
		'infinite_map',
		'mapping_type',
		'nsamples',
		'gamma',
		[0.323, 'L_colorlabel', 'L_color'],
		'hdri_multiply'
	]
	
	visibility = {
		'infinite_map':		{ 'type': 'infinite' },
		'mapping_type':		{ 'type': 'infinite', 'infinite_map': LO({'!=': ''}) },
		'hdri_multiply':	{ 'type': 'infinite', 'infinite_map': LO({'!=': ''}) },
		'gamma':			{ 'type': 'infinite', 'infinite_map': LO({'!=': ''}) },
		'nsamples':			{ 'type': 'infinite', 'infinite_map': LO({'!=': ''}) },
	}
	
	properties = TC_L.properties[:] + [
		{
			'type': 'enum',
			'attr': 'type',
			'name': 'Type',
			'items': [
				('infinite', 'Infinite', 'infinite'),
				('distant', 'Distant', 'distant'),
			],
			'expand': True
		},
		{
			'type': 'bool',
			'attr': 'hdri_multiply',
			'name': 'Multiply by colour',
			'description': 'Mutiply the HDRI map by the lamp colour',
			'default': False
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'infinite_map',
			'name': 'HDRI Map',
			'description': 'HDR image to use for lighting',
			'default': ''
		},
		{
			'type': 'enum',
			'attr': 'mapping_type',
			'name': 'Map Type',
			'default': 'latlong',
			'items': [
				('latlong', 'Lat Long', 'latlong'),
				('angular', 'Angular', 'angular'),
				('vcross', 'Vert Cross', 'vcross')
			]
		},
		{
			'type': 'float',
			'attr': 'gamma',
			'name': 'Gamma',
			'description': 'Light source gamma',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 6,
			'soft_max': 6,
		},
		{
			'type': 'int',
			'attr': 'nsamples',
			'name': 'Shadow ray samples',
			'description': 'The suggested number of shadow samples',
			'default': 1 ,
			'min': 1 ,
			'soft_min': 1 ,
			'max': 100,
			'soft_max': 100,
		},
	]
	
	def get_paramset(self, lamp_object):
		params = ParamSet()
		
		if self.type == 'infinite':
			if self.infinite_map != '':
				if lamp_object.library is not None:
					hdri_path = bpy.path.abspath(self.infinite_map, lamp_object.library.filepath)
				else:
					hdri_path = self.infinite_map
				params.add_string('mapname', efutil.path_relative_to_export(hdri_path) )
				params.add_string('mapping', self.mapping_type)
				params.add_float('gamma', self.gamma)
				params.add_integer('nsamples', self.nsamples)
				
			if self.infinite_map == '' or self.hdri_multiply:
				params.add_color('L', self.L_color)
		else:
			params.add_color('L', self.L_color)
		
		return params

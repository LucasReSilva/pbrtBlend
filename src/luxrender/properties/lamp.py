# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
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

from ef.ef import declarative_property_group
from ef.validate import Logic_Operator as LO

from luxrender.properties import dbo
from luxrender.export import ParamSet

from luxrender.properties.texture import ColorTextureParameter

class LampColorTextureParameter(ColorTextureParameter):
	def texture_slot_set_attr(self):
		return lambda s,c: getattr(c, 'luxrender_lamp')
	
	def texture_collection_finder(self):
		return lambda s,c: s.object.data
	
	def get_visibility(self):
		vis = {
			'%s_colortexture' % self.attr:	{ '%s_usecolortexture' % self.attr: True },
		}
		return vis

TC_L = LampColorTextureParameter('L', 'Colour')

def lamp_visibility():
	vis = {
		'power':				{ 'type': 'AREA'},
		'efficacy':				{ 'type': 'AREA'},
		
		'turbidity':			{ 'type': 'SUN' },
		'sunsky_type':			{ 'type': 'SUN' },
		
		'infinite_map':			{ 'type': 'HEMI' },
		'mapping_type':			{ 'type': 'HEMI', 'infinite_map': LO({'!=': ''}) },
		
		'L_color':				{ 'type': LO({'!=': 'SUN'}) },
		'L_usecolortexture':	{ 'type': LO({'!=': 'SUN'}) },
		'L_colortexture':		{ 'type': LO({'!=': 'SUN'}), 'L_usecolortexture': True }
	}
	
	# Add TC_L manually, because we need to exclude it from SUN
	#vis.update(TC_L.get_visibility())
	
	return vis

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API
class luxrender_lamp(declarative_property_group):
	'''
	Storage class for LuxRender Camera settings.
	This class will be instantiated within a Blender
	lamp object.
	'''
	
	controls = TC_L.get_controls() + [
		'importance', 'lightgroup',
		['power','efficacy'],
		'turbidity', 'sunsky_type',
		'infinite_map',
		'mapping_type',
	]
	
	visibility = lamp_visibility()
	
	properties = TC_L.get_properties() + [
		{
			# hidden value for visibility control
			'type': 'string',
			'attr': 'type',
			'default': 'UNSUPPORTED',
		},
		{
			'type': 'string',
			'attr': 'lightgroup',
			'name': 'Light Group',
			'description': 'Name of group to put this light in',
			'default': 'default'
		},
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
			'type': 'float',
			'attr': 'importance',
			'name': 'Importance',
			'description': 'Light source importance',
			'default': 0.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e3,
			'soft_max': 1e3,
		},
		
		# Sun
		{
			'type': 'float',
			'attr': 'turbidity',
			'name': 'turbidity',
			'default': 2.2,
			'min': 0.7,
			'soft_min': 0.7,
			'max': 50.0,
			'soft_max': 50.0,
		},
		{
			'type': 'enum',
			'attr': 'sunsky_type',
			'name': 'Sky Type',
			'default': 'sunsky',
			'items': [
				('sunsky', 'Sun & Sky', 'sunsky'),
				('sun', 'Sun Only', 'sun'),
				#('sky', 'Sky Only', 'sky'),	# sky only doesn't work
			]
		},
		
		# HEMI / INFINITE
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
	]

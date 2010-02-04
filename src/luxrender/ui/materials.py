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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
from ef.ui import context_panel
from ef.ui import material_settings_panel
from ef.ui import described_layout

from ef.ef import ef

import properties



class material_editor(context_panel, material_settings_panel, described_layout):
	bl_label = 'LuxRender Materials'
	context_name = 'luxrender'
	
	property_group = properties.luxrender_material
	
	controls = [
		# Common props
		'material',
		
		# Used by many
		'kd',
		'kr',
		'kt',
		
		[0.33, 'ior_preset', ['ior_list', 'ior']],
		
		# Car paint
		'carpaint_label',
		'carpaint_preset',
		
		['carpaint_ks1', 'carpaint_ks2', 'carpaint_ks3'],
        'carpaint_r',
		#['carpaint_r1','carpaint_r2','carpaint_r3'],
        'carpaint_m',
		#['carpaint_m1','carpaint_m2','carpaint_m3'],
		
		# Glass
		
	]
	
	selection = {
		# Used by many
		'kd':					[{ 'material': 'carpaint' }],
		'kr':					[{ 'material': 'glass' }],
		'kt':					[{ 'material': 'glass' }],
		'ior_preset':			[{ 'material': 'glass' }],
		'ior_list':				[{ 'material': 'glass' }, { 'ior_preset': True }],
		'ior':					[{ 'material': 'glass' }, { 'ior_preset': False }],
	
		# Car paint
		'carpaint_label':		[{ 'material': 'carpaint' }],
		'carpaint_preset':		[{ 'material': 'carpaint' }],
		# Car paint custom
		'carpaint_kd':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
		'carpaint_ks1':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
		'carpaint_ks2':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
		'carpaint_ks3':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
		
        'carpaint_r':           [{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#       'carpaint_r1':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_r2':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_r3':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
        
        'carpaint_m':           [{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_m1':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_m2':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_m3':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
		
		# Glass
		
	}
	
	properties = [
		# Material Type Select
		{
			'type': 'enum',
			'attr': 'material',
			'name': 'Type',
			'description': 'LuxRender material type',
			'items': [
				('carpaint', 'Car Paint', 'carpaint'),
				('glass', 'Glass', 'glass'),
				('roughglass','Rough Glass','roughglass'),
				('glossy','Glossy','glossy'),
				('matte','Matte','matte'),
				('mattetranslucent','Matte Translucent','mattetranslucent'),
				('metal','Metal','metal'),
				('shinymetal','Shiny Metal','shinymetal'),
				('mirror','Mirror','mirror'),
				('mix','Mix','mix'),
				('null','Null','null'),
				('boundvolume','Bound Volume','boundvolume'),
				('light','Light','light'),
				('portal','Portal','portal'),
			]
		},
		
		# Used by many mats
		{
			'type': 'float_vector',
			'attr': 'kd',
			'name': 'Diffuse Colour',
			'description': 'Diffuse Colour',
			'size': 3,
            'default': (0.8, 0.8, 0.8),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3,
            'subtype': 'COLOR'
		},
		{
			'type': 'float_vector',
			'attr': 'kr',
			'name': 'Reflection Colour',
			'description': 'Reflection Colour',
			'size': 3,
            'default': (0.8, 0.8, 0.8),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3,
            'subtype': 'COLOR'
		},
		{
			'type': 'float_vector',
			'attr': 'kt',
			'name': 'Transmission Colour',
			'description': 'Transmission Colour',
			'size': 3,
            'default': (0.8, 0.8, 0.8),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3,
            'subtype': 'COLOR'
		},
		{
			'type': 'bool',
			'attr': 'ior_preset',
			'name': 'IOR Preset',
			'description': 'IOR Preset',
			'default': True,
		},
		{
			'type': 'enum',
			'attr': 'ior_list',
			'name': '',
			'description': 'IOR Preset',
			'default': '1.5',
			'items': [
				('-1', 'IOR Preset', 'IOR Preset'),
				('1.5', 'Fused Silica Glass', 'Fused Silica Glass'),
				('0', '-- TODO --', '0'),
			]
		},
		{
			'type': 'float',
			'attr': 'ior',
			'name': '',
			'description': 'IOR',
			'default': 1,
			'min': 0,
			'soft_min': 0,
			'max': 10,
			'soft_max': 10,
		},
		
		
		# Car paint
		{
			'type': 'text',
			'attr': 'carpaint_label',
			'name': 'Car Paint Settings',
		},
		{
			'type': 'enum',
			'attr': 'carpaint_preset',
			'name': 'Preset',
			'description': 'Preset Car Paint Settings',
			'default': 'custom',
			'items': [
				('custom','Custom','custom'),
				('fordf8','Ford F8','fordf8'),
				('polaris','Polaris Silver','polaris'),
				('opel','Opel Titan','opel'),
				('bmw339','BMW 339','bmw339'),
				('2k','2K Acrylic','2k'),
				('white','White','white'),
				('blue','Blue','blue'),
				('bluematte','Blue Matte','bluematte'),
			]
		},
		{
			'type': 'float_vector',
			'attr': 'carpaint_ks1',
			'name': 'Specular Layer 1',
			'description': 'Specular Layer 1 Colour',
			'size': 3,
            'default': (0.8, 0.8, 0.8),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3,
            'subtype': 'COLOR'
		},
		{
			'type': 'float_vector',
			'attr': 'carpaint_ks2',
			'name': 'Specular Layer 2',
			'description': 'Specular Layer 2 Colour',
			'size': 3,
            'default': (0.8, 0.8, 0.8),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3,
            'subtype': 'COLOR'
		},
		{
			'type': 'float_vector',
			'attr': 'carpaint_ks3',
			'name': 'Specular Layer 3',
			'description': 'Specular Layer 3 Colour',
			'size': 3,
            'default': (0.8, 0.8, 0.8),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3,
            'subtype': 'COLOR'
		},
        
#		{
#			'type': 'float',
#			'attr': 'carpaint_r1',
#			'name': 'R 1',
#			'description': 'Specular Layer 1 Roughness',
#			'default': 1,
#			'min': 0,
#			'soft_min': 0,
#			'max': 1,
#			'soft_max': 1,
#		},
#		{
#			'type': 'float',
#			'attr': 'carpaint_r2',
#			'name': 'R 2',
#			'description': 'Specular Layer 2 Roughness',
#			'default': 1,
#			'min': 0,
#			'soft_min': 0,
#			'max': 1,
#			'soft_max': 1,
#		},
#		{
#			'type': 'float',
#			'attr': 'carpaint_r3',
#			'name': 'R 3',
#			'description': 'Specular Layer 3 Roughness',
#			'default': 1,
#			'min': 0,
#			'soft_min': 0,
#			'max': 1,
#			'soft_max': 1,
#		},
        {
            'type': 'float_vector',
            'attr': 'carpaint_r',
            'name': 'R',
            'description': 'Specular Layer Roughness',
            'size': 3,
            'default': (1.0, 1.0, 1.0),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3
        },
#		{
#			'type': 'float',
#			'attr': 'carpaint_m1',
#			'name': 'M 1',
#			'description': 'Specular Layer 1 Fresnel',
#			'default': 1,
#			'min': 0,
#			'soft_min': 0,
#			'max': 1,
#			'soft_max': 1,
#		},
#		{
#			'type': 'float',
#			'attr': 'carpaint_m2',
#			'name': 'M 2',
#			'description': 'Specular Layer 2 Fresnel',
#			'default': 1,
#			'min': 0,
#			'soft_min': 0,
#			'max': 1,
#			'soft_max': 1,
#		},
#		{
#			'type': 'float',
#			'attr': 'carpaint_m3',
#			'name': 'M 3',
#			'description': 'Specular Layer 3 Fresnel',
#			'default': 1,
#			'min': 0,
#			'soft_min': 0,
#			'max': 1,
#			'soft_max': 1,
#		},
        {
            'type': 'float_vector',
            'attr': 'carpaint_m',
            'name': 'M',
            'description': 'Specular Layer Fresnel',
            'size': 3,
            'default': (1.0, 1.0, 1.0),
            'step': 0.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 1.0,
            'soft_max': 1.0,
            'precision': 3
        },
		
		# Glass
		
	]
	
	# Overridden to provide data storage in the material, not the scene
	def draw(self, context):
		if context.material is not None:
			if not hasattr(context.material, 'luxrender_material'):
				#ef.ef.ef.log('Initialising Indigo properties in material %s'%context.material.name)
				ef.init_properties(context.material, [{
					'type': 'pointer',
					'attr': self.property_group.__name__,
					'ptype': self.property_group,
					'name': self.property_group.__name__,
					'description': self.property_group.__name__
				}])
				ef.init_properties(self.property_group, self.properties)
			
			for p in self.controls:
				self.draw_column(p, self.layout, context.material)

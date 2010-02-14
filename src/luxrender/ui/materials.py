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
# Blender API
import bpy
from properties_material import MaterialButtonsPanel

# EF API
from ef.ui import described_layout
from ef.ef import ef

# Lux API
import luxrender.properties

class material_editor(MaterialButtonsPanel, described_layout):
	bl_label = 'LuxRender Materials'
	COMPAT_ENGINES = {'luxrender'}
	
	
	property_group = luxrender.properties.luxrender_material
	# prevent creating luxrender_material property group in Scene
	property_group_non_global = True
	
	
	@staticmethod
	def property_reload():
		for mat in bpy.data.materials:
			material_editor.property_create(mat)
	
	@staticmethod
	def property_create(mat):
		if not hasattr(mat, material_editor.property_group.__name__):
			#ef.log('Initialising properties in material %s'%context.material.name)
			ef.init_properties(mat, [{
				'type': 'pointer',
				'attr': material_editor.property_group.__name__,
				'ptype': material_editor.property_group,
				'name': material_editor.property_group.__name__,
				'description': material_editor.property_group.__name__
			}], cache=False)
			ef.init_properties(material_editor.property_group, material_editor.properties, cache=False)
	
	# Overridden to provide data storage in the material, not the scene
	def draw(self, context):
		if context.material is not None:
			material_editor.property_create(context.material)
			
			for p in self.controls:
				self.draw_column(p, self.layout, context.material, supercontext=context)
	
	controls = [
		# Common props
		'material',
		
		# type-specific presets here
#		'carpaint_preset',
		
		
		# Standard channels used by many
#		'kd',
#		'kr',
#		'kt',
		
		# Other standard parameters
#		[0.33, 'ior_preset', ['ior_list', 'ior']],
		
		
		# Material specific parameters
		
		## Car paint
#		'carpaint_ks1', 'carpaint_ks2', 'carpaint_ks3',
#		'carpaint_r', 'carpaint_m',
		
		# Glass
		
	]
	
	selection = {
		# Used by many
		
		# TODO: selection mechanism is inadequate; cannot correctly switch kd visibility.
#		'kd':					[{ 'material': ['carpaint','matte'] }],
#		'kr':					[{ 'material': 'glass' }],
#		'kt':					[{ 'material': 'glass' }],
#		'ior_preset':			[{ 'material': 'glass' }],
#		'ior_list':				[{ 'material': 'glass' }, { 'ior_preset': True }],
#		'ior':					[{ 'material': 'glass' }, { 'ior_preset': False }],
	
		# Car paint
#		'carpaint_label':		[{ 'material': 'carpaint' }],
#		'carpaint_preset':		[{ 'material': 'carpaint' }],
		
		# Car paint custom
#		'carpaint_ks1':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_ks2':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_ks3':			[{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_r':		   [{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],
#		'carpaint_m':		   [{ 'material': 'carpaint' }, { 'carpaint_preset': 'custom' }],

		
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
		
#		texture.Texture(
#			'kd',
#			name = 'Diffuse Colour',
#			description = 'Diffuse Colour',
#		),
#		texture.Texture(
#			'kr',
#			name = 'Reflection Colour',
#			description = 'Reflection Colour',
#		),
#		texture.Texture(
#			'kt',
#			name = 'Transmission Colour',
#			description = 'Transmission Colour',
#		),
		
		
#		{
#			'type': 'bool',
#			'attr': 'ior_preset',
#			'name': 'IOR Preset',
#			'description': 'IOR Preset',
#			'default': True,
#		},
#		{
#			'type': 'enum',
#			'attr': 'ior_list',
#			'name': '',
#			'description': 'IOR Preset',
#			'default': '1.5',
#			'items': [
#				('-1', 'IOR Preset', 'IOR Preset'),
#				('1.5', 'Fused Silica Glass', 'Fused Silica Glass'),
#				('0', '-- TODO --', '0'),
#			]
#		},
#		{
#			'type': 'float',
#			'attr': 'ior',
#			'name': '',
#			'description': 'IOR',
#			'default': 1,
#			'min': 0,
#			'soft_min': 0,
#			'max': 10,
#			'soft_max': 10,
#		},
		
		
		# Car paint
#		{
#			'type': 'enum',
#			'attr': 'carpaint_preset',
#			'name': 'Preset',
#			'description': 'Preset Car Paint Settings',
#			'default': 'custom',
#			'items': [
#				('custom','Custom','custom'),
#				('fordf8','Ford F8','fordf8'),
#				('polaris','Polaris Silver','polaris'),
#				('opel','Opel Titan','opel'),
#				('bmw339','BMW 339','bmw339'),
#				('2k','2K Acrylic','2k'),
#				('white','White','white'),
#				('blue','Blue','blue'),
#				('bluematte','Blue Matte','bluematte'),
#			]
#		},
		
#		texture.Texture(
#			'carpaint_ks1',
#			name = 'Specular Layer 1',
#			description = 'Specular Layer 1 Colour',
#		),
#		texture.Texture(
#			'carpaint_ks2',
#			name = 'Specular Layer 2',
#			description = 'Specular Layer 2 Colour',
#		),
#		texture.Texture(
#			'carpaint_ks3',
#			name = 'Specular Layer 3',
#			description = 'Specular Layer 3 Colour',
#		),
		
#		{
#			'type': 'float_vector',
#			'attr': 'carpaint_r',
#			'name': 'Layer Roughnesses',
#			'description': 'Specular Layer Roughness',
#			'size': 3,
#			'default': (1.0, 1.0, 1.0),
#			'step': 0.1,
#			'min': 0.0,
#			'soft_min': 0.0,
#			'max': 1.0,
#			'soft_max': 1.0,
#			'precision': 3
#		},
#		{
#			'type': 'float_vector',
#			'attr': 'carpaint_m',
#			'name': 'Layer Fresnels',
#			'description': 'Specular Layer Fresnel',
#			'size': 3,
#			'default': (1.0, 1.0, 1.0),
#			'step': 0.1,
#			'min': 0.0,
#			'soft_min': 0.0,
#			'max': 1.0,
#			'soft_max': 1.0,
#			'precision': 3
#		},
		
		# Glass
		
	]
	

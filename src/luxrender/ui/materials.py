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
from ef.validate import Logic_AND as A, Logic_OR as O, Logic_Operator as OP

# Lux API
import luxrender.properties.material
from luxrender.ui.textures import ParamTextureFloat, ParamTextureColor

def ParamMaterial(attr, name, property_group):
	return [
		{
			'attr': '%s_material' % attr,
			'type': 'string',
			'name': '%s_material' % attr,
			'description': '%s_material' % attr,
		},
		{
			'type': 'prop_object',
			'attr': attr,
			'src': lambda s,c: s.object,
			'src_attr': 'material_slots',
			'trg': lambda s,c: getattr(c, property_group),
			'trg_attr': '%s_material' % attr,
			'name': name
		},
	]

def has_property(property_name):
	'''
	Refer to http://www.luxrender.net/static/materials-parameters.xhtml
	for contents of this mapping
	'''
	
	map = {
		'amount':			O(['mix']),
		'architectural':	O(['glass', 'glass2']),
		'bumpmap':			O(['carpaint', 'glass', 'glass2', 'glossy_lossy', 'glossy', 'matte', 'mattetranslucent', 'metal', 'mirror', 'roughglass', 'shinymetal']),
		'cauchyb':			O(['glass', 'roughglass']),
		'd':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'dispersion':		O(['glass2']),
		'film':				O(['glass', 'mirror', 'shinymetal']),
		'filmindex':		O(['glass', 'mirror', 'shinymetal']),
		'index':			O(['glass', 'glossy_lossy', 'glossy', 'roughglass']),
		'Ka':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'Kd':				O(['carpaint', 'glossy_lossy', 'glossy', 'matte']),
		'Kr':				O(['glass', 'mattetranslucent', 'mirror', 'roughglass', 'shinymetal']),
		'Ks':				O(['glossy_lossy', 'glossy', 'shinymetal']),
		'Ks1':				O(['carpaint']),
		'Ks2':				O(['carpaint']),
		'Ks3':				O(['carpaint']),
		'Kt':				O(['glass', 'mattetranslucent', 'roughglass']),
		'M1':				O(['carpaint']),
		'M2':				O(['carpaint']),
		'M3':				O(['carpaint']),
		'name':				O(['carpaint', 'metal']),
		'namedmaterial1':	O(['mix']),
		'namedmaterial2':	O(['mix']),
		'R1':				O(['carpaint']),
		'R2':				O(['carpaint']),
		'R3':				O(['carpaint']),
		'sigma':			O(['matte', 'mattetranslucent']),
		'uroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
		'vroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
	}
	
	return map[property_name]

class material_editor(MaterialButtonsPanel, described_layout):
	'''
	Material Editor UI Panel
	'''
	
	bl_label = 'LuxRender Materials'
	COMPAT_ENGINES = {'luxrender'}
	
	
	property_group = luxrender.properties.material.luxrender_material
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
		
		# 'preset' options
		'name',
		
		# 'Matte' options
		'Kd',
		[0.9,'sigma_floatvalue','sigma_usetexture'],
		'sigma_texture',
		
		# 'Glossy' options
		'Ka',
		'Ks',
		[0.9, 'd_floatvalue', 'd_usetexture'],
		'd_texture',
		[0.9, 'uroughness_floatvalue', 'uroughness_usetexture'],
		'uroughness_texture',
		[0.9, 'vroughness_floatvalue', 'vroughness_usetexture'],
		'vroughness_texture',
		
		# 'Glassy' options
		'architectural',
		[0.9, 'index_floatvalue', 'index_usetexture'],
		'index_texture',
		[0.9, 'cauchyb_floatvalue', 'cauchyb_usetexture'],
		'cauchyb_texture',
		'Kr',
		'Kt',
		[0.9, 'film_floatvalue', 'film_usetexture'],
		'film_texture',
		[0.9, 'filmindex_floatvalue', 'filmindex_usetexture'],
		'filmindex_texture',
		'dispersion',
		
		# Carpaint options
		'Ks1', 'Ks2', 'Ks3',
		[0.9, 'M1_floatvalue', 'M1_usetexture'],
		'M1_texture',
		[0.9, 'M2_floatvalue', 'M2_usetexture'],
		'M2_texture',
		[0.9, 'M3_floatvalue', 'M3_usetexture'],
		'M3_texture',
		[0.9, 'R1_floatvalue', 'R1_usetexture'],
		'R1_texture',
		[0.9, 'R2_floatvalue', 'R2_usetexture'],
		'R2_texture',
		[0.9, 'R3_floatvalue', 'R3_usetexture'],
		'R3_texture',
		
		# Other options
		[0.9, 'bumpmap_floatvalue', 'bumpmap_usetexture'],
		'bumpmap_texture',
		
		# Mix Material
		[0.9, 'amount_floatvalue', 'amount_usetexture'],
		'amount_texture',
		'namedmaterial1',
		'namedmaterial2',
	]
	
	visibility = {
		'amount_usetexture':		{ 'material': has_property('amount') },
		'amount_floatvalue':		{ 'material': has_property('amount') },
		'amount_texture':			{ 'material': has_property('amount'), 'amount_usetexture': True },
		'architectural':			{ 'material': has_property('architectural') },
		'bumpmap_usetexture':		{ 'material': has_property('bumpmap') },
		'bumpmap_floatvalue':		{ 'material': has_property('bumpmap') },
		'bumpmap_texture':			{ 'material': has_property('bumpmap'), 'bumpmap_usetexture': True },
		'cauchyb_usetexture':		{ 'material': has_property('cauchyb') },
		'cauchyb_floatvalue':		{ 'material': has_property('cauchyb') },
		'cauchyb_texture':			{ 'material': has_property('cauchyb'), 'cauchyb_usetexture': True },
		'd_usetexture':				{ 'material': has_property('d') },
		'd_floatvalue':				{ 'material': has_property('d') },
		'd_texture':				{ 'material': has_property('d'), 'd_usetexture': True },
		'dispersion':				{ 'material': has_property('dispersion') },
		'film_usetexture':			{ 'material': has_property('film') },
		'film_floatvalue':			{ 'material': has_property('film') },
		'film_texture':				{ 'material': has_property('film'), 'film_usetexture': True },
		'filmindex_usetexture':		{ 'material': has_property('filmindex') },
		'filmindex_floatvalue':		{ 'material': has_property('filmindex') },
		'filmindex_texture':		{ 'material': has_property('filmindex'), 'filmindex_usetexture': True },
		'index_usetexture':			{ 'material': has_property('index') },
		'index_floatvalue':			{ 'material': has_property('index') },
		'index_texture':			{ 'material': has_property('index'), 'index_usetexture': True },
		'Ka':						{ 'material': has_property('Ka') },
		'Kd':						{ 'material': has_property('Kd') },
		'Kr':						{ 'material': has_property('Kr') },
		'Ks':						{ 'material': has_property('Ks') },
		'Ks1':						{ 'material': has_property('Ks1') },
		'Ks2':						{ 'material': has_property('Ks2') },
		'Ks3':						{ 'material': has_property('Ks3') },
		'Kt':						{ 'material': has_property('Kt') },
		'M1_usetexture':			{ 'material': has_property('M1') },
		'M2_usetexture':			{ 'material': has_property('M2') },
		'M3_usetexture':			{ 'material': has_property('M3') },
		'M1_floatvalue':			{ 'material': has_property('M1') },
		'M2_floatvalue':			{ 'material': has_property('M2') },
		'M3_floatvalue':			{ 'material': has_property('M3') },
		'M1_texture':				{ 'material': has_property('M1'), 'M1_usetexture': True },
		'M2_texture':				{ 'material': has_property('M2'), 'M2_usetexture': True },
		'M3_texture':				{ 'material': has_property('M3'), 'M3_usetexture': True },
		'name':						{ 'material': has_property('name') },
		'namedmaterial1':			{ 'material': has_property('namedmaterial1') },
		'namedmaterial2':			{ 'material': has_property('namedmaterial2') },
		'R1_usetexture':			{ 'material': has_property('R1') },
		'R2_usetexture':			{ 'material': has_property('R2') },
		'R3_usetexture':			{ 'material': has_property('R3') },
		'R1_floatvalue':			{ 'material': has_property('R1') },
		'R2_floatvalue':			{ 'material': has_property('R2') },
		'R3_floatvalue':			{ 'material': has_property('R3') },
		'R1_texture':				{ 'material': has_property('R1'), 'R1_usetexture': True },
		'R2_texture':				{ 'material': has_property('R2'), 'R2_usetexture': True },
		'R3_texture':				{ 'material': has_property('R3'), 'R3_usetexture': True },
		'sigma_usetexture':			{ 'material': has_property('sigma') },
		'sigma_floatvalue':			{ 'material': has_property('sigma') },
		'sigma_texture':			{ 'material': has_property('sigma'), 'sigma_usetexture': True },
		'uroughness_usetexture':	{ 'material': has_property('uroughness') },
		'uroughness_floatvalue':	{ 'material': has_property('uroughness') },
		'uroughness_texture':		{ 'material': has_property('uroughness'), 'uroughness_usetexture': True },
		'vroughness_usetexture':	{ 'material': has_property('vroughness') },
		'vroughness_floatvalue':	{ 'material': has_property('vroughness') },
		'vroughness_texture':		{ 'material': has_property('vroughness'), 'vroughness_usetexture': True },
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
				('glass2', 'Glass2', 'glass2'),
				('roughglass','Rough Glass','roughglass'),
				('glossy','Glossy','glossy'),
				('glossy_lossy','Glossy (Lossy)','glossy_lossy'),
				('matte','Matte','matte'),
				('mattetranslucent','Matte Translucent','mattetranslucent'),
				('metal','Metal','metal'),
				('shinymetal','Shiny Metal','shinymetal'),
				('mirror','Mirror','mirror'),
				('mix','Mix','mix'),
				('null','Null','null'),
			],
		},
	] + \
	ParamTextureFloat('amount', 'Mix Amount', 'luxrender_material') + \
	[
		{
			'type': 'bool',
			'attr': 'architectural',
			'name': 'Architectural',
			'default': False
		},
	] + \
	ParamTextureFloat('bumpmap', 'Bump Map', 'luxrender_material') + \
	ParamTextureFloat('cauchyb', 'Cauchy B', 'luxrender_material') + \
	ParamTextureFloat('d', 'Absorption Depth', 'luxrender_material') + \
	[
		{
			'type': 'bool',
			'attr': 'dipsersion',
			'name': 'Dispersion',
			'default': False
		},
	] + \
	ParamTextureFloat('film', 'Thin Film', 'luxrender_material') + \
	ParamTextureFloat('filmindex', 'Film IOR', 'luxrender_material') + \
	ParamTextureFloat('index', 'IOR', 'luxrender_material') + \
	ParamTextureColor('Ka', 'Absorption color', 'luxrender_material') + \
	ParamTextureColor('Kd', 'Diffuse color', 'luxrender_material') + \
	ParamTextureColor('Kr', 'Reflection color', 'luxrender_material') + \
	ParamTextureColor('Ks', 'Specular color', 'luxrender_material') + \
	ParamTextureColor('Ks1', 'Specular color 1', 'luxrender_material') + \
	ParamTextureColor('Ks2', 'Specular color 2', 'luxrender_material') + \
	ParamTextureColor('Ks3', 'Specular color 3', 'luxrender_material') + \
	ParamTextureColor('Kt', 'Transmission color', 'luxrender_material') + \
	ParamTextureFloat('M1', 'M1', 'luxrender_material') + \
	ParamTextureFloat('M2', 'M2', 'luxrender_material') + \
	ParamTextureFloat('M3', 'M3', 'luxrender_material') + \
	[
		{
			'type': 'string',
			'attr': 'name',
			'name': 'Name'
		},
	] + \
	ParamMaterial('namedmaterial1', 'Material 1', 'luxrender_material') + \
	ParamMaterial('namedmaterial2', 'Material 2', 'luxrender_material') + \
	ParamTextureFloat('R1', 'R1', 'luxrender_material') + \
	ParamTextureFloat('R2', 'R2', 'luxrender_material') + \
	ParamTextureFloat('R3', 'R3', 'luxrender_material') + \
	ParamTextureFloat('sigma', 'Sigma', 'luxrender_material') + \
	ParamTextureFloat('uroughness', 'uroughness', 'luxrender_material') + \
	ParamTextureFloat('vroughness', 'vroughness', 'luxrender_material')


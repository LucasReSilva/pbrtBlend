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
import luxrender.properties.material
from ..properties.util import has_property 
from ..properties.texture import FloatTexture, ColorTexture

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

# TODO: add default values

# Float Textures
TF_amount		= FloatTexture('material', 'amount', 'Mix Amount',		'luxrender_material')
TF_bumpmap		= FloatTexture('material', 'bumpmap', 'Bump Map',		'luxrender_material')
TF_cauchyb		= FloatTexture('material', 'cauchyb', 'Cauchy B',		'luxrender_material')
TF_d			= FloatTexture('material', 'd', 'Absorption Depth',		'luxrender_material')
TF_film			= FloatTexture('material', 'film', 'Thin Film',			'luxrender_material')
TF_filmindex	= FloatTexture('material', 'filmindex', 'Film IOR',		'luxrender_material')
TF_index		= FloatTexture('material', 'index', 'IOR',				'luxrender_material', min=0.0, max=25.0, default=1.0)
TF_M1			= FloatTexture('material', 'M1', 'M1',					'luxrender_material')
TF_M2			= FloatTexture('material', 'M2', 'M2',					'luxrender_material')
TF_M3			= FloatTexture('material', 'M3', 'M3',					'luxrender_material')
TF_R1			= FloatTexture('material', 'R1', 'R1',					'luxrender_material')
TF_R2			= FloatTexture('material', 'R2', 'R2',					'luxrender_material')
TF_R3			= FloatTexture('material', 'R3', 'R3',					'luxrender_material')
TF_sigma		= FloatTexture('material', 'sigma', 'Sigma',			'luxrender_material')
TF_uroughness	= FloatTexture('material', 'uroughness', 'uroughness',	'luxrender_material')
TF_vroughness	= FloatTexture('material', 'vroughness', 'vroughness',	'luxrender_material')

# Color Textures
TC_Ka	= ColorTexture('material', 'Ka', 'Absorption color',	'luxrender_material')
TC_Kd	= ColorTexture('material', 'Kd', 'Diffuse color',		'luxrender_material')
TC_Kr	= ColorTexture('material', 'Kr', 'Reflection color',	'luxrender_material')
TC_Ks	= ColorTexture('material', 'Ks', 'Specular color',		'luxrender_material')
TC_Ks1	= ColorTexture('material', 'Ks1', 'Specular color 1',	'luxrender_material')
TC_Ks2	= ColorTexture('material', 'Ks2', 'Specular color 2',	'luxrender_material')
TC_Ks3	= ColorTexture('material', 'Ks3', 'Specular color 3',	'luxrender_material')
TC_Kt	= ColorTexture('material', 'Kt', 'Transmission color',	'luxrender_material')

def material_visibility():
	# non-texture properties
	vis = {
		'architectural':			{ 'material': has_property('material', 'architectural') },
		'dispersion':				{ 'material': has_property('material', 'dispersion') },
		'name':						{ 'material': has_property('material', 'name') },
		'namedmaterial1':			{ 'material': has_property('material', 'namedmaterial1') },
		'namedmaterial2':			{ 'material': has_property('material', 'namedmaterial2') },
	}
	
	# Float Texture based properties
	vis.update( TF_amount.get_visibility() )
	vis.update( TF_bumpmap.get_visibility() )
	vis.update( TF_cauchyb.get_visibility() )
	vis.update( TF_d.get_visibility() )
	vis.update( TF_film.get_visibility() )
	vis.update( TF_filmindex.get_visibility() )
	vis.update( TF_index.get_visibility() )
	vis.update( TF_M1.get_visibility() )
	vis.update( TF_M2.get_visibility() )
	vis.update( TF_M3.get_visibility() )
	vis.update( TF_R1.get_visibility() )
	vis.update( TF_R2.get_visibility() )
	vis.update( TF_R3.get_visibility() )
	vis.update( TF_sigma.get_visibility() )
	vis.update( TF_uroughness.get_visibility() )
	vis.update( TF_vroughness.get_visibility() )
	
	# Color Texture based properties
	vis.update( TC_Ka.get_visibility() )
	vis.update( TC_Kd.get_visibility() )
	vis.update( TC_Kr.get_visibility() )
	vis.update( TC_Ks.get_visibility() )
	vis.update( TC_Ks1.get_visibility() )
	vis.update( TC_Ks2.get_visibility() )
	vis.update( TC_Ks3.get_visibility() )
	vis.update( TC_Kt.get_visibility() )
	
	return vis

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
		
	] + \
	TC_Kd.get_controls() + \
	TF_sigma.get_controls() + \
	TC_Ka.get_controls() + \
	TC_Ks.get_controls() + \
	TF_d.get_controls() + \
	TF_uroughness.get_controls() + \
	TF_vroughness.get_controls() + \
	[
		# 'Glassy' options
		'architectural',
	] + \
	TF_index.get_controls() + \
	TF_cauchyb.get_controls() + \
	TC_Kr.get_controls() + \
	TC_Kt.get_controls() + \
	TF_film.get_controls() + \
	TF_filmindex.get_controls() + \
	[
		'dispersion',
		
		# Carpaint options
	] + \
	TC_Ks1.get_controls() + \
	TC_Ks2.get_controls() + \
	TC_Ks3.get_controls() + \
	TF_M1.get_controls() + \
	TF_M2.get_controls() + \
	TF_M3.get_controls() + \
	TF_R1.get_controls() + \
	TF_R2.get_controls() + \
	TF_R3.get_controls() + \
	TF_bumpmap.get_controls() + \
	TF_amount.get_controls() + \
	[
		# Mix Material
		'namedmaterial1',
		'namedmaterial2',
	]
	
	visibility = material_visibility()
	
	properties = [
		# Material Type Select
		{
			'type': 'enum',
			'attr': 'material',
			'name': 'Type',
			'description': 'LuxRender material type',
			'default': 'matte',
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
	TF_amount.get_properties() + \
	[
		{
			'type': 'bool',
			'attr': 'architectural',
			'name': 'Architectural',
			'default': False
		},
	] + \
	TF_bumpmap.get_properties() + \
	TF_cauchyb.get_properties() + \
	TF_d.get_properties() + \
	[
		{
			'type': 'bool',
			'attr': 'dipsersion',
			'name': 'Dispersion',
			'default': False
		},
	] + \
	TF_film.get_properties() + \
	TF_filmindex.get_properties() + \
	TF_index.get_properties() + \
	TC_Ka.get_properties() + \
	TC_Kd.get_properties() + \
	TC_Kr.get_properties() + \
	TC_Ks.get_properties() + \
	TC_Ks1.get_properties() + \
	TC_Ks2.get_properties() + \
	TC_Ks3.get_properties() + \
	TC_Kt.get_properties() + \
	TF_M1.get_properties() + \
	TF_M2.get_properties() + \
	TF_M3.get_properties() + \
	[
		{
			'type': 'string',
			'attr': 'name',
			'name': 'Name'
		},
	] + \
	ParamMaterial('namedmaterial1', 'Material 1', 'luxrender_material') + \
	ParamMaterial('namedmaterial2', 'Material 2', 'luxrender_material') + \
	TF_R1.get_properties()+ \
	TF_R2.get_properties() + \
	TF_R3.get_properties() + \
	TF_sigma.get_properties() + \
	TF_uroughness.get_properties() + \
	TF_vroughness.get_properties()


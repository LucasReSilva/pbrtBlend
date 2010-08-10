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
from ..properties.texture import has_property 
from ..properties.texture import FloatTextureParameter, ColorTextureParameter

def MaterialParameter(attr, name, property_group):
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

# Float Textures
TF_amount		= FloatTextureParameter('material', 'amount', 'Mix Amount',				'luxrender_material', add_float_value=True, min=0.0, default=0.5, max=1.0 )
TF_bumpmap		= FloatTextureParameter('material', 'bumpmap', 'Bump Map',				'luxrender_material', add_float_value=True, precision=6, multiply_float=True, ignore_zero=True )
TF_cauchyb		= FloatTextureParameter('material', 'cauchyb', 'Cauchy B',				'luxrender_material', add_float_value=True, default=0.0, min=0.0, max=1.0 ) # default 0.0 for OFF
TF_d			= FloatTextureParameter('material', 'd', 'Absorption Depth',			'luxrender_material', add_float_value=True, default=0.15, min=0.0, max=15.0 )
TF_film			= FloatTextureParameter('material', 'film', 'Thin Film Thickness (nm)',	'luxrender_material', add_float_value=True, min=0.0, default=0.0, max=1500.0 ) # default 0.0 for OFF
TF_filmindex	= FloatTextureParameter('material', 'filmindex', 'Film IOR',			'luxrender_material', add_float_value=True, default=1.5, min=1.0, max=6.0 )
TF_index		= FloatTextureParameter('material', 'index', 'IOR',						'luxrender_material', add_float_value=True, min=0.0, max=25.0, default=1.0)
TF_M1			= FloatTextureParameter('material', 'M1', 'M1',							'luxrender_material', add_float_value=True, default=1.0, min=0.0, max=0.0 )
TF_M2			= FloatTextureParameter('material', 'M2', 'M2',							'luxrender_material', add_float_value=True, default=1.0, min=0.0, max=0.0 )
TF_M3			= FloatTextureParameter('material', 'M3', 'M3',							'luxrender_material', add_float_value=True, default=1.0, min=0.0, max=0.0 )
TF_R1			= FloatTextureParameter('material', 'R1', 'R1',							'luxrender_material', add_float_value=True, default=1.0, min=0.0, max=0.0 )
TF_R2			= FloatTextureParameter('material', 'R2', 'R2',							'luxrender_material', add_float_value=True, default=1.0, min=0.0, max=0.0 )
TF_R3			= FloatTextureParameter('material', 'R3', 'R3',							'luxrender_material', add_float_value=True, default=1.0, min=0.0, max=0.0 )
TF_sigma		= FloatTextureParameter('material', 'sigma', 'Sigma',					'luxrender_material', add_float_value=True, min=0.0, max=100.0 )
TF_uroughness	= FloatTextureParameter('material', 'uroughness', 'uroughness',			'luxrender_material', add_float_value=True, min=0.00001, max=1.0, default=0.0002 )
TF_vroughness	= FloatTextureParameter('material', 'vroughness', 'vroughness',			'luxrender_material', add_float_value=True, min=0.00001, max=1.0, default=0.0002 )

# Color Textures
TC_Ka			= ColorTextureParameter('material', 'Ka', 'Absorption color',	'luxrender_material', default=(0.2,0.2,0.2) )
TC_Kd			= ColorTextureParameter('material', 'Kd', 'Diffuse color',		'luxrender_material', default=(0.64,0.64,0.64) )
TC_Kr			= ColorTextureParameter('material', 'Kr', 'Reflection color',	'luxrender_material', default=(1.0,1.0,1.0) )
TC_Ks			= ColorTextureParameter('material', 'Ks', 'Specular color',		'luxrender_material', default=(0.25,0.25,0.25) )
TC_Ks1			= ColorTextureParameter('material', 'Ks1', 'Specular color 1',	'luxrender_material', default=(1.0,1.0,1.0) )
TC_Ks2			= ColorTextureParameter('material', 'Ks2', 'Specular color 2',	'luxrender_material', default=(1.0,1.0,1.0) )
TC_Ks3			= ColorTextureParameter('material', 'Ks3', 'Specular color 3',	'luxrender_material', default=(1.0,1.0,1.0) )
TC_Kt			= ColorTextureParameter('material', 'Kt', 'Transmission color',	'luxrender_material', default=(1.0,1.0,1.0) )

def material_visibility():
	# non-texture properties
	vis = {
		'architectural':			{ 'material': has_property('material', 'architectural') },
		'dispersion':				{ 'material': has_property('material', 'dispersion') },
		'name':						{ 'material': has_property('material', 'name') },
		'namedmaterial1':			{ 'material': has_property('material', 'namedmaterial1') },
		'namedmaterial2':			{ 'material': has_property('material', 'namedmaterial2') },
	}
	
	# Float Texture parameters
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
	
	# Color Texture parameters
	vis.update( TC_Ka.get_visibility() )
	vis.update( TC_Kd.get_visibility() )
	vis.update( TC_Kr.get_visibility() )
	vis.update( TC_Ks.get_visibility() )
	vis.update( TC_Ks1.get_visibility() )
	vis.update( TC_Ks2.get_visibility() )
	vis.update( TC_Ks3.get_visibility() )
	vis.update( TC_Kt.get_visibility() )
	
	# Add compositing options for distributedpath
	vis.update({
		'compositing_label':				{ 'integrator_type': 'distributedpath' },
		'compo_visible_material':			{ 'integrator_type': 'distributedpath' },
		'compo_visible_emission':			{ 'integrator_type': 'distributedpath' },
		'compo_visible_indirect_material':	{ 'integrator_type': 'distributedpath' },
		'compo_visible_indirect_emission':	{ 'integrator_type': 'distributedpath' },
		'compo_override_alpha':				{ 'integrator_type': 'distributedpath' },
		'compo_override_alpha_value':		{ 'integrator_type': 'distributedpath', 'compo_override_alpha': True },
	})
	
	return vis

class material_editor(MaterialButtonsPanel, described_layout, bpy.types.Panel):
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
			
			# Set the integrator type in this material in order to show compositing options 
			context.material.luxrender_material.integrator_type = context.scene.luxrender_integrator.surfaceintegrator
			
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
	[
		'dispersion',
	] + \
	TF_cauchyb.get_controls() + \
	TC_Kr.get_controls() + \
	TC_Kt.get_controls() + \
	TF_film.get_controls() + \
	TF_filmindex.get_controls() + \
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
		
		# Compositing options for distributedpath
		'compositing_label',
		['compo_visible_material',
		'compo_visible_emission'],
		['compo_visible_indirect_material',
		'compo_visible_indirect_emission'],
		'compo_override_alpha',
		'compo_override_alpha_value'
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
			'attr': 'dispersion',
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
	MaterialParameter('namedmaterial1', 'Material 1', 'luxrender_material') + \
	MaterialParameter('namedmaterial2', 'Material 2', 'luxrender_material') + \
	TF_R1.get_properties()+ \
	TF_R2.get_properties() + \
	TF_R3.get_properties() + \
	TF_sigma.get_properties() + \
	TF_uroughness.get_properties() + \
	TF_vroughness.get_properties() + \
	[
		# hidden parameter to hold current integrator type - updated on draw()
		{
			'type': 'string',
			'attr': 'integrator_type',
		},
		{
			'type': 'text',
			'attr': 'compositing_label',
			'name': 'Compositing options',
		},
		{
			'type': 'bool',
			'attr': 'compo_visible_material',
			'name': 'Visible Material',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'compo_visible_emission',
			'name': 'Visible Emission',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'compo_visible_indirect_material',
			'name': 'Visible Indirect Material',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'compo_visible_indirect_emission',
			'name': 'Visible Indirect Emission',
			'default': True
		},
		{
			'type': 'bool',
			'attr': 'compo_override_alpha',
			'name': 'Override Alpha',
			'default': False
		},
		{
			'type': 'float',
			'attr': 'compo_override_alpha_value',
			'name': 'Override Alpha Value',
			'default': 0.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0,
		},
	]

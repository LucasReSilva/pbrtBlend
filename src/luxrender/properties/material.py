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
import re

import bpy

from extensions_framework import declarative_property_group
from extensions_framework import util as efutil

from .. import LuxRenderAddon
from ..properties.texture import (
	FloatTextureParameter, ColorTextureParameter, import_paramset_to_blender_texture
)
from ..export import ParamSet
from ..export.materials import (
	MaterialCounter, ExportedMaterials, ExportedTextures, get_texture_from_scene
)
from ..outputs import LuxManager, LuxLog
from ..outputs.pure_api import LUXRENDER_VERSION
from ..util import dict_merge

def MaterialParameter(attr, name, property_group):
	return [
		{
			'attr': '%s_material' % attr,
			'type': 'string',
			'name': '%s_material' % attr,
			'description': '%s_material' % attr,
			'save_in_preset': True
		},
		{
			'type': 'prop_search',
			'attr': attr,
			'src': lambda s,c: s.object,
			'src_attr': 'material_slots',
			'trg': lambda s,c: getattr(c, property_group),
			'trg_attr': '%s_material' % attr,
			'name': name
		},
	]

def VolumeParameter(attr, name):
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
			'trg': lambda s,c: c.luxrender_material,
			'trg_attr': '%s_volume' % attr,
			'name': name
		},
	]

# TODO: add override props to *TextureParameter instead of using these sub-types

class SubGroupFloatTextureParameter(FloatTextureParameter):
	def texture_slot_set_attr(self):
		# Looks in a different location than other FloatTextureParameters
		return lambda s,c: c.luxrender_material

def texture_append_visibility(vis_main, textureparam_object, vis_append):
	for prop in textureparam_object.properties:
		if 'attr' in prop.keys():
			if not prop['attr'] in vis_main.keys():
				vis_main[prop['attr']] = {}
			for vk, vi in vis_append.items():
				vis_main[prop['attr']][vk] = vi
	return vis_main

# Float Textures
TF_bumpmap				= SubGroupFloatTextureParameter('bumpmap', 'Bump Map',				add_float_value=True, min=-1.0, max=1.0, default=0.0, precision=6, multiply_float=True, ignore_zero=True )
TF_amount				= FloatTextureParameter('amount', 'Mix Amount',						add_float_value=True, min=0.0, default=0.5, max=1.0 )
TF_cauchyb				= FloatTextureParameter('cauchyb', 'Cauchy B',						add_float_value=True, default=0.0, min=0.0, max=1.0 ) # default 0.0 for OFF
TF_d					= FloatTextureParameter('d', 'Absorption Depth',					add_float_value=True, default=0.0, min=0.0, max=15.0 ) # default 0.0 for OFF
TF_film					= FloatTextureParameter('film', 'Thin Film Thickness (nm)',			add_float_value=True, min=0.0, default=0.0, max=1500.0 ) # default 0.0 for OFF
TF_filmindex			= FloatTextureParameter('filmindex', 'Film IOR',					add_float_value=True, default=1.3333, min=1.0, max=6.0 ) # default 1.3333 for a coating of a water-based solution
TF_index				= FloatTextureParameter('index', 'IOR',								add_float_value=True, min=0.0, max=25.0, default=1.519) #default of something other than 1.0 so glass and roughglass render propery with defaults
TF_M1					= FloatTextureParameter('M1', 'M1',									add_float_value=True, default=0.033, min=0.0001, max=1.0 ) #carpaint defaults set for a basic gray clearcoat paint job, as a "setting suggestion"
TF_M2					= FloatTextureParameter('M2', 'M2',									add_float_value=True, default=0.055, min=0.0001, max=1.0 ) #set m1-3 min to .0001, carpaint will take 0.0 as being max (1.0)
TF_M3					= FloatTextureParameter('M3', 'M3',									add_float_value=True, default=0.100, min=0.0001, max=1.0 )
TF_R1					= FloatTextureParameter('R1', 'R1',									add_float_value=True, min=0.00001, max=1.0, default=0.08 )
TF_R2					= FloatTextureParameter('R2', 'R2',									add_float_value=True, min=0.00001, max=1.0, default=0.03 )
TF_R3					= FloatTextureParameter('R3', 'R3',									add_float_value=True, min=0.00001, max=1.0, default=0.06 )
TF_sigma				= FloatTextureParameter('sigma', 'Sigma',							add_float_value=True, min=0.0, max=100.0 )
TF_uroughness			= FloatTextureParameter('uroughness', 'uroughness',					add_float_value=True, min=0.00001, max=1.0, default=0.075 )
TF_vroughness			= FloatTextureParameter('vroughness', 'vroughness',					add_float_value=True, min=0.00001, max=1.0, default=0.075 )
TF_backface_d			= FloatTextureParameter('bf_d', 'Backface Absorption Depth',		real_attr='backface_d', add_float_value=True, default=0.0, min=0.0, max=15.0 ) # default 0.0 for OFF
TF_backface_index		= FloatTextureParameter('bf_index', 'Backface IOR',					real_attr='backface_index', add_float_value=True, min=0.0, max=25.0, default=1.0)
TF_backface_uroughness	= FloatTextureParameter('bf_uroughness', 'Backface uroughness',		real_attr='backface_uroughness', add_float_value=True, min=0.00001, max=1.0, default=0.25 ) #backface roughness is high than front by default, will usually be for backs of leaves or cloth
TF_backface_vroughness	= FloatTextureParameter('bf_vroughness', 'Backface vroughness',		real_attr='backface_vroughness', add_float_value=True, min=0.00001, max=1.0, default=0.25 )
TF_g					= FloatTextureParameter('g', 'Scattering asymmetry',				add_float_value=True, default=0.0, min=-1.0, max=1.0 ) # default 0.0 for Uniform

# Color Textures
TC_Ka					= ColorTextureParameter('Ka', 'Absorption color',					default=(0.0,0.0,0.0) )
TC_Kd					= ColorTextureParameter('Kd', 'Diffuse color',						default=(0.64,0.64,0.64) )
TC_Kr					= ColorTextureParameter('Kr', 'Reflection color',					default=(0.7,0.7,0.7) ) # 1.0 reflection color is not sane for mirror or shinymetal, 0.7 does not signifcantly affect glass or roughglass
TC_Ks					= ColorTextureParameter('Ks', 'Specular color',						default=(0.25,0.25,0.25) )
TC_Ks1					= ColorTextureParameter('Ks1', 'Specular color 1',					default=(0.8,0.8,0.8) )
TC_Ks2					= ColorTextureParameter('Ks2', 'Specular color 2',					default=(0.5,0.5,0.5) )
TC_Ks3					= ColorTextureParameter('Ks3', 'Specular color 3',					default=(0.5,0.5,0.5) )
TC_Kt					= ColorTextureParameter('Kt', 'Transmission color',					default=(1.0,1.0,1.0) )
TC_backface_Ka			= ColorTextureParameter('backface_Ka', 'Backface Absorption color',	default=(0.0,0.0,0.0) )
TC_backface_Kd			= ColorTextureParameter('backface_Kd', 'Backface Diffuse color',	default=(0.64,0.64,0.64) )
TC_backface_Ks			= ColorTextureParameter('backface_Ks', 'Backface Specular color',	default=(0.25,0.25,0.25) )

mat_names = {
	
	# Categories are disabled for now, doesn't seem worth it
	# and there's no agreeable correct way to do it
	#('Matte', (
		'matte': 'Matte',
		'mattetranslucent': 'Matte Translucent',
	#)),
	
	#('Glossy', (
		'glossy': 'Glossy',
		'glossy_lossy': 'Glossy (Lossy)',
		'glossytranslucent': 'Glossy Translucent',
	#)),
	
	#('Glass', (
		'glass': 'Glass',
		'glass2': 'Glass2',
		'roughglass': 'Rough Glass',
		'mirror': 'Mirror',
	#)),
	
	#('Metal', (
		'carpaint': 'Car Paint',
		'metal': 'Metal',
		'shinymetal': 'Shiny Metal',
	#)),
	
	#('Other', (
		'velvet': 'Velvet',
		'scatter': 'Scatter',
		'mix': 'Mix',
		'null': 'Null',
	#))
}

@LuxRenderAddon.addon_register_class
class MATERIAL_OT_set_luxrender_type(bpy.types.Operator):
	bl_idname = 'material.set_luxrender_type'
	bl_label = 'Set LuxRender material type'
	
	mat_name = bpy.props.StringProperty()
	
	@classmethod
	def poll(cls, context):
		return	context.material and \
				context.material.luxrender_material
	
	def execute(self, context):
		context.material.luxrender_material.set_type( self.properties.mat_name )
		return {'FINISHED'}

#def draw_generator(operator, m_names):
#	def draw(self, context):
#		sl = self.layout
#		for m_name, m_label in sorted(m_names):
#			op = sl.operator(operator, text=m_label)
#			op.mat_name = m_name
#			op.mat_label = m_label
#	return draw

@LuxRenderAddon.addon_register_class
class MATERIAL_MT_luxrender_type(bpy.types.Menu):
	bl_label = 'Material Type'
	
#	NESTED MENU SYSTEM, perhaps for future use
#	submenus = []
#	for mat_cat, mat_cat_list in sorted(mat_names):
#		submenu_idname = 'MATERIAL_MT_luxrender_mat_cat%d'%len(submenus)
#		submenus.append(
#			LuxRenderAddon.addon_register_class(type(
#				submenu_idname,
#				(bpy.types.Menu,),
#				{
#					'bl_idname': submenu_idname,
#					'bl_label': mat_cat,
#					'draw': draw_generator('MATERIAL_OT_set_luxrender_type', mat_cat_list)
#				}
#			))
#		)
#	def draw(self, context):
#		sl = self.layout
#		for sm in self.submenus:
#			sl.menu(sm.bl_idname)
	
	# Flat-list menu system
	def draw(self, context):
		sl = self.layout
		for m_name in sorted(mat_names.keys()):
			op = sl.operator('MATERIAL_OT_set_luxrender_type', text=mat_names[m_name])
			op.mat_name = m_name
	
@LuxRenderAddon.addon_register_class
class luxrender_material(declarative_property_group):
	'''
	Storage class for LuxRender Material settings.
	'''
	
	ef_attach_to = ['Material']
	
	controls = [
		# Type select Menu is drawn manually
		'Interior',
		'Exterior'
	] + \
	TF_bumpmap.controls
	
	visibility = dict_merge({}, TF_bumpmap.visibility)
	
	properties = [
		# The following two items are set by the preset menu and operator.
		{
			'attr': 'type_label',
			'name': 'LuxRender Type',
			'type': 'string',
			'default': 'Matte',
			'save_in_preset': True
		},
		{
			'type': 'string',
			'attr': 'type',
			'name': 'Type',
			'default': 'matte',
			'save_in_preset': True
		},
	] + \
		TF_bumpmap.properties + \
		VolumeParameter('Interior', 'Interior') + \
		VolumeParameter('Exterior', 'Exterior')
	
	def set_type(self, mat_type):
		self.type = mat_type
		self.type_label = mat_names[mat_type]
	
	# Decide which material property sets the viewport object
	# colour for each material type. If the property name is
	# not set, then the color won't be changed.
	master_color_map = {
		'carpaint': 'Kd',
		'glass': 'Kt',
		'roughglass': 'Kt',
		'glossy': 'Kd',
		'glossy_lossy': 'Kd',
		'matte': 'Kd',
		'mattetranslucent': 'Kt',
		'shinymetal': 'Ks',
		'mirror': 'Kr',
	}
	
	def reset(self, prnt=None):
		super().reset()
		# Also reset sub-property groups
		for a in mat_names.keys():
			getattr(self, 'luxrender_mat_%s'%a).reset()
		
		if prnt:
			prnt.luxrender_emission.reset()
			prnt.luxrender_transparency.reset()
	
	def set_master_color(self, blender_material):
		'''
		This little function will set the blender material colour to the value
		given in the material panel.
		CAVEAT: you can only call this method in an operator context.
		'''
		
		if self.type in self.master_color_map.keys():
			submat = getattr(self, 'luxrender_mat_%s'%self.type)
			submat_col = getattr(submat, '%s_color' % self.master_color_map[self.type])
			if blender_material.diffuse_color != submat_col:
				blender_material.diffuse_color = submat_col
	
	def export(self, lux_context, material, mode='indirect'):
		with MaterialCounter(material.name):
			if not (mode=='indirect' and material.name in ExportedMaterials.exported_material_names):
				if self.type == 'mix':
					# First export the other mix mats
					m1_name = self.luxrender_mat_mix.namedmaterial1_material
					if m1_name == '':
						raise Exception('Unassigned mix material slot 1 on material %s' % material.name)
					m1 = bpy.data.materials[m1_name]
					m1.luxrender_material.export(lux_context, m1, 'indirect')
					
					m2_name = self.luxrender_mat_mix.namedmaterial2_material
					if m2_name == '':
						raise Exception('Unassigned mix material slot 2 on material %s' % material.name)
					
					m2 = bpy.data.materials[m2_name]
					m2.luxrender_material.export(lux_context, m2, 'indirect')
				
				material_params = ParamSet()
				
				sub_type = getattr(self, 'luxrender_mat_%s'%self.type)
				
				alpha_type = None
				# find alpha texture if material should be transparent
				if hasattr(material, 'luxrender_transparency') and material.luxrender_transparency.transparent:
					alpha_type, alpha_amount = material.luxrender_transparency.export(lux_context, material)
				
				# Bump mapping
				if self.type not in ['mix', 'null']:
					material_params.update( TF_bumpmap.get_paramset(self) )
				
				material_params.update( sub_type.get_paramset(material) )
				
				# DistributedPath compositing
				if LuxManager.CurrentScene.luxrender_integrator.surfaceintegrator == 'distributedpath':
					material_params.update( self.luxrender_mat_compositing.get_paramset() )
				
				if alpha_type == None:
					mat_type = self.type
				else: # export mix for transparency
					material_params.add_string('type', self.type)
					ExportedMaterials.makeNamedMaterial(lux_context, material.name + '_null', ParamSet().add_string('type', 'null'))
					ExportedMaterials.makeNamedMaterial(lux_context, material.name + '_base', material_params)
					ExportedMaterials.export_new_named(lux_context)
					
					# replace material params with mix
					mat_type = 'mix'
					material_params = ParamSet() \
						.add_string('namedmaterial1', material.name + '_null') \
						.add_string('namedmaterial2', material.name + '_base')
					if alpha_type == 'float':
						material_params.add_float('amount', alpha_amount)
					else:
						material_params.add_texture('amount', alpha_amount)
					
				if mode == 'indirect':
					material_params.add_string('type', mat_type)
					ExportedMaterials.makeNamedMaterial(lux_context, material.name, material_params)
					ExportedMaterials.export_new_named(lux_context)
				elif mode == 'direct':
					lux_context.material(mat_type, material_params)
			
		return material.luxrender_emission.use_emission
	
	def load_lbm2(self, context, lbm2, blender_mat, blender_obj):
		'''
		Load LBM2 data into this material, either from LRMDB or from file
		(Includes setting up textures and volumes!)
		
		NOTE: this function may well overwrite material settings if the
		imported data contains objects of the same name as exists in the
		scene already.
		It will also clear and reset all material and texture slots.
		'''
		
		# Remove all materials assigned to blender_obj
		while len(blender_obj.material_slots) > 0:
			bpy.ops.object.material_slot_remove()
		
		for tsi in range(18):
			blender_mat.texture_slots.clear(tsi)
		
		# Change the name of this material to the target material in the lbm2 data
		blender_mat.name = lbm2['name']
		
		material_index=0
		
		for lbm2_obj in lbm2['objects']:
			# Add back all the textures
			if lbm2_obj['type'] == 'Texture':
				
				# parse variant and type first
				vt_matches = re.match('"(.*)" "(.*)"', lbm2_obj['extra_tokens'])
				if vt_matches.lastindex != 2:
					continue	# not a valid texture!
				
				variant, tex_type = vt_matches.groups()
				
				tex_slot = blender_mat.texture_slots.add()
				if lbm2_obj['name'] not in bpy.data.textures:
					bpy.data.textures.new(name=lbm2_obj['name'],type='NONE')
				
				blender_tex = bpy.data.textures[lbm2_obj['name']]
				tex_slot.texture = blender_tex
				
				lxt = bpy.data.textures[lbm2_obj['name']].luxrender_texture
				
				# Restore default texture settings
				lxt.reset()
				
				# TODO: error checking for correct type
				if not tex_type.startswith('blender_'):
					lxt.set_type(tex_type)
					subtype = getattr(lxt, 'luxrender_tex_%s'%tex_type)
					subtype.load_paramset(variant, lbm2_obj['paramset'])
				else:
					lxt.set_type('BLENDER')
					# do the reverse of export.materials.convert_texture
					import_paramset_to_blender_texture(blender_tex, tex_type, lbm2_obj['paramset'])
				
				lxt.luxrender_tex_mapping.load_paramset(lbm2_obj['paramset'])
				lxt.luxrender_tex_transform.load_paramset(lbm2_obj['paramset'])
			
			# Add back all the materials
			if lbm2_obj['type'] == 'MakeNamedMaterial':
				if lbm2_obj['name'] not in bpy.data.materials:
					bpy.data.materials.new(name=lbm2_obj['name'])
				
				bpy.ops.object.material_slot_add()
				blender_obj.material_slots[material_index].material = bpy.data.materials[lbm2_obj['name']]
				
				# Update an existing material with data from lbm2
				lxm = bpy.data.materials[lbm2_obj['name']].luxrender_material
				# reset this material
				lxm.reset(prnt=bpy.data.materials[lbm2_obj['name']])
				
				# Set up bump map
				TF_bumpmap.load_paramset(lxm, lbm2_obj['paramset'])
				
				subtype = None
				
				# First iterate for the material type, because
				# we need to know which sub PropertyGroup to 
				# set the other paramsetitems in
				for paramsetitem in lbm2_obj['paramset']:
					if paramsetitem['name'] == 'type':
						lxm.set_type( paramsetitem['value'] )
						subtype = getattr(lxm, 'luxrender_mat_%s'%paramsetitem['value'])
				
				if subtype != None:
					subtype.load_paramset(lbm2_obj['paramset'])
				
				material_index+=1
		
		
		for lbm2_obj in lbm2['objects']:
			# Load volume data in a separate loop to ensure
			# that any textures used have already been created
			if lbm2_obj['type'] == 'MakeNamedVolume':
				# parse volume type first
				vt_matches = re.match('"(.*)"', lbm2_obj['extra_tokens'])
				if vt_matches.lastindex != 1:
					continue	# not a valid volume!
				
				scene_vols = context.scene.luxrender_volumes.volumes
				try:
					# Use existing vol if present
					volm = scene_vols[lbm2_obj['name']]
				except KeyError:
					# else make a new one
					scene_vols.add()
					volm = scene_vols[len(scene_vols)-1]
					volm.name = lbm2_obj['name']
				
				volm.reset()
				
				volm.type = vt_matches.groups()[0]
				# load paramset will also assign any textures used to the world
				volm.load_paramset(context.scene.world, lbm2_obj['paramset'])
		
		# restore interior/exterior from metadata, if present
		if 'metadata' in lbm2.keys():
			if 'interior' in lbm2['metadata'].keys():
				self.Interior_volume = lbm2['metadata']['interior']
			if 'exterior' in lbm2['metadata'].keys():
				self.Exterior_volume = lbm2['metadata']['exterior']
		
		self.set_master_color(blender_mat)
		blender_mat.preview_render_type = blender_mat.preview_render_type

@LuxRenderAddon.addon_register_class
class luxrender_mat_compositing(declarative_property_group):
	'''
	Storage class for LuxRender Material compositing settings
	for DistributedPath integrator.
	'''
	
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'enabled',
		['visible_material',
		'visible_emission'],
		['visible_indirect_material',
		'visible_indirect_emission'],
		'override_alpha',
		'override_alpha_value',
	]
	
	visibility = {
		'visible_material':					{ 'enabled': True },
		'visible_emission':					{ 'enabled': True },
		'visible_indirect_material':		{ 'enabled': True },
		'visible_indirect_emission':		{ 'enabled': True },
		'override_alpha':					{ 'enabled': True },
		'override_alpha_value':				{ 'enabled': True, 'override_alpha': True },
	}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'enabled',
			'name': 'Use compositing settings',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'visible_material',
			'name': 'Visible Material',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'visible_emission',
			'name': 'Visible Emission',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'visible_indirect_material',
			'name': 'Visible Indirect Material',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'visible_indirect_emission',
			'name': 'Visible Indirect Emission',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'override_alpha',
			'name': 'Override Alpha',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'override_alpha_value',
			'name': 'Override Alpha Value',
			'default': 0.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0,
			'save_in_preset': True
		},
	]
	
	def get_paramset(self):
		compo_params = ParamSet()
		
		if self.enabled:
			compo_params.add_bool('compo_visible_material', self.visible_material)
			compo_params.add_bool('compo_visible_emission', self.visible_emission)
			compo_params.add_bool('compo_visible_indirect_material', self.visible_indirect_material)
			compo_params.add_bool('compo_visible_indirect_emission', self.visible_indirect_emission)
			compo_params.add_bool('compo_override_alpha', self.override_alpha)
			if self.override_alpha:
				compo_params.add_float('compo_override_alpha_value', self.override_alpha_value)
		
		return compo_params
	
	def load_paramset(self, ps):
		for psi in ps:
			for prop in self.properties:
				if prop['type'] == psi['type'] and prop['attr'] == psi['name']:
					setattr(self, psi['name'], psi['value'])

class TransparencyFloatTextureParameter(FloatTextureParameter):
	def texture_slot_set_attr(self):
		# Looks in a different location than other ColorTextureParameters
		return lambda s,c: c.luxrender_transparency

TF_alpha = TransparencyFloatTextureParameter('alpha', 'Alpha', add_float_value=False, default=1.0, min=0.0, max=1.0 )

@LuxRenderAddon.addon_register_class
class luxrender_transparency(declarative_property_group):
	'''
	Storage class for LuxRender Material alpha transparency settings.
	'''
	
	ef_attach_to = ['Material']
	
	controls = [
		# 'transparent', # drawn in header 
		'alpha_source',
		'alpha_value',
	] + \
		TF_alpha.controls + \
	[
		'inverse',
	]
	
	visibility = dict_merge(
		{
			'alpha_source': { 'transparent': True },
			'alpha_value': { 'transparent': True, 'alpha_source': 'constant' },
			'inverse': { 'transparent': True, 'alpha_source': 'texture' },
		},
		TF_alpha.visibility
	)
	visibility = texture_append_visibility(visibility, TF_alpha, { 'transparent': True, 'alpha_source': 'texture' })
	
	properties = [
		{
			'type': 'bool',
			'attr': 'transparent',
			'name': 'Transparent',
			'description': 'Enable alpha transparency',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'alpha_source',
			'name': 'Alpha source',
			'default': 'diffusealpha',
			'items': [
				('texture', 'texture', 'texture'),
				('diffuseintensity', 'diffuse/reflection intensity', 'diffuseintensity'),
				('diffusemean', 'diffuse/reflection mean', 'diffusemean'),
				('diffusealpha', 'diffuse/reflection alpha', 'diffusealpha'),
				('constant', 'constant', 'constant')
			],
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'alpha_value',
			'name': 'Alpha value',
			'default': 0.5,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'inverse',
			'name': 'Inverse',
			'description': 'Use the inverse of the alpha source',
			'default': False,
			'save_in_preset': True
		},
	] + \
		TF_alpha.properties
	
	sourceMap = {
		'carpaint': 'Kd',
		'glass': 'Kr',
		'glossy': 'Kd',
		'glossy_lossy': 'Kd',
		'glossytranslucent': 'Kd',
		'matte': 'Kd',
		'mattetranslucent': 'Kr',
		'mirror': 'Kr',
		'roughglass': 'Kr',
		'scatter': 'Kd',
		'shinymetal': 'Kr',
		'velvet': 'Kd'
	}
	
	def export(self, lux_context, material):
		lux_material = getattr(material.luxrender_material, 'luxrender_mat_%s'%material.luxrender_material.type)
		
		alpha_type = None
		
		if self.alpha_source == 'texture':
			alpha_type = 'texture'
			alpha_amount = self.alpha_floattexturename
			# export texture
			TF_alpha.get_paramset(self)
			
			if self.inverse:
				params = ParamSet() \
					.add_float('tex1', 1.0) \
					.add_float('tex2', 0.0) \
					.add_texture('amount', alpha_amount)
				
				alpha_amount = alpha_amount + '_alpha'
				
				ExportedTextures.texture(
					lux_context,
					alpha_amount,
					'float',
					'mix',
					params
				)
				ExportedTextures.export_new(lux_context)
			
		elif self.alpha_source == 'constant':
			alpha_type = 'float'
			alpha_amount = self.alpha_value
		elif material.luxrender_material.type in self.sourceMap:
			# grab base texture in case it's not diffuse channel
			texture_name = getattr(lux_material, '%s_colortexturename' % self.sourceMap[material.luxrender_material.type])
			if texture_name != '':
				texture = get_texture_from_scene(LuxManager.CurrentScene, texture_name)
				lux_texture = texture.luxrender_texture
				if lux_texture.type == 'imagemap':
					src_texture = lux_texture.luxrender_tex_imagemap
					
					channelMap = {
						'diffusealpha': 'alpha', 
						'diffusemean': 'mean',
						'diffuseintensity': 'colored_mean',
					}
					
					params = ParamSet() \
						.add_string('filename', efutil.path_relative_to_export(src_texture.get_filename(texture))) \
						.add_string('channel', channelMap[self.alpha_source]) \
						.add_integer('discardmipmaps', src_texture.discardmipmaps) \
						.add_string('filtertype', src_texture.filtertype) \
						.add_float('maxanisotropy', src_texture.maxanisotropy) \
						.add_string('wrap', src_texture.wrap)
					params.update( lux_texture.luxrender_tex_mapping.get_paramset(LuxManager.CurrentScene) )
					
					alpha_type = 'texture'
					alpha_amount = texture_name + '_alpha'
					
					ExportedTextures.texture(
						lux_context,
						alpha_amount,
						'float',
						'imagemap',
						params
					)
					ExportedTextures.export_new(lux_context)
		
		if alpha_type == None:
			LuxLog('WARNING: Invalid alpha texture for material ''%s'', disabling transparency' % material.name)
			return None, None
		
		return alpha_type, alpha_amount

@LuxRenderAddon.addon_register_class
class luxrender_mat_carpaint(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'name'
	] + \
		TF_d.controls + \
		TC_Ka.controls + \
		TC_Kd.controls + \
		TC_Ks1.controls + \
		TC_Ks2.controls + \
		TC_Ks3.controls + \
		TF_M1.controls + \
		TF_M2.controls + \
		TF_M3.controls + \
		TF_R1.controls + \
		TF_R2.controls + \
		TF_R3.controls
	
	visibility = dict_merge(
		TF_d.visibility,
		TC_Ka.visibility,
		TC_Kd.visibility,
		TC_Ks1.visibility,
		TC_Ks2.visibility,
		TC_Ks3.visibility,
		TF_M1.visibility,
		TF_M2.visibility,
		TF_M3.visibility,
		TF_R1.visibility,
		TF_R2.visibility,
		TF_R3.visibility
	)
	
	visibility = texture_append_visibility(visibility, TC_Kd, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TC_Ks1, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TC_Ks2, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TC_Ks3, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TF_M1, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TF_M2, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TF_M3, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TF_R1, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TF_R2, { 'name': '-' })
	visibility = texture_append_visibility(visibility, TF_R3, { 'name': '-' })
	
	properties = [
		{
			'type': 'enum',
			'attr': 'name',
			'name': 'Preset',
			'items': [
				('-', 'Manual settings', '-'),
				('2k acrylack', '2k Acrylack', '2k acrylack'),
				('blue', 'Blue', 'blue'),
				('blue matte', 'Blue Matte', 'blue matte'),
				('bmw339', 'BMW 339', 'bmw339'),
				('ford f8', 'Ford F8', 'ford f8'),
				('opel titan', 'Opel Titan', 'opel titan'),
				('polaris silber', 'Polaris Silber', 'polaris silber'),
				('white', 'White', 'white'),
			],
			'save_in_preset': True
		},
	] + \
		TF_d.properties + \
		TC_Ka.properties + \
		TC_Kd.properties + \
		TC_Ks1.properties + \
		TC_Ks2.properties + \
		TC_Ks3.properties + \
		TF_M1.properties + \
		TF_M2.properties + \
		TF_M3.properties + \
		TF_R1.properties + \
		TF_R2.properties + \
		TF_R3.properties
	
	def get_paramset(self, material):
		carpaint_params = ParamSet()
		
		if self.d_floatvalue > 0:
			carpaint_params.update( TF_d.get_paramset(self) )
			carpaint_params.update( TC_Ka.get_paramset(self) )
		
		if self.name == '-':	# Use manual settings
			carpaint_params.update( TC_Kd.get_paramset(self) )
			carpaint_params.update( TC_Ks1.get_paramset(self) )
			carpaint_params.update( TC_Ks2.get_paramset(self) )
			carpaint_params.update( TC_Ks3.get_paramset(self) )
			carpaint_params.update( TF_M1.get_paramset(self) )
			carpaint_params.update( TF_M2.get_paramset(self) )
			carpaint_params.update( TF_M3.get_paramset(self) )
			carpaint_params.update( TF_R1.get_paramset(self) )
			carpaint_params.update( TF_R2.get_paramset(self) )
			carpaint_params.update( TF_R3.get_paramset(self) )
		else:					# Use preset
			carpaint_params.add_string('name', self.name)
		
		return carpaint_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'name': 'string'
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])
		
		TF_d.load_paramset(self, ps)
		TC_Ka.load_paramset(self, ps)
		TC_Kd.load_paramset(self, ps)
		TC_Ks1.load_paramset(self, ps)
		TC_Ks2.load_paramset(self, ps)
		TC_Ks3.load_paramset(self, ps)
		TF_M1.load_paramset(self, ps)
		TF_M2.load_paramset(self, ps)
		TF_M3.load_paramset(self, ps)
		TF_R1.load_paramset(self, ps)
		TF_R2.load_paramset(self, ps)
		TF_R3.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_glass(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'architectural',
	] + \
		TF_cauchyb.controls + \
		TF_film.controls + \
		TF_filmindex.controls + \
	[
		'draw_ior_menu'
	] + \
		TF_index.controls + \
		TC_Kr.controls + \
		TC_Kt.controls
	
	visibility = dict_merge(
		TF_cauchyb.visibility,
		TF_film.visibility,
		TF_filmindex.visibility,
		TF_index.visibility,
		TC_Kr.visibility,
		TC_Kt.visibility
	)
	
	properties = [
		{
			'type': 'ef_callback',
			'attr': 'draw_ior_menu',
			'method': 'draw_ior_menu',
		},
		{
			'type': 'bool',
			'attr': 'architectural',
			'name': 'Architectural',
			'default': False,
			'save_in_preset': True
		},
	] + \
		TF_cauchyb.properties + \
		TF_film.properties + \
		TF_filmindex.properties + \
		TF_index.properties + \
		TC_Kr.properties + \
		TC_Kt.properties
	
	def get_paramset(self, material):
		glass_params = ParamSet()
		
		glass_params.add_bool('architectural', self.architectural)
		
		glass_params.update( TF_cauchyb.get_paramset(self) )
		glass_params.update( TF_film.get_paramset(self) )
		glass_params.update( TF_filmindex.get_paramset(self) )
		glass_params.update( TF_index.get_paramset(self) )
		glass_params.update( TC_Kr.get_paramset(self) )
		glass_params.update( TC_Kt.get_paramset(self) )
		
		return glass_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'architectural': 'bool',
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])
		
		TF_cauchyb.load_paramset(self, ps)
		TF_film.load_paramset(self, ps)
		TF_filmindex.load_paramset(self, ps)
		TF_index.load_paramset(self, ps)
		TC_Kr.load_paramset(self, ps)
		TC_Kt.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_glass2(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'architectural',
		'dispersion'
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'architectural',
			'name': 'Architectural',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'dispersion',
			'name': 'Dispersion',
			'default': False,
			'save_in_preset': True
		},
	]
	
	def get_paramset(self, material):
		glass2_params = ParamSet()
		
		glass2_params.add_bool('architectural', self.architectural)
		glass2_params.add_bool('dispersion', self.dispersion)
		
		return glass2_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'architectural': 'bool',
			'dispersion': 'bool',
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])

@LuxRenderAddon.addon_register_class
class luxrender_mat_roughglass(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
	] + \
		TF_cauchyb.controls + \
	[
		'draw_ior_menu',
	] + \
		TF_index.controls + \
		TC_Kr.controls + \
		TC_Kt.controls + \
		TF_uroughness.controls + \
		TF_vroughness.controls
	
	visibility = dict_merge(
		TF_cauchyb.visibility,
		TF_index.visibility,
		TC_Kr.visibility,
		TC_Kt.visibility,
		TF_uroughness.visibility,
		TF_vroughness.visibility
	)
	
	properties = [
		{
			'type': 'ef_callback',
			'attr': 'draw_ior_menu',
			'method': 'draw_ior_menu',
		},
		
	] + \
		TF_cauchyb.properties + \
		TF_index.properties + \
		TC_Kr.properties + \
		TC_Kt.properties + \
		TF_uroughness.properties + \
		TF_vroughness.properties
	
	def get_paramset(self, material):
		roughglass_params = ParamSet()
		
		roughglass_params.update( TF_cauchyb.get_paramset(self) )
		roughglass_params.update( TF_index.get_paramset(self) )
		roughglass_params.update( TC_Kr.get_paramset(self) )
		roughglass_params.update( TC_Kt.get_paramset(self) )
		roughglass_params.update( TF_uroughness.get_paramset(self) )
		roughglass_params.update( TF_vroughness.get_paramset(self) )
		
		return roughglass_params
	
	def load_paramset(self, ps):
		#psi_accept = {
		#}
		#psi_accept_keys = psi_accept.keys()
		#for psi in ps:
		#	if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
		#		setattr(self, psi['name'], psi['value'])
		
		TF_cauchyb.load_paramset(self, ps)
		TF_index.load_paramset(self, ps)
		TC_Kr.load_paramset(self, ps)
		TC_Kt.load_paramset(self, ps)
		TF_uroughness.load_paramset(self, ps)
		TF_vroughness.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_glossy(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'multibounce'
	] + \
		TC_Kd.controls + \
		TF_d.controls + \
		TC_Ka.controls + \
	[
		'useior',
		'draw_ior_menu',
	] + \
		TF_index.controls + \
		TC_Ks.controls + \
		TF_uroughness.controls + \
		TF_vroughness.controls
	
	
	visibility = dict_merge(
		{
			'draw_ior_menu': { 'useior': True }
		},
		TF_d.visibility,
		TF_index.visibility,
		TC_Ka.visibility,
		TC_Kd.visibility,
		TC_Ks.visibility,
		TF_uroughness.visibility,
		TF_vroughness.visibility,
		{
			'alpha_source': { 'transparent': True }
		},
		TF_alpha.visibility
	)
	
	visibility = texture_append_visibility(visibility, TC_Ks, { 'useior': False })
	visibility = texture_append_visibility(visibility, TF_index, { 'useior': True })
	visibility = texture_append_visibility(visibility, TF_alpha, { 'transparent': True, 'alpha_source': 'separate' })
	
	properties = [
		{
			'type': 'ef_callback',
			'attr': 'draw_ior_menu',
			'method': 'draw_ior_menu',
		},
		{
			'type': 'bool',
			'attr': 'multibounce',
			'name': 'Multibounce',
			'description': 'Enable surface layer multi-bounce',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'useior',
			'name': 'Use IOR',
			'description': 'Use IOR/Reflective index input',
			'default': False,
			'save_in_preset': True
		},
	] + \
		TF_d.properties + \
		TF_index.properties + \
		TC_Ka.properties + \
		TC_Kd.properties + \
		TC_Ks.properties + \
		TF_uroughness.properties + \
		TF_vroughness.properties + \
		TF_alpha.properties
	
	def get_paramset(self, material):
		glossy_params = ParamSet()
		
		glossy_params.add_bool('multibounce', self.multibounce)
		
		if self.d_floatvalue > 0:
			glossy_params.update( TF_d.get_paramset(self) )
			glossy_params.update( TC_Ka.get_paramset(self) )
		
		glossy_params.update( TC_Kd.get_paramset(self) )
		
		if self.useior:
			glossy_params.update( TF_index.get_paramset(self) )
			glossy_params.add_color('Ks', (1.0, 1.0, 1.0))
		else:
			glossy_params.update( TC_Ks.get_paramset(self) )
			glossy_params.add_float('index', 0.0)
			
		glossy_params.update( TF_uroughness.get_paramset(self) )
		glossy_params.update( TF_vroughness.get_paramset(self) )
		
		return glossy_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'multibounce': 'bool'
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])
		
		TF_d.load_paramset(self, ps)
		TF_index.load_paramset(self, ps)
		TC_Ka.load_paramset(self, ps)
		TC_Kd.load_paramset(self, ps)
		TC_Ks.load_paramset(self, ps)
		TF_uroughness.load_paramset(self, ps)
		TF_vroughness.load_paramset(self, ps)
		TF_alpha.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_glossy_lossy(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
	] + \
		TC_Kd.controls + \
		TF_d.controls + \
		TC_Ka.controls + \
	[
		'useior',
		'draw_ior_menu',
	] + \
		TF_index.controls + \
		TC_Ks.controls + \
		TF_uroughness.controls + \
		TF_vroughness.controls
	
	visibility = dict_merge(
		{
			'draw_ior_menu': { 'useior': True }
		},
		TF_d.visibility,
		TF_index.visibility,
		TC_Ka.visibility,
		TC_Kd.visibility,
		TC_Ks.visibility,
		TF_uroughness.visibility,
		TF_vroughness.visibility
	)
	
	visibility = texture_append_visibility(visibility, TC_Ks, { 'useior': False })
	visibility = texture_append_visibility(visibility, TF_index, { 'useior': True })
	
	properties = [
		{
			'type': 'ef_callback',
			'attr': 'draw_ior_menu',
			'method': 'draw_ior_menu',
		},
		{
			'type': 'bool',
			'attr': 'useior',
			'name': 'Use IOR',
			'description': 'Use IOR/Reflective index input',
			'default': False,
			'save_in_preset': True
		}
	] + \
		TC_Kd.properties + \
		TF_d.properties + \
		TC_Ka.properties + \
		TF_index.properties + \
		TC_Ks.properties + \
		TF_uroughness.properties + \
		TF_vroughness.properties
	
	def get_paramset(self, material):
		glossy_lossy_params = ParamSet()
		
		if self.d_floatvalue > 0:
			glossy_lossy_params.update( TF_d.get_paramset(self) )
			glossy_lossy_params.update( TC_Ka.get_paramset(self) )
		
		glossy_lossy_params.update( TC_Kd.get_paramset(self) )
		
		if self.useior:
			glossy_lossy_params.update( TF_index.get_paramset(self) )
			glossy_lossy_params.add_color('Ks', (1.0, 1.0, 1.0))
		else:
			glossy_lossy_params.update( TC_Ks.get_paramset(self) )
			glossy_lossy_params.add_float('index', 0.0)
			
		glossy_lossy_params.update( TF_uroughness.get_paramset(self) )
		glossy_lossy_params.update( TF_vroughness.get_paramset(self) )
		
		return glossy_lossy_params
	
	def load_paramset(self, ps):
		#psi_accept = {
		#}
		#psi_accept_keys = psi_accept.keys()
		#for psi in ps:
		#	if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
		#		setattr(self, psi['name'], psi['value'])
		
		TC_Kd.load_paramset(self, ps)
		TF_d.load_paramset(self, ps)
		TC_Ka.load_paramset(self, ps)
		TF_index.load_paramset(self, ps)
		TC_Ks.load_paramset(self, ps)
		TF_uroughness.load_paramset(self, ps)
		TF_vroughness.load_paramset(self, ps)
	
@LuxRenderAddon.addon_register_class
class luxrender_mat_matte(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
	] + \
		TC_Kd.controls + \
		TF_sigma.controls
	
	visibility = dict_merge(
		TC_Kd.visibility,
		TF_sigma.visibility
	)
	
	properties = [
	] + \
		TC_Kd.properties + \
		TF_sigma.properties
	
	def get_paramset(self, material):
		matte_params = ParamSet()
		
		matte_params.update( TC_Kd.get_paramset(self) )
		matte_params.update( TF_sigma.get_paramset(self) )
		
		return matte_params
	
	def load_paramset(self, ps):
		TC_Kd.load_paramset(self, ps)
		TF_sigma.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_mattetranslucent(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'energyconserving'
	] + \
		TC_Kr.controls + \
		TC_Kt.controls + \
		TF_sigma.controls
	
	visibility = dict_merge(
		TC_Kr.visibility,
		TC_Kt.visibility,
		TF_sigma.visibility
	)
	
	properties = [
		{
			'type': 'bool',
			'attr': 'energyconserving',
			'name': 'Energy conserving',
			'description': 'Force energy conservation with regards to reflection and transmission',
			'default': False
		},
	] + \
		TC_Kr.properties + \
		TC_Kt.properties + \
		TF_sigma.properties
	
	def get_paramset(self, material):
		mattetranslucent_params = ParamSet()
		
		mattetranslucent_params.add_bool('energyconserving', self.energyconserving)
		
		mattetranslucent_params.update( TC_Kr.get_paramset(self) )
		mattetranslucent_params.update( TC_Kt.get_paramset(self) )
		mattetranslucent_params.update( TF_sigma.get_paramset(self) )
		
		return mattetranslucent_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'energyconserving': 'bool'
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])
		
		TC_Kr.load_paramset(self, ps)
		TC_Kt.load_paramset(self, ps)
		TF_sigma.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_glossytranslucent(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'multibounce',
	] + \
		TC_Kt.controls + \
		TC_Kd.controls + \
		TF_d.controls + \
		TC_Ka.controls + \
	[
		'useior',
		'draw_ior_menu',
	] + \
		TF_index.controls + \
		TC_Ks.controls + \
		TF_uroughness.controls + \
		TF_vroughness.controls + \
	[
		'two_sided',
		'backface_multibounce',
	] + \
		TF_backface_d.controls + \
		TC_backface_Ka.controls + \
	[
		'bf_useior'
	] + \
		TF_backface_index.controls + \
		TC_backface_Ks.controls + \
		TF_backface_uroughness.controls + \
		TF_backface_vroughness.controls
	
	visibility = dict_merge(
		TC_Kt.visibility,
		TC_Kd.visibility,
		TF_d.visibility,
		TC_Ka.visibility,
		TF_index.visibility,
		TC_Ks.visibility,
		TF_uroughness.visibility,
		TF_vroughness.visibility,
		
		TF_backface_d.visibility,
		TC_backface_Ka.visibility,
		TC_backface_Kd.visibility,
		TF_backface_index.visibility,
		TC_backface_Ks.visibility,
		TF_backface_uroughness.visibility,
		TF_backface_vroughness.visibility,
		{
			'draw_ior_menu':			{ 'useior': True },
			'backface_multibounce':	{ 'two_sided': True },
			'bf_useior': 			{ 'two_sided': True }
		}
	)
	
	visibility = texture_append_visibility(visibility, TC_Ks,					{ 'useior': False })
	visibility = texture_append_visibility(visibility, TF_index,				{ 'useior': True  })
	visibility = texture_append_visibility(visibility, TC_backface_Ka,			{ 'two_sided': True })
	visibility = texture_append_visibility(visibility, TC_backface_Kd,			{ 'two_sided': True })
	visibility = texture_append_visibility(visibility, TF_backface_d,			{ 'two_sided': True })
	visibility = texture_append_visibility(visibility, TF_backface_uroughness,	{ 'two_sided': True })
	visibility = texture_append_visibility(visibility, TF_backface_vroughness,	{ 'two_sided': True })
	visibility = texture_append_visibility(visibility, TC_backface_Ks,			{ 'two_sided': True, 'bf_useior': False })
	visibility = texture_append_visibility(visibility, TF_backface_index,		{ 'two_sided': True, 'bf_useior': True  })
	
	properties = [
		{
			'type': 'ef_callback',
			'attr': 'draw_ior_menu',
			'method': 'draw_ior_menu',
		},
		{
			'type': 'bool',
			'attr': 'multibounce',
			'name': 'Multibounce',
			'description': 'Enable surface layer multi-bounce',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'two_sided',
			'name': 'Two sided',
			'description': 'Different surface properties for back-face and front-face',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'backface_multibounce',
			'name': 'Backface Multibounce',
			'description': 'Enable back-surface layer multi-bounce',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'useior',
			'name': 'Use IOR',
			'description': 'Use IOR/Reflective index input',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'bf_useior',
			'name': 'Backface use IOR',
			'description': 'Use IOR/Reflective index input',
			'default': False,
			'save_in_preset': True
		}
	] + \
		TC_Kt.properties + \
		TC_Kd.properties + \
		TF_d.properties + \
		TC_Ka.properties + \
		TF_index.properties + \
		TC_Ks.properties + \
		TF_uroughness.properties + \
		TF_vroughness.properties + \
		TF_backface_d.properties + \
		TC_backface_Ka.properties + \
		TF_backface_index.properties + \
		TC_backface_Ks.properties + \
		TF_backface_uroughness.properties + \
		TF_backface_vroughness.properties
		
	def get_paramset(self, material):
		glossytranslucent_params = ParamSet()
		
		if self.d_floatvalue > 0:
			glossytranslucent_params.update( TF_d.get_paramset(self) )
			glossytranslucent_params.update( TC_Ka.get_paramset(self) )
		
		glossytranslucent_params.add_bool('onesided', not self.two_sided)
		glossytranslucent_params.add_bool('multibounce', self.multibounce)
		
		glossytranslucent_params.update( TC_Kt.get_paramset(self) )
		glossytranslucent_params.update( TC_Kd.get_paramset(self) )
		
		if self.useior:
			glossytranslucent_params.update( TF_index.get_paramset(self) )
			glossytranslucent_params.add_color('Ks', (1.0, 1.0, 1.0))
		else:
			glossytranslucent_params.update( TC_Ks.get_paramset(self) )
			glossytranslucent_params.add_float('index', 0.0)
			
		glossytranslucent_params.update( TF_uroughness.get_paramset(self) )
		glossytranslucent_params.update( TF_vroughness.get_paramset(self) )
		
		if self.two_sided:
			glossytranslucent_params.add_bool('backface_multibounce', self.backface_multibounce)
			
			if self.bf_d_floatvalue > 0:
				glossytranslucent_params.update( TF_backface_d.get_paramset(self) )
				glossytranslucent_params.update( TC_backface_Ka.get_paramset(self) )
			
			if self.bf_useior:
				glossytranslucent_params.update( TF_backface_index.get_paramset(self) )
				glossytranslucent_params.add_color('backface_Ks', (1.0, 1.0, 1.0))
			else:
				glossytranslucent_params.update( TC_backface_Ks.get_paramset(self) )
				glossytranslucent_params.add_float('backface_index', 0.0)
			
			glossytranslucent_params.update( TF_backface_uroughness.get_paramset(self) )
			glossytranslucent_params.update( TF_backface_vroughness.get_paramset(self) )
		
		return glossytranslucent_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'multibounce': 'bool',
			'backface_multibounce': 'bool',
			'onesided': 'bool'
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])
		
		TC_Kt.load_paramset(self, ps)
		TC_Kd.load_paramset(self, ps)
		TF_d.load_paramset(self, ps)
		TC_Ka.load_paramset(self, ps)
		TF_index.load_paramset(self, ps)
		TC_Ks.load_paramset(self, ps)
		TF_uroughness.load_paramset(self, ps)
		TF_vroughness.load_paramset(self, ps)
		TF_backface_d.load_paramset(self, ps)
		TC_backface_Ka.load_paramset(self, ps)
		TF_backface_index.load_paramset(self, ps)
		TC_backface_Ks.load_paramset(self, ps)
		TF_backface_uroughness.load_paramset(self, ps)
		TF_backface_vroughness.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_metal(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'name',
		'filename',
	] + \
		TF_uroughness.controls + \
		TF_vroughness.controls
	
	visibility = dict_merge({
			'filename':	{ 'name': 'nk' }
		},
		TF_uroughness.visibility,
		TF_vroughness.visibility
	)
	
	properties = [
		{
			'type': 'enum',
			'attr': 'name',
			'name': 'Preset',
			'items': [
				('nk', 'Use nk File', 'nk'),
				('amorphous carbon', 'amorphous carbon', 'amorphous carbon'),
				('copper', 'copper', 'copper'),
				('gold', 'gold', 'gold'),
				('silver', 'silver', 'silver'),
				('aluminium', 'aluminium', 'aluminium')
			],
			'save_in_preset': True
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'filename',
			'name': 'NK file',
			'save_in_preset': True
		},
	] + \
		TF_uroughness.properties + \
		TF_vroughness.properties
	
	def get_paramset(self, material):
		metal_params = ParamSet()
		
		metal_params.update( TF_uroughness.get_paramset(self) )
		metal_params.update( TF_vroughness.get_paramset(self) )
		
		if self.name == 'nk':	# use an NK data file
			if material.library is not None:
				nk_path = bpy.path.abspath(self.filename, material.library.filepath)
			else:
				nk_path = self.filename
			metal_params.add_string('filename', efutil.path_relative_to_export(nk_path) )
		else:					# use a preset name
			metal_params.add_string('name', self.name)
		
		return metal_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'name': 'string',
			'filename': 'string'
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])
		
		TF_uroughness.load_paramset(self, ps)
		TF_vroughness.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_scatter(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
	] + \
		TC_Kd.controls + \
		TF_g.controls
	
	visibility = dict_merge(
		TC_Kd.visibility,
		TF_g.visibility
	)
	
	properties = [
	] + \
		TC_Kd.properties + \
		TF_g.properties
	
	def get_paramset(self, material):
		scatter_params = ParamSet()
		
		scatter_params.update( TC_Kd.get_paramset(self) )
		scatter_params.update( TF_g.get_paramset(self) )
		
		return scatter_params
	
	def load_paramset(self, ps):
		#psi_accept = {
		#}
		#psi_accept_keys = psi_accept.keys()
		#for psi in ps:
		#	if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
		#		setattr(self, psi['name'], psi['value'])
		
		TC_Kd.load_paramset(self, ps)
		TF_g.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_shinymetal(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
	] + \
		TF_film.controls + \
		TF_filmindex.controls + \
		TC_Kr.controls + \
		TC_Ks.controls + \
		TF_uroughness.controls + \
		TF_vroughness.controls
	
	visibility = dict_merge(
		TF_film.visibility,
		TF_filmindex.visibility,
		TC_Kr.visibility,
		TC_Ks.visibility,
		TF_uroughness.visibility,
		TF_vroughness.visibility
	)
	
	properties = [
	] + \
		TF_film.properties + \
		TF_filmindex.properties + \
		TC_Kr.properties + \
		TC_Ks.properties + \
		TF_uroughness.properties + \
		TF_vroughness.properties
	
	def get_paramset(self, material):
		shinymetal_params = ParamSet()
		
		shinymetal_params.update( TF_film.get_paramset(self) )
		shinymetal_params.update( TF_filmindex.get_paramset(self) )
		shinymetal_params.update( TC_Kr.get_paramset(self) )
		shinymetal_params.update( TC_Ks.get_paramset(self) )
		shinymetal_params.update( TF_uroughness.get_paramset(self) )
		shinymetal_params.update( TF_vroughness.get_paramset(self) )
		
		return shinymetal_params
	
	def load_paramset(self, ps):
		#psi_accept = {
		#}
		#psi_accept_keys = psi_accept.keys()
		#for psi in ps:
		#	if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
		#		setattr(self, psi['name'], psi['value'])
		
		TF_film.load_paramset(self, ps)
		TF_filmindex.load_paramset(self, ps)
		TC_Kr.load_paramset(self, ps)
		TC_Ks.load_paramset(self, ps)
		TF_uroughness.load_paramset(self, ps)
		TF_vroughness.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_mirror(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
	] + \
		TF_film.controls + \
		TF_filmindex.controls + \
		TC_Kr.controls
	
	visibility = dict_merge(
		TF_film.visibility,
		TF_filmindex.visibility,
		TC_Kr.visibility
	)
	
	properties = [
	] + \
		TF_film.properties + \
		TF_filmindex.properties + \
		TC_Kr.properties
	
	def get_paramset(self, material):
		mirror_params = ParamSet()
		
		mirror_params.update( TF_film.get_paramset(self) )
		mirror_params.update( TF_filmindex.get_paramset(self) )
		mirror_params.update( TC_Kr.get_paramset(self) )
		
		return mirror_params
	
	def load_paramset(self, ps):
		#psi_accept = {
		#}
		#psi_accept_keys = psi_accept.keys()
		#for psi in ps:
		#	if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
		#		setattr(self, psi['name'], psi['value'])
		
		TF_film.load_paramset(self, ps)
		TF_filmindex.load_paramset(self, ps)
		TC_Kr.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_mix(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = [
		'namedmaterial1',
		'namedmaterial2',
	] + \
		TF_amount.controls
	
	visibility = TF_amount.visibility
	
	properties = [
	] + \
		TF_amount.properties + \
		MaterialParameter('namedmaterial1', 'Material 1', 'luxrender_mat_mix') + \
		MaterialParameter('namedmaterial2', 'Material 2', 'luxrender_mat_mix')
	
	def get_paramset(self, material):
		mix_params = ParamSet()
		
		mix_params.add_string('namedmaterial1', self.namedmaterial1_material)
		mix_params.add_string('namedmaterial2', self.namedmaterial2_material)
		mix_params.update( TF_amount.get_paramset(self) )
		
		return mix_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'namedmaterial1': 'string',
			'namedmaterial2': 'string'
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, '%s_material'%psi['name'], psi['value'])
		
		TF_amount.load_paramset(self, ps)

@LuxRenderAddon.addon_register_class
class luxrender_mat_null(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = []
	visibility = {}
	properties = []
	
	def get_paramset(self, material):
		return ParamSet()
	
	def load_paramset(self, ps):
		pass

@LuxRenderAddon.addon_register_class
class luxrender_mat_velvet(declarative_property_group):
	ef_attach_to = ['luxrender_material']
	
	controls = TC_Kd.controls + [
		'thickness',
		'advanced',
		'p1', 'p2', 'p3',
	]
	
	visibility = dict_merge({
		'p1':	{ 'advanced': True },
		'p2':	{ 'advanced': True },
		'p3':	{ 'advanced': True },
	}, TC_Kd.visibility)
	
	properties = TC_Kd.properties + [
		{
			'type': 'bool',
			'attr': 'advanced',
			'name': 'Advanced',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'thickness',
			'name': 'Thickness',
			'default': 0.1,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'p1',
			'name': 'p1',
			'default': -2.0,
			'min': -100.0,
			'soft_min': -100.0,
			'max': 100.0,
			'soft_max': 100.0,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'p2',
			'name': 'p2',
			'default': 10.0,
			'min': -100.0,
			'soft_min': -100.0,
			'max': 100.0,
			'soft_max': 100.0,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'p3',
			'name': 'p3',
			'default': 2.0,
			'min': -100.0,
			'soft_min': -100.0,
			'max': 100.0,
			'soft_max': 100.0,
			'save_in_preset': True
		},
	]
	
	def get_paramset(self, material):
		velvet_params = ParamSet()
		
		velvet_params.update( TC_Kd.get_paramset(self) )
		
		velvet_params.add_float('thickness', self.thickness)
		if self.advanced:
			velvet_params.add_float('p1', self.p1)
			velvet_params.add_float('p2', self.p2)
			velvet_params.add_float('p3', self.p3)
		
		return velvet_params
	
	def load_paramset(self, ps):
		psi_accept = {
			'thickness': 'float',
			'p1': 'float',
			'p2': 'float',
			'p3': 'float',
		}
		psi_accept_keys = psi_accept.keys()
		for psi in ps:
			if psi['name'] in psi_accept_keys and psi['type'].lower() == psi_accept[psi['name']]:
				setattr(self, psi['name'], psi['value'])
		
		TC_Kd.load_paramset(self, ps)

class EmissionColorTextureParameter(ColorTextureParameter):
	def texture_slot_set_attr(self):
		# Looks in a different location than other ColorTextureParameters
		return lambda s,c: c.luxrender_emission

TC_L = EmissionColorTextureParameter('L', 'Emission color', default=(1.0,1.0,1.0) )

@LuxRenderAddon.addon_register_class
class luxrender_emission(declarative_property_group):
	'''
	Storage class for LuxRender Material emission settings.
	'''
	
	ef_attach_to = ['Material']
	
	controls = [
		#'use_emission', # drawn in header
		'lightgroup',
	] + \
	TC_L.controls + \
	[
		'gain',
		'power',
		'efficacy',
	]
	
	visibility = {
		'lightgroup': 			{ 'use_emission': True },
		'L_colorlabel': 		{ 'use_emission': True },
		'L_color': 				{ 'use_emission': True },
		'L_usecolortexture':	{ 'use_emission': True },
		'L_colortexture':		{ 'use_emission': True, 'L_usecolortexture': True },
		'L_multiplycolor':		{ 'use_emission': True, 'L_usecolortexture': True },
		'gain': 				{ 'use_emission': True },
		'power': 				{ 'use_emission': True },
		'efficacy': 			{ 'use_emission': True },
	}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'use_emission',
			'name': 'Use Emission',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'string',
			'attr': 'lightgroup',
			'name': 'Light Group',
			'default': 'default',
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'gain',
			'name': 'Gain',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e8,
			'soft_max': 1e8,
			'precision': 6,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'power',
			'name': 'Power',
			'default': 100.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e5,
			'soft_max': 1e5,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'efficacy',
			'name': 'Efficacy',
			'default': 17.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1e4,
			'soft_max': 1e4,
			'save_in_preset': True
		},
	] + \
	TC_L.properties
	
	def api_output(self):
		arealightsource_params = ParamSet() \
				.add_float('gain', self.gain) \
				.add_float('power', self.power) \
				.add_float('efficacy', self.efficacy)
		arealightsource_params.update( TC_L.get_paramset(self) )
		return 'area', arealightsource_params

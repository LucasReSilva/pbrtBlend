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
from luxrender.ui.textures import ParamTextureFloat

def ParamMaterial(attr, name, descr, property_group):
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
			'name': descr
		},
	]

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
		
		# Mix Material,
		'amount',
		'namedmaterial1',
		'namedmaterial2',
	]
	
	visibility = {
		# Mix Material
		'amount':                 { 'material': 'mix' },
		'namedmaterial1':         { 'material': 'mix' },
		'namedmaterial2':         { 'material': 'mix' },
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
			],
		},
	] + \
	ParamTextureFloat('amount', 'Amount', 'Mix Amount', 'luxrender_material', type='COMPACT') + \
	ParamMaterial('namedmaterial1', 'Material 1', 'First Material', 'luxrender_material') + \
	ParamMaterial('namedmaterial2', 'Material 2', 'Second Material', 'luxrender_material')
	

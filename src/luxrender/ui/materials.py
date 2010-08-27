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
from ef.ui import property_group_renderer
from ef.ef import init_properties

# Lux API
from luxrender.properties.material import luxrender_material, luxrender_emission

class _lux_material_base(MaterialButtonsPanel, property_group_renderer):
	COMPAT_ENGINES = {'luxrender'}
	
	object_property_groups = [
		luxrender_emission,
		luxrender_material,
	]
	
	@classmethod
	def property_reload(cls):
		for mat in bpy.data.materials:
			cls.property_create(mat)
	
	@classmethod
	def property_create(cls, mat):
		for property_group in cls.object_property_groups:
			if not hasattr(mat, property_group.__name__):
				init_properties(mat, [{
					'type': 'pointer',
					'attr': property_group.__name__,
					'ptype': property_group,
					'name': property_group.__name__,
					'description': property_group.__name__
				}], cache=False)
				init_properties(property_group, property_group.properties, cache=False)
	
	# Overridden to provide data storage in the material, not the scene
	def draw(self, context):
		if context.material is not None:
			self.property_create(context.material)
			
			# Set the integrator type in this material in order to show compositing options 
			context.material.luxrender_material.integrator_type = context.scene.luxrender_integrator.surfaceintegrator
			
			for property_group_name in self.display_property_groups:
				property_group = getattr(context.material, property_group_name)
				for p in property_group.controls:
					self.draw_column(p, self.layout, context.material, supercontext=context, property_group=property_group)

class material_editor(_lux_material_base, bpy.types.Panel):
	'''
	Material Editor UI Panel
	'''
	
	bl_label = 'LuxRender Materials'
	
	display_property_groups = [
		'luxrender_material',
	]

class material_emission(_lux_material_base, bpy.types.Panel):
	'''
	Material Emission Settings
	'''
	
	bl_label = 'LuxRender Material Emission'
	
	display_property_groups = [
		'luxrender_emission',
	]

class material_volumes(MaterialButtonsPanel, property_group_renderer, bpy.types.Panel):
	bl_label = 'LuxRender Material Volumes'
	COMPAT_ENGINES = {'luxrender'}
	
	display_property_groups = [
		'luxrender_volumes'
	]
	
	# overridden in order to draw selected luxrender_volume_data property group
	def draw(self, context):
		super().draw(context)
		if len(context.scene.luxrender_volumes.volumes) > 0:
			current_vol_ind = context.scene.luxrender_volumes.volumes_index
			current_vol = context.scene.luxrender_volumes.volumes[current_vol_ind]
			# 'name' is not a member of current_vol.properties,
			# so we draw it explicitly
			self.layout.prop(
				current_vol, 'name'
			)
			# Here we use a combined (IDPropertyGroup, described_layout) object
			# that can draw itself to the layout of this panel.
			for control in current_vol.controls:
				self.draw_column(
					control,
					self.layout,
					current_vol,
					current_vol,
					property_group = current_vol
				)

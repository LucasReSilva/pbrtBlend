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
from properties_data_mesh import MeshButtonsPanel 

# EF API
from ef.ui import described_layout
from ef.ef import ef

# Lux API
import luxrender.properties.mesh

class meshes(MeshButtonsPanel, described_layout, bpy.types.Panel):
	bl_label = 'LuxRender Mesh Options'
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender.properties.mesh.luxrender_mesh

	# prevent creating luxrender_material property group in Scene
	property_group_non_global = True

	@staticmethod
	def property_reload():
		for mesh in bpy.data.meshes:
			meshes.property_create(mesh)
	
	@staticmethod
	def property_create(mesh):
		if not hasattr(mesh, meshes.property_group.__name__):
			ef.init_properties(mesh, [{
				'type': 'pointer',
				'attr': meshes.property_group.__name__,
				'ptype': meshes.property_group,
				'name': meshes.property_group.__name__,
				'description': meshes.property_group.__name__
			}], cache=False)
			ef.init_properties(meshes.property_group, meshes.properties, cache=False)
	
	# Overridden to provide data storage in the lamp, not the scene
	def draw(self, context):
		if context.mesh is not None:

			# LuxRender properties
			for p in self.controls:
				self.draw_column(p, self.layout, context.mesh, supercontext=context)
	
	# luxrender properties
	controls = [
		'portal',
		['subdiv','sublevels'],
		['nsmooth', 'sharpbound'],
	]
	
	visibility = {
		
		'nsmooth':		{ 'subdiv': True },
		'sharpbound':	{ 'subdiv': True },
		'sublevels':	{ 'subdiv': True }
	}
	
	properties = [
		{
			'type': 'bool',
			'attr': 'portal',
			'name': 'Exit Portal',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'subdiv',
			'name': 'Use Subdivision',
			'default': False,
		},
		{
			'type': 'bool',
			'attr': 'nsmooth',
			'name': 'Use Autosmoothing',
			'default': True,
		},
		{
			'type': 'bool',
			'attr': 'sharpbound',
			'name': 'Sharpen Bounds',
			'default': False,
		},
		{
			'type': 'int',
			'attr': 'sublevels',
			'name': 'Subdivision Levels',
			'default': 2,
			'min': 0,
			'soft_min': 0,
			'max': 15,
			'soft_max': 15
		},
	]


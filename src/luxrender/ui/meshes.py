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
from ef.ui import property_group_renderer
from ef.ef import init_properties

# Lux API
from luxrender.properties.mesh import luxrender_mesh

class meshes(MeshButtonsPanel, property_group_renderer, bpy.types.Panel):
	bl_label = 'LuxRender Mesh Options'
	COMPAT_ENGINES = {'luxrender'}
	
	display_property_groups = [
		'luxrender_mesh',
	]
	
	# Overridden to draw property groups from mesh object, not the scene
	def draw(self, context):
		if context.mesh is not None:
			
			for property_group_name in self.display_property_groups:
				property_group = getattr(context.mesh, property_group_name)
				for p in property_group.controls:
					self.draw_column(p, self.layout, context.mesh, supercontext=context, property_group=property_group)

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
import bpy

from properties_data_camera import CameraButtonsPanel

# EF API
from ef.ui import property_group_renderer
from ef.ef import init_properties

from luxrender.properties.camera import luxrender_camera, luxrender_colorspace, luxrender_tonemapping

class camera_panel(CameraButtonsPanel, property_group_renderer):
	COMPAT_ENGINES = {'luxrender'}
	
	# Overridden to draw property groups from camera object, not the scene
	def draw(self, context):
		if context.camera is not None:
			
			# Show only certain controls for Blender's perspective camera type 
			context.camera.luxrender_camera.is_perspective = (context.camera.type == 'PERSP')
			
			for property_group_name in self.display_property_groups:
				property_group = getattr(context.camera, property_group_name)
				for p in property_group.controls:
					self.draw_column(p, self.layout, context.camera, supercontext=context, property_group=property_group)

class camera(camera_panel, bpy.types.Panel):
	bl_label = 'LuxRender Camera'
	
	display_property_groups = [
		'luxrender_camera'
	]
	

class colorspace(camera_panel, bpy.types.Panel):
	bl_label = 'LuxRender Colour Space'
	
	display_property_groups = [
		'luxrender_colorspace'
	]
	

class tonemapping(camera_panel, bpy.types.Panel):
	bl_label = 'LuxRender ToneMapping'
	
	display_property_groups = [
		'luxrender_tonemapping'
	]

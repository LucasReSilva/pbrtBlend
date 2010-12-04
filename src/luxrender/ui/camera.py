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
#
import bpy

from properties_data_camera import CameraButtonsPanel

from extensions_framework.ui import property_group_renderer

class camera_panel(CameraButtonsPanel, property_group_renderer):
	COMPAT_ENGINES = {'luxrender'}
	
class camera(camera_panel, bpy.types.Panel):
	bl_label = 'LuxRender Camera'
	
	display_property_groups = [
		( ('camera',), 'luxrender_camera' )
	]
	

class colorspace(camera_panel, bpy.types.Panel):
	bl_label = 'LuxRender Colour Space'
	
	display_property_groups = [
		( ('camera',), 'luxrender_colorspace' )
	]
	

class tonemapping(camera_panel, bpy.types.Panel):
	bl_label = 'LuxRender ToneMapping'
	
	display_property_groups = [
		( ('camera',), 'luxrender_tonemapping' )
	]

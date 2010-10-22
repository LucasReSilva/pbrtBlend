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
from properties_material import MaterialButtonsPanel

from addon_framework.ui import property_group_renderer

class luxrender_material_base(MaterialButtonsPanel, property_group_renderer):
	COMPAT_ENGINES	= {'luxrender'}

class luxrender_material_sub(MaterialButtonsPanel, property_group_renderer):
	#bl_options		= {'HIDE_HEADER'}
	COMPAT_ENGINES	= {'luxrender'}
	LUX_COMPAT		= set()
	
	@classmethod
	def poll(cls, context):
		'''
		Only show LuxRender panel if luxrender_material.material in LUX_COMPAT
		'''
		
		return super().poll(context) and context.material.luxrender_material.type in cls.LUX_COMPAT

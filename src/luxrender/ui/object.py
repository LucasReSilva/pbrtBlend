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

from properties_object import ObjectButtonsPanel

from extensions_framework.ui import property_group_renderer

class object(ObjectButtonsPanel, property_group_renderer, bpy.types.Panel):
	'''
	Object settings
	'''
	
	bl_label = 'LuxRender Object Settings'
	COMPAT_ENGINES = {'luxrender'}
	
	@classmethod
	def poll(cls, context):
		engine = context.scene.render.engine
		return context.object and context.object.type in ['MESH','SURFACE','FONT'] and (engine in cls.COMPAT_ENGINES)
	
	display_property_groups = [
		( ('object',), 'luxrender_object' )
	]


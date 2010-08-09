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

class luxrender_volume_data(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender volume data. The
	luxrender_world object will store 1 or more of
	these in its CollectionProperty 'volumes'
	'''
	
	p1 = bpy.props.StringProperty(
		name = 'Prop1',
		description = 'Prop1 Descr.',
	)

class luxrender_world(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender World settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	pass
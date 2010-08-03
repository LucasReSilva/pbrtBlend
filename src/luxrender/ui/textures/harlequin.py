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

from ...export import ParamSet
from ..textures import luxrender_texture_base

class harlequin(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		harlequin_params = ParamSet()
		
		return set(), harlequin_params

class ui_panel_harlequin(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender harlequin Texture'
	
	LUX_COMPAT = {'harlequin'}
	
	property_group = harlequin
	
	controls = [
		# None
	]
	
	visibility = {} 
	
	properties = [
		{
			'attr': 'variant',
			'type': 'string',
			'default': 'color'
		},
	]

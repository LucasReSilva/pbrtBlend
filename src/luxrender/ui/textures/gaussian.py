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

from luxrender.export import ParamSet
from luxrender.ui.textures import luxrender_texture_base

class gaussian(bpy.types.IDPropertyGroup):
	
	def get_paramset(self):
		
		return set(), ParamSet().add_float('energy', self.energy) \
								.add_float('wavelength', self.wavelength) \
								.add_float('width', self.width)

class ui_panel_gaussian(luxrender_texture_base, bpy.types.Panel):
	bl_label = 'LuxRender Gaussian Texture'
	
	LUX_COMPAT = {'gaussian'}
	
	property_group = gaussian
	
	controls = [
		'energy',
		'wavelength',
		'width',
	]
	
	visibility = {}
	
	properties = [
		{
			'type': 'string',
			'attr': 'variant',
			'default': 'color'
		},
		{
			'type': 'float',
			'attr': 'energy',
			'name': 'Energy',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 1.0,
			'soft_max': 1.0
		},
		{
			'type': 'float',
			'attr': 'wavelength',
			'name': 'Wavelength (nm)',
			'default': 550.0,
			'min': 380.0,
			'soft_min': 380.0,
			'max': 720.0,
			'soft_max': 720.0,
		},
		{
			'type': 'float',
			'attr': 'width',
			'name': 'Width (nm)',
			'default': 50.0,
			'min': 20.0,
			'soft_min': 20.0,
			'max': 300.0,
			'soft_max': 300.0,
		},
	]
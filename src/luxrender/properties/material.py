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

from ef.validate import Logic_OR as O

def material_property_map():
	'''
	Refer to http://www.luxrender.net/static/materials-parameters.xhtml
	for contents of this mapping
	'''
	
	return {
		'amount':			O(['mix']),
		'architectural':	O(['glass', 'glass2']),
		'bumpmap':			O(['carpaint', 'glass', 'glass2', 'glossy_lossy', 'glossy', 'matte', 'mattetranslucent', 'metal', 'mirror', 'roughglass', 'shinymetal']),
		'cauchyb':			O(['glass', 'roughglass']),
		'd':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'dispersion':		O(['glass2']),
		'film':				O(['glass', 'mirror', 'shinymetal']),
		'filmindex':		O(['glass', 'mirror', 'shinymetal']),
		'index':			O(['glass', 'glossy_lossy', 'glossy', 'roughglass']),
		'Ka':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'Kd':				O(['carpaint', 'glossy_lossy', 'glossy', 'matte']),
		'Kr':				O(['glass', 'mattetranslucent', 'mirror', 'roughglass', 'shinymetal']),
		'Ks':				O(['glossy_lossy', 'glossy', 'shinymetal']),
		'Ks1':				O(['carpaint']),
		'Ks2':				O(['carpaint']),
		'Ks3':				O(['carpaint']),
		'Kt':				O(['glass', 'mattetranslucent', 'roughglass']),
		'M1':				O(['carpaint']),
		'M2':				O(['carpaint']),
		'M3':				O(['carpaint']),
		'name':				O(['carpaint', 'metal']),
		'namedmaterial1':	O(['mix']),
		'namedmaterial2':	O(['mix']),
		'R1':				O(['carpaint']),
		'R2':				O(['carpaint']),
		'R3':				O(['carpaint']),
		'sigma':			O(['matte', 'mattetranslucent']),
		'uroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
		'vroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
	}
	
def has_material_property(property_name):
	return material_property_map()[property_name]

class luxrender_material(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender Material settings.
	This class will be instantiated within a Blender Material
	object.
	'''
	
	pass

class luxrender_emission(bpy.types.IDPropertyGroup):
	'''
	Storage class for LuxRender Material emission settings.
	This class will be instantiated within a Blender Material
	object.
	'''
	
	pass

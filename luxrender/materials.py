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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
class materials():
	# This render engine's UI display name
	__label__ = 'LuxRender'
	
	# This should match the engine __main__ class name,
	# and is used to detect if the UI should draw engine-
	# specific panels etc.
	context_name = 'luxrender'
	
	all_properties = []
	
	@classmethod
	def get_all_properties(r_class):
		for s in [	r_class.materials,
				]:
			for p in s:
				r_class.all_properties.append(p)
		
		return r_class.all_properties
	
	materials_layout = [
		'lux_material'
	]
	
	materials = [
		{
			'type': 'enum',
			'attr': 'lux_material',
			'name': 'Type',
			'description': 'LuxRender material type',
			'items': [
				('carpaint', 'Car Paint', 'carpaint'),
				('glass', 'Glass', 'glass'),
				('roughglass','Rough Glass','roughglass'),
				('glossy','Glossy','glossy'),
				('matte','Matte','matte'),
				('mattetranslucent','Matte Translucent','mattetranslucent'),
				('metal','Metal','metal'),
				('shinymetal','Shiny Metal','shinymetal'),
				('mirror','Mirror','mirror'),
				('mix','Mix','mix'),
				('null','Null','null'),
				('boundvolume','Bound Volume','boundvolume'),
				('light','Light','light'),
				('portal','Portal','portal'),
			]
		}
	]

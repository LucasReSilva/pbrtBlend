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
from ef import declarative_property_group

from luxrender.properties import dbo
from luxrender.export import ParamSet

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

class luxrender_volumeintegrator(declarative_property_group):
	'''
	Storage class for LuxRender Volume Integrator settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	controls = [
		'volumeintegrator', 'stepsize'
	]
	
	properties = [
		{
			'type': 'enum',
			'attr': 'volumeintegrator',
			'name': 'Volume Integrator',
			'description': 'Volume Integrator',
			'default': 'single',
			'items': [
				('emission', 'Emission', 'emission'),
				('single', 'Single', 'single'),
			],
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'stepsize',
			'name': 'Step Size',
			'description': 'Volume Integrator Step Size',
			'default': 1.0,
			'min': 0.0,
			'soft_min': 0.0,
			'max': 100.0,
			'soft_max': 100.0,
			'save_in_preset': True
		}
	]
	
	def api_output(self):
		'''
		Format this class's members into a LuxRender ParamSet
		
		Returns dict
		'''
		
		params = ParamSet()
		
		params.add_float('stepsize', self.stepsize)
		
		out = self.volumeintegrator, params
		dbo('VOLUME INTEGRATOR', out)
		return out

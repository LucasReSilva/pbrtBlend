
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Michael Klemm
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
import math
import os

import bpy

from extensions_framework import util as efutil
from extensions_framework import declarative_property_group
from extensions_framework.validate import Logic_OR as O, Logic_AND as A

from .. import LuxRenderAddon
from ..export import get_worldscale, get_output_filename
from ..export import ParamSet, LuxManager
from ..export import fix_matrix_order
from ..outputs.pure_api import LUXRENDER_VERSION


@LuxRenderAddon.addon_register_class
class luxrender_hair(declarative_property_group):
	'''
	Storage class for LuxRender Hair Rendering settings.
	'''
	ef_attach_to = ['ParticleSettings']
	controls = ['hair_size',
				'use_binary_output',
				'resolution',
	]

	properties = [
		{
			'type': 'float',
			'attr': 'hair_size',
			'name': 'hair size',
			'description': 'Thickness of hair',
			'default': 0.00005,
			'min': 0.000001,
			'soft_min': 0.000001,
			'max': 1000.0,
			'soft_max': 1000.0,
			'precision': 3,
			'sub_type': 'DISTANCE',
			'unit': 'LENGTH',
		},
		{
			'type': 'bool',
			'attr': 'use_binary_output',
			'name': 'Use Binary output file',
			'description': 'Use binary hair description file for export',
			'default': False,
		},
		{
			'type': 'int',
			'attr': 'resolution',
			'name': 'Resolution of hair strand',
			'description': 'Resolution of hair strand (power of 2)',			
			'default': 3,
			'min': 1,
			'soft_min': 1,
			'max': 10,
			'soft_max': 10,
		},                
	]
			
            

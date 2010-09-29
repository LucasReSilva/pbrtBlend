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
from ef.validate import Logic_OR as O

from luxrender.properties import dbo
from luxrender.export import ParamSet

class luxrender_accelerator(declarative_property_group):
	'''
	Storage class for LuxRender Accelerator settings.
	This class will be instantiated within a Blender scene
	object.
	'''
	
	controls = [
		[0.7, 'accelerator', 'advanced'],
		
		'intersectcost',
		'traversalcost',
		'emptybonus'
		'treetype',
		'costsample',
		'maxprims',
		'maxdepth',
		'refineimmediately',
		'maxprimsperleaf',
		'fullsweepthreshold',
		'skipfactor',
	]
	
	visibility = {
		'intersectcost':		{ 'advanced': True, 'accelerator': O(['bvh', 'tabreckdtree']) },
		'traversalcost':		{ 'advanced': True, 'accelerator': O(['bvh', 'tabreckdtree']) },
		'emptybonus':			{ 'advanced': True, 'accelerator': O(['bvh', 'tabreckdtree']) },
		'treetype':				{ 'advanced': True, 'accelerator': 'bvh' },
		'costsample':			{ 'advanced': True, 'accelerator': 'bvh' },
		'maxprims':				{ 'advanced': True, 'accelerator': 'tabreckdtree' },
		'maxdepth':				{ 'advanced': True, 'accelerator': 'tabreckdtree' },
		'refineimmediately':	{ 'advanced': True, 'accelerator': 'grid' },
		'maxprimsperleaf':		{ 'advanced': True, 'accelerator': 'qbvh' },
		'fullsweepthreshold':	{ 'advanced': True, 'accelerator': 'qbvh' },
		'skipfactor':			{ 'advanced': True, 'accelerator': 'qbvh' },
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'accelerator',
			'name': 'Accelerator',
			'description': 'Scene accelerator type',
			'default': 'tabreckdtree',
			'items': [
				#('none', 'none', 'None'),
				#('bruteforce', 'bruteforce', 'bruteforce'),
				('tabreckdtree', 'KD Tree', 'tabreckdtree'),
				('grid', 'Grid', 'grid'),
				('bvh', 'BVH', 'bvh'),
				('qbvh', 'QBVH', 'qbvh'),
			]
		},
		{
			'attr': 'advanced',
			'type': 'bool',
			'name': 'Advanced',
			'default': False,
		},
		{
			'attr': 'intersectcost',
			'type': 'int',
			'name': 'Intersect Cost',
			'default': 80
		},
		{
			'attr': 'traversalcost',
			'type': 'int',
			'name': 'Traversal Cost',
			'default': 1
		},
		{
			'attr': 'emptybonus',
			'type': 'float',
			'name': 'Empty Bonus',
			'default': 0.2
		},
		{
			'attr': 'treetype',
			'type': 'enum',
			'name': 'Tree Type',
			'default': '2',
			'items': [
				('2', 'Binary', '2'),
				('4', 'Quad', '4'),
				('8', 'Oct', '8'),
			]
		},
		{
			'attr': 'costsample',
			'type': 'int',
			'name': 'Costsample',
			'default': 0
		},
		{
			'attr': 'maxprims',
			'type': 'int',
			'name': 'Max. Prims',
			'default': 1
		},
		{
			'attr': 'maxdepth',
			'type': 'int',
			'name': 'Max. depth',
			'default': -1
		},
		{
			'attr': 'refineimmediately',
			'type': 'bool',
			'name': 'Refine Immediately',
			'default': False
		},
		{
			'attr': 'maxprimsperleaf',
			'type': 'int',
			'name': 'Max. prims per leaf',
			'default': 4
		},
		{
			'attr': 'fullsweepthreshold',
			'type': 'int',
			'name': 'Full sweep threshold',
			'default': 16,
		},
		{
			'attr': 'skipfactor',
			'type': 'int',
			'name': 'Skip factor',
			'default': 1
		},
	]
	
	def api_output(self):
		'''
		Format this class's members into a LuxRender ParamSet
		
		Returns tuple
		'''
		
		params = ParamSet()
		
		if self.advanced:
			if self.accelerator == 'tabreckdtree':
				params.add_float('intersectcost', self.intersectcost)
				params.add_float('traversalcost', self.traversalcost)
				params.add_float('emptybonus', self.emptybonus)
				params.add_integer('maxprims', self.maxprims)
				params.add_integer('maxdepth', self.maxdepth)
			
			if self.accelerator == 'grid':
				params.add_bool('refineimmediately', self.refineimmediately)
			
			if self.accelerator == 'bvh':
				params.add_integer('treetype', self.treetype)
				params.add_integer('costsamples', self.costsamples)
				params.add_integer('intersectcost', self.intersectcost)
				params.add_integer('traversalcost', self.traversalcost)
				params.add_float('emptybonus', self.emptybonus)
			
			if self.accelerator == 'qbvh':
				params.add_integer('maxprimsperleaf', self.maxprimsperleaf)
				params.add_integer('fullsweepthreshold', self.fullsweepthreshold)
				params.add_integer('skipfactor', self.skipfactor)
		
		out = self.accelerator, params
		dbo('ACCELERATOR', out)
		return out

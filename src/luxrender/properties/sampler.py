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
from extensions_framework import declarative_property_group
from extensions_framework.validate import Logic_OR as O, Logic_AND as A

from .. import LuxRenderAddon
from ..export import ParamSet

@LuxRenderAddon.addon_register_class
class luxrender_sampler(declarative_property_group):
	'''
	Storage class for LuxRender Sampler settings.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		[ 0.7, 'sampler', 'advanced'],
		['haltspp','halttime'],
		
		'chainlength',
		
		'basesampler',
		'pixelsampler',
		'pixelsamples',
		
		'largemutationprob',
		#'mutationrange',
		'maxconsecrejects',
		'usevariance',
	]
	
	visibility = {
		'chainlength':			{ 'sampler': 'erpt' },
		'mutationrange':		{ 'advanced': True, 'sampler': O(['erpt', 'metropolis']) },
		'basesampler':			{ 'sampler': 'erpt' },
		'pixelsampler':			O([{ 'sampler': O(['lowdiscrepancy', 'random']) },			{'sampler':'erpt', 'basesampler':O(['lowdiscrepancy', 'random'])} ]),
		'pixelsamples':			O([{ 'sampler': O(['lowdiscrepancy', 'random']) },			{'sampler':'erpt', 'basesampler':O(['lowdiscrepancy', 'random'])} ]),
		'maxconsecrejects':		A([{ 'advanced': True }, O([{ 'sampler': 'metropolis' },	{'sampler':'erpt', 'basesampler': 'metropolis' } ]) ]),
		'largemutationprob':	O([{ 'sampler': 'metropolis' },								{'sampler':'erpt', 'basesampler': 'metropolis' } ]),
		'usevariance':			O([{ 'sampler': 'metropolis' },								{'sampler':'erpt', 'basesampler': 'metropolis' } ]),
	}
	
	properties = [
		{
			'type': 'enum',
			'attr': 'sampler',
			'name': 'Sampler Type',
			'description': 'Sampler Type',
			'default': 'metropolis',
			'items': [
				('metropolis', 'Metropolis', 'metropolis'),
				('erpt', 'ERPT', 'erpt'),
				('lowdiscrepancy', 'Low Discrepancy', 'lowdiscrepancy'),
				('random', 'Random', 'random')
			],
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'advanced',
			'name': 'Advanced',
			'description': 'Configure advanced sampler settings',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'haltspp',
			'name': 'Halt SPP',
			'description': 'Halt the rendering at this number of samples/px (0=disabled)',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 65535,
			'soft_max': 65535,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'halttime',
			'name': 'Halt time',
			'description': 'Halt the rendering at this number seconds (0=disabled)',
			'default': 0,
			'min': 0,
			'soft_min': 0,
			'max': 65535,
			'soft_max': 65535,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'largemutationprob',
			'name': 'Large Mutation Probability',
			'description': 'Large Mutation Probability',
			'default': 0.4,
			'min': 0,
			'max': 1,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'maxconsecrejects',
			'name': 'Max. Consecutive Rejections',
			'description': 'Maximum number of consecutive rejections',
			'default': 512,
			'min': 0,
			'max': 32768,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'usevariance',
			'name': 'Use Variance',
			'description': 'Use Variance',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'basesampler',
			'name': 'Base Sampler',
			'items': [
				('random','random', 'random'),
				('lowdiscrepancy', 'lowdiscrepancy', 'lowdiscrepancy'),
				('metropolis', 'metropolis', 'metropolis')
			],
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'chainlength',
			'name': 'Chain Length',
			'description': 'Chain Length',
			'default': 512,
			'min': 1,
			'max': 32768,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'mutationrange',
			'name': 'Mutation Range',
			'default': 256,
			'min': 1,
			'max': 32768,
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'pixelsampler',
			'name': 'Pixel Sampler',
			'description': 'Pixel sampling strategy',
			'default': 'lowdiscrepancy',
			'items': [
				('linear', 'Linear', 'linear'),
				('tile', 'Tile', 'tile'),
				('vegas', 'Vegas', 'vegas'),
				('lowdiscrepancy', 'Low Discrepancy', 'lowdiscrepancy'),
				('hilbert', 'Hilbert', 'hilbert'),
			],
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'pixelsamples',
			'name': 'Pixel Samples',
			'description': 'Average number of samples taken per pixel. More samples create a higher quality image at the cost of render time',
			'default': 4,
			'min': 1,
			'max': 8192,
			'save_in_preset': True
		},
	]
	
	def api_output(self):
		'''
		Format this class's members into a LuxRender ParamSet
		
		Returns tuple
		'''
		
		params = ParamSet()
		
		if self.sampler in ['random', 'lowdiscrepancy'] or (self.sampler == 'erpt' and self.basesampler in ['random', 'lowdiscrepancy']):
			params.add_integer('pixelsamples', self.pixelsamples)
			params.add_string('pixelsampler', self.pixelsampler)
		
		if self.sampler == 'erpt':
			params.add_integer('chainlength', self.chainlength)
			params.add_string('basesampler', self.basesampler)
		
		if self.sampler == 'metropolis' or (self.sampler == 'erpt' and self.basesampler == 'metropolis'):
			params.add_float('largemutationprob', self.largemutationprob)
			params.add_bool('usevariance', self.usevariance)
			
		if self.advanced:
			if self.sampler == 'metropolis' or (self.sampler == 'erpt' and self.basesampler == 'metropolis'):
				params.add_integer('maxconsecrejects', self.maxconsecrejects)
		
		return self.sampler, params

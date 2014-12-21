# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Simon Wendsche (BYOB)
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

from ..extensions_framework import declarative_property_group
from ..extensions_framework.validate import Logic_AND as A

from .. import LuxRenderAddon


@LuxRenderAddon.addon_register_class
class luxcore_samplersettings(declarative_property_group):
    """
    Storage class for LuxCore sampler settings.
    """
    
    ef_attach_to = ['Scene']
    alert = {}

    controls = [
                  'sampler_type',
                  'advanced',
                  'largesteprate',
                  'maxconsecutivereject',
                  'imagemutationrate',
    ]
    
    visibility = {
        'advanced': {'sampler_type': 'METROPOLIS'},
        'largesteprate': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'}, ]),
        'maxconsecutivereject': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'}, ]),
        'imagemutationrate': A([{'advanced': True}, {'sampler_type': 'METROPOLIS'}, ]),
    }

    properties = [
        {
            'type': 'enum',
            'attr': 'sampler_type',
            'name': 'Sampler',
            'description': 'Pixel sampling algorithm to use',
            'default': 'METROPOLIS',
            'items': [
                ('METROPOLIS', 'Metropolis', 'Keleman-style metropolis light transport'),
                ('SOBOL', 'Sobol', 'Use a Sobol sequence'),
                ('RANDOM', 'Random', 'Completely random sampler')
            ],
            'save_in_preset': True
        },
        {
            'type': 'bool',
            'attr': 'advanced',
            'name': 'Advanced Sampler Settings',
            'description': 'Configure advanced sampler settings',
            'default': False,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'largesteprate',
            'name': 'Large Mutation Probability',
            'description': 'Probability of a completely random mutation rather than a guided one. Lower values \
            increase sampler strength',
            'default': 0.4,
            'min': 0,
            'max': 1,
            'slider': True,
            'save_in_preset': True
        },
        {
            'type': 'int',
            'attr': 'maxconsecutivereject',
            'name': 'Max. Consecutive Rejections',
            'description': 'Maximum amount of samples in a particular area before moving on. Setting this too low \
            may mute lamps and caustics',
            'default': 512,
            'min': 128,
            'max': 2048,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'imagemutationrate',
            'name': 'Image Mutation Rate',
            'description': '',
            'default': 0.1,
            'min': 0,
            'max': 1,
            'slider': True,
            'save_in_preset': True
        },
    ]
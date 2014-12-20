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
from ..extensions_framework.validate import Logic_OR as O, Logic_Operator as LO

from .. import LuxRenderAddon


@LuxRenderAddon.addon_register_class
class luxcore_filtersettings(declarative_property_group):
    """
    Storage class for LuxCore filter settings.
    """

    ef_attach_to = ['Scene']

    controls = [
        'filter_type',
        'filter_width',
    ]

    alert = {}

    properties = [
        {
            'type': 'enum',
            'attr': 'filter_type',
            'name': 'Filter',
            'description': 'Pixel filter to use',
            'default': 'BLACKMANHARRIS',
            'items': [
                ('BLACKMANHARRIS', 'Blackman-Harris', 'desc'),
                ('MITCHELL', 'Mitchell', 'desc'),
                ('MITCHELL_SS', 'Mitchell_SS', 'desc'),
                ('BOX', 'Box', 'desc'),
                ('GAUSSIAN', 'Gaussian', 'desc'),
            ],
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'filter_width',
            'name': 'Filter Width',
            'description': 'Width of pixel filter curve. Higher values are smoother and more blurred',
            'default': 2.0,
            'min': 0.5,
            'soft_min': 0.5,
            'max': 10.0,
            'soft_max': 4.0,
            'save_in_preset': True
        },
    ]

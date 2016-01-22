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

from .. import LuxRenderAddon


@LuxRenderAddon.addon_register_class
class luxcore_scenesettings(declarative_property_group):
    """
    Storage class for LuxCore scene settings.
    """
    
    ef_attach_to = ['Scene']
    alert = {}

    controls = [
                  'imageScale'
    ]

    properties = [
        #{
        #    'type': 'text',
        #    'attr': 'label',
        #    'name': 'Scene Settings:'
        #},
        {
            'type': 'float',
            'attr': 'imageScale',
            'name': 'Texture Scale',
            'description': 'If less than 100%, image textures are scaled down',
            'default': 100.0,
            'min': 1.0,
            'max': 100.0,
            'precision': 0,
            'subtype': 'PERCENTAGE',
            'slider': True,
            'save_in_preset': True
        }
    ]
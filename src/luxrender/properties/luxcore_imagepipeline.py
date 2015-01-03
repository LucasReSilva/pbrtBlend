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
from ..extensions_framework.validate import Logic_OR as O, Logic_AND as A

from .. import LuxRenderAddon


@LuxRenderAddon.addon_register_class
class luxrender_imagepipeline_element(declarative_property_group):
    """
    Storage class for LuxRender imagepipeline elements. The
    luxcore_imagepipeline_settings object will store 1 or more of
    these in its CollectionProperty 'elements'.
    """

    ef_attach_to = []  # not attached
    alert = {}

    
    controls = [  # drawn manually in the UI class (ui/render_panels.py)
        'type',
        'tonemapper_type',
    ]
    
    '''
    visibility = {
        'tonemapper_type': {'type': 'tonemapper'},
        # TODO: the rest
    }
    '''
    
    properties = [
        {
            'type': 'enum',
            'attr': 'type',
            'name': 'Element Type',
            'description': 'Type of the imagepipeline element',
            'default': 'tonemapper',
            'items': [
                ('tonemapper', 'Tonemapper', 'A tonemapper converts the image from HDR to LDR'),
                ('gamma_correct', 'Gamma Correction', 'Blender expects 1.0 as input gamma for rendered images'),
                ('output_switcher', 'Output Switcher', 'Makes it possible to use AOVs as elements in the imagepipeline'),
            ],
            'save_in_preset': True
        },
        # Tonemapper
        {
            'type': 'enum',
            'attr': 'tonemapper_type',
            'name': 'Tonemapper',
            'description': 'A tonemapper converts the image from HDR to LDR',
            'default': 'TONEMAP_AUTOLINEAR',
            'items': [
                ('TONEMAP_AUTOLINEAR', 'Linear (Auto)', 'Simple auto-exposure'),
                ('TONEMAP_LINEAR', 'Linear', 'Brightness is controlled by the scale value'),
                ('TONEMAP_LUXLINEAR', 'Linear (Manual)', 'Uses camera settings (ISO, f-stop and shuttertime)'),
                ('TONEMAP_REINHARD02', 'Reinhard', 'Non-linear tonemapper that adapts to the image brightness'),
            ],
            'save_in_preset': True
        },
        # Linear tonemapper settings
        {
            'type': 'float',
            'attr': 'linear_scale',
            'name': 'Scale',
            'description': 'Brightness factor of the image',
            'default': 1.0,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 10000.0,
            'soft_max': 10.0,
            'save_in_preset': True
        },
        # Reinhard tonemapper settings
        {
            'type': 'float',
            'attr': 'reinhard_prescale',
            'name': 'Pre',
            'description': 'Reinhard Pre-Scale factor',
            'default': 1.0,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 25.0,
            'soft_max': 25.0,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'reinhard_postscale',
            'name': 'Post',
            'description': 'Reinhard Post-Scale factor',
            'default': 1.2,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 25.0,
            'soft_max': 25.0,
            'save_in_preset': True
        },
        {
            'type': 'float',
            'attr': 'reinhard_burn',
            'name': 'Burn',
            'description': 'Reinhard Burn factor',
            'default': 6.0,
            'min': 0.01,
            'soft_min': 0.01,
            'max': 25.0,
            'soft_max': 25.0,
            'save_in_preset': True
        },
        # Gamma correction settings
        {
            'type': 'float',
            'attr': 'gamma',
            'name': 'Gamma',
            'description': 'Gamma factor to apply (note: Blender expects 1.0 from rendered images)',
            'default': 1.0,
            'min': -20,
            'soft_min': -1,
            'max': 20.0,
            'soft_max': 4.0,
            'save_in_preset': True
        },
        # Output switcher settings
        # TODO: enum of AOV channels
    ]

@LuxRenderAddon.addon_register_class
class luxcore_imagepipeline_settings(declarative_property_group):
    """
    Storage class for LuxCore imagepipeline settings.
    """
    
    ef_attach_to = ['Scene']
    
    alert = {}

    controls = [
        'imagepipeline_label',
        ['ignore',
         'op_lg_add'],
    ]

    properties = [
        {
            'type': 'text',
            'name': 'Image Pipeline',
            'attr': 'imagepipeline_label',
        },
        {
            'type': 'collection',
            'ptype': luxrender_imagepipeline_element,
            'name': 'elements',
            'attr': 'elements',
            'items': []
        },
        {
            'type': 'int',
            'name': 'element_index',
            'attr': 'element_index',
        },
        {
            'type': 'operator',
            'attr': 'op_element_add',
            'operator': 'luxrender.lightgroup_add',
            'text': 'Add',
            'icon': 'ZOOMIN',
        },
    ]

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
from properties_data_camera import DataButtonsPanel as CameraPanel

import ef.ui
import luxrender.properties.tonemapping

class tonemapping(CameraPanel, ef.ui.described_layout):
    bl_label = 'LuxRender ToneMapping'
    
    property_group = luxrender.properties.tonemapping.luxrender_tonemapping
    
    controls = [
        'type',
        
        # Reinhard
        ['reinhard_prescale', 'reinhard_postscale', 'reinhard_burn'],
    ]
    
    visibility = {
        'reinhard_prescale':            { 'type': 'reinhard' },
        'reinhard_postscale':           { 'type': 'reinhard' },
        'reinhard_burn':                { 'type': 'reinhard' },
    }
    
    properties = [
        {
            'type': 'enum',
            'attr': 'type',
            'name': 'Tonemapper',
            'description': 'Choose tonemapping type',
            'default': 'reinhard',
            'items': [
                ('reinhard', 'Reinhard', 'reinhard'),
                ('linear', 'Linear', 'linear'),
                ('contrast', 'Contrast', 'contrast'),
                ('maxwhite', 'Maxwhite', 'maxwhite')
            ]
        },
        {
            'type': 'float',
            'attr': 'reinhard_prescale',
            'name': 'Pre',
            'description': 'Reinhard Pre-Scale factor',
            'default': 2.0,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 25.0,
            'soft_max': 25.0
        },
        {
            'type': 'float',
            'attr': 'reinhard_postscale',
            'name': 'Post',
            'description': 'Reinhard Post-Scale factor',
            'default': 1.1,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 25.0,
            'soft_max': 25.0
        },
        {
            'type': 'float',
            'attr': 'reinhard_burn',
            'name': 'Burn',
            'description': 'Reinhard Burn factor',
            'default': 6.0,
            'min': 0.0,
            'soft_min': 0.0,
            'max': 25.0,
            'soft_max': 25.0
        },
    ]
    
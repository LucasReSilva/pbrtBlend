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
class luxcore_rendering_controls(declarative_property_group):
    """
    Storage class for settings that can be changed during the rendering process,
    e.g. pause/resume, tonemapping settings and other imagepipeline options
    """
    
    ef_attach_to = ['Scene']
    alert = {}

    controls = [
        'pause_render'
    ]
    
    visibility = {

    }

    properties = [
        {
            'type': 'bool',
            'attr': 'pause_render',
            'name': 'Pause Render',
            'description': '',
            'default': False,
        },
    ]

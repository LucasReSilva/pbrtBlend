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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
from properties_texture import context_tex_datablock

from ef.ui import context_panel
from ef.ui import texture_settings_panel
from ef.ui import described_layout

from ef.ef import ef

import properties

class texture_editor(context_panel, texture_settings_panel, described_layout):
    bl_label = 'LuxRender Textures'
    COMPAT_ENGINES = {'luxrender'}
    
    property_group = properties.luxrender_texture
    # prevent creating luxrender_texture property group in Scene
    property_group_non_global = True
    
    # Overridden to provide data storage in the texture, not the scene
    def draw(self, context):
        if context.texture is not None:
            if not hasattr(context.texture, self.property_group.__name__):
                ef.init_properties(context.texture, [{
                    'type': 'pointer',
                    'attr': self.property_group.__name__,
                    'ptype': self.property_group,
                    'name': self.property_group.__name__,
                    'description': self.property_group.__name__
                }], cache=False)
                ef.init_properties(self.property_group, self.properties, cache=False)
            
            for p in self.controls:
                self.draw_column(p, self.layout, context.texture, supercontext=context)
    
    controls = [
        'type',
        
        ['tex1_label', 'tex2_label'],
        ['tex1', 'tex2']
    ]
    
    selection = {
    }
    
    properties = [
        {
            'attr': 'type',
            'type': 'enum',
            'name': 'Type',
            'description': 'LuxRender Texture Type',
            'items': [
                ('scale','scale','scale'),
            ],
        },
        {
            'type': 'text',
            'attr': 'tex1_label',
            'name': 'Texture 1'
        },
        {
            'type': 'text',
            'attr': 'tex2_label',
            'name': 'Texture 2'
        },
        {
            'type': 'int',
            'attr': 'tex1_index',
            'name': 'tex1_index',
            'description': 'tex1_index',
            'min': 0,  'soft_min': 0,
            'max': 17, 'soft_max': 17,
        },
        {
            'type': 'int',
            'attr': 'tex2_index',
            'name': 'tex2_index',
            'description': 'tex2_index',
            'min': 0,  'soft_min': 0,
            'max': 17, 'soft_max': 17,
        },
        {
            'attr': 'tex1',
            'type': 'template_list',
            # source data list
            'src': lambda s,c: context_tex_datablock(s),
            'src_attr': 'texture_slots',
            # target property
            'trg': lambda s,c: c.luxrender_texture,
            'trg_attr': 'tex1_index',
            'text': 'Texture 1',
        },
        {
            'attr': 'tex2',
            'type': 'template_list',
            # source data list
            'src': lambda s,c: context_tex_datablock(s),
            'src_attr': 'texture_slots',
            # target property
            'trg': lambda s,c: c.luxrender_texture,
            'trg_attr': 'tex2_index',
            'text': 'Texture 2',
        },
        
        
    ]
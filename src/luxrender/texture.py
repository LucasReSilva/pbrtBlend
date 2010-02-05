'''
Created on 5 Feb 2010

@author: doug
'''

import bpy
import random

from ef.ef import ef

import properties


# TODO probably re-write all of this into custom textures instead of material properties
# TODO cannot next textures (eg. for mix)

class Texture(dict):
    '''
    Special dict class to construct a texture channel for Lux material
    '''
    
    def __init__(self, channel_name, **kwargs):
        self.update({
            'attr': channel_name,
            'type': 'pointer',
            'ptype': properties.luxrender_channel,
            
            # controls, selection and properties mirror those of described_layout
            
            'controls':
            [
                'label',
                'type',
                'constant',
            ],
            'selection':
            {
                'constant':    [{'type':'constant'}],
            },
            'properties':
            [
                {
                    'attr': 'label',
                    'type': 'text',
                    'name': kwargs['description']
                },
                {
                    'attr': 'type',
                    'type': 'enum',
                    'name': 'Type',
                    'description': 'Select channel type',
                    'items': [
                        ('constant','constant','constant'),
                        ('bilerp','bilerp','bilerp'),
                        ('checkerboard','checkerboard','checkerboard'),
                        ('constant','constant','constant'),
                        ('dots','dots','dots'),
                        ('fbm','fbm','fbm'),
                        ('imagemap','imagemap','imagemap'),
                        ('marble','marble','marble'),
                        ('mix','mix','mix'),
                        ('scale','scale','scale'),
                        ('uv','uv','uv'),
                        ('windy','windy','windy'),
                        ('wrinkled','wrinkled','wrinkled'),
                        ('blender_clouds','blender_clouds','blender_clouds'),
                        ('blender_musgrave','blender_musgrave','blender_musgrave'),
                        ('blender_marble','blender_marble','blender_marble'),
                        ('blender_wood ','blender_wood ','blender_wood '),
                    ]
                },
                {
                    'attr': 'constant',
                    'type': 'float_vector',
                    'name': 'Constant',
                    'description': 'Constant',
                    'size': 3,
                    'default': (0.8, 0.8, 0.8),
                    'step': 0.1,
                    'min': 0.0,
                    'soft_min': 0.0,
                    'max': 1.0,
                    'soft_max': 1.0,
                    'precision': 3,
                    'subtype': 'COLOR'
                }
            ]
        })
        
        # can set items from keyword args in constructor
        self.update(kwargs)
        
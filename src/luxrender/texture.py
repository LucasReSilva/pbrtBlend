'''
Created on 5 Feb 2010

@author: doug
'''

import bpy
import random

from ef.ef import ef

import properties

def all_defaults(channel_name):
    return 

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
            
            'controls': [
                'label',
                'type',
                'constant',
            ],
            'selection': {
                'constant':    [{'type':'constant'}],
            },
            'properties': [
                {
                    'attr': 'label',
                    'type': 'text',
                    'name': 'Channel %s'%channel_name
                },
                {
                    'attr': 'type',
                    'type': 'enum',
                    'name': 'Type',
                    'description': 'Select channel type',
                    'items': [
                        ('constant','constant','constant'),
                    ]
                },
                {
                    'attr': 'constant',
                    'type': 'float_vector',
                    'name': 'Constant Colour',
                    'description': 'Test Colour',
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
        
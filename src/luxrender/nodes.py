'''
Created on 5 Feb 2010

@author: doug
'''
import bpy

class node_props(bpy.types.IDPropertyGroup):
    pass

class test_node(bpy.types.TextureNode):
    property_group = node_props
    
    name = "TEST NODE"
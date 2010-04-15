# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, Genscher
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
from math import degrees

import bpy, mathutils

from luxrender.module.file_api import Files
from luxrender.export import matrix_to_list

def attr_light(l, name, type, params, transform=None):
    '''
    l            pylux.Context
    name         string
    type         string
    params       dict
    transform    None or list
    
    This method outputs a lightSource of the given name and
    type to context l. The lightSource will be wrapped in a
    transformBegin...transformEnd block if a transform is
    given, otherwise it will appear in an attributeBegin...
    attributeEnd block.
    
    Returns None
    '''
    
    if transform is not None:
        l.transformBegin(comment=name, file=Files.MAIN)
        l.transform(transform)
    else:
        l.attributeBegin(comment=name, file=Files.MAIN)
        
    l.lightSource(type, list(params.items()))
    
    if transform is not None:
        l.transformEnd()
    else:
        l.attributeEnd()

def lights(l, scene):
    '''
    l            pylux.Context
    scene        bpy.types.scene
    
    Iterate over the given scene's light sources,
    and export the compatible ones to the context l.
    
    Returns Boolean indicating if any light sources
    were exported.
    '''
    
    sel = scene.objects
    have_light = False

    for ob in sel:
        
        if ob.type != 'LAMP':
            continue
        
        if ob.data.type == 'SUN':
            invmatrix = mathutils.Matrix(ob.matrix).invert()
            es = {
                'sundir': (invmatrix[0][2], invmatrix[1][2], invmatrix[2][2])
            }
            attr_light(l, ob.name, 'sunsky', es)
            have_light = True
        
        if ob.data.type == 'SPOT':
            coneangle = degrees(ob.data.spot_size) * 0.5
            conedeltaangle = degrees(ob.data.spot_size * 0.5 * ob.data.spot_blend)
            es = {
                'L': [i for i in ob.data.color],
                'from': (0,0,0),
                'to': (0,0,-1),
                'coneangle': coneangle,
                'conedeltaangle': conedeltaangle,
                'gain': ob.data.energy
            }
            attr_light(l, ob.name, 'spot', es, transform=matrix_to_list(ob.matrix))
            have_light = True

        if ob.data.type == 'POINT':
            es = {
                'L': [i for i in ob.data.color],
                'gain': ob.data.energy,
                'from': (0,0,0)
            }
            attr_light(l, ob.name, 'point', es, transform=matrix_to_list(ob.matrix))
            have_light = True
        
        if ob.data.type == 'AREA':
            es = {
                'L': [i for i in ob.data.color],
                'gain': ob.data.energy,
                'power': 100.0,
                'efficacy': 17.0
            }
            
            l.attributeBegin(ob.name, file=Files.MAIN)
            
            l.transform(matrix_to_list(ob.matrix))

            l.arealightSource('area', list(es.items()))

            areax = ob.data.size

            if ob.data.shape == 'SQUARE': areay = areax
            elif ob.data.shape == 'RECTANGLE': areay = ob.data.size_y
            else: areay = areax # not supported yet

            points = [-areax/2, areay/2, 0.0, areax/2, areay/2, 0.0, areax/2, -areay/2, 0.0, -areax/2, -areay/2, 0.0]
            ss = {
                'indices': [0, 1, 2, 0, 2, 3],
                'P': points
            }
            l.shape('trianglemesh', list(ss.items()))
            l.attributeEnd()

            have_light = True

    return have_light
        

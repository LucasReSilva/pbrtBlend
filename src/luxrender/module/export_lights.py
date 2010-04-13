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

import bpy, Mathutils

from luxrender.module.file_api import Files
from luxrender.module import matrix_to_list

def attr_light(l, name, type, params, transform=None):
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
    
    sel = scene.objects
    for ob in sel:
        
        if ob.type not in ('LAMP'):
            continue
        
        if ob.data.type == 'SUN':
            invmatrix = Mathutils.Matrix(ob.matrix).invert()
            es = {
                'sundir': (invmatrix[0][2], invmatrix[1][2], invmatrix[2][2])
            }
            attr_light(l, ob.name, 'sunsky', es)
        
        if ob.data.type == 'SPOT':
            coneangle = degrees(ob.data.spot_size) * 0.5
            conedeltaangle = degrees(ob.data.spot_size * 0.5 * ob.data.spot_blend)
            es = {
                'L': [i*ob.data.energy for i in ob.data.color],
                'from': (0,0,0),
                'to': (0,0,-1),
                'coneangle': coneangle,
                'conedeltaangle': conedeltaangle
            }
            attr_light(l, ob.name, 'spot', es, transform=matrix_to_list(ob.matrix))
        
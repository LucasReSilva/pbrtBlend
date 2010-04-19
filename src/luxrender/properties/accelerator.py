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
import bpy

from luxrender.properties import dbo
from luxrender.export import Paramset

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

class luxrender_accelerator(bpy.types.IDPropertyGroup):
    '''
    Storage class for LuxRender Accelerator settings.
    This class will be instantiated within a Blender scene
    object.
    '''
    
    def api_output(self):
        '''
        Format this class's members into a LuxRender ParamSet
        
        Returns tuple
        '''
        
        params = Paramset()
        
        if self.accelerator == 'tabreckdtree':
            params.add_float('intersectcost', self.kd_intcost)
            params.add_float('traversalcost', self.kd_travcost)
            params.add_float('emptybonus', self.kd_ebonus)
            params.add_integer('maxprims', self.kd_maxprims)
            params.add_integer('maxdepth', self.kd_maxdepth)
        
        if self.accelerator == 'grid':
            params.add_bool('refineimmediately', self.grid_refineim)
            
        if self.accelerator == 'qbvh':
            params.add_integer('maxprimsperleaf', self.qbvh_maxprims)
        
        out = self.accelerator, params
        dbo('ACCELERATOR', out)
        return out

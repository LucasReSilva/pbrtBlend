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
        
        Returns dict
        '''
        
        d={}
        
        if self.accelerator == 'tabreckdtree':
            d['float intersectcost']        = self.kd_intcost
            d['float traversalcost']        = self.kd_travcost
            d['float emptybonus']           = self.kd_ebonus
            d['integer maxprims']           = self.kd_maxprims
            d['integer maxdepth']           = self.kd_maxdepth
        
        if self.accelerator == 'grid':
            d['bool refineimmediately']     = self.grid_refineim
            
        if self.accelerator == 'qbvh':
            d['integer maxprimsperleaf']    = self.qbvh_maxprims
#            d['fullsweepthreshold']     = self.??
#            d['skipfactor']             = self.??
        
        out = self.accelerator, list(d.items())
        dbo('ACCELERATOR', out)
        return out

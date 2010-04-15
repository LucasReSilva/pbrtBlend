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

class luxrender_filter(bpy.types.IDPropertyGroup):
    '''
    Storage class for LuxRender PixelFilter settings.
    This class will be instantiated within a Blender scene
    object.
    '''
    
    def api_output(self):
        '''
        Format this class's members into a LuxRender ParamSet
        
        Returns dict
        '''
        
        d={}
        
        d['xwidth'] = self.xwidth
        d['ywidth'] = self.ywidth
        
        if self.filter == 'box':
            pass
        
        if self.filter == 'gaussian':
            d['alpha'] = self.gaussian_alpha
        
        if self.filter == 'mitchell':
            d['B'] = self.mitchell_b
            d['C'] = self.mitchell_c
        
        if self.filter == 'sinc':
            d['tau'] = self.sinc_tau
        
        if self.filter == 'triangle':
            pass
        
        out = self.filter, list(d.items())
        dbo('FILTER', out)
        return out

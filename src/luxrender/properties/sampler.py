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

class luxrender_sampler(bpy.types.IDPropertyGroup):
    '''
    Storage class for LuxRender Sampler settings.
    This class will be instantiated within a Blender scene
    object.
    '''
    
    def api_output(self):
        '''
        Format this class's members into a LuxRender ParamSet
        
        Returns dict
        '''
        
        d = {}
        
        if self.sampler in ['random', 'lowdiscrepancy']:
            d['pixelsamples']         = self.pixelsamples
            d['pixelsampler']         = self.pixelsampler
        
        if self.sampler == 'erpt':
            d['initsamples']          = self.erpt_initsamples
            d['chainlength']          = self.erpt_chainlength
#            d['mutationrange']        = self.erpt_mutationrange
        
        if self.sampler == 'metropolis':
            d['initsamples']          = self.metro_initsamples
            d['maxconsecrejects']     = self.metro_mncr
            d['largemutationprob']    = self.metro_lmprob
#            d['micromutationprob']    = self.??
#            d['mutationrange']        = self.??
            d['usevariance']          = self.metro_variance
        
        out = self.sampler, list(d.items())
        dbo('SAMPLER', out)
        return out

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

DEBUG = True

if DEBUG:
    import pprint
def dbo(m,o):
    if DEBUG: 
        print(m)
        pprint.pprint(o, width=1, indent=1)
        

# TODO: adapt values written to d based on simple/advanced views

# TODO: check parameter completeness against Lux API

import bpy

class luxrender_texture(bpy.types.IDPropertyGroup):
    pass

class luxrender_material(bpy.types.IDPropertyGroup):
    pass

class luxrender_engine(bpy.types.IDPropertyGroup):
    pass
  
class luxrender_sampler(bpy.types.IDPropertyGroup):
    def api_output(self):
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
            
   
class luxrender_integrator(bpy.types.IDPropertyGroup):
    def api_output(self):
        d={}
        
        if self.surfaceintegrator in ['directlighting', 'path']:
            d['lightstrategy']    = self.strategy
#            d['maxdepth']         = self.??
        
        if self.surfaceintegrator == 'bidirectional':
            d['eyedepth']         = self.bidir_edepth
            d['lightdepth']       = self.bidir_ldepth
#            d['eyerrthreshold']   = self.??
#            d['lightrrthreshold'] = self.??
        
        if self.surfaceintegrator == 'distributedpath':
            d['strategy']         = self.strategy
#            d['diffusedepth']     = self.??
#            d['glossydepth']      = self.??
#            d['speculardepth']    = self.??
        
#        if self.lux_surfaceintegrator == 'exphotonmap':
#            pass
        
        out = self.surfaceintegrator, list(d.items())
        dbo('SURFACE INTEGRATOR', out)
        return out
   
class luxrender_volume(bpy.types.IDPropertyGroup):
    def api_output(self):
        d={}
        
        d['stepsize'] = self.stepsize
        
        out = self.volumeintegrator, list(d.items())
        dbo('VOLUME INTEGRATOR', out)
        return out

class luxrender_filter(bpy.types.IDPropertyGroup):
    def api_output(self):
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
   
class luxrender_accelerator(bpy.types.IDPropertyGroup):
    def api_output(self):
        d={}
        
        if self.accelerator == 'tabreckdtree':
            d['intersectcost']          = self.kd_intcost
            d['traversalcost']          = self.kd_travcost
            d['emptybonus']             = self.kd_ebonus
            d['maxprims']               = self.kd_maxprims
            d['maxdepth']               = self.kd_maxdepth
        
        if self.accelerator == 'grid':
            d['refineimmediately']      = self.grid_refineim
            
        if self.accelerator == 'qbvh':
            d['maxprimsperleaf']        = self.qbvh_maxprims
#            d['fullsweepthreshold']     = self.??
#            d['skipfactor']             = self.??
        
        out = self.accelerator, list(d.items())
        dbo('ACCELERATOR', out)
        return out

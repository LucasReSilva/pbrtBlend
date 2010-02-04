'''
Created on 4 Feb 2010

@author: doug
'''
import bpy

DEBUG = True

if DEBUG:
    import pprint
def dbo(o):
    if DEBUG: pprint.pprint(o, width=1, indent=1)
        

# TODO adapt values written to d based on simple/advanced views

# TODO check parameter completeness against Lux API

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
        dbo(out)
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
        dbo(out)
        return out
   
class luxrender_volume(bpy.types.IDPropertyGroup):
    pass

class luxrender_filter(bpy.types.IDPropertyGroup):
    pass
   
class luxrender_accelerator(bpy.types.IDPropertyGroup):
    def api_output(self):
        d={}
        
        out = self.accelerator, list(d.items())
        dbo(out)
        return out
        

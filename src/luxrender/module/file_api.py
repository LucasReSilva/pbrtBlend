'''
Created on 10 Apr 2010

@author: doug
'''

import sys

import luxrender.pylux
import luxrender.module.paramset

class lux(object):
    
    class Context(luxrender.pylux.Context):
        '''
        Wrap the real pylux Context object so that we can
        change the behaviour of certain API calls (ie. write
        to files and use the Context to monitor rendering)
        '''
        
        files = []
        
        def wf(self, ind, st, tabs=0):
            '''
            Write a string followed by newline to file index ind
            '''
            if len(self.files) == 0:
                self.set_filename('test')
            
            self.files[ind].write('%s%s\n' % ('\t'*tabs, st))
        
        def param_formatter(self, param):
            fs_num = '"%s %s" [%s]'
            fs_str = '"%s %s" ["%s"]'
            
            k, v = param
            if k in luxrender.module.paramset.FLOAT:
                return fs_num % ('float', k, '%f' % v)
            elif k in luxrender.module.paramset.FLOAT_VEC:
                return fs_num % ('float', k, ' '.join(['%f'%i for i in v]))
            elif k in luxrender.module.paramset.INT:
                return fs_num % ('integer', k, '%i' % v)
            elif k in luxrender.module.paramset.INT_VEC:
                return fs_num % ('integer', k, ' '.join(['%i'%i for i in v]))
            elif k in luxrender.module.paramset.STRING:
                return fs_str % ('string', k, v)
            elif k in luxrender.module.paramset.BOOL:
                if v:
                    return fs_str % ('bool', k, 'true')
                else:
                    return fs_str % ('bool', k, 'false')
                
            return '# unknown param %s : %s' % (k,v)
        
        def set_filename(self, name):
            self.files = [
                sys.stdout, #open('%s.lxs' % name, 'w'),
                sys.stdout, #open('%s-mat.lxm' % name, 'w'),
                sys.stdout, #open('%s-geom.lxo' % name, 'w'),
            ]
            
        def sampler(self, *args):
            name, params = args
            self.wf(0, 'Sampler "%s"' % name)
            for p in params:
                self.wf(0, self.param_formatter(p), 1)
        
        def accelerator(self, *args):
            name, params = args
            self.wf(0, 'Accelerator "%s"' % name)
            for p in params:
                self.wf(0, self.param_formatter(p), 1)
        
        def surfaceIntegrator(self, *args):
            name, params = args
            self.wf(0, 'SurfaceIntegrator "%s"' % name)
            for p in params:
                self.wf(0, self.param_formatter(p), 1)
        
        def volumeIntegrator(self, *args):
            name, params = args
            self.wf(0, 'VolumeIntegrator "%s"' % name)
            for p in params:
                self.wf(0, self.param_formatter(p), 1)
        
        def pixelFilter(self, *args):
            name, params = args
            self.wf(0, 'PixelFilter "%s"' % name)
            for p in params:
                self.wf(0, self.param_formatter(p), 1)
        
        def lookAt(self, *args):
            self.wf(0, 'LookAt %s' % ' '.join(['%f'%i for i in args]))
        
        def camera(self, *args):
            name, params = args
            self.wf(0, 'Camera "%s"' % name)
            for p in params:
                self.wf(0, self.param_formatter(p), 1)
        
        def film(self, *args):
            name, params = args
            self.wf(0, 'Film "%s"' % name)
            for p in params:
                self.wf(0, self.param_formatter(p), 1)
        
        def worldBegin(self, *args):
            self.wf(0, 'WorldBegin')
        
        def worldEnd(self, *args):
            '''
            Don't actually write any WorldEnd to file!
            '''
            
            for f in self.files:
                f.close()
            
#            self.parse(self.files[0].name)  # Main scene file
#            self.parse(self.files[1].name)  # Materials
#            self.parse(self.files[2].name)  # Geometry
            luxrender.pylux.Context.worldEnd(self)
        
        def lightSource(self, *args):
            pass
        
        
        
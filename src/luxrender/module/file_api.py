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

import sys

from ef.ef import ef 

import luxrender.pylux
import luxrender.module
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
            elif k in luxrender.module.paramset.VEC:
                return fs_num % ('vector', k, ' '.join(['%f'%i for i in v]))
            elif k in luxrender.module.paramset.POINT:
                return fs_num % ('point', k, ' '.join(['%f'%i for i in v]))
            elif k in luxrender.module.paramset.NORMAL:
                return fs_num % ('normal', k, ' '.join(['%f'%i for i in v]))
            elif k in luxrender.module.paramset.COLOR:
                return fs_num % ('color', k, ' '.join(['%f'%i for i in v]))
            elif k in luxrender.module.paramset.TEXTURE:
                return fs_str % ('texture', k, v)
            elif k in luxrender.module.paramset.BOOL:
                if v:
                    return fs_str % ('bool', k, 'true')
                else:
                    return fs_str % ('bool', k, 'false')
                
            return '# unknown param %s : %s' % (k,v)
        
        def set_filename(self, name):
            for f in self.files:
                f.close()
            
            self.files = [
                open('%s.lxs' % name, 'w'),
                open('%s-mat.lxm' % name, 'w'),
                open('%s-geom.lxo' % name, 'w'),
            ]
            
            self.wf(0, '# Main Scene File')
            self.wf(1, '# Materials File')
            self.wf(2, '# Geometry File')
            
        def _api(self, identifier, args, file=0):
            name, params = args
            self.wf(file, '\n%s "%s"' % (identifier, name))
            for p in params:
                self.wf(file, self.param_formatter(p), 1)
            
        def sampler(self, *args):
            self._api('Sampler', args)
        
        def accelerator(self, *args):
            self._api('Accelerator', args)
        
        def surfaceIntegrator(self, *args):
            self._api('SurfaceIntegrator', args)
        
        def volumeIntegrator(self, *args):
            self._api('VolumeIntegrator', args)
        
        def pixelFilter(self, *args):
            self._api('PixelFilter', args)
        
        def lookAt(self, *args):
            self.wf(0, '\nLookAt %s' % ' '.join(['%f'%i for i in args]))
        
        def camera(self, *args):
            self._api('Camera', args)
        
        def film(self, *args):
            self._api('Film', args)
        
        def worldBegin(self, *args):
            self.wf(0, '\nWorldBegin')
        
        def worldEnd(self, *args):
            #Don't actually write any WorldEnd to file yet!
            luxrender.module.LuxLog('Wrote scene files')
            for f in self.files:
                f.close()
                luxrender.module.LuxLog(' %s' % f.name)
            
            # Now start the rendering by parsing the files we just wrote
            self.parse(self.files[0].name, False)  # Main scene file
            self.parse(self.files[1].name, False)  # Materials
            self.parse(self.files[2].name, False)  # Geometry
            luxrender.pylux.Context.worldEnd(self)
            
            # Add the final WorldEnd so that the file is usable directly in LuxRender
            f=open(self.files[0].name, 'a')
            f.write('\nInclude "%s"' % self.files[1].name)
            f.write('\nInclude "%s"' % self.files[2].name)
            f.write('\n\nWorldEnd\n')
            f.close()
        
        def lightSource(self, *args):
            self._api('LightSource', args)
        
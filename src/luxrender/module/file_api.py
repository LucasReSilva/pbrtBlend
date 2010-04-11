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

class Files(object):
    MAIN = 0
    MATS = 1
    GEOM = 2

class Custom_Context(luxrender.pylux.Context):
    '''
    Wrap the real pylux Context object so that we can
    change the behaviour of certain API calls (ie. write
    to files and use the Context to monitor rendering)
    '''
    
    files = []
    current_file = Files.MAIN
    
    def wf(self, ind, st, tabs=0):
        '''
        Write a string followed by newline to file index ind
        '''
        
        if len(self.files) == 0:
            self.set_filename('default')
        
        self.files[ind].write('%s%s\n' % ('\t'*tabs, st))
    
    def param_formatter(self, param):
        '''
        Try to detect the parameter type (via paramset) and
        format it as a string.
        '''
        
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
        '''
        Open the main, materials, and geometry files for output
        '''
        
        # If any files happen to be open, close them and start again
        for f in self.files:
            f.close()
        
        self.files = [
            open('%s.lxs' % name, 'w'),
            open('%s-mat.lxm' % name, 'w'),
            open('%s-geom.lxo' % name, 'w'),
        ]
        
        self.wf(Files.MAIN, '# Main Scene File')
        self.wf(Files.MATS, '# Materials File')
        self.wf(Files.GEOM, '# Geometry File')
        
    def set_output_file(self, file):
        self.current_file = file
        
    def _api(self, identifier, args=[], file=None):
        if file is not None:
            self.set_output_file(file)
        
        # name is a string, and params a list
        name, params = args
        self.wf(self.current_file, '\n%s "%s"' % (identifier, name))
        for p in params:
            self.wf(self.current_file, self.param_formatter(p), 1)
        
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
        self.wf(Files.MAIN, '\nLookAt %s' % ' '.join(['%f'%i for i in args]))
    
    def camera(self, *args):
        self._api('Camera', args)
    
    def film(self, *args):
        self._api('Film', args)
    
    def worldBegin(self, *args):
        self.wf(Files.MAIN, '\nWorldBegin')
    
    def lightSource(self, *args):
        self._api('LightSource', args)
        
    def attributeBegin(self, file=None):
        '''
        The AttributeBegin block could be used to switch
        the current output file, seeing as we will probably
        be exporting LightSources to the LXS and other
        geometry to LXO.
        '''
        
        self.wf(Files.GEOM, '\nAttributeBegin', file=file)
        
    def attributeEnd(self):
        self.wf(Files.GEOM, '\nAttributeEnd')
        
    def transform(self, *args):
        # TODO: detect 4x4 matrix input, or 16-item list input
        self.wf(Files.GEOM, '\nTransform [%s]' % ' '.join(['%f'%i for i in args]))
        
    def shape(self, *args):
        self._api('Shape', file=Files.GEOM)
        
    def material(self, name):
        self.wf(Files.GEOM, '\nMaterial "%s"' % name)
    
    def texture(self, name, type, texture, *params):
        self.wf(Files.MATS, '\nTexture "%s" "%s" "%s"' % (name, type, texture))
        for p in params:
            self.wf(Files.MATS, self.param_formatter(p), 1)
    
    def worldEnd(self):
        #Don't actually write any WorldEnd to file yet!
        
        # Include the other files
        self.wf(Files.MAIN, '\nInclude "%s"' % self.files[Files.MATS].name)   # Materials
        self.wf(Files.MAIN, '\nInclude "%s"' % self.files[Files.GEOM].name)   # Geometry
        
        # Close files
        luxrender.module.LuxLog('Wrote scene files')
        for f in self.files:
            f.close()
            luxrender.module.LuxLog(' %s' % f.name)
        
        # Now start the rendering by parsing the main scene file we just wrote
        self.parse(self.files[Files.MAIN].name, False)  # Main scene file
        super(luxrender.pylux.Context, self).worldEnd()
        
        # Add the includes and final WorldEnd so that the file is usable directly in LuxRender
        f=open(self.files[Files.MAIN].name, 'a')
        f.write('\nWorldEnd\n')
        f.close()
        
# Replace the pylux.Context with our own extension
luxrender.pylux.Context = Custom_Context

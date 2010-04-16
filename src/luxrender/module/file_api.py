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
        ind             int
        st              string
        tabs            int
        
        Write a string followed by newline to file index ind.
        Optionally indent the string by a number of tabs
        
        Returns None
        '''
        
        if len(self.files) == 0:
            self.set_filename('default')
        
        self.files[ind].write('%s%s\n' % ('\t'*tabs, st))
    
    def param_formatter(self, param):
        '''
        param            tuple(2)
        
        Detect the parameter type and format it as a string.
        
        Returns string
        '''
        
        fs_num = '"%s %s" [%s]'
        fs_str = '"%s %s" ["%s"]'
        
        k, v = param
        
        tokens = k.split(' ')
        if len(tokens) != 2:
            return '# unknown param %s : %s' % (k,v)
        
        t_type, t_name = tokens
        
        if t_type == "float" and type(v) in (list, tuple):
            return fs_num % ('float', t_name, ' '.join(['%f'%i for i in v]))
        if t_type == "float":
            return fs_num % ('float', t_name, '%f' % v)
        if t_type == "integer" and type(v) in (list, tuple):
            return fs_num % ('integer', t_name, ' '.join(['%i'%i for i in v]))
        if t_type == "integer":
            return fs_num % ('integer', t_name, '%i' % v)
        if t_type == "string":
            return fs_str % ('string', t_name, v)
        if t_type == "vector":
            return fs_num % ('vector', t_name, ' '.join(['%f'%i for i in v]))
        if t_type == "point":
            return fs_num % ('point', t_name, ' '.join(['%f'%i for i in v]))
        if t_type == "normal":
            return fs_num % ('normal', t_name, ' '.join(['%f'%i for i in v]))
        if t_type == "color":
            return fs_num % ('color', t_name, ' '.join(['%f'%i for i in v]))
        if t_type == "texture":
            return fs_str % ('texture', t_name, v)
        if t_type == "bool":
            if v:
                return fs_str % ('bool', t_name, 'true')
            else:
                return fs_str % ('bool', t_name, 'false')
            
        return '# unknown param %s : %s' % (k,v)
    
    def set_filename(self, name):
        '''
        name            string
        
        Open the main, materials, and geometry files for output,
        using filenames based on the given name.
        
        Returns None
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
        '''
        file            int
        
        Switch next output to the given file index
        
        Returns None
        '''
        
        self.current_file = file
        
    def _api(self, identifier, args=[], file=None):
        '''
        identifier            string
        args                  list
        file                  None or int
        
        Make a standard pylux.Context API call. In this case
        the identifier followed by its name followed by its
        formatted parameters are written to either the current
        output file, or the file specified by the given index.
        
        Returns None
        '''
        
        if file is not None:
            self.set_output_file(file)
        
        # name is a string, and params a list
        name, params = args
        self.wf(self.current_file, '\n%s "%s"' % (identifier, name))
        for p in params:
            self.wf(self.current_file, self.param_formatter(p), 1)
    
    
    # Wrapped pylux.Context API calls follow ...
    
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

    def arealightSource(self, *args):
        self._api('AreaLightSource', args)
        
    def attributeBegin(self, comment='', file=None):
        '''
        comment            string
        file               None or int
        
        The AttributeBegin block can be used to switch
        the current output file, seeing as we will probably
        be exporting LightSources to the LXS and other
        geometry to LXO.
        '''
        
        self._api('AttributeBegin # ', [comment, []], file=file)
        
    def attributeEnd(self):
        self._api('AttributeEnd #', ['', []])
    
    def transformBegin(self, comment='', file=None):
        '''
        comment            string
        file               None or int
        
        See attributeBegin
        '''
        
        self._api('TransformBegin # ', [comment, []], file=file)
    
    def transformEnd(self):
        self._api('TransformEnd #', ['', []])
        
    def transform(self, values):
        self.wf(self.current_file, '\nTransform [%s]' % ' '.join(['%f'%i for i in values]))
        
    def shape(self, *args):
        self._api('Shape', args, file=self.current_file)
        
    def material(self, *args):
        #self.wf(Files.GEOM, '\nMaterial "%s"' % name)
        self._api('Material', args)
    
    def texture(self, name, type, texture, *params):
        self.wf(Files.MATS, '\nTexture "%s" "%s" "%s"' % (name, type, texture))
        for p in params:
            self.wf(Files.MATS, self.param_formatter(p), 1)
    
    def worldEnd(self):
        '''
        Special handling of worldEnd API.
        See inline comments for further info
        '''
        
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
        #super(luxrender.pylux.Context, self).worldEnd()
        luxrender.pylux.Context.worldEnd(self)
        
        # Add the includes and final WorldEnd so that the file is usable directly in LuxRender
        f=open(self.files[Files.MAIN].name, 'a')
        f.write('\nWorldEnd\n')
        f.close()

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

class ParamSetItem(object):
    
    type  = None
    type_name = None
    name  = None
    value = None
    
    def __init__(self, *args):
        self.type, self.name, self.value = args
        self.type_name = "%s %s" % (self.type, self.name)
    
    def __repr__(self):
        return "<%s:%s:%s>" % (self.type, self.name, self.value)
    
    def to_string(self):
        fs_num = '"%s %s" [%s]'
        fs_str = '"%s %s" ["%s"]'
        
        if self.type == "float" and type(self.value) in (list, tuple):
            return fs_num % ('float', self.name, ' '.join(['%f'%i for i in self.value]))
        if self.type == "float":
            return fs_num % ('float', self.name, '%f' % self.value)
        if self.type == "integer" and type(self.value) in (list, tuple):
            return fs_num % ('integer', self.name, ' '.join(['%i'%i for i in self.value]))
        if self.type == "integer":
            return fs_num % ('integer', self.name, '%i' % self.value)
        if self.type == "string":
            return fs_str % ('string', self.name, self.value)
        if self.type == "vector":
            return fs_num % ('vector', self.name, ' '.join(['%f'%i for i in self.value]))
        if self.type == "point":
            return fs_num % ('point', self.name, ' '.join(['%f'%i for i in self.value]))
        if self.type == "normal":
            return fs_num % ('normal', self.name, ' '.join(['%f'%i for i in self.value]))
        if self.type == "color":
            return fs_num % ('color', self.name, ' '.join(['%f'%i for i in self.value]))
        if self.type == "texture":
            return fs_str % ('texture', self.name, self.value)
        if self.type == "bool":
            if self.value:
                return fs_str % ('bool', self.name, 'true')
            else:
                return fs_str % ('bool', self.name, 'false')
            
        return '# unknown param (%s, %s, %s)' % self

class ParamSet(list):
    
    names = []
    
    def update(self, other):
        for p in other:
            self.add(p.type, p.name, p.value)
    
    def add(self, type, name, value):
        if name in self.names:
            for p in self:
                if p.name == name:
                    self.remove(p)
        
        self.append(
            ParamSetItem(type, name, value)
        )
        self.names.append(name)
        
    def add_float(self, name, value):
        self.add('float', name, value)
       
    def add_integer(self, name, value):
        self.add('integer', name, value)
        
    def add_bool(self, name, value):
        self.add('bool', name, value)
        
    def add_string(self, name, value):
        self.add('string', name, value)
        
    def add_vector(self, name, value):
        self.add('vector', name, value)
        
    def add_point(self, name, value):
        self.add('point', name, value)
        
    def add_normal(self, name, value):
        self.add('normal', name, value)
        
    def add_color(self, name, value):
        self.add('color', name, value)
                 
    def add_texture(self, name, value):
        self.add('texture', name, value)

def matrix_to_list(matrix):
    '''
    matrix          Matrix
    
    Flatten a 4x4 matrix into a list
    
    Returns list[16]
    '''
    
    return [matrix[0][0], matrix[0][1], matrix[0][2], matrix[0][3],\
            matrix[1][0], matrix[1][1], matrix[1][2], matrix[1][3],\
            matrix[2][0], matrix[2][1], matrix[2][2], matrix[2][3],\
            matrix[3][0], matrix[3][1], matrix[3][2], matrix[3][3] ]
    
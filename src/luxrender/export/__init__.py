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
import math

import bpy, mathutils

class ParamSetItem(object):
	
	type		= None
	type_name	= None
	name		= None
	value		= None
	
	WRAP_WIDTH	= 100
	
	def __init__(self, *args):
		self.type, self.name, self.value = args
		self.type_name = "%s %s" % (self.type, self.name)
	
	def __repr__(self):
		return "<%s:%s:%s>" % (self.type, self.name, self.value)
	
	def list_wrap(self, lst, cnt, type='f'):
		fcnt = float(cnt)
		flen = float(len(lst))
		
		if flen > fcnt:
			str = ''
			if type == 'f':
				for row in range( math.ceil(flen/fcnt) ):
					str += ' '.join(['%0.15f'%i for i in lst[(row*cnt):(row+1)*cnt]]) + '\n'
			elif type == 'i':
				for row in range( math.ceil(flen/fcnt) ):
					str += ' '.join(['%i'%i for i in lst[(row*cnt):(row+1)*cnt]]) + '\n'
		else:
			if type == 'f':
				str = ' '.join(['%0.15f'%i for i in lst])
			elif type == 'i':
				str = ' '.join(['%i'%i for i in lst])
		return str
	
	def to_string(self):
		fs_num = '"%s %s" [%s]'
		fs_str = '"%s %s" ["%s"]'
		
		if self.type == "float" and type(self.value) in (list, tuple):
			lst = self.list_wrap(self.value, self.WRAP_WIDTH, 'f')
			return fs_num % ('float', self.name, lst)
		if self.type == "float":
			return fs_num % ('float', self.name, '%0.15f' % self.value)
		if self.type == "integer" and type(self.value) in (list, tuple):
			lst = self.list_wrap(self.value, self.WRAP_WIDTH, 'i')
			return fs_num % ('integer', self.name, lst)
		if self.type == "integer":
			return fs_num % ('integer', self.name, '%i' % self.value)
		if self.type == "string":
			return fs_str % ('string', self.name, self.value.replace('\\', '\\\\'))
		if self.type == "vector":
			lst = self.list_wrap(self.value, self.WRAP_WIDTH, 'f')
			return fs_num % ('vector', self.name, lst)
		if self.type == "point":
			lst = self.list_wrap(self.value, self.WRAP_WIDTH, 'f')
			return fs_num % ('point', self.name, lst)
		if self.type == "normal":
			lst = self.list_wrap(self.value, self.WRAP_WIDTH, 'f')
			return fs_num % ('normal', self.name, lst)
		if self.type == "color":
			return fs_num % ('color', self.name, ' '.join(['%0.8f'%i for i in self.value]))
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
		return self
	
	def add(self, type, name, value):
		if name in self.names:
			for p in self:
				if p.name == name:
					self.remove(p)
		
		self.append(
			ParamSetItem(type, name, value)
		)
		self.names.append(name)
		return self
	
	def add_float(self, name, value):
		self.add('float', name, value)
		return self
	
	def add_integer(self, name, value):
		self.add('integer', name, value)
		return self
	
	def add_bool(self, name, value):
		self.add('bool', name, bool(value))
		return self
	
	def add_string(self, name, value):
		self.add('string', name, str(value))
		return self
	
	def add_vector(self, name, value):
		self.add('vector', name, [i for i in value])
		return self
	
	def add_point(self, name, value):
		self.add('point', name, [p for p in value])
		return self
	
	def add_normal(self, name, value):
		self.add('normal', name, [n for n in value])
		return self
	
	def add_color(self, name, value):
		self.add('color', name, [c for c in value])
		return self
	
	def add_texture(self, name, value):
		self.add('texture', name, str(value))
		return self

def get_worldscale(scene=None, as_scalematrix=True):
	ws = 1.0
	
	if scene == None:
		scn_us = bpy.context.scene.unit_settings
	else:
		scn_us = scene.unit_settings
	
	if scn_us.system in ['METRIC', 'IMPERIAL']:
		# The units used in modelling are for display only. behind
		# the scenes everything is in meters
		ws = scn_us.scale_length
	
	if as_scalematrix:
		return mathutils.ScaleMatrix(ws, 4)
	else:
		return ws

def matrix_to_list(matrix, scene=None, apply_worldscale=False):
	'''
	matrix		  Matrix
	
	Flatten a 4x4 matrix into a list
	
	Returns list[16]
	'''
	
	if apply_worldscale:
		matrix = matrix.copy()
		sm = get_worldscale(scene=scene)
		matrix *= sm
		sm = get_worldscale(scene=scene, as_scalematrix = False)
		matrix[3][0] *= sm
		matrix[3][1] *= sm
		matrix[3][2] *= sm
		
	
	l = [	matrix[0][0], matrix[0][1], matrix[0][2], matrix[0][3],\
			matrix[1][0], matrix[1][1], matrix[1][2], matrix[1][3],\
			matrix[2][0], matrix[2][1], matrix[2][2], matrix[2][3],\
			matrix[3][0], matrix[3][1], matrix[3][2], matrix[3][3] ]
	
	return [float(i) for i in l]

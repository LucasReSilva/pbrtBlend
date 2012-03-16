# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
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
import collections, math, os

import bpy, mathutils

from extensions_framework import util as efutil

from ..outputs import LuxManager, LuxLog
from ..util import bencode_file2string_with_size

class ExportProgressThread(efutil.TimerThread):
	message = '%i%%'
	KICK_PERIOD = 0.2
	total_objects = 0
	exported_objects = 0
	last_update = 0
	def start(self, number_of_meshes):
		self.total_objects = number_of_meshes
		self.exported_objects = 0
		self.last_update = 0
		super().start()
	def kick(self):
		if self.exported_objects != self.last_update:
			self.last_update = self.exported_objects
			pc = int(100 * self.exported_objects/self.total_objects)
			LuxLog(self.message % pc)

class ExportCache(object):
	def __init__(self, name='Cache'):
		self.name = name
		self.cache_keys = set()
		self.cache_items = {}
		self.serial_counter = collections.Counter()
	
	def clear(self):
		self.__init__(name=self.name)
	
	def serial(self, name):
		s = self.serial_counter[name]
		self.serial_counter[name] += 1
		return s
	
	def have(self, ck):
		return ck in self.cache_keys
	
	def add(self, ck, ci):
		self.cache_keys.add(ck)
		self.cache_items[ck] = ci
		
	def get(self, ck):
		if self.have(ck):
			return self.cache_items[ck]
		else:
			raise Exception('Item %s not found in %s!' % (ck, self.name))

class ParamSetItem(list):
	
	WRAP_WIDTH	= 100
	
	def __init__(self, *args):
		self.type, self.name, self.value = args
		self.type_name = "%s %s" % (self.type, self.name)
		self.append(self.type_name)
		self.append(self.value)
	
	def getSize(self, vl=None):
		sz = 0
		
		if vl==None:
			vl=self.value
			sz+=100	# Rough overhead for encoded paramset item
		
		if type(vl) in (list,tuple):
			for v in vl:
				sz += self.getSize(vl=v)
		
		if type(vl) is str:
			sz += len(vl)
		if type(vl) is float:
			sz += 14
		if type(vl) is int:
			if vl==0:
				sz+=1
			else:
				sz += math.floor( math.log10(abs(vl)) ) + 1
		
		return sz
	
	def list_wrap(self, lst, cnt, type='f'):
		fcnt = float(cnt)
		flen = float(len(lst))
		
		if False: #flen > fcnt:
			# LIST WRAPPING DISABLED BECAUSE IT IS HIDEOUSLY EXPENSIVE
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
			if type(self.value) is list:
				return fs_num % ('string', self.name, '\n'.join(['"%s"'%v for v in self.value]))
			else:
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
			
		return '# unknown param (%s, %s, %s)' % (self.type, self.name, self.value)

class ParamSet(list):
	
	def __init__(self):
		self.names = []
		self.item_sizes = {}
	
	def increase_size(self, param_name, sz):
		self.item_sizes[param_name] = sz
	
	def getSize(self):
		sz = 0
		item_sizes_keys = self.item_sizes.keys()
		for p in self:
			if p.name in item_sizes_keys:
				sz += self.item_sizes[p.name]
			else:
				sz += p.getSize()
		return sz
	
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
		if type(value) is list:
			self.add('string', name, [str(v) for v in value])
		else:
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

def get_worldscale(as_scalematrix=True):
	ws = 1.0
	
	scn_us = LuxManager.CurrentScene.unit_settings
	
	if scn_us.system in ['METRIC', 'IMPERIAL']:
		# The units used in modelling are for display only. behind
		# the scenes everything is in meters
		ws = scn_us.scale_length
	
	if as_scalematrix:
		return mathutils.Matrix.Scale(ws, 4)
	else:
		return ws

def object_anim_matrix(scene, obj, frame_offset=1, ignore_scale=False):
	if obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0:
		next_frame = scene.frame_current + frame_offset
		
		anim_location = obj.location.copy()
		anim_rotation = obj.rotation_euler.copy()
		anim_scale    = obj.scale.copy()
		
		for fc in obj.animation_data.action.fcurves:
			if fc.data_path == 'location':
				anim_location[fc.array_index] = fc.evaluate(next_frame)
			if fc.data_path == 'rotation_euler':
				anim_rotation[fc.array_index] = fc.evaluate(next_frame)
			if fc.data_path == 'scale':
				anim_scale[fc.array_index] = fc.evaluate(next_frame)
		
		next_matrix  = mathutils.Matrix.Translation( mathutils.Vector(anim_location) )
		anim_rotn_e = mathutils.Euler(anim_rotation)
		anim_rotn_e.make_compatible(obj.rotation_euler)
		anim_rotn_e = anim_rotn_e.to_matrix().to_4x4()
		next_matrix *= anim_rotn_e
		
		if not ignore_scale:
			next_matrix *= mathutils.Matrix.Scale(anim_scale[0], 4, mathutils.Vector([1,0,0]))
			next_matrix *= mathutils.Matrix.Scale(anim_scale[1], 4, mathutils.Vector([0,1,0]))
			next_matrix *= mathutils.Matrix.Scale(anim_scale[2], 4, mathutils.Vector([0,0,1]))
		
		return next_matrix
	else:
		return False

# hack for the matrix order api change in r42816
# TODO remove this when obsolete
def fix_matrix_order_old(matrix):
	return matrix.transposed()
def fix_matrix_order_new(matrix):
	return matrix

if bpy.app.version[1] >= 62:
	fix_matrix_order = fix_matrix_order_new
else:
	fix_matrix_order = fix_matrix_order_old

def matrix_to_list(matrix, apply_worldscale=False):
	'''
	matrix		  Matrix
	
	Flatten a 4x4 matrix into a list
	
	Returns list[16]
	'''
	
	if apply_worldscale:
		matrix = matrix.copy()
		sm = get_worldscale()
		matrix *= sm
		sm = get_worldscale(as_scalematrix = False)
		matrix = fix_matrix_order(matrix) # matrix indexing hack
		matrix[0][3] *= sm
		matrix[1][3] *= sm
		matrix[2][3] *= sm
	else:
		matrix = fix_matrix_order(matrix) # matrix indexing hack

	
	l = [	matrix[0][0], matrix[1][0], matrix[2][0], matrix[3][0],\
		matrix[0][1], matrix[1][1], matrix[2][1], matrix[3][1],\
		matrix[0][2], matrix[1][2], matrix[2][2], matrix[3][2],\
		matrix[0][3], matrix[1][3], matrix[2][3], matrix[3][3] ]
	
	return [float(i) for i in l]

def process_filepath_data(scene, obj, file_path, paramset, parameter_name):
	file_basename		= os.path.basename(file_path)
	library_filepath	= obj.library.filepath if obj.library else ''
	file_library_path	= efutil.filesystem_path(bpy.path.abspath(file_path, library_filepath))
	file_relative		= efutil.filesystem_path(file_library_path) if obj.library else efutil.filesystem_path(file_path)
	
	if scene.luxrender_engine.allow_file_embed():
		paramset.add_string(parameter_name, file_basename)
		encoded_data, encoded_size = bencode_file2string_with_size(file_relative)
		paramset.increase_size('%s_data' % parameter_name, encoded_size)
		paramset.add_string('%s_data' % parameter_name, encoded_data.splitlines() )
	else:
		paramset.add_string(parameter_name, file_relative)

def get_output_filename(scene):
	return '%s.%s.%05d' % (efutil.scene_filename(), bpy.path.clean_name(scene.name), scene.frame_current)

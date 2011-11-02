# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond, neo2068
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
# System Libs
from __future__ import division
from ctypes import cdll, c_uint, c_float, cast, POINTER, byref, sizeof
import os, struct, sys

# Blender Libs
import bpy

# LuxRender libs
from . import ParamSet, matrix_to_list, LuxManager
from ..outputs import LuxLog
from ..outputs.file_api import Files

class library_loader():
	
	load_lzo_attempted = False
	load_lzma_attempted = False
	
	# imported compression libraries
	has_lzo = False
	lzodll = None
	
	has_lzma = False
	lzmadll = None
	
	ver_str = '%d.%d' % bpy.app.version[0:2]
	
	platform_search = {
		'lzo': {
			'darwin': [
				bpy.utils.user_resource('SCRIPTS','addons/luxrender/liblzo2.dylib' ),
				bpy.app.binary_path[:-7] + ver_str + '/scripts/addons/luxrender/liblzo2.dylib'
			],
			'win32': [
				'lzo.dll',
				bpy.utils.user_resource('SCRIPTS','addons/luxrender/lzo.dll'),
				bpy.app.binary_path[:-11] + ver_str + '/scripts/addons/luxrender/lzo.dll'
			],
			'linux2': [
				'/usr/lib/liblzo2.so',
				'/usr/lib/liblzo2.so.2',
				bpy.app.binary_path[:-7] + ver_str + '/scripts/addons/luxrender/liblzo2.so'
			],
		},
		'lzma': {
			'darwin': [
				bpy.utils.user_resource('SCRIPTS','addons/luxrender/liblzmadec.dylib'),
				bpy.app.binary_path[:-7] + ver_str + '/scripts/addons/luxrender/liblzmadec.dylib'
			],
			'win32': [
				'lzma.dll',
				bpy.utils.user_resource('SCRIPTS','addons/luxrender/lzma.dll'),
				bpy.app.binary_path[:-11] + ver_str + '/scripts/addons/luxrender/lzma.dll'
			],
			'linux2': [
				'/usr/lib/liblzma.so',
				'/usr/lib/liblzma.so.2',
				bpy.app.binary_path[:-7] + ver_str + '/scripts/addons/luxrender/liblzma.so'
			]
		}
	}
	
	@classmethod
	def load_lzo(cls):
		# Only attempt load once per session
		if not cls.load_lzo_attempted:
			
			for sp in cls.platform_search['lzo'][sys.platform]:
				try:
					cls.lzodll = cdll.LoadLibrary(sp)
					cls.has_lzo = True
					break
				except Exception:
					continue
			
			if cls.has_lzo:
				LuxLog('Volumes: LZO Library found')
			else:
				LuxLog('Volumes: LZO Library not found')
			
			cls.load_lzo_attempted = True
		
		return cls.has_lzo, cls.lzodll
	
	@classmethod
	def load_lzma(cls):
		# Only attempt load once per session
		if not cls.load_lzma_attempted:
			
			for sp in cls.platform_search['lzma'][sys.platform]:
				try:
					cls.lzmadll = cdll.LoadLibrary(sp)
					cls.has_lzma = True
					break
				except Exception:
					continue
			
			if cls.has_lzma:
				LuxLog('Volumes: LZMA Library found')
			else:
				LuxLog('Volumes: LZMA Library not found')
			
			cls.load_lzma_attempted = True
		
		return cls.has_lzma, cls.lzmadll

def read_cache(smokecache, is_high_res, amplifier):
	scene = LuxManager.CurrentScene
	
	# NOTE - dynamic libraries are not loaded until needed, further down
	# the script...
	
	###################################################################################################
	# Read cache
	# Pointcache file format:
	#	name								   size of uncompressed data
	#--------------------------------------------------------------------------------------------------
	#	header								( 20 Bytes)
	#	data_segment for shadow values		( cell_count * sizeof(float) Bytes)
	#	data_segment for density values		( cell_count * sizeof(float) Bytes)
	#	data_segment for density,old values	( cell_count * sizeof(float) Bytes)
	#	data_segment for heat values		( cell_count * sizeof(float) Bytes)
	#	data_segment for heat, old values	( cell_count * sizeof(float) Bytes)
	#	data_segment for vx values		( cell_count * sizeof(float) Bytes)
	#	data_segment for vy values		( cell_count * sizeof(float) Bytes)
	#	data_segment for vz values		( cell_count * sizeof(float) Bytes)
	#	data_segment for vx, old values		( cell_count * sizeof(float) Bytes)
	#	data_segment for vy, old values		( cell_count * sizeof(float) Bytes)
	#	data_segment for vz, old values		( cell_count * sizeof(float) Bytes)
	#	data_segment for obstacles values	( cell_count * sizeof(char) Bytes)
	# if simulation is high resolution additionally:
	#	data_segment for density values		( big_cell_count * sizeof(float) Bytes)
	#	data_segment for density,old values	( big_cell_count * sizeof(float) Bytes)
	#	data_segment for tcu values		( cell_count * sizeof(u_int) Bytes)
	#	data_segment for tcv values		( cell_count * sizeof(u_int) Bytes)
	#	data_segment for tcw values		( cell_count * sizeof(u_int) Bytes)
	#
	# header format:
	#	BPHYSICS		(Tag-String, 8 Bytes)
	#	data type		(u_int, 4 Bytes)		=> 3 - PTCACHE_TYPE_SMOKE_DOMAIN
	#	cell count		(u_int, 4 Bytes)		Resolution of the smoke simulation
	#	user data type	(u_int int, 4 Bytes)                    not used by smoke simulation
	#
	# data segment format:
	#	compressed flag	(u_char, 1 Byte)			=> 0 - uncompressed data,
	#								   1 - LZO compressed data,
	#								   2 - LZMA compressed data
	#	stream size		(u_int, 4 Bytes)		size of data stream
	#	data stream		(u_char, (stream_size) Bytes)	data stream
	# if lzma-compressed additionally:
	#	props size		(u_int, 4 Bytes)		size of props ( has to be 5 Bytes)
	#	props			(u_char, (props_size) Bytes)	props data for lzma decompressor
	#
	###################################################################################################
	density = []
	cachefilepath = []
	cachefilename = []
	if not smokecache.is_baked:
		LuxLog('Volumes: Smoke data has to be baked for export')
	else:
		cachefilepath = os.path.join(
			os.path.splitext(os.path.dirname(bpy.data.filepath))[0],
			"blendcache_" + os.path.splitext(os.path.basename(bpy.data.filepath))[0]
		)
		cachefilename = smokecache.name+"_{0:06d}_{1:02d}.bphys".format(scene.frame_current,smokecache.index)
		fullpath = os.path.join( cachefilepath, cachefilename )
		if not os.path.exists(fullpath):
			LuxLog('Volumes: Cachefile doesn''t exist: %s' % fullpath)
		else:
			cachefile = open(fullpath, "rb")
			buffer = cachefile.read(8)
			temp = ""
			stream_size = c_uint()
			props_size = c_uint()
			outlen = c_uint()
			compressed = 0
			
			for i in range(len(buffer)):
				temp = temp + chr(buffer[i])
			
			SZ_FLOAT = sizeof(c_float)
			SZ_UINT  = sizeof(c_uint)
			
			if temp == "BPHYSICS":	#valid cache file
				data_type = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
				#print("Data type: {0:1d}".format(data_type))
				if (data_type == 3) or (data_type == 4):
					cell_count = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
					#print("Cell count: {0:1d}".format(cell_count))
					struct.unpack("1I", cachefile.read(SZ_UINT))[0]
					
					# Shadow values
					compressed = struct.unpack("1B", cachefile.read(1))[0]
					if not compressed:
						cachefile.read(SZ_FLOAT*cell_count)
					else:
						stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
						cachefile.read(stream_size)
						if compressed == 2:
							props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(props_size)
					
					# Density values
					compressed = struct.unpack("1B", cachefile.read(1))[0]
					if not compressed:
						cachefile.read(SZ_FLOAT*cell_count)
					else:
						stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
						stream = cachefile.read(stream_size)
						if compressed == 2:
							props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							props = cachefile.read(props_size)
					
					if is_high_res:
						# Densitiy, old values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						
						# Heat values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						
						# Heat, old values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						# vx values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						# vy values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						# vz values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						# vx, old values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						# vy,old values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						# vz,old values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						# Obstacle values
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								cachefile.read(props_size)
						
						# dt value
						cachefile.read(4)
						# dx value
						cachefile.read(4)
						
						# High resolution
						# Density values
						
						cell_count = cell_count * amplifier * amplifier * amplifier
						
						compressed = struct.unpack("1B", cachefile.read(1))[0]
						if not compressed:
							cachefile.read(SZ_FLOAT*cell_count)
						else:
							stream_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
							stream = cachefile.read(stream_size)
							if compressed == 2:
								props_size = struct.unpack("1I", cachefile.read(SZ_UINT))[0]
								props = cachefile.read(props_size)
					
					if compressed == 1:
						has_lzo, lzodll = library_loader.load_lzo()
						if has_lzo:
							LuxLog('Volumes: De-compressing LZO stream of length {0:0d} bytes...'.format(stream_size))
							#print("Cell count: %d"%cell_count)
							uncomp_stream = (c_float*cell_count*SZ_FLOAT)()
							p_dens = cast(uncomp_stream, POINTER(c_float))
							
							#call lzo decompressor
							lzodll.lzo1x_decompress(stream,stream_size,p_dens,byref(outlen), None)
							
							for i in range(cell_count):
								density.append(p_dens[i])
						else:
							LuxLog('Volumes: Cannot read compressed LZO stream; no library loaded')
					
					elif compressed == 2:
						has_lzma, lzmadll = library_loader.load_lzma()
						if has_lzma:
							LuxLog('Volumes: De-compressing LZMA stream of length {0:0d} bytes...'.format(stream_size))
							#print("Cell count: %d"%cell_count)
							uncomp_stream = (c_float*cell_count*SZ_FLOAT)()
							p_dens = cast(uncomp_stream, POINTER(c_float))
							outlen = c_uint(cell_count*SZ_FLOAT)
							
							#call lzma decompressor
							lzmadll.LzmaUncompress(p_dens, byref(outlen), stream, byref(c_uint(stream_size)), props, props_size)
							
							for i in range(cell_count):
								density.append(p_dens[i])
						else:
							LuxLog('Volumes: Cannot read compressed LZMA stream; no library loaded')
			
			cachefile.close()
			#endif cachefile exists
			return density
	return []

def export_smoke(lux_context, scene):
	#Search smoke domain objects
	for object in scene.objects:
		for mod in object.modifiers:
			if mod.name == 'Smoke':
				if mod.smoke_type == 'DOMAIN':
					eps = 0.000001
					domain = object
					p = []
					# gather smoke domain settings
					BBox = domain.bound_box
					p.append([BBox[0][0], BBox[0][1], BBox[0][2]])
					p.append([BBox[6][0], BBox[6][1], BBox[6][2]])
					set = mod.domain_settings
					resolution = set.resolution_max
					smokecache = set.point_cache
					density = read_cache(smokecache, set.use_high_resolution, set.amplify+1)

					#standard values for volume material
					sigma_s = [1.0, 1.0, 1.0]
					sigma_a = [1.0, 1.0, 1.0]
					g = 0.0

					if hasattr(domain.active_material,'luxrender_material'):
						int_v = object.active_material.luxrender_material.Interior_volume
						for volume in scene.luxrender_volumes.volumes:
							if volume.name == int_v and volume.type == 'homogeneous':
								data = volume.api_output(lux_context)[1]
								for param in data:
									if param[0] == 'color sigma_a': sigma_a = param[1]
									if param[0] == 'color sigma_s': sigma_s = param[1]
									if param[0] == 'color g': g = param[1][0]


					max = domain.dimensions[0]
					if (max - domain.dimensions[1]) < -eps: max = domain.dimensions[1]
					if (max - domain.dimensions[2]) < -eps: max = domain.dimensions[2]
					
					big_res = [int(round(resolution*domain.dimensions[0]/max,0)),int(round(resolution*domain.dimensions[1]/max,0)),int(round(resolution*domain.dimensions[2]/max,0))]
					if set.use_high_resolution: big_res = [big_res[0]*(set.amplify+1), big_res[1]*(set.amplify+1), big_res[2]*(set.amplify+1)]

					if len(density) == big_res[0]*big_res[1]*big_res[2]:
						lux_context.attributeBegin(comment=domain.name, file=Files.VOLM)
						lux_context.transform(matrix_to_list(domain.matrix_world, apply_worldscale=True))
						volume_params = ParamSet() \
										.add_integer('nx', big_res[0]) \
										.add_integer('ny', big_res[1]) \
										.add_integer('nz', big_res[2]) \
										.add_point('p0',p[0]) \
										.add_point('p1',p[1]) \
										.add_float('density', density) \
										.add_color('sigma_a', sigma_a) \
										.add_color('sigma_s', sigma_s) \
										.add_float('g', g)
						lux_context.volume('volumegrid', volume_params)
						lux_context.attributeEnd()

						LuxLog('Volumes: Volume Exported: %s' % domain.name)
					else:
						LuxLog('Volumes: Volume Export failed: %s' % domain.name)

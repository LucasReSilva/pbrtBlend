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
import os

from luxrender.outputs import LuxLog

class Files(object):
	MAIN = 0
	MATS = 1
	GEOM = 2

class Custom_Context(object):
	'''
	Wrap the real pylux Context object so that we can
	change the behaviour of certain API calls (ie. write
	to files and use the Context to monitor rendering)
	'''
	
	API_TYPE = 'FILE'
	
	context_name = ''
	files = []
	file_names = []
	current_file = Files.MAIN
	parse_at_worldend = True
	
	def __init__(self, name):
		self.context_name = name
	
	def wf(self, ind, st, tabs=0):
		'''
		ind					int
		st					string
		tabs				int
		
		Write a string followed by newline to file index ind.
		Optionally indent the string by a number of tabs
		
		Returns None
		'''
		
		if len(self.files) == 0:
			self.set_filename('default')
		
		self.files[ind].write('%s%s\n' % ('\t'*tabs, st))
		self.files[ind].flush()
		
	def set_filename(self, name, LXS=True, LXM=True, LXO=True):
		'''
		name				string
		
		Open the main, materials, and geometry files for output,
		using filenames based on the given name.
		
		Returns None
		'''
		
		# If any files happen to be open, close them and start again
		for f in self.files:
			if f is not None:
				f.close()
		
		self.files = []
		self.file_names = []
		
		self.file_names.append('%s.lxs' % name)
		if LXS:
			self.files.append(open(self.file_names[Files.MAIN], 'w'))
			self.wf(Files.MAIN, '# Main Scene File')
		else:
			self.files.append(None)
		
		self.file_names.append('%s-mat.lxm' % name)
		if LXM:
			self.files.append(open(self.file_names[Files.MATS], 'w'))
			self.wf(Files.MATS, '# Materials File')
		else:
			self.files.append(None)
		
		self.file_names.append('%s-geom.lxo' % name)
		if LXO:
			self.files.append(open(self.file_names[Files.GEOM], 'w'))
			self.wf(Files.GEOM, '# Geometry File')
		else:
			self.files.append(None)
		
	def set_output_file(self, file):
		'''
		file				int
		
		Switch next output to the given file index
		
		Returns None
		'''
		
		self.current_file = file
		
	def _api(self, identifier, args=[], file=None):
		'''
		identifier			string
		args				list
		file				None or int
		
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
			self.wf(self.current_file, p.to_string(), 1)
	
	# Wrapped pylux.Context API calls follow ...

	def objectBegin(self, name, file=None):
		self._api('ObjectBegin ', [name, []], file=file)

	def objectEnd(self, comment=''):
		self._api('ObjectEnd # ', [comment, []])
	
	def objectInstance(self, name):
		self._api('ObjectInstance ', [name, []])
	
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
	
	def coordinateSystem(self, name):
		self._api('CoordinateSystem', [name, []])
	
	def identity(self):
		self._api('Identity #', ['', []])
	
	def camera(self, *args):
		self._api('Camera', args)
	
	def film(self, *args):
		self._api('Film', args)
	
	def worldBegin(self, *args):
		self.wf(Files.MAIN, '\nWorldBegin')
	
	def lightGroup(self, *args):
		self._api('LightGroup', args)
	
	def lightSource(self, *args):
		self._api('LightSource', args)

	def areaLightSource(self, *args):
		self._api('AreaLightSource', args)

	def motionInstance(self, name, start, stop, motion_name):
		self.wf(self.current_file, '\nMotionInstance "%s" %f %f "%s"' % (name, start, stop, motion_name))
		
	def attributeBegin(self, comment='', file=None):
		'''
		comment				string
		file				None or int
		
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
		comment				string
		file				None or int
		
		See attributeBegin
		'''
		
		self._api('TransformBegin # ', [comment, []], file=file)
	
	def transformEnd(self):
		self._api('TransformEnd #', ['', []])
		
	def transform(self, values):
		self.wf(self.current_file, '\nTransform [%s]' % ' '.join(['%0.15f'%i for i in values]))
		
	def shape(self, *args):
		self._api('Shape', args, file=self.current_file)
	
	def portalShape(self, *args):
		self._api('PortalShape', args, file=self.current_file)
		
	def material(self, *args):
		self._api('Material', args)
		
	def namedMaterial(self, name):
		self._api('NamedMaterial', [name, []])
	
	def makeNamedMaterial(self, name, params):
		self.wf(Files.MATS, '\nMakeNamedMaterial "%s"' % name)
		for p in params:
			self.wf(Files.MATS, p.to_string(), 1)
	
	def makeNamedVolume(self, name, type, params):
		self.wf(Files.MATS, '\nMakeNamedVolume "%s" "%s"' % (name, type))
		for p in params:
			self.wf(Files.MATS, p.to_string(), 1)
	
	def texture(self, name, type, texture, params):
		self.wf(self.current_file, '\nTexture "%s" "%s" "%s"' % (name, type, texture))
		for p in params:
			self.wf(self.current_file, p.to_string(), 1)
	
	def worldEnd(self):
		'''
		Special handling of worldEnd API.
		See inline comments for further info
		'''
		
		if self.files[Files.MAIN] is not None:
			# Include the other files if they exist
			for idx in [Files.MATS, Files.GEOM]:
				if os.path.exists(self.file_names[idx]):
					self.wf(Files.MAIN, '\nInclude "%s"' % self.file_names[idx])
			
			# End of the world as we know it
			self.wf(Files.MAIN, 'WorldEnd')
		
		# Close files
		LuxLog('Wrote scene files')
		for f in self.files:
			if f is not None:
				f.close()
				LuxLog(' %s' % f.name)
	
	def cleanup(self):
		self.exit()
	
	def exit(self):
		# If any files happen to be open, close them and start again
		for f in self.files:
			if f is not None:
				f.close()
	
	def wait(self):
		pass
	
	def parse(self, filename, async):
		'''
		In a deviation from the API, this function returns a new context,
		which must be passed back to LuxManager so that it can control the
		rendering process.
		'''
		from luxrender.outputs.pure_api import PYLUX_AVAILABLE
		if PYLUX_AVAILABLE:
			from luxrender.outputs.pure_api import Custom_Context as Pylux_Context
			c = Pylux_Context(self.context_name)
			c.parse(filename, async)
			
			return c
		else:
			raise Exception('This method requires pylux')

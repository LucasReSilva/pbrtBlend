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
import collections, json

class Custom_Context(object):
	'''
	Imitate the real pylux Context object so that we can
	write materials to LBM2 files using the same API
	
	NOTE; not all API calls are supported by this context,
	just enough to allow material/texture/volume export
	'''
	
	API_TYPE = 'FILE'
	
	def __init__(self, name):
		self.context_name = name
		self.lbm2_name = ''
		self.lbm2_category = -1
		self.lbm2_version = '0.8'
		self.lbm2_objects = []
	
	def set_material_metadata(self, name, category=-1, version='0.8'):
		self.lbm2_name = name
		self.lbm2_category = category
		self.lbm2_version = version
	
	def _get_lbm2(self, add_comment=False):
		# The only reason to use OrderedDict is so that _comment
		# appears at the top of the file
		
		lbm2_data = collections.OrderedDict()
		if add_comment: lbm2_data['_comment'] = 'LBM2 material data saved by LuxBlend25'
		lbm2_data['name'] = self.lbm2_name
		lbm2_data['category_id'] = self.lbm2_category
		lbm2_data['version'] = self.lbm2_version
		lbm2_data['objects'] = self.lbm2_objects
		return lbm2_data
	
	def write(self, filename):
		with open(filename, 'w') as output_file:
			
			json.dump(
				self._get_lbm2(add_comment=True),
				output_file,
				indent=2
			)
	
	def upload(self, lrmdb_client):
		if lrmdb_client.loggedin:
			s = lrmdb_client.server_instance()
			upload = s.material.submit(dict(self._get_lbm2()))
			if type(upload) is str:
				raise Exception(upload)
			return upload
		else:
			raise Exception("Not logged in!")
	
	def getRenderingServersStatus(self):
		return []
	
	def _api(self, identifier, args=[], extra_tokens=''):
		'''
		identifier			string
		args				list
		
		Make a standard pylux.Context API call. In this case
		the API call is translated into a minimal dict that
		will later be passed to json.dump
		
		Returns None
		'''
		
		# name is a string, and params a list
		name, params = args
		
		obj = {
			'type': identifier,
			'name': name,
			'extra_tokens': extra_tokens,
			'paramset': [],
		}
		
		for p in params:
			obj['paramset'].append({
				'type': p.type,
				'name': p.name,
				'value': p.value
			})
			
		self.lbm2_objects.append(obj)
	
	# Wrapped pylux.Context API calls follow ...
	
	#def objectBegin(self, name, file=None):
	#	self._api('ObjectBegin ', [name, []], file=file)
	
	#def objectEnd(self, comment=''):
	#	self._api('ObjectEnd # ', [comment, []])
	
	#def objectInstance(self, name):
	#	self._api('ObjectInstance ', [name, []])
	
	#def portalInstance(self, name):
	#	# Backwards compatibility
	#	if LUXRENDER_VERSION < '0.8':
	#		LuxLog('WARNING: Exporting PortalInstance as ObjectInstance; Portal will not be effective')
	#		self._api('ObjectInstance ', [name, []])
	#	else:
	#		self._api('PortalInstance ', [name, []])
	
	#def renderer(self, *args):
	#	self._api('Renderer', args)
	
	#def sampler(self, *args):
	#	self._api('Sampler', args)
	
	#def accelerator(self, *args):
	#	self._api('Accelerator', args)
	
	#def surfaceIntegrator(self, *args):
	#	self._api('SurfaceIntegrator', args)
	
	#def volumeIntegrator(self, *args):
	#	self._api('VolumeIntegrator', args)
	
	#def pixelFilter(self, *args):
	#	self._api('PixelFilter', args)
	
	#def lookAt(self, *args):
	#	self.wf('\nLookAt %s' % ' '.join(['%f'%i for i in args]))
	
	#def coordinateSystem(self, name):
	#	self._api('CoordinateSystem', [name, []])
	
	#def identity(self):
	#	self._api('Identity #', ['', []])
	
	#def camera(self, *args):
	#	self._api('Camera', args)
	
	#def film(self, *args):
	#	self._api('Film', args)
	
	#def worldBegin(self, *args):
	#	self.wf('\nWorldBegin')
	
	#def lightGroup(self, *args):
	#	self._api('LightGroup', args)
	
	#def lightSource(self, *args):
	#	self._api('LightSource', args)
	
	#def areaLightSource(self, *args):
	#	self._api('AreaLightSource', args)
	
	#def motionInstance(self, name, start, stop, motion_name):
	#	self.wf('\nMotionInstance "%s" %f %f "%s"' % (name, start, stop, motion_name))
		
	#def attributeBegin(self, comment='', file=None):
	#	self._api('AttributeBegin # ', [comment, []], file=file)
		
	#def attributeEnd(self):
	#	self._api('AttributeEnd #', ['', []])
	
	#def transformBegin(self, comment='', file=None):
	#	self._api('TransformBegin # ', [comment, []], file=file)
	
	#def transformEnd(self):
	#	self._api('TransformEnd #', ['', []])
	
	#def concatTransform(self, values):
	#	self.wf('\nConcatTransform [%s]' % ' '.join(['%0.15f'%i for i in values]))
	
	#def transform(self, values):
	#	self.wf('\nTransform [%s]' % ' '.join(['%0.15f'%i for i in values]))
	
	#def scale(self, x,y,z):
	#	self.wf('\nScale %s' % ' '.join(['%0.15f'%i for i in [x,y,z]]))
	
	#def rotate(self, a,x,y,z):
	#	self.wf('\nRotate %s' % ' '.join(['%0.15f'%i for i in [a,x,y,z]]))
	
	#def shape(self, *args):
	#	self._api('Shape', args, file=self.current_file)
	
	#def portalShape(self, *args):
	#	self._api('PortalShape', args, file=self.current_file)
	
	#def material(self, *args):
	#	self._api('Material', args)
	
	#def namedMaterial(self, name):
	#	self._api('NamedMaterial', [name, []])
	
	def makeNamedMaterial(self, name, params):
		self._api("MakeNamedMaterial", [name, params])
	
	def makeNamedVolume(self, name, type, params):
		self._api("MakeNamedVolume", [name, params], extra_tokens='"%s"'%type)
	
	def interior(self, name):
		self._api('Interior ', [name, []])
	
	def exterior(self, name):
		self._api('Exterior ', [name, []])
	
	#def volume(self, args):
	#	self._api("Volume", *args)
	
	def texture(self, name, type, texture, params):
		self._api("Texture", [name, params], extra_tokens='"%s" "%s"' % (type,texture))
	
	#def worldEnd(self):
	#	self.wf('WorldEnd')
	
	def cleanup(self):
		pass
	
	def exit(self):
		pass
	
	def wait(self):
		pass

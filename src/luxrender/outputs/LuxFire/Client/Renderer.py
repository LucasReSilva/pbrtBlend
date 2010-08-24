# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# LuxFire Distributed Rendering System
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

#------------------------------------------------------------------------------ 
# Pyro Imports
import Pyro.util
#------------------------------------------------------------------------------ 

class RemoteCallable(object):
	'''
	Function proxy for remote pylux.Context
	'''
	
#===============================================================================
#   ATTRIBUTES
#===============================================================================
	
	# Remote RenderServer object to call
	RemoteRenderer = None
	
	# Name of the Context method to call
	remote_method   = None
	
#================================================================================
#   INITIALISATION
#================================================================================
	
	def __init__(self, RemoteRenderer, remote_method):
		'''
		Initialise callable with a RemoteRenderer and a method name
		'''
		
		self.RemoteRenderer = RemoteRenderer
		self.remote_method = remote_method
	
#================================================================================
#   INVOKATION
#================================================================================
	
	def __call__(self, *a, **k):
		'''
		Proxy calling this object to the remote Context
		'''
		
		#try:
		#print('Calling %s()' % self.remote_method)
		a = list(a)
		for i,arg in enumerate(a):
			# Convert ParamSet object to nested lists
			if type(arg).__name__ == 'ParamSet':
				a[i] = [list(i) for i in arg]
			#print('%s -> %s' % (type(arg), type(a[i])))
		
		if self.remote_method in ['attributeBegin', 'transformBegin']:
			return self.RemoteRenderer.luxcall(self.remote_method)
		else:
			return self.RemoteRenderer.luxcall(self.remote_method, *a, **k)
		#except Exception as err:
		#	# Get meaningful output from remote exception;
		#	# Boost.Python exceptions cannot be pickled
		#	print(''.join( Pyro.util.getPyroTraceback(err) ))
#===============================================================================
#   END
#===============================================================================


class RendererClient(object):
	'''
	Client proxy for a remote RendererServer object
	'''
	
#===============================================================================
#   ATTRIBUTES
#===============================================================================

	# Remote RenderServer object
	RemoteRenderer = None
	
	# List of methods and attributes in the remote Context object
	RemoteContextMethods = []
	
	API_TYPE = 'LFC'
	
#================================================================================
#   INITIALISATION
#================================================================================
	
	def __init__(self, RemoteRenderer):
		'''
		Initialise client object with the server object, and ask the
		server which methods and attributes the remote Context has
		'''
		
		self.RemoteRenderer = RemoteRenderer
		self.RemoteContextMethods = RemoteRenderer.get_context_methods()
		#print('LuxFire Server has methods: %s' % self.RemoteContextMethods)
	
#================================================================================
#   INVOKATION
#================================================================================
	
	def __getattr__(self, m):
		'''
		When asking this client for an attribute or method, first check
		to see if we should call the remote Context, if not then try
		to find the attribute or method in the RendererServer
		'''
		
		if m in self.RemoteContextMethods:
			return RemoteCallable(self.RemoteRenderer, m)
		elif not m.startswith('_'):
			return getattr(self.RemoteRenderer, m)
		else:
			raise AttributeError('Cannot access remote private members')
	
#===============================================================================
#   END
#===============================================================================

# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# David Bucciarelli
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
import shutil
import tempfile
import os
import platform
import re
import bpy

from collections import Iterable
from ..outputs import LuxLog

def ToValidLuxCoreName(name):
	return re.sub('[^_0-9a-zA-Z]+', '_', name)

def LuxCoreLogHandler(msg):
	LuxLog(msg)

def FlattenStrCollection(coll):
	for i in coll:
		if isinstance(i, Iterable):
			if (type(i) is str):
				yield i
			else:
				for subc in FlattenStrCollection(i):
					yield subc

def UseLuxCore():
	return True if bpy.context.scene.luxrender_engine.selected_luxrender_api == 'luxcore' else False

def ScenePrefix():
	return 'importlib.import_module(\'bpy\').context.scene.'

if not 'PYLUXCORE_AVAILABLE' in locals():
	try:
		if platform.system() == 'Windows':
			# On Windows, shared libraries cannot be overwritten
			# while loaded.
			# In order to facilitate in-place updates on Windows, 
			# copy luxcore to temp directory and load from there
			import sys
			orig_sys_path = sys.path
			try:
				sdir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
				sname = os.path.join(sdir, 'pyluxcore.pyd')
				
				tdir = os.path.abspath(os.path.join(os.path.realpath(tempfile.gettempdir()), 'luxblend25'))
				tname = os.path.join(tdir, 'pyluxcore.pyd')
				
				if not os.path.isdir(tdir):
					os.mkdir(tdir)
				
				import filecmp
				# Check if temp module is up to date, in case multiple copies of Blender
				# is launched. May still fail if launched in too quick succession but better
				# than nothing. Also avoids redundant copy.
				if not (os.path.isfile(tname) and filecmp.cmp(sname, tname, shallow=False)):
					LuxLog('Updating dynamic pyluxcore module')
					# files are not equal, if copy fails then fall back
					shutil.copyfile(sname, tname)
				
				# override sys.path for module loading
				sys.path.insert(0, tdir)
				
				import pyluxcore
				LuxLog('Using dynamic pyluxcore module')
				
			except Exception as e:
				LuxLog('Error loading dynamic pyluxcore module: %s' % str(e))
				LuxLog('Falling back to regular pyluxcore module')
				sys.path = orig_sys_path
				from .. import pyluxcore
				
			# reset sys.path (safer here than in try block)
			sys.path = orig_sys_path
		else:
			from .. import pyluxcore
		
		pyluxcore.Init(LuxCoreLogHandler)
		LUXCORE_VERSION = pyluxcore.Version()

		PYLUXCORE_AVAILABLE = True
		LuxLog('Using pyluxcore version %s' % LUXCORE_VERSION)
		
	except ImportError as err:
		LuxLog('WARNING: Binary pyluxcore module not available! Visit http://www.luxrender.net/ to obtain one for your system.')
		LuxLog(' (ImportError was: %s)' % err)
		PYLUXCORE_AVAILABLE = False

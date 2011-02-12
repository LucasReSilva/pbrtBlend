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
'''
LuxRender Addon for Blender 2.5
'''

bl_info = {
	"name": "LuxRender",
	"author": "Doug Hammond (dougal2)",
	"version": (0, 8, 0, 'RC1'),
	"blender": (2, 5, 6),
	"api": 34784,
	"category": "Render",
	"location": "Render > Engine > LuxRender",
	"warning": "",
	"wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/LuxBlend",
	"tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=23361&group_id=153&atid=514",
	"description": "This Addon will allow you to render your scenes with the LuxRender engine."
}
bl_addon_info = {
	"name": "LuxRender",
	"author": "Doug Hammond (dougal2)",
	"version": (0, 8, 0, 'RC1'),
	"blender": (2, 5, 6),
	"api": 34784,
	"category": "Render",
	"location": "Render > Engine > LuxRender",
	"warning": "",
	"wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/LuxBlend",
	"tracker_url": "http://projects.blender.org/tracker/index.php?func=detail&aid=23361&group_id=153&atid=514",
	"description": "This Addon will allow you to render your scenes with the LuxRender engine."
}



if 'core' in locals():
	import imp
	imp.reload(core)
else:
	import bpy
	from extensions_framework import Addon
	addon_register_class, register, unregister = Addon().init_functions()
	
	# Importing the core package causes class registration magic with the
	# above Addon() instance, due to the addon_register_class decorator
	from luxrender import core

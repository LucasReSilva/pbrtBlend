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
bl_info = {
	"name": "LuxRender",
	"author": "LuxRender Project: Doug Hammond (dougal2), Asbjørn Heid (LordCrc), Daniel Genrich (Genscher), Jens Verwiebe, Jason Clarke (JtheNinja), neo2068",
	"version": (1, 2, 1),
	"blender": (2, 6, 5),
	"api": 44256,
	"category": "Render",
	"location": "Info Header > Engine dropdown menu",
	"warning": "",
	"wiki_url": "http://www.luxrender.net/wiki/LuxBlend25_Manual",
	"tracker_url": "http://www.luxrender.net/mantis",
	"description": "LuxRender integration for Blender"
}

if 'core' in locals():
	import imp
	imp.reload(core)
else:
	import bpy
	
	from extensions_framework import Addon
	LuxRenderAddon = Addon(bl_info)
	register, unregister = LuxRenderAddon.init_functions()
	
	# Importing the core package causes extensions_framework managed
	# RNA class registration via @LuxRenderAddon.addon_register_class
	from . import core

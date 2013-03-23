# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 LuxRender Add-On
# --------------------------------------------------------------------------
#
# Authors:
# Jens Verwiebe, Jason Clarke
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

import re

import bpy

from extensions_framework import declarative_property_group

from .. import LuxRenderAddon
from ..properties.texture import (
	FloatTextureParameter, ColorTextureParameter, FresnelTextureParameter,
	import_paramset_to_blender_texture, shorten_name, refresh_preview
)
from ..export import ParamSet, process_filepath_data
from ..export.materials import (
	MaterialCounter, ExportedMaterials, ExportedTextures, add_texture_parameter, get_texture_from_scene
)
from ..outputs import LuxManager, LuxLog
from ..util import dict_merge

@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_harlequin(bpy.types.Node):
	'''Harlequin texture node'''
	bl_idname = 'luxrender_texture_harlequin_node'
	bl_label = 'Harlequin Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketColor', 'Color')
		
@LuxRenderAddon.addon_register_class
class luxrender_texture_type_node_windy(bpy.types.Node):
	'''Windy texture node'''
	bl_idname = 'luxrender_texture_windy_node'
	bl_label = 'Windy Texture'
	bl_icon = 'TEXTURE'

	def init(self, context):
		self.outputs.new('NodeSocketFloat', 'Float')
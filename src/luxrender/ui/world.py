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
import bpy
from properties_world import WorldButtonsPanel 

# EF API
from ef.ui import described_layout
from ef.ef import ef

# Lux API
import luxrender.properties.world

class LUXRENDER_OT_volume_add(bpy.types.Operator):
	bl_idname = "luxrender.volume_add"
	bl_label = "Add LuxRender Volume"
	
	def invoke(self, context, event):
		v = context.scene.luxrender_world.volumes
		v.add()
		v[len(v)-1].name = 'New Volume'
		return {'FINISHED'}
	
class LUXRENDER_OT_volume_remove(bpy.types.Operator):
	bl_idname = "luxrender.volume_remove"
	bl_label = "Remove LuxRender Volume"
	
	def invoke(self, context, event):
		w = context.scene.luxrender_world
		w.volumes.remove( w.volumes_index )
		return {'FINISHED'}

class world(WorldButtonsPanel, described_layout, bpy.types.Panel):
	bl_label = 'LuxRender World Options'
	COMPAT_ENGINES = {'luxrender'}
	
	property_group = luxrender.properties.world.luxrender_world
	
	controls = [
		'volumes_label',
		'volumes_select',
		['op_vol_add', 'op_vol_rem']
	]
	
	visibility = {
		
	}
	
	properties = [
		{
			'type': 'collection',
			'ptype': luxrender.properties.world.luxrender_volume_data,
			'name': 'volumes',
			'attr': 'volumes',
			'items': [
				
			]
		},
		{
			'type': 'text',
			'attr': 'volumes_label',
			'name': 'Volumes',
		},
		{
			'type': 'int',
			'name': 'volumes_index',
			'attr': 'volumes_index',
		},
		{
			'type': 'template_list',
			'name': 'volumes_select',
			'attr': 'volumes_select',
			'trg': lambda sc,c: c.luxrender_world,
			'trg_attr': 'volumes_index',
			'src': lambda sc,c: c.luxrender_world,
			'src_attr': 'volumes',
		},
		{
			'type': 'operator',
			'attr': 'op_vol_add',
			'operator': 'luxrender.volume_add',
			'text': 'Add',
			'icon': 'PLUS',
		},
		{
			'type': 'operator',
			'attr': 'op_vol_rem',
			'operator': 'luxrender.volume_remove',
			'text': 'Remove',
			'icon': 'X',
		},
	]
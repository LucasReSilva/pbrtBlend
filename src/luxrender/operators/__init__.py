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
# Blender Libs
import bpy
from presets import AddPresetBase

# LuxRender Libs
from luxrender.export.scene import SceneExporter

# Per-IDPropertyGroup preset handling

class LUXRENDER_MT_base(object):
	preset_operator = "script.execute_preset"
	def draw(self, context):
		return bpy.types.Menu.draw_preset(self, context)

class LUXRENDER_OT_preset_base(AddPresetBase):
	pass

class LUXRENDER_MT_presets_engine(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Engine Presets"
	preset_subdir = "luxrender/engine"

class LUXRENDER_OT_preset_engine_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_engine_add'
	bl_label = 'Add LuxRender Engine settings preset'
	preset_menu = 'LUXRENDER_MT_presets_engine'
	preset_values = [
		'bpy.context.scene.luxrender_engine.%s'%v['attr'] for v in bpy.types.luxrender_engine.get_exportable_properties()
	] + [
		'bpy.context.scene.luxrender_sampler.%s'%v['attr'] for v in bpy.types.luxrender_sampler.get_exportable_properties()
	] + [
		'bpy.context.scene.luxrender_integrator.%s'%v['attr'] for v in bpy.types.luxrender_integrator.get_exportable_properties()
	] + [
		'bpy.context.scene.luxrender_volumeintegrator.%s'%v['attr'] for v in bpy.types.luxrender_volumeintegrator.get_exportable_properties()
	] + [
		'bpy.context.scene.luxrender_filter.%s'%v['attr'] for v in bpy.types.luxrender_filter.get_exportable_properties()
	] + [
		'bpy.context.scene.luxrender_accelerator.%s'%v['attr'] for v in bpy.types.luxrender_accelerator.get_exportable_properties()
	]
	preset_subdir = 'luxrender/engine'

class LUXRENDER_MT_presets_networking(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Networking Presets"
	preset_subdir = "luxrender/networking"

class LUXRENDER_OT_preset_networking_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_networking_add'
	bl_label = 'Add LuxRender Networking settings preset'
	preset_menu = 'LUXRENDER_MT_presets_networking'
	preset_values = [
		'bpy.context.scene.luxrender_networking.%s'%v['attr'] for v in bpy.types.luxrender_networking.get_exportable_properties()
	]
	preset_subdir = 'luxrender/networking'

class LUXRENDER_MT_presets_material(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Material Presets"
	preset_subdir = "luxrender/material"

class LUXRENDER_OT_preset_material_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_material_add'
	bl_label = 'Add LuxRender Material settings preset'
	preset_menu = 'LUXRENDER_MT_presets_material'
	preset_values =  []
	preset_subdir = 'luxrender/material'
	
	def execute(self, context):
		pv = [
			'bpy.context.material.luxrender_material.%s'%v['attr'] for v in bpy.types.luxrender_material.get_exportable_properties()
		] + [
			'bpy.context.material.luxrender_emission.%s'%v['attr'] for v in bpy.types.luxrender_emission.get_exportable_properties()
		] + [
			'bpy.context.material.luxrender_transparency.%s'%v['attr'] for v in bpy.types.luxrender_transparency.get_exportable_properties()
		]
		
		# store only the sub-properties of the selected lux material type
		lux_type = context.material.luxrender_material.type
		sub_type = getattr(bpy.types, 'luxrender_mat_%s' % lux_type)
		
		pv.extend([
			'bpy.context.material.luxrender_material.luxrender_mat_%s.%s'%(lux_type, v['attr']) for v in sub_type.get_exportable_properties()
		])
		
		self.preset_values = pv
		return super().execute(context)

class LUXRENDER_MT_presets_texture(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Texture Presets"
	preset_subdir = "luxrender/texture"

class LUXRENDER_OT_preset_texture_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_texture_add'
	bl_label = 'Add LuxRender Texture settings preset'
	preset_menu = 'LUXRENDER_MT_presets_texture'
	preset_values =  []
	preset_subdir = 'luxrender/texture'
	
	def execute(self, context):
		pv = [
			'bpy.context.texture.luxrender_texture.%s'%v['attr'] for v in bpy.types.luxrender_texture.get_exportable_properties()
		]
		
		# store only the sub-properties of the selected lux texture type
		lux_type = context.texture.luxrender_texture.type
		sub_type = getattr(bpy.types, 'luxrender_tex_%s' % lux_type)
		
		features, junk = getattr(context.texture.luxrender_texture, 'luxrender_tex_%s' % lux_type).get_paramset(context.scene)
		if '2DMAPPING' in features:
			pv.extend([
				'bpy.context.texture.luxrender_texture.luxrender_tex_mapping.%s'%v['attr'] for v in bpy.types.luxrender_tex_mapping.get_exportable_properties()
			])
		if '3DMAPPING' in features:
			pv.extend([
				'bpy.context.texture.luxrender_texture.luxrender_tex_transform.%s'%v['attr'] for v in bpy.types.luxrender_tex_transform.get_exportable_properties()
			])
		
		pv.extend([
			'bpy.context.texture.luxrender_texture.luxrender_tex_%s.%s'%(lux_type, v['attr']) for v in sub_type.get_exportable_properties()
		])
		
		self.preset_values = pv
		return super().execute(context)

# Volume data handling

class LUXRENDER_OT_volume_add(bpy.types.Operator):
	'''Add a new material volume definition to the scene'''
	
	bl_idname = "luxrender.volume_add"
	bl_label = "Add LuxRender Volume"
	
	new_volume_name = bpy.props.StringProperty(default='New Volume')
	
	def invoke(self, context, event):
		v = context.scene.luxrender_volumes.volumes
		v.add()
		new_vol = v[len(v)-1]
		new_vol.name = self.properties.new_volume_name
		return {'FINISHED'}
	
class LUXRENDER_OT_volume_remove(bpy.types.Operator):
	'''Remove the selected material volume definition'''
	
	bl_idname = "luxrender.volume_remove"
	bl_label = "Remove LuxRender Volume"
	
	def invoke(self, context, event):
		w = context.scene.luxrender_volumes
		w.volumes.remove( w.volumes_index )
		w.volumes_index = len(w.volumes)-1
		return {'FINISHED'}

# Export process

class EXPORT_OT_luxrender(bpy.types.Operator):
	bl_idname = 'export.luxrender'
	bl_label = 'Export LuxRender Scene (.lxs)'
	
	filename		= bpy.props.StringProperty(name='LXS filename')
	directory		= bpy.props.StringProperty(name='LXS directory')
	
	api_type		= bpy.props.StringProperty(options={'HIDDEN'}, default='FILE')	# Export target ['FILE','API',...]
	write_files		= bpy.props.BoolProperty(options={'HIDDEN'}, default=True)		# Write any files ?
	write_all_files	= bpy.props.BoolProperty(options={'HIDDEN'}, default=True)		# Force writing all files, don't obey UI settings
	
	scene			= bpy.props.StringProperty(options={'HIDDEN'}, default='')		# Specify scene to export
	
	def invoke(self, context, event):
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def execute(self, context):
		if self.properties.scene == '':
			scene = context.scene
		else:
			scene = bpy.data.scenes[self.properties.scene]
		
		return SceneExporter() \
				.set_report(self.report) \
				.set_properties(self.properties) \
				.set_scene(scene) \
				.export()

menu_func = lambda self, context: self.layout.operator("export.luxrender", text="Export LuxRender Scene...")
bpy.types.INFO_MT_file_export.append(menu_func)
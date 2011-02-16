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
import math

# LuxRender Libs
from .. import LuxRenderAddon
from ..export.scene import SceneExporter

# Per-IDPropertyGroup preset handling

class LUXRENDER_MT_base(object):
	preset_operator = "script.execute_preset"
	def draw(self, context):
		return bpy.types.Menu.draw_preset(self, context)

class LUXRENDER_OT_preset_base(AddPresetBase):
	pass

@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_engine(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Engine Presets"
	preset_subdir = "luxrender/engine"

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_engine_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_engine_add'
	bl_label = 'Add LuxRender Engine settings preset'
	preset_menu = 'LUXRENDER_MT_presets_engine'
	preset_values = []
	preset_subdir = 'luxrender/engine'
	
	def execute(self, context):
		self.preset_values = [
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
		return super().execute(context)

@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_networking(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Networking Presets"
	preset_subdir = "luxrender/networking"

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_networking_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_networking_add'
	bl_label = 'Add LuxRender Networking settings preset'
	preset_menu = 'LUXRENDER_MT_presets_networking'
	preset_values = []
	preset_subdir = 'luxrender/networking'
	
	def execute(self, context):
		self.preset_values = [
			'bpy.context.scene.luxrender_networking.%s'%v['attr'] for v in bpy.types.luxrender_networking.get_exportable_properties()
		]
		return super().execute(context)

@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_material(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Material Presets"
	preset_subdir = "luxrender/material"

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_material_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_material_add'
	bl_label = 'Add LuxRender Material settings preset'
	preset_menu = 'LUXRENDER_MT_presets_material'
	preset_values = []
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

@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_texture(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Texture Presets"
	preset_subdir = "luxrender/texture"

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_texture_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_texture_add'
	bl_label = 'Add LuxRender Texture settings preset'
	preset_menu = 'LUXRENDER_MT_presets_texture'
	preset_values = []
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

@LuxRenderAddon.addon_register_class
class LUXRENDER_MT_presets_volume(LUXRENDER_MT_base, bpy.types.Menu):
	bl_label = "LuxRender Volume Presets"
	preset_subdir = "luxrender/volume"

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_preset_volume_add(LUXRENDER_OT_preset_base, bpy.types.Operator):
	'''Save the current settings as a preset'''
	bl_idname = 'luxrender.preset_volume_add'
	bl_label = 'Add LuxRender Volume settings preset'
	preset_menu = 'LUXRENDER_MT_presets_volume'
	preset_values = []
	preset_subdir = 'luxrender/volume'
	
	def execute(self, context):
		ks = 'bpy.context.scene.luxrender_volumes.volumes[bpy.context.scene.luxrender_volumes.volumes_index].%s'
		pv = [
			ks%v['attr'] for v in bpy.types.luxrender_volume_data.get_exportable_properties()
		]
		
		self.preset_values = pv
		return super().execute(context)

@LuxRenderAddon.addon_register_class
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

@LuxRenderAddon.addon_register_class
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

@LuxRenderAddon.addon_register_class
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

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_convert_material(bpy.types.Operator):
	bl_idname = 'luxrender.convert_material'
	bl_label = 'Convert Blender material to LuxRender'
	
	def execute(self, context):
		
		try:
			blender_mat = context.material
			luxrender_mat = context.material.luxrender_material
			
			# TODO - check values marked #ASV - Arbitrary Scale Value
			
			luxrender_mat.Interior_volume = ''
			luxrender_mat.Exterior_volume = ''
			
			
			if blender_mat.raytrace_mirror.use and blender_mat.raytrace_mirror.reflect_factor >= 0.9:
			    # for high mirror reflection values switch to mirror material
			    luxrender_mat.type = 'mirror'
			    lmm = luxrender_mat.luxrender_mat_mirror
			    lmm.Kr_color = [i for i in blender_mat.mirror_color]
			    luxmat = lmm
			else if blender_mat.specular_intensity < 0.01:
			    # use matte as glossy mat with very low specular is not equal matte
			    luxrender_mat.type = 'matte'
			    lms = luxrender_mat.luxrender_mat_matte
			    lms.Kd_color = [blender_mat.diffuse_intensity*i for i in blender_mat.diffuse_color]
			    lmg.sigma_floatvalue = 0.0
			    luxmat = lms
			else:
			    luxrender_mat.type = 'glossy'
			    lmg = luxrender_mat.luxrender_mat_glossy
			    lmg.multibounce = False
			    lmg.useior = False
			    lmg.Kd_color = [blender_mat.diffuse_intensity*i for i in blender_mat.diffuse_color]
			    
			    logHardness = math.log(blender_mat.specular_hardness)
			    
			    # fit based on empirical measurements
			    # measurements based on intensity of 0.5, use linear scale for other intensities
			    specular_scale = 2.0 * max(0.0128415*logHardness**2 - 0.171266*logHardness + 0.575631, 0.0)
			    
			    lmg.Ks_color = [min(specular_scale * blender_mat.specular_intensity * i, 0.25) for i in blender_mat.specular_color]
			    
			    # fit based on empirical measurements
			    roughness = min(max(0.757198 - 0.120395*logHardness, 0.0), 1.0)
			    
			    lmg.uroughness_floatvalue = roughness
			    lmg.vroughness_floatvalue = roughness
			    lmg.uroughness_usefloattexture = lmg.vroughness_usefloattexture = False
			    luxmat = lmg
			    
			
			# Emission
			lme = context.material.luxrender_emission
			if blender_mat.emit > 0:
				lme.use_emission = True
				lme.L_color = [1.0, 1.0, 1.0]
				lme.gain = blender_mat.emit
			else:
				lme.use_emission = False
			
			# Transparency
			lmt = context.material.luxrender_transparency
			if blender_mat.use_transparency:
				lmt.transparent = True
				lmt.alpha_source = 'constant'
				lmt.alpha_value = blender_mat.alpha
			else:
				lmt.transparent = False
			
			# iterate textures and build mix stacks according to influences
			Kd_stack = []
			Ks_stack = []
			bump_tex = None
			for tex_slot in blender_mat.texture_slots:
				if tex_slot != None:
					tex_slot.texture.luxrender_texture.type = 'BLENDER'
					if tex_slot.use_map_color_diffuse:
						dcf = tex_slot.diffuse_color_factor
						if tex_slot.use_map_diffuse:
							dcf *= tex_slot.diffuse_factor
						Kd_stack.append( (tex_slot.texture, dcf) )
					if tex_slot.use_map_color_spec:
						scf = tex_slot.specular_color_factor
						if tex_slot.use_map_specular:
							scf *= tex_slot.specular_factor
						Ks_stack.append( (tex_slot.texture, scf) )
					if tex_slot.use_map_normal:
						bump_tex = (tex_slot.texture, tex_slot.normal_factor)
			
			if luxrender_mat.type in ('matte', 'glossy'):
			    if len(Kd_stack) == 1:
				    tex = Kd_stack[0][0]
				    variant, paramset = tex.luxrender_texture.get_paramset(context.scene, tex)
				    if variant == 'color':
					    # assign the texture directly
					    luxmat.Kd_usecolortexture = True
					    luxmat.Kd_colortexturename = tex.name
					    luxmat.Kd_color = [i*Kd_stack[0][1] for i in lmg.Kd_color]
					    luxmat.Kd_multiplycolor = True
				    else:
					    # TODO - insert mix texture
					    # check there are enough free empty texture slots !
					    pass
			    elif len(Kd_stack) > 1:
				    # TODO - set up a mix stack.
				    # check there are enough free empty texture slots !
				    pass
			    else:
				    luxmat.Kd_usecolortexture = False
			
			if luxrender_mat.type in ('glossy'):
			    if len(Ks_stack) == 1:
				    tex = Ks_stack[0][0]
				    variant, paramset = tex.luxrender_texture.get_paramset(context.scene, tex)
				    if variant == 'color':
					    # assign the texture directly
					    luxmat.Ks_usecolortexture = True
					    luxmat.Ks_colortexturename = tex.name
					    luxmat.Ks_color = [i*Ks_stack[0][1] for i in lmg.Ks_color]
					    luxmat.Ks_multiplycolor = True
				    else:
					    # TODO - insert mix texture
					    # check there are enough free empty texture slots !
					    pass
			    elif len(Ks_stack) > 1:
				    # TODO - set up a mix stack.
				    # check there are enough free empty texture slots !
				    pass
			    else:
				    luxmat.Ks_usecolortexture = False
			
			if bump_tex != None:
				tex = bump_tex[0]
				variant, paramset = tex.luxrender_texture.get_paramset(context.scene, tex)
				if variant == 'float':
					luxrender_mat.bumpmap_usefloattexture = True
					luxrender_mat.bumpmap_floattexturename = tex.name
					luxrender_mat.bumpmap_floatvalue = bump_tex[1] / 50.0 #ASV
					luxrender_mat.bumpmap_multipyfloat = True
				else:
					# TODO - insert mix texture
					# check there are enough free empty texture slots !
					pass
			else:
				luxrender_mat.bumpmap_floatvalue = 0.0
				luxrender_mat.bumpmap_usefloattexture = False
			
			self.report({'INFO'}, 'Converted blender material "%s"' % blender_mat.name)
			return {'FINISHED'}
		except Exception as err:
			self.report({'ERROR'}, 'Cannot convert material: %s' % err)
			#import pdb
			#pdb.set_trace()
			return {'CANCELLED'}

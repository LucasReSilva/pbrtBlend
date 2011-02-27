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
import bpy, blf

from .. import LuxRenderAddon
from ..outputs import LuxLog

from .lrmdb_lib import lrmdb_client

def null_callback(context):
	pass

class ClickLocation(object):
	def __init__(self, font_id=0, x=0, y=0, z=0):
		self.font_id = font_id
		self.x = x
		self.y = y
		self.z = z
	def hit(self, region, mx, my):
		hx = self.x if self.x > 0 else region.width + self.x
		hy = self.y if self.y > 0 else region.height + self.y
		return ( my>hy and my<(hy+14) ) and ( mx>hx and mx<(hx+200))

class ActionText(object):
	def __init__(self, label, location=ClickLocation(), callback=null_callback, callback_args=tuple()):
		self.label = label
		self.location = location
		self.callback = callback
		self.callback_args = callback_args
	
	def draw(self, region):
		x = self.location.x if self.location.x > 0 else region.width + self.location.x
		y = self.location.y if self.location.y > 0 else region.height + self.location.y
		z = self.location.z
		blf.position( self.location.font_id, x, y, z )
		blf.draw(0, self.label )
	
	def execute(self, context):
		self.callback( context, *self.callback_args )

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_lrmdb_login(bpy.types.Operator):
	"""Log in to the LuxRender Materials Database"""
	
	bl_idname = 'luxrender.lrmdb_login'
	bl_label  = 'Log in to LRMDB'
	
	username = bpy.props.StringProperty(name='Username:')
	password = bpy.props.StringProperty(name='Password:')
	
	def execute(self, context):
		if self.properties.username and self.properties.password:
			try:
				s = lrmdb_client.server_instance()
				li = s.user.login(self.properties.username, self.properties.password)
				if not li:
					lrmdb_client.loggedin = False
					lrmdb_client.username = ''
					self.report({'ERROR'}, 'Login failure')
				else:
					lrmdb_client.loggedin = True
					lrmdb_client.username = self.properties.username
				return {'FINISHED'}
			except Exception as err:
				LuxLog('LRMDB ERROR: %s' % err)
				return {'CANCELLED'}
		else:
			self.report({'ERROR'}, 'Must supply both username and password')
			return {'CANCELLED'}
	
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_lrmdb_logout(bpy.types.Operator):
	"""Log out of the LuxRender Materials Database"""
	
	bl_idname = 'luxrender.lrmdb_logout'
	bl_label  = 'Log out of LRMDB'
	
	def execute(self, context):
		try:
			s = lrmdb_client.server_instance()
			li = s.user.logout()
			if not li:
				self.report({'ERROR'}, 'Logout failure')
			return {'FINISHED'}
		except Exception as err:
			LuxLog('LRMDB ERROR: %s' % err)
			return {'CANCELLED'}

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_lrmdb(bpy.types.Operator):
	"""Start the LuxRender Materials Database Interface"""
	
	bl_idname = 'luxrender.lrmdb'
	bl_label  = 'Start LRMDB'
	
	_active = False
	_region_callback = None
	
	actions = []
	
	def modal(self, context, event):
		context.area.tag_redraw()
		
		if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
			for action in self.actions:
				if action.location.hit(context.region, event.mouse_region_x, event.mouse_region_y):
					action.execute(context)
		
		if not LUXRENDER_OT_lrmdb._active or event.type == 'ESC':
			LUXRENDER_OT_lrmdb._active = False
			context.region.callback_remove(self._region_callback)
			self._region_callback = None
			
			return {'FINISHED'}
		
		return {'PASS_THROUGH'}
	
	def region_callback(self, context):
		blf.position(0, 75, 30, 0)
		blf.size(0, 14, 72)
		msg = 'LRMDB Material Chooser (ESC to close)'
		blf.draw(0, msg)
		
		for action in self.actions:
			action.draw(context.region)
	
	def select_material(self, context, mat_id):
		#LuxLog('Chose material %s' % mat_id)
		
		if not context.active_object:
			LuxLog('WARNING: Select an object!')
			return
		if not context.active_object.active_material:
			LuxLog('WARNING: Selected object does not have active material')
			return
		
		try:
			context.area.tag_redraw()
			s = lrmdb_client.server_instance()
			md = s.material.get.data(mat_id)
		except Exception as err:
			LuxLog('LRMDB ERROR: Cannot get data: %s' % err)
			LUXRENDER_OT_lrmdb._active = False
			return
		
		try:
			for mat_part in md['objects']:
				# TODO, load all parts, not just the top-most one
				if mat_part['type'] == 'MakeNamedMaterial' and mat_part['name'] == md['name']:
					
					lxm = lxms = None
					
					# First iterate for the material type, because
					# we need to know which sub PropertyGroup to 
					# set the other paramsetitems in
					for paramsetitem in mat_part['paramset']:
						if paramsetitem['name'] == 'type':
							context.active_object.active_material.luxrender_material.type = paramsetitem['value']
							lxm  = context.active_object.active_material.luxrender_material
							lxms = getattr(context.active_object.active_material.luxrender_material, 'luxrender_mat_%s'%paramsetitem['value'])
					
					if lxms != None:
						paramset_map = {
							'Kd': 'Kd_color'
						}
						paramset_map_keys = paramset_map.keys()
						for paramsetitem in mat_part['paramset']:
							if paramsetitem['name'] in paramset_map_keys:
								setattr(lxms, paramset_map[paramsetitem['name']], paramsetitem['value'])
						
						lxm.set_master_color(context.active_object.active_material)
						context.active_object.active_material.preview_render_type = context.active_object.active_material.preview_render_type
			
			for a in context.screen.areas:
				a.tag_redraw()
		except KeyError as err:
			LuxLog('LRMDB ERROR: Bad material data')
	
	def show_category_items(self, context, cat_id, cat_name):
		#LuxLog('Chose category %s' % cat_id)
		try:
			context.area.tag_redraw()
			s = lrmdb_client.server_instance()
			ci = s.category.item(cat_id)
		except Exception as err:
			LuxLog('LRMDB ERROR: Cannot get data: %s' % err)
			LUXRENDER_OT_lrmdb._active = False
			return
		
		#LuxLog(ci)
		
		if len(ci) > 0:
			self.reset_actions()
			
			self.actions.append(
				ActionText(
					'Category "%s"' % cat_name,
					ClickLocation(0,75,-30,0)
				)
			)
			
			i=1
			for mat_id, mat_header in ci.items():
				if mat_header['published'] == 1 and mat_header['type'] == 'Material':
					ofsy =  -30 - (i*30)
					self.actions.append(
						ActionText(
							mat_header['name'],
							ClickLocation(0,85,ofsy,0),
							self.select_material,
							(mat_id,)
						)
					)
					i+=1
			
			self.draw_back_link(i)
	
	def show_category_list(self, context):
		try:
			context.area.tag_redraw()
			s = lrmdb_client.server_instance()
			ct = s.category.tree()
			lrmdb_client.check_login()
		except Exception as err:
			LuxLog('LRMDB ERROR: Cannot get data: %s' % err)
			LUXRENDER_OT_lrmdb._active = False
			return
		
		def display_category(ctg, i=0, j=0):
			for cat_id, cat in ctg.items():
				ofsy =  -30 - (i*30)
				self.actions.append(
					ActionText(
						cat['name'] + ' (%s)' % cat['items'],
						ClickLocation(0,75+j,ofsy,0),
						self.show_category_items,
						(cat_id, cat['name'])
					)
				)
				if 'subcategories' in cat.keys():
					i = display_category(cat['subcategories'], i+1, j+10)
				else:
					i+=1
			return i
		
		if len(ct) > 0:
			self.reset_actions()
			self.actions.append(
				ActionText(
					'Categories',
					ClickLocation(0,75,-30,0)
				)
			)
			display_category(ct, 1)
	
	def begin_login(self, context):
		bpy.ops.luxrender.lrmdb_login('INVOKE_DEFAULT')
	
	def end_login(self, context):
		bpy.ops.luxrender.lrmdb_logout()
		self.reset_actions()
		LUXRENDER_OT_lrmdb._active = False
	
	def reset_actions(self):
		self.actions = []
		self.draw_loggedin()
	
	def draw_loggedin(self):
		if lrmdb_client.loggedin:
			self.actions.extend([
				ActionText(
					'Logged In:',
					ClickLocation(0,-150,-30,0),
					null_callback,
					tuple()
				),
				ActionText(
					lrmdb_client.username,
					ClickLocation(0,-150,-60,0),
					null_callback,
					tuple()
				),
				
				ActionText(
					'Log out',
					ClickLocation(0,-150,-90,0),
					self.end_login,
					tuple()
				)
			])
		else:
			self.actions.extend([
				ActionText(
					'Log In',
					ClickLocation(0,-150,-30,0),
					self.begin_login,
					tuple()
				),
			])
	
	def draw_back_link(self, i):
		ofsy = -30 - (i*30)
		self.actions.append(
			ActionText(
				'< Back to categories',
				ClickLocation(0,60,ofsy,0),
				self.show_category_list,
				tuple()
			)
		)
	
	def execute(self, context):
		if LUXRENDER_OT_lrmdb._active:
			LuxLog('LRMDB ERROR: Already running!')
			return {'CANCELLED'}
		
		context.window_manager.modal_handler_add(self)
		self._region_callback = context.region.callback_add(self.region_callback, (context,), 'POST_PIXEL')
		context.area.tag_redraw()
		LUXRENDER_OT_lrmdb._active = True
		
		# Fire the first phase: list categories
		self.show_category_list(context)
		
		return {'RUNNING_MODAL'}
	
	@classmethod
	def poll(cls, context):
		return context.scene.render.engine == LuxRenderAddon.BL_IDNAME

def lrmdb_operators(self, context):
	if context.scene.render.engine == LuxRenderAddon.BL_IDNAME:
		row = self.layout.row(align=True)
		row.operator("luxrender.lrmdb", text="LuxRender Materials", icon='MATERIAL_DATA')
#	
bpy.types.VIEW3D_HT_header.append(lrmdb_operators)

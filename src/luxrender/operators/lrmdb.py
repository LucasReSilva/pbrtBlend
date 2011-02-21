import xmlrpc.client

import bpy, blf

from .. import LuxRenderAddon
from ..outputs import LuxLog

class lrmdb_client(object):
	#static
	server = None
	
	@staticmethod
	def server_instance():
		if lrmdb_client.server == None:
			lrmdb_client.server = xmlrpc.client.ServerProxy(
				"http://www.luxrender.net/lrmdb2/ixr",
				#transport=CookieTransport,
				#verbose=True
			)
			
		return lrmdb_client.server

def null_callback(context):
	pass

class ClickRegion(object):
	def __init__(self, font_id=0, x=0, y=0, z=0):
		self.font_id = font_id
		self.x = x
		self.y = y
		self.z = z
	def hit(self, mx, my):
		return ( my>self.y and my<(self.y+14) )

class ActionText(object):
	def __init__(self, label, region=ClickRegion(), callback=null_callback, callback_args=tuple()):
		self.label = label
		self.region = region
		self.callback = callback
		self.callback_args = callback_args
	
	def draw(self):
		blf.position( self.region.font_id, self.region.x, self.region.y, self.region.z )
		blf.draw(0, self.label )
	
	def execute(self, context):
		self.callback( context, *self.callback_args )

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_lrmdb(bpy.types.Operator):
	"""Start the LuxRender Materials Database Interface"""
	
	bl_idname = 'luxrender.lrmdb'
	bl_label  = 'Start LRMDB'
	
	_active = False
	_ui_region = None
	_region_callback = None
	_loading_msg = False
	
	actions = []
	
	def modal(self, context, event):
		context.area.tag_redraw()
		
		if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
			for action in self.actions:
				if action.region.hit(event.mouse_region_x, event.mouse_region_y):
					action.execute(context)
		
		if not LUXRENDER_OT_lrmdb._active or event.type == 'ESC':
			LUXRENDER_OT_lrmdb._active = False
			self._ui_region.callback_remove(self._region_callback)
			self._ui_region = None
			self._region_callback = None
			
			return {'FINISHED'}
		
		return {'PASS_THROUGH'}
	
	def region_callback(self, context):
		blf.position(0, 75, 30, 0)
		blf.size(0, 14, 72)
		msg = 'LRMDB Material Chooser (ESC to close)'
		if self._loading_msg:
			msg += ' Loading ...'
		blf.draw(0, msg)
		
		for action in self.actions:
			action.draw()
	
	def select_material(self, context, mat_id):
		#LuxLog('Chose material %s' % mat_id)
		
		try:
			self._loading_msg = True
			context.area.tag_redraw()
			s = lrmdb_client.server_instance()
			md = s.material.get.data(mat_id)
			self._loading_msg = False
		except Exception as err:
			LuxLog('LRMDB ERROR: Cannot get data: %s' % err)
			LUXRENDER_OT_lrmdb._active = False
			return
		
		#import pprint
		#pprint.pprint(md, indent=1, width=1)
		
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
			self._loading_msg = True
			context.area.tag_redraw()
			s = lrmdb_client.server_instance()
			ci = s.category.item(cat_id)
			self._loading_msg = False
		except Exception as err:
			LuxLog('LRMDB ERROR: Cannot get data: %s' % err)
			LUXRENDER_OT_lrmdb._active = False
			return
		
		#LuxLog(ci)
		
		if len(ci) > 0:
			self.actions = []
			
			ofsy = self._ui_region.height - 30
			self.actions.append(
				ActionText(
					'Category "%s"' % cat_name,
					ClickRegion(0,75,ofsy,0)
				)
			)
			
			i=1
			for mat_id, mat_header in ci.items():
				if mat_header['published'] == 1 and mat_header['type'] == 'Material':
					ofsy = self._ui_region.height - 30 - (i*30)
					self.actions.append(
						ActionText(
							mat_header['name'],
							ClickRegion(0,85,ofsy,0),
							self.select_material,
							(mat_id,)
						)
					)
					i+=1
			
			self.draw_back_link(i)
	
	def show_category_list(self, context):
		
		try:
			self._loading_msg = True
			context.area.tag_redraw()
			s = lrmdb_client.server_instance()
			ct = s.category.tree()
			self._loading_msg = False
		except Exception as err:
			LuxLog('LRMDB ERROR: Cannot get data: %s' % err)
			LUXRENDER_OT_lrmdb._active = False
			return
		
		#LuxLog(ct)
		
		def display_category(ctg, i=0, j=0):
			for cat_id, cat in ctg.items():
				ofsy = self._ui_region.height - 30 - (i*30)
				self.actions.append(
					ActionText(
						cat['name'] + ' (%s)' % cat['items'],
						ClickRegion(0,75+j,ofsy,0),
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
			self.actions = []
			self.actions.append(
				ActionText(
					'Categories',
					ClickRegion(0,75,self._ui_region.height - 30,0)
				)
			)
			display_category(ct, 1)
	
	def draw_back_link(self, i):
		ofsy = self._ui_region.height - 30 - (i*30)
		self.actions.append(
			ActionText(
				'< Back to categories',
				ClickRegion(0,60,ofsy,0),
				self.show_category_list,
				tuple()
			)
		)
	
	def execute(self, context):
		
		if LUXRENDER_OT_lrmdb._active:
			LuxLog('LRMDB ERROR: Already running!')
			return {'CANCELLED'}
		
		self._ui_region = context.region
		
		context.window_manager.modal_handler_add(self)
		self._region_callback = self._ui_region.callback_add(self.region_callback, (context,), 'POST_PIXEL')
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
		row.operator("luxrender.lrmdb", text="", icon='MATERIAL_DATA')
#	
bpy.types.VIEW3D_HT_header.append(lrmdb_operators)
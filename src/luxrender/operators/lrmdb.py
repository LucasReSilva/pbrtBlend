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

@LuxRenderAddon.addon_register_class
class LUXRENDER_OT_lrmdb(bpy.types.Operator):
	"""Start the LuxRender Materials Database Interface"""
	
	bl_idname = 'luxrender.lrmdb'
	bl_label  = 'Start LRMDB'
	
	_active = False
	_ui_region = None
	_region_callback = None
	_loading_msg = False
	
	draw_items = []
	click_items = []
	
	def clicked_in_region(self, event, click_region):
		mrx = event.mouse_region_x
		mry = event.mouse_region_y
		cf, cx, cy, cz = click_region
		
		if mry>=cy and mry<=(cy+14): return True
		
	def modal(self, context, event):
		context.area.tag_redraw()
		
		if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
			# The user clicked on something !
			for click_region, callback, callback_data in self.click_items:
				if self.clicked_in_region(event, click_region):
					callback( context, *callback_data )
		
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
		
		for ps, txt in self.draw_items:
			blf.position( *ps )
			blf.draw(0, txt)
	
	def null_click(self, context):
		pass
	
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
			self.draw_items = []
			self.click_items = []
			
			ofsy = self._ui_region.height - 30
			mat_region = (0,75,ofsy,0)
			self.draw_items.append(
				(
					mat_region,
					'Category "%s"' % cat_name
				)
			)
			self.click_items.append(
				(
					mat_region,
					self.null_click,
					tuple()
				)
			)
			
			i=0
			for mat_id, mat_header in ci.items():
				if mat_header['published'] == 1 and mat_header['type'] == 'Material':
					i+=1
					ofsy = self._ui_region.height - 30 - (i*30)
					mat_region = (0,75,ofsy,0)
					self.draw_items.append(
						(
							mat_region,
							mat_header['name']
						)
					)
					self.click_items.append(
						(
							mat_region,
							self.select_material,
							(mat_id,)
						)
					)
			
			self.draw_back_link(i+1)
	
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
				i+=1
				ofsy = self._ui_region.height - 30 - (i*30)
				cat_region = (0,75+j,ofsy,0)
				self.draw_items.append(
					(
						cat_region,
						cat['name'] + ' (%s)' % cat['items']
					)
				)
				self.click_items.append(
					(
						cat_region,
						self.show_category_items,
						(cat_id, cat['name'])
					)
				)
				if 'subcategories' in cat.keys():
					i = display_category(cat['subcategories'], i, j+10)
			return i
		
		if len(ct) > 0:
			self.draw_items = []
			self.click_items = []
			display_category(ct)
	
	def draw_back_link(self, i):
		ofsy = self._ui_region.height - 30 - (i*30)
		cat_region = (0,60,ofsy,0)
		self.draw_items.append(
			(
				cat_region,
				'< Back to categories'
			)
		)
		self.click_items.append(
			(
				cat_region,
				self.show_category_list,
				tuple()
			)
		)
	
	def find_3d_view(self, context):
		self._ui_region = context.region
		return True
		
		for a in context.screen.areas:
			if a.type == 'VIEW_3D':
				for r in a.regions:
					if r.type == 'WINDOW':
						self._ui_area = a
						print(dir(r))
						self._ui_region = r
						return True
		return False
	
	def execute(self, context):
		
		if LUXRENDER_OT_lrmdb._active:
			LuxLog('LRMDB ERROR: Already running!')
			return {'CANCELLED'}
		
		if self.find_3d_view(context):
			context.window_manager.modal_handler_add(self)
			self._region_callback = self._ui_region.callback_add(self.region_callback, (context,), 'POST_PIXEL')
			context.area.tag_redraw()
			LUXRENDER_OT_lrmdb._active = True
			
			# Fire the first phase: list categories
			self.show_category_list(context)
			
			return {'RUNNING_MODAL'}
		else:
			LuxLog('LRMDB ERROR: Could not find 3D view to hijack')
			return {'CANCELLED'}

def lrmdb_operators(self, context):
	row = self.layout.row(align=True)
	row.operator("luxrender.lrmdb", text="", icon='MATERIAL_DATA')
#	
bpy.types.VIEW3D_HT_header.append(lrmdb_operators)
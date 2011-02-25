import bpy, blf

from .. import LuxRenderAddon
from ..outputs import LuxLog

from .lrmdb_lib import lrmdb_client
from luxrender.operators.lrmdb_lib import lrmdb_client

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
		return ( my>hy and my<(hy+14) )

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
		
		try:
			context.area.tag_redraw()
			s = lrmdb_client.server_instance()
			md = s.material.get.data(mat_id)
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
		
		#LuxLog(ct)
		
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
		# invoke a menu operator to begin login process
		pass
	
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

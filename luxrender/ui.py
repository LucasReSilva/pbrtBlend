from ef.ui import context_panel
from ef.ui import render_settings_panel
from ef.ui import material_settings_panel

from properties import properties

class Main_Render_Settings(properties, context_panel, render_settings_panel):
	__label__ = 'LuxRender Engine Configuration'
	
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		
		for property in self.properties:
			layout.itemR(scene, property['attr'])
			
class Sampler_Render_Settings(properties, context_panel, render_settings_panel):
	__label__ = 'LuxRender Sampler Configuration'
	
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		
		for property in self.sampler_properties['common']:
			layout.itemR(scene, property['attr'])
		
		if (scene.lux_sampler_advanced):
			for property in self.sampler_properties['common_advanced']:
				layout.itemR(scene, property['attr'])
			for property in self.sampler_properties[scene.lux_sampler + '_advanced']:
				layout.itemR(scene, property['attr'])
		else:
			for property in self.sampler_properties[scene.lux_sampler]:
				layout.itemR(scene, property['attr'])
				
class Integrator_Render_Settings(properties, context_panel, render_settings_panel):
	__label__ = 'LuxRender Surface Integrator Configuration'
	
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		
		for property in self.integrator_properties['common']:
			layout.itemR(scene, property['attr'])
		
		if (scene.lux_integrator_advanced):
			for property in self.integrator_properties['common_advanced']:
				layout.itemR(scene, property['attr'])
			for property in self.integrator_properties[scene.lux_surfaceintegrator + '_advanced']:
				layout.itemR(scene, property['attr'])
		else:
			for property in self.integrator_properties[scene.lux_surfaceintegrator]:
				layout.itemR(scene, property['attr'])

class Material_Settings(properties, context_panel, material_settings_panel):
	def draw(self, context):
		layout = self.layout
		
		ob = context.object
		type = ob.type.capitalize()
		
		row = layout.row()
		row.itemL(text="Hello world!", icon='ICON_WORLD_DATA')
		col = layout.column()
		row = col.row()
		row.itemL(text="The currently selected object is: "+ob.name)
		row = col.row()
		if type == 'Mesh':
			row.itemL(text="It is a mesh containing "+str(len(ob.data.verts))+" vertices.")
		else:
			row.itemL(text="it is a "+type+".")
		row = layout.row()
		row.alignment = 'RIGHT'
		row.itemL(text="The end")

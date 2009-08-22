from engines.engine import engine_base

from ui import Main_Render_Settings
from ui import Sampler_Render_Settings
from ui import Integrator_Render_Settings
from properties import properties

# Add standard Blender Interface elements
import buttons_scene
buttons_scene.SCENE_PT_render.COMPAT_ENGINES.add('luxrender')
buttons_scene.SCENE_PT_dimensions.COMPAT_ENGINES.add('luxrender')
buttons_scene.SCENE_PT_output.COMPAT_ENGINES.add('luxrender')
del buttons_scene

# Then define all custom stuff
class luxrender(properties, engine_base):
	__label__ = 'LuxRender'
		
	interfaces = [
		Main_Render_Settings,
		Sampler_Render_Settings,
		Integrator_Render_Settings
	]
		
	def render(self, scene):
		pass

	

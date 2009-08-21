from engines.engine import engine_base

from ui import Main_Render_Settings
from ui import Sampler_Render_Settings
from ui import Integrator_Render_Settings
from properties import properties

class luxrender(properties, engine_base):
	__label__ = 'LuxRender'
		
	interfaces = [
		Main_Render_Settings,
		Sampler_Render_Settings,
		Integrator_Render_Settings
	]
		
	def render(self, scene):
		pass

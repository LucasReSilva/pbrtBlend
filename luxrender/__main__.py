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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
from ef.engine import engine_base

import ui.render_panels
import ui.materials

from ef.ef import ef

# Add standard Blender Interface elements
import buttons_scene
buttons_scene.SCENE_PT_render.COMPAT_ENGINES.add('luxrender')
buttons_scene.SCENE_PT_dimensions.COMPAT_ENGINES.add('luxrender')
buttons_scene.SCENE_PT_output.COMPAT_ENGINES.add('luxrender')
del buttons_scene
import buttons_material
buttons_material.MATERIAL_PT_context_material.COMPAT_ENGINES.add('luxrender')
del buttons_material

# Then define all custom stuff
class _luxrender(engine_base):
	__label__ = 'LuxRender'
		
	interfaces = [
		ui.render_panels.engine,
		ui.render_panels.sampler,
		ui.render_panels.integrator,
		ui.render_panels.volume,
		ui.render_panels.filter,
		ui.render_panels.accelerator,
		
		ui.materials.material_editor
	]
		
	def render(self, scene):
		pass

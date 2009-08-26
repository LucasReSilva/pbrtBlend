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
from ef.ef import ef

from ef.ui import context_panel
from ef.ui import render_settings_panel
from ef.ui import material_settings_panel
from ef.ui import described_layout

import properties.settings
import properties.materials

class Lux_Main_Render_Settings(
	properties.settings.main,
	context_panel,
	render_settings_panel,
	described_layout):
	__label__ = 'LuxRender Engine Configuration'
			
class Lux_Sampler_Render_Settings(
	properties.settings.sampler,
	context_panel,
	render_settings_panel,
	described_layout):
	__label__ = 'Sampler'
				
class Lux_Integrator_Render_Settings(
	properties.settings.sintegrator,
	context_panel,
	render_settings_panel,
	described_layout):
	__label__ = 'Surface Integrator'

class Lux_Volume_Integrator_Render_Settings(
	properties.settings.vintegrator,
	context_panel,
	render_settings_panel,
	described_layout):
	__label__ = 'Volume Integrator'
			
class Lux_Filter_Render_Settings(
	properties.settings.filter,
	context_panel,
	render_settings_panel,
	described_layout):
	__label__ = 'Filter'

class Lux_Accel_Render_Settings(
	properties.settings.accelerator,
	context_panel,
	render_settings_panel,
	described_layout):
	__label__ = 'Accelerator'

class Lux_Material_Settings(
	properties.materials.materials,
	context_panel,
	material_settings_panel,
	described_layout):
	__label__ = 'LuxRender Materials'
	
	def draw(self, context):
		if context.material is not None:
			if not hasattr(context.material, 'lux_material'):
				ef.init_properties(context.material, self.materials)
		
			for p in self.controls:
				self.draw_column(p, self.layout, context.material)


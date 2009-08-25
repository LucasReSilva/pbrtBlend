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
from ef.ui import context_panel
from ef.ui import render_settings_panel
from ef.ui import material_settings_panel
from ef.ui import described_layout

from properties import properties

class Lux_Main_Render_Settings(properties, context_panel, render_settings_panel, described_layout):
	__label__ = 'LuxRender Engine Configuration'
	
	selection_lookup = {
		'lux_threads':				[{ 'lux_threads_auto': False }],
		'lux_file_lxs':				[{ 'lux_singlefile': False }],
		'lux_file_lxo':				[{ 'lux_singlefile': False }],
		'lux_file_lxm':				[{ 'lux_singlefile': False }],
		'lux_file_lxv':				[{ 'lux_singlefile': False }],
	}
	
	def draw(self, context):
		for p in self.engine_layout:
			self.draw_column(p, self.layout, context.scene)
			
class Lux_Sampler_Render_Settings(properties, context_panel, render_settings_panel, described_layout):
	__label__ = 'Sampler'
	
	selection_lookup = {
		'lux_sampler_advanced':				[{ 'lux_sampler': 'metropolis'}],
	
		'lux_sampler_metro_strength':		[{ 'lux_sampler_advanced': False }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_lmprob':			[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_mncr':			[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_initsamples':	[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		'lux_sampler_metro_variance':		[{ 'lux_sampler_advanced': True  }, { 'lux_sampler': 'metropolis'}],
		
		'lux_sampler_erpt_initsamples':		[{ 'lux_sampler': 'erpt'}],
		'lux_sampler_erpt_chainlength':		[{ 'lux_sampler': 'erpt'}],
		'lux_sampler_erpt_stratawidth':		[{ 'lux_sampler': 'erpt'}],
		
		'lux_sampler_ld_pixelsampler':		[{ 'lux_sampler': 'lowdiscrepancy'}],
		'lux_sampler_ld_samples':			[{ 'lux_sampler': 'lowdiscrepancy'}],
		
		'lux_sampler_rnd_pixelsampler':		[{ 'lux_sampler': 'random'}],
		'lux_sampler_rnd_xsamples':			[{ 'lux_sampler': 'random'}],
		'lux_sampler_rnd_ysamples':			[{ 'lux_sampler': 'random'}],
	}
	
	def draw(self, context):
		for p in self.sampler_layout:
			self.draw_column(p, self.layout, context.scene)
				
class Lux_Integrator_Render_Settings(properties, context_panel, render_settings_panel, described_layout):
	__label__ = 'Surface Integrator'
	
	selection_lookup = {
		'lux_integrator_strategy':		[{ 'lux_integrator_advanced': True  }],
		
		'lux_integrator_bidir_depth':	[{ 'lux_integrator_advanced': False }, { 'lux_surfaceintegrator': 'bidirectional' }],
		'lux_integrator_bidir_edepth':	[{ 'lux_integrator_advanced': True  }, { 'lux_surfaceintegrator': 'bidirectional' }],
		'lux_integrator_bidir_ldepth':	[{ 'lux_integrator_advanced': True  }, { 'lux_surfaceintegrator': 'bidirectional' }],
	}
	
	def draw(self, context):
		for p in self.integrator_layout:
			self.draw_column(p, self.layout, context.scene)

class Lux_Volume_Integrator_Render_Settings(properties, context_panel, render_settings_panel, described_layout):
	__label__ = 'Volume Integrator'
	
	selection_lookup = {}
	
	def draw(self, context):
		for p in self.volume_integrator_layout:
			self.draw_column(p, self.layout, context.scene)
			
class Lux_Filter_Render_Settings(properties, context_panel, render_settings_panel, described_layout):
	__label__ = 'Filter'
	
	selection_lookup = {
		'lux_filter_xwidth':				[{ 'lux_filter_advanced': True }],
		'lux_filter_ywidth':				[{ 'lux_filter_advanced': True }],
		
		'lux_filter_gaussian_alpha':		[{ 'lux_filter_advanced': True }, { 'lux_filter': 'gaussian' }],
		
		'lux_filter_mitchell_mode':			[{ 'lux_filter_advanced': True }, { 'lux_filter': 'mitchell' }],
		'lux_filter_mitchell_b':			[{ 'lux_filter_advanced': True }, { 'lux_filter': 'mitchell' }, { 'lux_filter_mitchell_mode': 'manual' }],
		'lux_filter_mitchell_c':			[{ 'lux_filter_advanced': True }, { 'lux_filter': 'mitchell' }, { 'lux_filter_mitchell_mode': 'manual' }],		
		'lux_filter_mitchell_sharpness':	[{ 'lux_filter': 'mitchell' }],
		
		'lux_filter_sinc_tau':				[{ 'lux_filter_advanced': True }, { 'lux_filter': 'sinc' }],
	}
	
	def draw(self, context):
		for p in self.filter_layout:
			self.draw_column(p, self.layout, context.scene)

class Lux_Accel_Render_Settings(properties, context_panel, render_settings_panel, described_layout):
	__label__ = 'Accelerator'
	
	selection_lookup = {
		'lux_accel_kd_intcost':			[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_travcost':		[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_ebonus':			[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_maxprims':		[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_kd_maxdepth':		[{ 'lux_accelerator': 'tabreckdtree' }],
		'lux_accel_grid_refineim':		[{ 'lux_accelerator': 'grid' }],
		'lux_accel_qbvh_maxprims':		[{ 'lux_accelerator': 'qbvh' }],
	}
	
	def draw(self, context):
		for p in self.accelerator_layout:
			self.draw_column(p, self.layout, context.scene)

class Lux_Material_Settings(properties, context_panel, material_settings_panel):
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

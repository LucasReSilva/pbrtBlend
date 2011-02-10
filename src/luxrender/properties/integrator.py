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
from extensions_framework import declarative_property_group, ef_initialise_properties
from extensions_framework.validate import Logic_OR as O, Logic_Operator as LO

from luxrender.properties import dbo
from luxrender.export import ParamSet
from luxrender.outputs import LuxLog 

@ef_initialise_properties
class luxrender_integrator(declarative_property_group):
	'''
	Storage class for LuxRender SurfaceIntegrator settings.
	'''
	
	ef_attach_to = ['Scene']
	
	controls = [
		[ 0.7, 'surfaceintegrator', 'advanced'],
		
		'lightstrategy',
		
		# bidir +
		['eyedepth', 'lightdepth'],
		['eyerrthreshold', 'lightrrthreshold'],
		
		# dl +
		'maxdepth',
		
		# dp
		['lbl_direct',
		'directsamples'],
		['directsampleall',
		'directdiffuse',
		'directglossy'],
		['lbl_indirect',
		'indirectsamples'],
		['indirectsampleall',
		'indirectdiffuse',
		'indirectglossy'],
		'lbl_diffuse',
		['diffusereflectsamples',
		'diffusereflectdepth'],
		['diffuserefractsamples',
		'diffuserefractdepth'],
		'lbl_glossy',
		['glossyreflectsamples',
		'glossyreflectdepth'],
		['glossyrefractsamples',
		'glossyrefractdepth'],
		'lbl_specular',
		['specularreflectdepth',
		'specularrefractdepth'],
		'lbl_rejection',
		['diffusereflectreject',
		'diffusereflectreject_threshold'],
		['diffuserefractreject',
		'diffuserefractreject_threshold'],
		['glossyreflectreject',
		'glossyreflectreject_threshold'],
		['glossyrefractreject',
		'glossyrefractreject_threshold'],
		
		# epm
		'maxphotondepth',
		'directphotons',
		'causticphotons',
		'indirectphotons',
		'radiancephotons',
		'nphotonsused',
		'maxphotondist',
		'finalgather',
		'finalgathersamples',
		'gatherangle',
		'renderingmode',
		'rrstrategy',
		'rrcontinueprob',
		# epm advanced
		'distancethreshold',
		'photonmapsfile',
		'dbg_enabledirect',
		'dbg_enableradiancemap',
		'dbg_enableindircaustic',
		'dbg_enableindirdiffuse',
		'dbg_enableindirspecular',
		
		# igi
		'nsets',
		'nlights',
		'mindist',
		
		# path
		'includeenvironment',
	]
	
	visibility = {
		# bidir +
		'lightstrategy':					{ 'advanced': True, 'surfaceintegrator': LO({'!=': 'bidirectional'}) },
		'eyedepth':							{ 'surfaceintegrator': 'bidirectional' },
		'lightdepth':						{ 'surfaceintegrator': 'bidirectional' },
		'eyerrthreshold':					{ 'advanced': True, 'surfaceintegrator': 'bidirectional' },
		'lightrrthreshold':					{ 'advanced': True, 'surfaceintegrator': 'bidirectional' },
		
		# dl +
		'maxdepth':							{ 'surfaceintegrator': O(['directlighting', 'exphotonmap', 'igi', 'path']) },
		
		# dp
		'lbl_direct':						{ 'surfaceintegrator': 'distributedpath' },
		'directsampleall':					{ 'surfaceintegrator': 'distributedpath' },
		'directsamples':					{ 'surfaceintegrator': 'distributedpath' },
		'directdiffuse':					{ 'surfaceintegrator': 'distributedpath' },
		'directglossy':						{ 'surfaceintegrator': 'distributedpath' },
		'lbl_indirect':						{ 'surfaceintegrator': 'distributedpath' },
		'indirectsampleall':				{ 'surfaceintegrator': 'distributedpath' },
		'indirectsamples':					{ 'surfaceintegrator': 'distributedpath' },
		'indirectdiffuse':					{ 'surfaceintegrator': 'distributedpath' },
		'indirectglossy':					{ 'surfaceintegrator': 'distributedpath' },
		'lbl_diffuse':						{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectsamples':			{ 'surfaceintegrator': 'distributedpath' },
		'diffuserefractdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'diffuserefractsamples':			{ 'surfaceintegrator': 'distributedpath' },
		'lbl_glossy':						{ 'surfaceintegrator': 'distributedpath' },
		'glossyreflectdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyreflectsamples':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyrefractdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyrefractsamples':				{ 'surfaceintegrator': 'distributedpath' },
		'lbl_specular':						{ 'surfaceintegrator': 'distributedpath' },
		'specularreflectdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'specularrefractdepth':				{ 'surfaceintegrator': 'distributedpath' },
		'lbl_rejection':					{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectreject':				{ 'surfaceintegrator': 'distributedpath' },
		'diffusereflectreject_threshold':	{ 'diffusereflectreject': True, 'surfaceintegrator': 'distributedpath' },
		'diffuserefractreject':				{ 'surfaceintegrator': 'distributedpath' },
		'diffuserefractreject_threshold':	{ 'diffuserefractreject': True, 'surfaceintegrator': 'distributedpath' },
		'glossyreflectreject':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyreflectreject_threshold':	{ 'glossyreflectreject': True, 'surfaceintegrator': 'distributedpath' },
		'glossyrefractreject':				{ 'surfaceintegrator': 'distributedpath' },
		'glossyrefractreject_threshold':	{ 'glossyrefractreject': True, 'surfaceintegrator': 'distributedpath' },
		
		# epm
		'maxphotondepth':					{ 'surfaceintegrator': 'exphotonmap' },
		'directphotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'causticphotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'indirectphotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'radiancephotons':					{ 'surfaceintegrator': 'exphotonmap' },
		'nphotonsused':						{ 'surfaceintegrator': 'exphotonmap' },
		'maxphotondist':					{ 'surfaceintegrator': 'exphotonmap' },
		'finalgather':						{ 'surfaceintegrator': 'exphotonmap' },
		'finalgathersamples':				{ 'finalgather': True, 'surfaceintegrator': 'exphotonmap' },
		'gatherangle':						{ 'finalgather': True, 'surfaceintegrator': 'exphotonmap' },
		'renderingmode':					{ 'surfaceintegrator': 'exphotonmap' },
		'rrstrategy':						{ 'surfaceintegrator': O(['exphotonmap', 'path']) },
		'rrcontinueprob':					{ 'surfaceintegrator': O(['exphotonmap', 'path']) },
		# epm advanced
		'distancethreshold':				{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'photonmapsfile':					{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enabledirect':					{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableradiancemap':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableindircaustic':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableindirdiffuse':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		'dbg_enableindirspecular':			{ 'advanced': True, 'surfaceintegrator': 'exphotonmap' },
		
		# igi
		'nsets':							{ 'surfaceintegrator': 'igi' },
		'nlights':							{ 'surfaceintegrator': 'igi' },
		'mindist':							{ 'surfaceintegrator': 'igi' },
		
		# path
		'includeenvironment':				{ 'surfaceintegrator': 'path' },
	}
	
	properties = [
		{
			'type': 'enum', 
			'attr': 'surfaceintegrator',
			'name': 'Surface Integrator',
			'description': 'Surface Integrator',
			'default': 'bidirectional',
			'items': [
				('bidirectional', 'Bi-Directional', 'bidirectional'),
				('path', 'Path', 'path'),
				('directlighting', 'Direct Lighting', 'directlighting'),
				('distributedpath', 'Distributed Path', 'distributedpath'),
				('igi', 'Instant Global Illumination', 'igi',),
				('exphotonmap', 'Ex-Photon Map', 'exphotonmap'),
			],
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'advanced',
			'name': 'Advanced',
			'description': 'Configure advanced integrator settings',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'lightstrategy',
			'name': 'Light Strategy',
			'description': 'Light Sampling Strategy',
			'default': 'auto',
			'items': [
				('auto', 'Auto', 'auto'),
				('one', 'One', 'one'),
				('all', 'All', 'all'),
				('importance', 'Importance', 'importance'),
				('powerimp', 'Power', 'powerimp'),
				('allpowerimp', 'All Power', 'allpowerimp'),
				('logpowerimp', 'Log Power', 'logpowerimp')
			],
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'eyedepth',
			'name': 'Eye Depth',
			'description': 'Max recursion depth for ray casting from eye',
			'default': 16,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'int', 
			'attr': 'lightdepth',
			'name': 'Light Depth',
			'description': 'Max recursion depth for ray casting from light',
			'default': 16,
			'min': 0,
			'max': 2048,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'eyerrthreshold',
			'name': 'Eye RR Threshold',
			'default': 0.0,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'lightrrthreshold',
			'name': 'Light RR Threshold',
			'default': 0.0,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'maxdepth',
			'name': 'Max. depth',
			'default': 8,
			'save_in_preset': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_direct',
			'name': 'Direct light sampling',
		},
		{
			'type': 'bool',
			'attr': 'directsampleall',
			'name': 'Sample all',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'directsamples',
			'name': 'Samples',
			'default': 1,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'directdiffuse',
			'name': 'Diffuse',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'directglossy',
			'name': 'Glossy',
			'default': True,
			'save_in_preset': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_indirect',
			'name': 'Indirect light sampling',
		},
		{
			'type': 'bool',
			'attr': 'indirectsampleall',
			'name': 'Sample all',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'indirectsamples',
			'name': 'Samples',
			'default': 1,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'indirectdiffuse',
			'name': 'Diffuse',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'indirectglossy',
			'name': 'Glossy',
			'default': True,
			'save_in_preset': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_diffuse',
			'name': 'Diffuse settings',
		},
		{
			'type': 'int',
			'attr': 'diffusereflectdepth',
			'name': 'Reflection depth',
			'default': 3,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'diffusereflectsamples',
			'name': 'Reflection samples',
			'default': 1,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'diffuserefractdepth',
			'name': 'Refraction depth',
			'default': 5,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'diffuserefractsamples',
			'name': 'Refraction samples',
			'default': 1,
			'save_in_preset': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_glossy',
			'name': 'Glossy settings',
		},
		{
			'type': 'int',
			'attr': 'glossyreflectdepth',
			'name': 'Reflection depth',
			'default': 2,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'glossyreflectsamples',
			'name': 'Reflection samples',
			'default': 1,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'glossyrefractdepth',
			'name': 'Refraction depth',
			'default': 5,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'glossyrefractsamples',
			'name': 'Refraction samples',
			'default': 1,
			'save_in_preset': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_specular',
			'name': 'Specular settings',
		},
		{
			'type': 'int',
			'attr': 'specularreflectdepth',
			'name': 'Reflection depth',
			'default': 3,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'specularrefractdepth',
			'name': 'Refraction depth',
			'default': 5,
			'save_in_preset': True
		},
		
		{
			'type': 'text',
			'attr': 'lbl_rejection',
			'name': 'Rejection settings',
		},
		{
			'type': 'bool',
			'attr': 'diffusereflectreject',
			'name': 'Diffuse reflection reject',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'diffusereflectreject_threshold',
			'name': 'Threshold',
			'default': 10.0,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'diffuserefractreject',
			'name': 'Diffuse refraction reject',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'diffuserefractreject_threshold',
			'name': 'Threshold',
			'default': 10.0,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'glossyreflectreject',
			'name': 'Glossy reflection reject',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'glossyreflectreject_threshold',
			'name': 'Threshold',
			'default': 10.0,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'glossyrefractreject',
			'name': 'Glossy refraction reject',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'glossyrefractreject_threshold',
			'name': 'Threshold',
			'default': 10.0,
			'save_in_preset': True
		},
		
		{
			'type': 'int',
			'attr': 'maxphotondepth',
			'name': 'Max. photon depth',
			'default': 10,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'directphotons',
			'name': 'Direct photons',
			'default': 1000000,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'causticphotons',
			'name': 'Caustic photons',
			'default': 20000,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'indirectphotons',
			'name': 'Indirect photons',
			'default': 200000,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'radiancephotons',
			'name': 'Radiance photons',
			'default': 200000,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'nphotonsused',
			'name': 'Number of photons used',
			'default': 50,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'maxphotondist',
			'name': 'Max. photon distance',
			'default': 0.1,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'finalgather',
			'name': 'Final Gather',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'finalgathersamples',
			'name': 'Final gather samples',
			'default': 32,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'gatherangle',
			'name': 'Gather angle',
			'default': 10.0,
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'renderingmode',
			'name': 'Rendering mode',
			'default': 'directlighting',
			'items': [
				('directlighting', 'directlighting', 'directlighting'),
				('path', 'path', 'path'),
			],
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'distancethreshold',
			'name': 'Distance threshold',
			'default': 0.75,
			'save_in_preset': True
		},
		{
			'type': 'string',
			'subtype': 'FILE_PATH',
			'attr': 'photonmapsfile',
			'name': 'Photonmaps file',
			'default': '',
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'dbg_enabledirect',
			'name': 'Debug: Enable direct',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableradiancemap',
			'name': 'Debug: Enable radiance map',
			'default': False,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableindircaustic',
			'name': 'Debug: Enable indirect caustics',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableindirdiffuse',
			'name': 'Debug: Enable indirect diffuse',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'dbg_enableindirspecular',
			'name': 'Debug: Enable indirect specular',
			'default': True,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'nsets',
			'name': 'Number of sets',
			'default': 4,
			'save_in_preset': True
		},
		{
			'type': 'int',
			'attr': 'nlights',
			'name': 'Number of lights',
			'default': 64,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'mindist',
			'name': 'Min. Distance',
			'default': 0.1,
			'save_in_preset': True
		},
		{
			'type': 'float',
			'attr': 'rrcontinueprob',
			'name': 'RR continue probability',
			'default': 0.65,
			'save_in_preset': True
		},
		{
			'type': 'enum',
			'attr': 'rrstrategy',
			'name': 'RR strategy',
			'default': 'efficiency',
			'items': [
				('efficiency', 'efficiency', 'efficiency'),
				('probability', 'probability', 'probability'),
				('none', 'none', 'none'),
			],
			'save_in_preset': True
		},
		{
			'type': 'bool',
			'attr': 'includeenvironment',
			'name': 'Include Environment',
			'default': True,
			'save_in_preset': True
		},
	]
	
	def api_output(self, engine_properties):
		'''
		Format this class's members into a LuxRender ParamSet
		
		Returns tuple
		'''
		
		params = ParamSet()
		
		if engine_properties.renderer == 'hybrid' and self.lightstrategy != 'one':
			LuxLog('Incompatible lightstrategy for Hybrid renderer. Changing to "One".')
			self.advanced = True
			self.lightstrategy = 'one'
		
		if self.surfaceintegrator == 'bidirectional':
			params.add_integer('eyedepth', self.eyedepth) \
				  .add_integer('lightdepth', self.lightdepth)
			if self.advanced:
				params.add_float('eyerrthreshold', self.eyerrthreshold)
				params.add_float('lightrrthreshold', self.lightrrthreshold)
		
		if self.surfaceintegrator == 'directlighting':
			params.add_integer('maxdepth', self.maxdepth)
		
		if self.surfaceintegrator == 'distributedpath':
			params.add_bool('directsampleall', self.directsampleall) \
				  .add_integer('directsamples', self.directsamples) \
				  .add_bool('directdiffuse', self.directdiffuse) \
				  .add_bool('directglossy', self.directglossy) \
				  .add_bool('indirectsampleall', self.indirectsampleall) \
				  .add_integer('indirectsamples', self.indirectsamples) \
				  .add_bool('indirectdiffuse', self.indirectdiffuse) \
				  .add_bool('indirectglossy', self.indirectglossy) \
				  .add_integer('diffusereflectdepth', self.diffusereflectdepth) \
				  .add_integer('diffusereflectsamples', self.diffusereflectsamples) \
				  .add_integer('diffuserefractdepth', self.diffuserefractdepth) \
				  .add_integer('diffuserefractsamples', self.diffuserefractsamples) \
				  .add_integer('glossyreflectdepth', self.glossyreflectdepth) \
				  .add_integer('glossyreflectsamples', self.glossyreflectsamples) \
				  .add_integer('glossyrefractdepth', self.glossyrefractdepth) \
				  .add_integer('glossyrefractsamples', self.glossyrefractsamples) \
				  .add_integer('specularreflectdepth', self.specularreflectdepth) \
				  .add_integer('specularrefractdepth', self.specularrefractdepth) \
				  .add_bool('diffusereflectreject', self.diffusereflectreject) \
				  .add_float('diffusereflectreject_threshold', self.diffusereflectreject_threshold) \
				  .add_bool('diffuserefractreject', self.diffuserefractreject) \
				  .add_float('diffuserefractreject_threshold', self.diffuserefractreject_threshold) \
				  .add_bool('glossyreflectreject', self.glossyreflectreject) \
				  .add_float('glossyreflectreject_threshold', self.glossyreflectreject_threshold) \
				  .add_bool('glossyrefractreject', self.glossyrefractreject) \
				  .add_float('glossyrefractreject_threshold', self.glossyrefractreject_threshold)
		
		if self.surfaceintegrator == 'exphotonmap':
			params.add_integer('maxdepth', self.maxdepth) \
				  .add_integer('maxphotondepth', self.maxphotondepth) \
				  .add_integer('directphotons', self.directphotons) \
				  .add_integer('causticphotons', self.causticphotons) \
				  .add_integer('indirectphotons', self.indirectphotons) \
				  .add_integer('radiancephotons', self.radiancephotons) \
				  .add_integer('nphotonsused', self.nphotonsused) \
				  .add_float('maxphotondist', self.maxphotondist) \
				  .add_bool('finalgather', self.finalgather) \
				  .add_integer('finalgathersamples', self.finalgathersamples) \
				  .add_string('renderingmode', self.renderingmode) \
				  .add_float('gatherangle', self.gatherangle) \
				  .add_string('rrstrategy', self.rrstrategy) \
				  .add_float('rrcontinueprob', self.rrcontinueprob)
			if self.advanced:
				params.add_float('distancethreshold', self.distancethreshold) \
					  .add_string('photonmapsfile', self.photonmapsfile) \
					  .add_bool('dbg_enabledirect', self.dbg_enabledirect) \
					  .add_bool('dbg_enableradiancemap', self.dbg_enableradiancemap) \
					  .add_bool('dbg_enableindircaustic', self.dbg_enableindircaustic) \
					  .add_bool('dbg_enableindirdiffuse', self.dbg_enableindirdiffuse) \
					  .add_bool('dbg_enableindirspecular', self.dbg_enableindirspecular)
		
		if self.surfaceintegrator == 'igi':
			params.add_integer('nsets', self.nsets) \
				  .add_integer('nlights', self.nlights) \
				  .add_integer('maxdepth', self.maxdepth) \
				  .add_float('mindist', self.mindist)
		
		if self.surfaceintegrator == 'path':
			params.add_integer('maxdepth', self.maxdepth) \
				  .add_float('rrcontinueprob', self.rrcontinueprob) \
				  .add_string('rrstrategy', self.rrstrategy) \
				  .add_bool('includeenvironment', self.includeenvironment)
		
		if self.advanced and self.surfaceintegrator != 'bidirectional':
			params.add_string('lightstrategy', self.lightstrategy)
		
		out = self.surfaceintegrator, params
		dbo('SURFACE INTEGRATOR', out)
		return out

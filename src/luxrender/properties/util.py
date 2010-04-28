'''
Created on 26 Apr 2010

@author: doug
'''

from ef.validate import Logic_AND as A, Logic_OR as O, Logic_Operator as OP

def has_property(parent_type, property_name):
	if parent_type == 'material':
		return has_material_property(property_name)
	elif parent_type == 'texture':
		return has_texture_property(property_name)
	
#------------------------------------------------------------------------------ 

def texture_property_translate(name):
	xlate = {
		'f_brickmodtex': 'brickmodtex',
		'f_brickrun': 'brickrun',
		'f_bricktex': 'bricktex',
		'f_mortartex': 'mortartex',
		'f_tex1': 'tex1',
		'f_tex2': 'tex2',
	}
	
	if name in xlate.keys():
		return xlate[name]
	else:
		return name

def texture_property_map():
	'''
	Refer to http://www.luxrender.net/static/textures-parameters.xhtml
	for contents of this mapping
	'''
	
	return {
		'A':				O(['sellmeier']),
		'aamode':			O(['checkerboard']),
		'amount':			O(['mix']),
		'B':				O(['sellmeier']),
		'brickbevel':		O(['brick']),
		'brickbond':		O(['brick']),
		'brickdepth':		O(['brick']),
		'brickheight':		O(['brick']),
		'brickmodtex':		O(['brick']),
		'brickrun':			O(['brick']),
		'bricktex':			O(['brick']),
		'brickwidth':		O(['brick']),
		'C':				O(['sellmeier']),
		'cauchya':			O(['cauchy']),
		'cauchyb':			O(['cauchy']),
		'channel':			O(['imagemap']),
		#'coltype': ,
		'data':				O(['irregulardata', 'regulardata']),
		'dimension':		O(['checkerboard']),
		'discardmipmaps':	O(['imagemap']),
		#'distamount': ,
		#'distmetric': ,
		'end':				O(['regulardata']),
		'energy':			O(['equalenergy', 'frequency', 'gaussian']),
		'filename':			O(['imagemap', 'tabulateddata', 'tabulatedfresnel']),
		'filtertype':		O(['imagemap']),
		#'flipxy': ,
		'freq':				O(['frequency']),
		'gain':				O(['imagemap']),
		'gamma':			O(['imagemap']),
		#'h': ,
		'index':			O(['cauchy']),
		'inside':			O(['dots']),
		#'lacu': ,
		'mapping':			O(['bilerp', 'checkerboard', 'dots', 'imagemap', 'uv']),
		'maxanisotropy':	O(['imagemap']),
		#'minkowsky_exp': ,
		'mortarsize':		O(['brick']),
		'mortartex':		O(['brick']),
		#'nabla': ,
		'name':				O(['lampspectrum', 'tabulatedfresnel']),
		#'noisebasis': ,
		#'noisebasis2': ,
		#'noisedepth': ,
		#'noisesize': ,
		'octaves':			O(['fbm', 'marble', 'wrinkled']),
		#'octs': ,
		#'offset': ,
		#'outscale': ,
		'outside':			O(['dots']),
		'phase':			O(['frequency']),
		'roughness':		O(['fbm', 'marble', 'wrinkled']),
		'scale':			O(['marble']),
		'start':			O(['regulardata']),
		'temperature':		O(['blackbody']),
		'tex1':				O(['checkerboard', 'mix', 'scale']),
		'tex2':				O(['checkerboard', 'mix', 'scale']),
		#'turbulence': ,
		#'type': ,
		'udelta':			O(['bilerp', 'checkerboard', 'dots', 'imagemap', 'uv']),
		'uscale':			O(['bilerp', 'checkerboard', 'dots', 'imagemap', 'uv']),
		'v1':				O(['bilerp', 'checkerboard', 'dots', 'imagemap', 'uv']),
		'v2':				O(['bilerp', 'checkerboard', 'dots', 'imagemap', 'uv']),
		'v00':				O(['bilerp']),
		'v01':				O(['bilerp']),
		'v10':				O(['bilerp']),
		'v11':				O(['bilerp']),
		'value':			O(['constant']),
		'variation':		O(['marble']),
		'vdelta':			O(['bilerp', 'checkerboard', 'dots', 'imagemap', 'uv']),
		'vscale':			O(['bilerp', 'checkerboard', 'dots', 'imagemap', 'uv']),
		#'w1': ,
		#'w2': ,
		#'w3': ,
		#'w4': ,
		'wavelength':		O(['gaussian']),
		'wavelengths':		O(['irregulardata']),
		'width':			O(['gaussian']),
		'wrap':				O(['imagemap']),
		
	}

def has_texture_property(property_name):
	
	property_name = texture_property_translate(property_name)
	return texture_property_map()[property_name]

#------------------------------------------------------------------------------ 

def material_property_map():
	'''
	Refer to http://www.luxrender.net/static/materials-parameters.xhtml
	for contents of this mapping
	'''
	
	return {
		'amount':			O(['mix']),
		'architectural':	O(['glass', 'glass2']),
		'bumpmap':			O(['carpaint', 'glass', 'glass2', 'glossy_lossy', 'glossy', 'matte', 'mattetranslucent', 'metal', 'mirror', 'roughglass', 'shinymetal']),
		'cauchyb':			O(['glass', 'roughglass']),
		'd':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'dispersion':		O(['glass2']),
		'film':				O(['glass', 'mirror', 'shinymetal']),
		'filmindex':		O(['glass', 'mirror', 'shinymetal']),
		'index':			O(['glass', 'glossy_lossy', 'glossy', 'roughglass']),
		'Ka':				O(['carpaint', 'glossy_lossy', 'glossy']),
		'Kd':				O(['carpaint', 'glossy_lossy', 'glossy', 'matte']),
		'Kr':				O(['glass', 'mattetranslucent', 'mirror', 'roughglass', 'shinymetal']),
		'Ks':				O(['glossy_lossy', 'glossy', 'shinymetal']),
		'Ks1':				O(['carpaint']),
		'Ks2':				O(['carpaint']),
		'Ks3':				O(['carpaint']),
		'Kt':				O(['glass', 'mattetranslucent', 'roughglass']),
		'M1':				O(['carpaint']),
		'M2':				O(['carpaint']),
		'M3':				O(['carpaint']),
		'name':				O(['carpaint', 'metal']),
		'namedmaterial1':	O(['mix']),
		'namedmaterial2':	O(['mix']),
		'R1':				O(['carpaint']),
		'R2':				O(['carpaint']),
		'R3':				O(['carpaint']),
		'sigma':			O(['matte', 'mattetranslucent']),
		'uroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
		'vroughness':		O(['glossy_lossy', 'glossy', 'metal', 'roughglass', 'shinymetal']),
	}
	
def has_material_property(property_name):
	return material_property_map()[property_name]

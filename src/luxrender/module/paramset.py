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
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#

# ref core/paramset.cpp

'''
At some point, I really hope that this lot is replaced with something smarter - dougal2
'''

FLOAT = [
    'B', 'C',
    'a', 'aconst', 'alpha', 'aperture', 'aperture_diameter',
    'b', 'baseflatness', 'bconst', 'brickdepth', 'brickheight', 'brickwidth', 'bright', 'bumpmapsampledistance', 'burn',
    'cconst', 'compo_override_alpha_value', 'coneangle', 'conedeltaangle', 'contrast', 'contrast_ywa', 'cropwindow',
    'dconst', 'diffusereflectreject_threshold', 'distamount', 'distancethreshold', 'dmoffset', 'dmscale',
    'econst', 'efficacy', 'emptybonus', 'end', 'energy', 'exposure', 'eyerrthreshold',
    'filmdiag', 'filmdistance', 'focaldistance', 'fov', 'frameaspectratio', 'freq', 'fstop', 'fullsweepthreshold',
    'g', 'gain', 'gamma', 'gatherangle', 'glossyreflectreject_threshold', 'glossyrefractreject_threshold',
    'h', 'height', 'hither',
    'innerradius',
    'lacu', 'largemutationprob', 'lensradius', 'lightrrthreshold', 'linear_exposure', 'linear_fstop', 'linear_gamma', 'linear_sensitivity',
    'major_radius', 'maxY', 'maxanisotropy', 'maxphotondist', 'micromutationprob', 'mindist', 'minkovsky_exp', 'minorradius', 'mortarsize', 'mutationtange',
    'nabla', 'noiseoffset', 'noisescale', 'noisesize',
    'octs', 'offset', 'omega', 'outscale',
    'phimax', 'postscale', 'power', 'prescale',
    'radius', 'reinhard_burn', 'reinhard_postscale', 'reinhard_prescale', 'relsize', 'roughness', 'rrcontinueprob',
    'scale', 'sensitivity', 'sharpness', 'shutterclose', 'shutteropen', 'spheresize', 'start', 'stepsize',
    'tau', 'temperature', 'thetamax', 'thetamix', 'turbidity', 'turbulance',
    'u0', 'u1', 'udelta', 'uscale',
    'v0', 'v00', 'v01', 'v1', 'v11', 'value', 'variability', 'variation', 'vdelta', 'vscale',
    'w1', 'w2', 'w3', 'w4', 'wavelength', 'width',
    'xwidth',
    'yon', 'ywa', 'ywidth',
    'zmax', 'zmin'
]

INT = [
    'blades',
    'causticphotons', 'chainlength', 'coltype', 'costsamples',
    'diffusereflectdepth', 'diffusereflectsamples', 'diffuserefractdepth', 'diffuserefractsamples', 'dimension', 'directphotons', 'directsamples', 'discardmipmaps', 'displayinterval',
    'eyedepth',
    'finalgathersamples',
    'glossyreflectdepth', 'glossyreflectsamples', 'glossyrefractdepth', 'glossyrefractsamples',
    'haltspp',
    'indirectphotons', 'indirectsamples', 'initsamples', 'intersectcost',
    'lightdepth',
    'maxconsecrejects', 'maxdepth', 'maxphotondepth', 'maxprims', 'maxprimsperleaf',
    'nlevels', 'nlights', 'noisedepth', 'nphotonused', 'nsamples', 'nsets', 'nsubdivlevels', 'nu', 'nv', 'nx', 'ny', 'nz',
    'octaves',
    'pixelsamples', 'power',
    'radiancephotons', 'reject_warmup',
    'skipfactor', 'specularreflectdepth', 'specularrefractdepth', 'spheres',
    'traversalcost', 'treetype',
    'uorder',
    'vorder',
    'writeinterval',
    'xresolution', 'xsamples',
    'yresolution', 'ysamples'
]

FLOAT_VEC = [
    'Pw', 'Pz',
    'density',
    'screenwindow',
    'st',
    'uknots', 'uv',
    'vknots'
]

INT_VEC = [
    'indices',
]

POINT = [
    'P',
    'from',
    'p0', 'p1', 'p2',
    'to'
]

NORMAL = [ 'N' ]

VEC = [
    'rotate',
    'scale', 'sundir',
    'translate',
    'updir',
    'v1', 'v2'
]

BOOL = [
    'architectural', 'autofocus',
    'compo_override_alpha', 'compo_use_key', 'compo_visible_emission', 'compo_visible_indirect_emission', 'compo_visible_indirect_material', 'compo_visible_material',
    'dbg_enabledirect', 'dbg_enableindircaustic', 'dbg_enableindirdiffuse', 'dbg_enableindirspecular', 'dbg_enableradiancemap', 'debug', 'diffusereflectreject', 'diffuserefractreject', 'directdiffuse', 'directglossy', 'directsampleall', 'dmnormalsmooth', 'dmsharpboundary',
    'finalgather', 'flipxy', 'flipz',
    'glossyreflectdirect', 'glossyrefractdirect',
    'includeenvironment', 'indirectdiffuse', 'indirectglossy', 'indirectsampleall', 
    'premultiplyalpha',
    'refineimmediately', 'restart_resume_flm',
    'smooth',
    'usevariance',
    'write_exr', 'write_exr_ZBuf', 'write_exr_applyimaging', 'write_exr_gamutclamp', 'write_exr_halftype', 'write_png', 'write_png_16bit', 'write_png_ZBuf', 'write_png_gamutclamp', 'write_resume_flm', 'write_tga', 'write_tga_ZBuf', 'write_tga_gamutclamp'
]

STRING = [
    'aamode', 'acceltype',
    'basesampler',
    'displacementmap', 'distmetric', 'distribution',
    'endtransform',
    'filename',
    'filtertype',
    'iesname',
    'ldr_clamp_method', 'lightstrategy',
    'mapname', 'mapping',
    'name', 'namedmaterial1', 'namedmaterial2',
    'noisebasis', 'noisebasis2', 'noisetype',
    'photonmapsfile', 'pixelsampler',
    'quadtype',
    'renderingmode', 'rrstrategy',
    'scheme', 'shutterdistribution', 'specfile', 'strategy', 'subdivscheme',
    'tonemapkernel', 'tritype', 'type',
    'wrap', 'write_exr_channels', 'write_exr_compressiontype', 'write_exr_zbuf_normalization', 'write_png_channels', 'write_pxr_zbuf_normalization', 'write_tga_channels', 'write_tga_zbuf_normalization',
    
]

TEXTURE = [
    'Ka', 'Kd', 'Kr', 'Ks', 'Ks1', 'Ks2', 'Ks3', 'Kt',
    'L',
    'M1', 'M2', 'M3',
    'R1', 'R2', 'R3',
    'amount',
    'bricktex', 'bumpmap',
    'cauchyb',
    'd',
    'film', 'filmindex',
    'index', 'inside',
    'mortartex',
    'outside',
    'sigma',
    'tex1', 'tex2',
    'uroughness',
    'vroughness'
]

COLOR = [
    'L', 'Le',
    'compo_key_color',
    'sigma_a', 'sigma_s',
    'v00', 'v01', 'v10', 'v11', 'value'
]
'''
Created on 10 Apr 2010

@author: doug
'''

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
    'scale', 'screenwindow', 'sensitivity', 'sharpness', 'shutterclose', 'shutteropen', 'spheresize', 'start', 'stepsize',
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
    'st',
    'uknots', 'uv',
    'vknots'
]

INT_VEC = [
    'indices',
]

BOOL = [
    
]

STRING = [
    
]


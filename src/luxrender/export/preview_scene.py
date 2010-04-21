
from luxrender.export import ParamSet
from luxrender.export.film import resolution

def preview_scene_setup(scene, lux_context):
    
    HALTSPP = 512
    
    # Film
    xr, yr = resolution(scene)
    
    film_params = ParamSet() \
        .add_integer('xresolution', int(xr)) \
        .add_integer('yresolution', int(yr)) \
        .add_string('filename', 'default') \
        .add_bool('write_exr', False) \
        .add_bool('write_png', True) \
        .add_bool('write_tga', False) \
        .add_bool('write_resume_flm', False) \
        .add_integer('displayinterval', 3) \
        .add_integer('writeinterval', 3) \
        .add_integer('haltspp', HALTSPP) \
        .add_string('tonemapkernel', 'reinhard')
    lux_context.film('fleximage', film_params)
    
    # Pixel Filter
#    pixelfilter_params = ParamSet() \
#        .add_float('xwidth', 1.5) \
#        .add_float('ywidth', 1.5) \
#        .add_float('B', 0.333) \
#        .add_float('C', 0.333) \
#        .add_bool('supersample', True)
#    lux_context.pixelFilter('mitchell', pixelfilter_params)
    
    # Sampler
    sampler_params = ParamSet() \
        .add_string('pixelsampler', 'hilbert') \
        .add_integer('pixelsamples', 2)
    lux_context.sampler('lowdiscrepancy', sampler_params)
    
    # Surface Integrator
    surfaceintegrator_params = ParamSet() \
        .add_integer('directsamples', 1) \
        .add_integer('diffusereflectdepth', 0) \
        .add_integer('diffusereflectsamples', 0) \
        .add_integer('diffuserefractdepth', 0) \
        .add_integer('diffuserefractsamples', 0) \
        .add_integer('glossyreflectdepth', 0) \
        .add_integer('glossyreflectsamples', 0) \
        .add_integer('glossyrefractdepth', 0) \
        .add_integer('glossyrefractsamples', 0) \
        .add_integer('specularreflectdepth', 1) \
        .add_integer('specularrefractdepth', 1)
    lux_context.surfaceIntegrator('distributedpath', surfaceintegrator_params)
    
def preview_scene_lights(lux_context):
    # Light
#    lux_context.transformBegin()
#    lux_context.transform([
#        -0.549843,  0.655945,   0.517116, 0.000000,
#        -0.733248, -0.082559,  -0.674931, 0.000000,
#        -0.400025, -0.750280,   0.526365, 0.000000,
#        -5.725639, -13.646054, 10.546618, 1.000000
#    ])
#    light_params = ParamSet() \
#        .add_color('L', (1.0,1.0,1.0)) \
#        .add_point('from', (0.0,0.0,0.0)) \
#        .add_point('to', (0.0, 0.0, -1.0)) \
#        .add_float('coneangle', 25) \
#        .add_float('conedeltaangle', 13.34) \
#        .add_float('gain', 5)
#    lux_context.lightSource('spot', light_params)
#    lux_context.transformEnd()
    lux_context.attributeBegin()
    lux_context.lightSource('sunsky', ParamSet().add_vector('sundir', (-0.04,0.89,0.44)))
    lux_context.attributeEnd()

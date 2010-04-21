
from luxrender.export import ParamSet
from luxrender.export.film import resolution

def preview_scene_setup(scene, lux_context):
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
        .add_integer('haltspp', 64) \
        .add_string('tonemapkernel', 'reinhard') \
        .add_integer('reject_warmup', 64)
        
    lux_context.film('fleximage', film_params)
    
    pixelfilter_params = ParamSet() \
        .add_float('xwidth', 1.5) \
        .add_float('ywidth', 1.5) \
        .add_float('B', 0.333) \
        .add_float('C', 0.333) \
        .add_bool('supersample', True)
        
    lux_context.pixelFilter('mitchell', pixelfilter_params)
    
    sampler_params = ParamSet() \
        .add_string('pixelsampler', 'hilbert') \
        .add_integer('pixelsamples', 64)
        
    lux_context.sampler('lowdiscrepancy', sampler_params)
    
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
